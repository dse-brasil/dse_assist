# ADR 0001: Utilização do ChromaDB como Banco Vetorial (RAG)

## Status
Aceito

## Data
2026-06-13

## Contexto
O **DSE.Assist** necessita de um mecanismo de busca semântica para recuperar informações da base de conhecimento da comunidade (Retrieval-Augmented Generation - RAG) e responder a dúvidas técnicas dos usuários. Além disso, precisamos salvar o histórico de perguntas e respostas para análise futura e auditoria de observabilidade.

## Alternativas Consideradas

* **FAISS (Facebook AI Similarity Search):**
  * *Prós:* Extremamente rápido, execução local e indexação eficiente.
  * *Contras:* Não gerencia metadados de forma relacional simples e não possui uma API de banco de dados nativa em nuvem integrada por padrão.
* **Weaviate ou Qdrant:**
  * *Prós:* Bancos de dados vetoriais corporativos completos com suporte nativo a nuvem.
  * *Contras:* Curva de aprendizado e configuração de infraestrutura inicial desproporcional para o escopo inicial do projeto.

## Decisão
Decidimos utilizar o **ChromaDB** (acessado localmente ou através do Chroma Cloud) como nosso banco vetorial.

## Justificativa
1. **Integração Python Nativa:** O SDK do ChromaDB integra-se perfeitamente em poucos minutos com o ecossistema Python do projeto.
2. **Gerenciamento Simples de Metadados:** Permite associar campos como `source`, `user_id`, `username`, `command` e `ingested_at` diretamente aos vetores, essencial para a validação de procedência do *Zero Trust RAG*.
3. **Escalabilidade Inicial:** O plano gratuito/inicial do Chroma Cloud atende plenamente ao volume da comunidade sem custos ou complexidade operacional.

## Consequências
* **Positivas:** Ingestão rápida via `migration.py` e consultas semânticas diretas e limpas no provedor RAG.
* **Negativas:** Dependência da disponibilidade da API do Chroma Cloud para o funcionamento das respostas com contexto.
