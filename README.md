# DSE.Assist (DSE Bot) — IA, RAG e Segurança para Comunidades de Dados

![Versão](https://img.shields.io/badge/vers%C3%A3o-v1.2.0-blueviolet)

O **DSE.Assist** é o assistente oficial da comunidade **Data Science Enthusiasts (DSE)** no Discord. Desenvolvido em Python, o bot integra Inteligência Artificial avançada com busca semântica em banco vetorial (**RAG**) e implementa uma arquitetura robusta de **segurança cibernética** contra ataques modernos como *Prompt Injection* e *RAG Poisoning*.

---

## 🚀 Principais Funcionalidades

### 1. Interação Inteligente & Comandos Slash
O bot responde a comandos dinâmicos usando embeds interativos:
* **`/ask [pergunta]`**: Resposta direta a qualquer pergunta técnica sobre ciência de dados.
* **`/explain [conceito]`**: Explica conceitos de Machine Learning, Estatística ou Programação de forma didática com analogias.
* **`/code [pedido]`**: Gera código Python comentado e formatado seguindo as melhores práticas do ecossistema de DS.
* **`/dataset [tema]`**: Sugere datasets públicos e de alta qualidade (Kaggle, UCI, HuggingFace) para praticar.
* **`/roadmap [nível]`**: Gera um plano de estudos personalizado para níveis **Iniciante**, **Intermediário** ou **Avançado**.
* **`/quiz`**: Gera uma pergunta interativa de múltipla escolha com resposta oculta sob *spoiler* do Discord.

### 2. Conversa Livre em Canal Dedicado
No canal configurado (padrão `ia-comunidade`), o bot responde a qualquer mensagem sem a necessidade de comandos slash, agindo como um tutor de inteligência artificial sempre disponível.

### 3. Boas-Vindas Dinâmicas
Ao entrar no servidor, novos membros recebem um embed personalizado de boas-vindas com orientações de início.

### 4. Painel Web Administrativo (Dashboard)
Uma interface web de página única (SPA) com tema escuro e visual premium que permite monitorar e configurar o assistente em tempo real:
* **Uptime e Latência**: Monitoramento do tempo de atividade e tempo de resposta da API do Discord.
* **Métricas e Gráficos**: Série temporal interativa detalhando o volume de interações diárias (chamadas aprovadas, barradas por segurança e erros).
* **Hot Reload de Configurações**: Altere o modelo da IA (provedores Gemini, OpenAI e Groq), chaves de API, canais de atuação e parâmetros de RAG em tempo de execução sem reiniciar o bot.
* **Auditor Criptográfico**: Validador que atesta a integridade do ledger (`security_audit.jsonl`) recalculando as assinaturas SHA-256 de todas as interações.
* **Volumetria do Chroma**: Contadores visuais exibindo a quantidade de chunks indexados na base vetorial (RAG e Histórico).

#### 📸 Capturas de Tela do Dashboard
Aqui estão alguns exemplos visuais das abas e funções do painel web administrativo:

##### Painel de Controle Principal (Dashboard)
Interface principal exibindo o status do bot, latência, uptime, gráficos de interações diárias, rankings de usuários/comandos ativos e o validador de integridade.
![Dashboard Principal](imgs/Dashboard%201917x907.png)

##### Configurações da IA (Provedor)
Formulário dinâmico para ajustar os provedores de modelo de linguagem base (Gemini, OpenAI, Groq), chaves de API e canais de chat/boas-vindas do Discord.
![Configuração IA](imgs/Provedor%20IA%201917x907.png)

##### Parâmetros do Mecanismo RAG
Ajuste fino do corte de similaridade mínima, número de chunks buscados e credenciais do banco vetorial Chroma, acompanhado por contadores de volumetria ativa.
![Busca RAG](imgs/Busca%20RAG%201917x907.png)

##### Logs de Auditoria do Ledger
Grade detalhada e buscável de interações registradas no log imutável de segurança, permitindo inspecionar prompts, respostas e hashes SHA-256 de cada transação.
![Logs de Auditoria](imgs/Logs%20de%20Auditoria%201917x907.png)

---

## 🔒 Arquitetura de Segurança Cibernética

Projetado sob princípios modernos de segurança de aplicações com LLM, o DSE.Assist implementa uma arquitetura de segurança multicamadas:

### 🛡️ 1. Proteção Ativa contra Prompt Injection (Input Validation & Data Isolation)
Para evitar que atacantes manipulem o comportamento do LLM via prompts diretos (como comandos para ignorar instruções ou requisitar dados restritos de usuários) ou indiretos injetados via RAG:
* **Filtro de Entrada Ativo (Input Validation):** O sistema intercepta o prompt do usuário antes do processamento pela IA e executa uma varredura com heurísticas regex refinadas buscando por comandos de manipulação e controle (ex: *ignore*, *esqueça*, *forget*, *override*, *bypass*). Caso detectado, a requisição é abortada de imediato (economizando cota de API da IA), respondendo ao usuário com uma mensagem de segurança e registrando o log no ledger como `REJECTED` (computado nas estatísticas de **Barradas por Segurança**).
* **Tags Semânticas XML:** As entradas de usuários e trechos do RAG são envelopados em delimitadores estruturados (`<user_input>` e `<retrieved_context>`).
* **System Prompt Blindado:** Os prompts de sistema contam com diretrizes de segurança globais (`DATA_SEPARATION_INSTRUCTION`) que instruem a IA a tratar o conteúdo das tags estritamente como dados passivos de análise, rejeitando qualquer ordem de execução ("ignore as regras anteriores", etc.).

### 🛡️ 2. Confiança Zero em RAG (Anti RAG Poisoning)
Para mitigar a injeção de documentos maliciosos na base vetorial que induzam a IA a alucinar ou falsificar fatos:
* **Validação de Metadados:** Fontes sem autoria rastreada ou de origem desconhecida são sumariamente descartadas no RAG.
* **Validação de Saída (Output Verification):** O sistema analisa a resposta final. Se a IA citar uma fonte de dados (ex: `.md`, `.pdf`) que **não** constava na lista de documentos legítimos recuperados do banco vetorial para aquela busca, a resposta é interceptada, bloqueada e substituída por uma mensagem amigável de erro de segurança.

### 🛡️ 3. Ledger de Auditoria Criptográfica (WORM Logging)
Todas as interações são salvas em um log local imutável (`security_audit.jsonl`):
* **Cadeia de Hashes (SHA-256):** Cada linha do log contém o timestamp, ID de usuário, prompt com tags, resposta e o hash SHA-256 de seus campos concatenado ao hash da linha anterior (`prev_hash`), operando como uma blockchain local.
* **Detecção de Fraude:** Qualquer edição retroativa para apagar ou adulterar prompts ou respostas quebra a integridade da cadeia de hashes, sendo imediatamente acusada por scripts de auditoria externa.

### 🛡️ 4. Princípio do Menor Privilégio (PoLP)
* O agente de IA opera em modo de leitura-apenas (sem acesso a APIs de execução ou permissão de escrita local), minimizando a superfície de exposição caso a IA sofra comprometimento.

---

## 🏗️ Estrutura do Projeto

```
bot_discord_dse/
├── bot.py                        # Ponto de entrada do bot
├── migration.py                  # CLI de ingestão e testes RAG
├── requirements.txt              # Dependências do Python
├── .env                          # Variáveis de ambiente locais (não versionado)
├── .env.example                  # Template das configurações
├── .gitignore                    # Regras de exclusão de arquivos sensíveis
│
├── dashboard/                    # 🖥️ Painel administrativo web (novo)
│   ├── server.py                 # API REST e servidor web aiohttp
│   └── static/                   # Interface SPA (HTML, CSS, JS e Chart.js)
│
├── ai_providers/                 # 🔌 Sistema modular de IAs
│   ├── __init__.py               # Factory de provedores
│   ├── base.py                   # Classe base abstrata
│   ├── gemini.py                 # Integração com Google Gemini
│   ├── openai_provider.py        # Integração com OpenAI GPT
│   ├── groq_provider.py          # Integração com Groq (Llama/Mixtral)
│   ├── rag_provider.py           # Wrapper de segurança e busca semântica RAG
│   └── security_logger.py        # Módulo de log criptográfico imutável
│
├── cogs/                         # 🧩 Módulos do Bot (extensões)
│   ├── ai_commands.py            # Slash commands do bot
│   ├── community.py              # Boas-vindas e escuta de canais
│   └── utils.py                  # Helpers, limitadores de requisição e embeds
│
└── config/                       # ⚙️ Configurações e Prompts
    ├── __init__.py
    └── prompts.py                # Prompts do sistema e instruções de segurança
```

---

## 🛠️ Configuração e Instalação

### 1. Pré-requisitos
* Python 3.9 ou superior instalado.
* Conta e Token de Bot criados no [Discord Developer Portal](https://discord.com/developers/applications).
* API Key do provedor de IA de sua preferência (ex: [Google AI Studio](https://aistudio.google.com/app/apikey) para Gemini).
* Instância/API Key do [Chroma Cloud](https://www.trychroma.com/).

### 2. Clonar o projeto e Instalar Dependências
```bash
git clone https://github.com/dse-brasil/dse_assist.git
cd dse_assist
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
Copie o template `.env.example` para `.env` e insira suas credenciais:
```bash
cp .env.example .env
```

Campos essenciais no `.env`:
```env
DISCORD_TOKEN=seu_token_do_discord_aqui

# Configurações de IA (opções: gemini | openai | groq)
AI_PROVIDER=gemini
AI_API_KEY=sua_chave_de_api_aqui
AI_MODEL=gemini-2.5-flash

# RAG & Chroma Cloud
RAG_ENABLED=true
RAG_COLLECTION=dse_knowledge_base
RAG_MIN_SIMILARITY=0.40
CHROMA_API_KEY=sua_chave_do_chroma_aqui
CHROMA_HOST=api.trychroma.com
CHROMA_TENANT=seu_tenant_aqui
CHROMA_DATABASE=dse
```

---

## 🗃️ Ingestão de Dados RAG (`migration.py`)

O assistente usa um banco vetorial no Chroma para buscar respostas na base de conhecimento local. Você pode gerenciar esse banco através da CLI de migração:

```bash
# Testar a conexão com o Chroma Cloud
python migration.py --test

# Ingerir um documento individual na base vetorial
python migration.py --source documento.md --type article --tags python,machine-learning

# Ingerir uma pasta inteira de arquivos recursivamente
python migration.py --source docs/ --recursive

# Testar a busca semântica diretamente pelo terminal
python migration.py --query "o que é overfitting?"
```

---

## 🚀 Como Iniciar o Bot

Para ligar o bot no Discord e iniciar o painel web administrativo:
```bash
python bot.py
```

Você deverá ver a saída indicando a conexão e sincronização com sucesso no terminal:
```
[IA] Provedor base: Google Gemini (gemini-2.5-flash)
[RAG] Ativo -> colecao='dse_knowledge_base' | n=4 | sim>=0.40
[IA] Provider ativo: Google Gemini (gemini-2.5-flash) + RAG
[OK] Cog carregado: cogs.ai_commands
[OK] Cog carregado: cogs.community
[DASHBOARD] Painel Web rodando em http://127.0.0.1:5000
[OK] Bot conectado como DSE_BOT#9020 (ID: ...)
[OK] 8 comandos slash sincronizados.
```

O dashboard administrativo web estará disponível no seu navegador em: **`http://127.0.0.1:5000`**.

---

## ⚖️ Licença

Este projeto é de uso interno e educacional da comunidade **Data Science Enthusiasts (DSE)**. Consulte as políticas internas de contribuição antes de realizar pull requests.
