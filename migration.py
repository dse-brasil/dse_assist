"""
Migration / Ingestão RAG — Pipeline de dados para o DSE Bot.

Funcionalidades:
  - Conexão com Chroma Cloud (via ai_providers/chroma_client.py)
  - Chunking line-based respeitando o limite de 16 KiB do Chroma
  - Metadados ricos para deduplicação e GroupBy na busca
  - Suporte a múltiplas fontes: arquivos .txt/.md, texto raw, URLs futuras
  - CLI simples para ingestão no terminal

Uso:
  python migration.py --source arquivo.md --collection dse_knowledge_base
  python migration.py --source pasta/docs/ --collection dse_knowledge_base
  python migration.py --test   (roda com documento de exemplo)

Requisitos:
  pip install chromadb python-dotenv
"""

import os
import sys
import uuid
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

# Fix encoding terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Importa o cliente Chroma compartilhado
sys.path.insert(0, str(Path(__file__).parent))
from ai_providers.chroma_client import get_client, get_or_create_collection, COLLECTION_KNOWLEDGE

load_dotenv()

# ─── Constantes ───────────────────────────────────────────────────────────────

CHUNK_MAX_BYTES   = 15_000   # margem de segurança abaixo dos 16 KiB do Chroma
CHUNK_OVERLAP_LINES = 2      # linhas de overlap entre chunks para manter contexto
SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".rst", ".csv"}


# ─── 1. Chunking Line-Based ───────────────────────────────────────────────────

