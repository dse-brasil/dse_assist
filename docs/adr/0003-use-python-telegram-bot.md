# ADR 0003: Integração do Canal de Mensageria Telegram via python-telegram-bot

## Status
Aceito

## Data
2026-06-13

## Contexto
Para expandir o alcance da comunidade **Data Science Enthusiasts (DSE)**, necessitamos de uma presença multiplataforma onde o bot consiga atuar não apenas no Discord, mas também em grupos e chats diretos do Telegram. A integração deve prover suporte a respostas inteligentes baseadas em RAG, interações por botões inline (Roadmaps e Quizzes) e auditoria de segurança centralizada.

## Alternativas Consideradas

* **Telethon ou Pyrogram:**
  * *Prós:* Baseados no protocolo MTProto nativo do Telegram. Permitem criar "Userbots" (contas de usuários simuladas por código) com alto controle de automação.
  * *Contras:* A configuração de chaves API (api_id e api_hash) é burocrática para o usuário final, e as dependências nativas de criptografia C/C++ podem causar problemas de compilação em sistemas Windows sem compiladores instalados.
* **aiogram:**
  * *Prós:* Framework moderno, assíncrono e muito popular para desenvolvimento de bots no Telegram.
  * *Contras:* Apresenta uma sintaxe de manipulação de filtros e states ligeiramente distinta das bibliotecas clássicas, exigindo um pouco mais de curva de adaptação para novos mantenedores iniciantes.

## Decisão
Decidimos utilizar a biblioteca oficial e atualizada **python-telegram-bot** (versão 20.0 ou superior).

## Justificativa
1. **Suporte Nativo a Asyncio:** A partir da versão 20.0, a biblioteca foi totalmente reescrita para rodar em cima do `asyncio`. Isso permite integrá-la ao loop de eventos do Discord bot sem a criação de novas threads (usando `asyncio.create_task(start_telegram_bot(bot))`).
2. **Polimorfismo de Inteligência Artificial:** Ao instanciarmos o bot do Telegram no mesmo processo, passamos a referência do objeto `bot.ai_provider` (que é o `RAGProvider` com segurança integrada). Isso garante que o Telegram herde de graça:
   * Busca RAG automática no Chroma.
   * Auditoria imutável criptográfica (`security_audit.jsonl`).
   * Prevenção ativa de injeção de prompt e Zero Trust RAG.
3. **Facilidade para Botões Inline:** O gerenciamento de `InlineKeyboardButton` e callbacks no `python-telegram-bot` é intuitivo, facilitando a criação de experiências ricas em interfaces de chat (como o quiz técnico e os roadmaps).

## Consequências
* **Positivas:** Redução drástica de código duplicado (aproveitamos 100% da inteligência e segurança do RAG do Discord), baixo consumo de processamento e facilidade para contribuir com comandos no arquivo `telegram_bot.py`.
* **Negativas:** Exige o gerenciamento de múltiplos tokens no arquivo `.env` (`DISCORD_TOKEN` e `TELEGRAM_TOKEN`), e a biblioteca `python-telegram-bot` é relativamente pesada em termos de dependências internas de rede.
