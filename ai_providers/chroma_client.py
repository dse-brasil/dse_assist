"""
Chroma Client — Conexão singleton com o Chroma Cloud.

Usado pelo pipeline de ingestão (migration.py) e futuramente
pelo RAGProvider no bot Discord.

Variáveis de ambiente necessárias (.env):
    CHROMA_HOST      → api.trychroma.com
    CHROMA_API_KEY   → chave de autenticação
    CHROMA_TENANT    → UUID do tenant
    CHROMA_DATABASE  → nome do banco (ex: dse)
"""

import os
from typing import Optional
import chromadb
from dotenv import load_dotenv

load_dotenv()

# ─── Nomes de coleções padrão ─────────────────────────────────────────────────
COLLECTION_KNOWLEDGE = "dse_knowledge_base"   # artigos, docs, tutoriais
COLLECTION_DISCORD   = "dse_discord_history"  # histórico curado do Discord
COLLECTION_RESEARCH  = "dse_research"         # papers acadêmicos

_client: Optional[chromadb.CloudClient] = None


def get_client() -> chromadb.CloudClient:
    """
    Retorna o cliente Chroma Cloud (singleton).
    Lança ValueError se as credenciais não estiverem configuradas.
    """
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("CHROMA_API_KEY", "").strip()
    tenant  = os.getenv("CHROMA_TENANT", "").strip()
    database = os.getenv("CHROMA_DATABASE", "dse").strip()

    if not api_key or api_key == "sua_api_key_aqui":
        raise ValueError(
            "CHROMA_API_KEY nao configurada no .env\n"
            "Obtenha em: https://trychroma.com → Dashboard → API Keys"
        )
    if not tenant:
        raise ValueError("CHROMA_TENANT nao configurado no .env")

    _client = chromadb.CloudClient(
        tenant=tenant,
        database=database,
        api_key=api_key,
    )
    return _client


def get_or_create_collection(
    name: str,
    space: str = "cosine",
) -> chromadb.Collection:
    """
    Retorna (ou cria) uma coleção com configuração otimizada para RAG.

    Args:
        name:  Nome da coleção.
        space: Métrica de distância — 'cosine' (padrão), 'l2' ou 'ip'.
    """
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": space},
    )