def chunk_text_by_lines(
    text: str,
    max_bytes: int = CHUNK_MAX_BYTES,
    overlap_lines: int = CHUNK_OVERLAP_LINES,
) -> list[str]:
    """
    Divide texto em chunks respeitando o limite de bytes do Chroma.

    Estratégia:
      - Divide por linhas (preserva estrutura de parágrafos/código)
      - Respeita max_bytes medido em UTF-8 (correto para textos com acentos)
      - Adiciona overlap de N linhas entre chunks para manter continuidade

    Args:
        text:         Texto bruto a ser dividido.
        max_bytes:    Limite máximo em bytes por chunk (padrão: 15.000).
        overlap_lines: Linhas repetidas entre chunks consecutivos.

    Returns:
        Lista de strings (chunks prontos para inserção).
    """
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current_lines: list[str] = []
    current_bytes = 0

    for line in lines:
        line_bytes = len(line.encode("utf-8"))

        # Linha sozinha já excede o limite → força chunk dela isolada
        if line_bytes > max_bytes:
            if current_lines:
                chunks.append("".join(current_lines).strip())
            # Divide a linha gigante por caractere (edge case)
            for i in range(0, len(line), max_bytes // 4):
                chunks.append(line[i:i + max_bytes // 4].strip())
            current_lines = []
            current_bytes = 0
            continue

        if current_bytes + line_bytes > max_bytes:
            # Salva chunk atual
            chunks.append("".join(current_lines).strip())
            # Overlap: carrega as últimas N linhas no próximo chunk
            current_lines = current_lines[-overlap_lines:] if overlap_lines else []
            current_bytes = sum(len(l.encode("utf-8")) for l in current_lines)

        current_lines.append(line)
        current_bytes += line_bytes

    # Último chunk
    if current_lines:
        last = "".join(current_lines).strip()
        if last:
            chunks.append(last)

    return [c for c in chunks if c]  # remove vazios


# ─── 2. Fingerprint (deduplicação) ────────────────────────────────────────────

def content_hash(text: str) -> str:
    """SHA-256 do conteúdo — usado para evitar reingestão de documentos idênticos."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ─── 3. Ingestão de um Documento ─────────────────────────────────────────────

def ingest_document(
    collection_name: str,
    document_text: str,
    source_name: str,
    doc_type: str = "text",
    tags: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict:
    """
    Processa e insere um documento na coleção Chroma.

    Fluxo:
      1. Gera document_id único (UUID + hash de conteúdo)
      2. Aplica chunking line-based
      3. Injeta metadados ricos em cada chunk
      4. Upsert no Chroma (suporta reingestão)

    Args:
        collection_name: Nome da coleção alvo.
        document_text:   Texto completo do documento.
        source_name:     Identificador da fonte (nome do arquivo, URL, etc.).
        doc_type:        Categoria: 'article', 'code', 'discord', 'research', 'text'.
        tags:            Lista de tags para filtragem posterior.
        overwrite:       Se True, remove versão anterior antes de inserir.

    Returns:
        Dict com estatísticas da ingestão.
    """
    client = get_client()
    collection = get_or_create_collection(collection_name)

    # IDs consistentes por fonte: permite overwrite sem duplicatas
    fingerprint = content_hash(document_text)
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, source_name))

    # Verifica se já existe (pelo source_name nos metadados)
    if not overwrite:
        existing = collection.get(
            where={"source": source_name},
            limit=1,
            include=[],
        )
        if existing["ids"]:
            print(f"  [SKIP] '{source_name}' ja esta indexado ({len(existing['ids'])} chunks).")
            print(f"         Use --overwrite para forcar reingestao.")
            return {"status": "skipped", "source": source_name}

    # Remove versão anterior se overwrite
    if overwrite:
        try:
            collection.delete(where={"source": source_name})
            print(f"  [DEL]  Versao anterior de '{source_name}' removida.")
        except Exception:
            pass  # Pode não existir ainda

    # Chunking
    chunks = chunk_text_by_lines(document_text)
    if not chunks:
        print(f"  [WARN] '{source_name}' resultou em 0 chunks. Verifique o conteudo.")
        return {"status": "empty", "source": source_name}

    ingested_at = datetime.now(timezone.utc).isoformat()

    ids, docs, metas = [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(f"{document_id}_c{i:04d}")
        docs.append(chunk)
        metas.append({
            # Identidade — usados no GroupBy durante a busca RAG
            "document_id":  document_id,
            "chunk_index":  i,
            "total_chunks": len(chunks),
            # Fonte e classificação
            "source":       source_name,
            "doc_type":     doc_type,
            "tags":         ",".join(tags or []),
            "fingerprint":  fingerprint,
            # Auditoria
            "ingested_at":  ingested_at,
            "chunk_bytes":  len(chunk.encode("utf-8")),
        })

    # Upsert em lotes de 100 (limite recomendado pelo Chroma Cloud)
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=docs[start:end],
            metadatas=metas[start:end],
        )

    stats = {
        "status":      "ok",
        "source":      source_name,
        "document_id": document_id,
        "chunks":      len(chunks),
        "collection":  collection_name,
        "fingerprint": fingerprint,
    }
    print(f"  [OK]  '{source_name}' -> {len(chunks)} chunks inseridos em '{collection_name}'")
    return stats


# ─── 4. Ingestão de Arquivos / Pastas ────────────────────────────────────────

def ingest_file(
    filepath: str | Path,
    collection_name: str = COLLECTION_KNOWLEDGE,
    doc_type: str = "text",
    tags: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict:
    """Lê um arquivo e o ingere no Chroma."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {filepath}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"  [WARN] Extensao '{path.suffix}' nao suportada. Tentando assim mesmo...")

    text = path.read_text(encoding="utf-8", errors="replace")
    return ingest_document(
        collection_name=collection_name,
        document_text=text,
        source_name=str(path.name),
        doc_type=doc_type,
        tags=tags or [path.suffix.lstrip(".")],
        overwrite=overwrite,
    )


def ingest_folder(
    folder: str | Path,
    collection_name: str = COLLECTION_KNOWLEDGE,
    doc_type: str = "text",
    overwrite: bool = False,
    recursive: bool = True,
) -> list[dict]:
    """Ingere todos os arquivos suportados de uma pasta."""
    folder = Path(folder)
    pattern = "**/*" if recursive else "*"
    files = [
        f for f in folder.glob(pattern)
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"  [WARN] Nenhum arquivo suportado encontrado em '{folder}'")
        return []

    print(f"\nIngerindo {len(files)} arquivos de '{folder}'...")
    results = []
    for f in sorted(files):
        try:
            result = ingest_file(f, collection_name, doc_type, overwrite=overwrite)
            results.append(result)
        except Exception as e:
            print(f"  [ERRO] '{f.name}': {e}")
            results.append({"status": "error", "source": str(f), "error": str(e)})
    return results


# ─── 5. Consulta de Teste (Sanity Check) ─────────────────────────────────────

def query_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 3,
) -> None:
    """Faz uma busca simples para validar a ingestão."""
    collection = get_or_create_collection(collection_name)
    results = collection.query(
        query_texts=[query_text],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    print(f"\n[QUERY] '{query_text}'")
    print(f"[COLLECTION] {collection_name} ({collection.count()} chunks totais)")
    print("-" * 60)
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        print(f"\nResultado {i+1}  |  Similaridade: {1 - dist:.3f}")
        print(f"Fonte: {meta.get('source')} | Chunk {meta.get('chunk_index')}/{meta.get('total_chunks')}")
        print(f"Trecho: {doc[:200]}...")
    print("-" * 60)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def run_test():
    """Documento de exemplo para validar a conexão e o pipeline."""
    print("\n[TEST] Rodando ingestao de documento de exemplo...")

    sample = """
    # Introdução ao Machine Learning

    Machine Learning (ML) é uma subárea da Inteligência Artificial que permite
    que sistemas aprendam com dados sem serem explicitamente programados para
    cada tarefa.

    ## Principais Algoritmos

    ### Aprendizado Supervisionado
    - Regressão Linear e Logística
    - Árvores de Decisão e Random Forest
    - Support Vector Machines (SVM)
    - Redes Neurais e Deep Learning

    ### Aprendizado Não Supervisionado
    - K-Means Clustering
    - DBSCAN
    - PCA (Análise de Componentes Principais)
    - Autoencoders

    ## Bibliotecas Python para DS/ML
    As principais ferramentas do ecossistema Python para Data Science são:
    - **pandas**: manipulação e análise de dados tabulares
    - **numpy**: computação numérica eficiente com arrays
    - **scikit-learn**: algoritmos de ML prontos para uso
    - **matplotlib/seaborn**: visualização de dados
    - **PyTorch/TensorFlow**: deep learning e redes neurais

    ## Pipeline Típico de ML
    1. Coleta e exploração de dados (EDA)
    2. Limpeza e pré-processamento (Feature Engineering)
    3. Divisão treino/validação/teste
    4. Treinamento e ajuste de hiperparâmetros
    5. Avaliação com métricas (Accuracy, F1, AUC-ROC)
    6. Deploy e monitoramento (MLOps)

    A comunidade Data Science Enthusiasts reúne profissionais e entusiastas
    interessados em aprender e aplicar essas técnicas em projetos reais.
    """ * 3  # Multiplica para testar chunking

    result = ingest_document(
        collection_name=COLLECTION_KNOWLEDGE,
        document_text=sample,
        source_name="intro_machine_learning_test.md",
        doc_type="article",
        tags=["ml", "introducao", "python", "test"],
        overwrite=True,
    )

    if result["status"] == "ok":
        print("\n[TEST] Validando busca...")
        query_collection(
            collection_name=COLLECTION_KNOWLEDGE,
            query_text="quais são os principais algoritmos de machine learning?",
            n_results=2,
        )
        print("\n[TEST] Pipeline RAG funcionando corretamente!")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="DSE Bot — Pipeline de Ingestao RAG para Chroma Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python migration.py --test
  python migration.py --source docs/artigo.md
  python migration.py --source docs/artigo.md --collection dse_research --type research
  python migration.py --source docs/ --recursive
  python migration.py --query "o que e overfitting?" --collection dse_knowledge_base
        """,
    )
    parser.add_argument("--source",     help="Arquivo ou pasta para ingerir")
    parser.add_argument("--collection", default=COLLECTION_KNOWLEDGE, help="Nome da colecao Chroma")
    parser.add_argument("--type",       default="text",   help="Tipo do doc: text, article, code, discord, research")
    parser.add_argument("--tags",       default="",       help="Tags separadas por virgula")
    parser.add_argument("--overwrite",  action="store_true", help="Reingerir mesmo se ja existir")
    parser.add_argument("--recursive",  action="store_true", help="Incluir subpastas")
    parser.add_argument("--query",      help="Testar busca na colecao")
    parser.add_argument("--test",       action="store_true", help="Roda ingestao de exemplo")

    args = parser.parse_args()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    print("=" * 60)
    print("  DSE Bot — Pipeline de Ingestao RAG")
    print("  Chroma Cloud:", os.getenv("CHROMA_DATABASE", "dse"))
    print("=" * 60)

    try:
        if args.test:
            run_test()

        elif args.query:
            query_collection(args.collection, args.query)

        elif args.source:
            path = Path(args.source)
            if path.is_dir():
                results = ingest_folder(
                    folder=path,
                    collection_name=args.collection,
                    doc_type=args.type,
                    overwrite=args.overwrite,
                    recursive=args.recursive,
                )
                ok = sum(1 for r in results if r.get("status") == "ok")
                print(f"\n[DONE] {ok}/{len(results)} documentos ingeridos com sucesso.")
            else:
                ingest_file(
                    filepath=path,
                    collection_name=args.collection,
                    doc_type=args.type,
                    tags=tags,
                    overwrite=args.overwrite,
                )
        else:
            parser.print_help()

    except ValueError as e:
        print(f"\n[ERRO] Configuracao: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
