# Roadmap do DSE.Assist (ROADMAP)

Este documento apresenta a evolução do **DSE.Assist**, consolidando o status das funcionalidades atuais e definindo os próximos marcos de desenvolvimento. O objetivo é dar visibilidade aos mantenedores e colaboradores de quais desafios técnicos estão priorizados para cada versão.

---

## 🗺️ Ciclo de Versões

```text
v1.2.0 (Atual)
├─ Ledger Criptográfico (WORM) ──── [✔]
├─ Telegram Multiplataforma ────── [✔]
├─ Hot Reload de Configurações ──── [✔]
└─ Painel Web (Dashboard SPA) ───── [✔]

v1.3.0 (Próxima)
├─ Sistema de Plugins/Skills ───── [🚧]
├─ Avaliação Automática RAG ────── [ ]
├─ Decodificação de Entradas ───── [ ]
└─ Memória de Conversação ──────── [ ]

v2.0 (Futuro)
├─ Suporte Multi-servidor ──────── [ ]
├─ API REST Pública ────────────── [ ]
└─ Marketplace de Skills ───────── [ ]
```

---

## 📌 Detalhamento dos Marcos

### Versão 1.2.0 (Marco Atual — Concluído)
Foco em observabilidade, segurança ativa, governança e integração multiplataforma.
* **Telegram Parallel Polling:** Acoplamento assíncrono do Telegram Updater ao loop de eventos existente, rodando em paralelo com o bot do Discord e a API.
* **Hot Reload de Configurações:** Mecanismo de re-instanciação de provedores de IA e RAG em memória através do dashboard aiohttp, sem necessidade de reinicializar a aplicação.
* **Ledger SHA-256 (WORM):** Gravação imutável local onde cada log é assinado digitalmente e acoplado ao anterior, prevenindo fraudes em relatórios de segurança.
* **Visualizações do Dashboard:** Integração gráfica (Chart.js) e monitoramento de volumetria no Chroma Cloud.

### Versão 1.3.0 (Próximo Marco — Em Desenvolvimento)
Foco em qualidade de respostas, extensibilidade e proteção avançada.
* **Sistema de Plugins (Skills):** Permitir que colaboradores criem novas habilidades (skills) modulares sem editar o core do bot (ex: consulta a previsão do tempo, busca de artigos científicos, etc.).
* **Avaliação Automática de Respostas (RAG Triad):** Implementar testes automatizados rodando em background para avaliar a qualidade das respostas geradas de acordo com três métricas:
  1. *Context Relevance:* A relevância do contexto recuperado para a pergunta.
  2. *Groundedness:* Se a resposta é totalmente baseada no contexto fornecido (sem alucinações).
  3. *Answer Relevance:* Se a resposta atende diretamente à pergunta do usuário.
* **Decodificador Sanitizado de Entradas:** Decodificar ativamente payloads em Base64, Hexadecimal e Unicode de forma antecipada no filtro de entrada, prevenindo técnicas complexas de ofuscação de Prompt Injection.
* **Memory Layer (Memória de Curto Prazo):** Criar uma camada leve de histórico de chat na sessão do usuário (utilizando Redis ou cache local em memória) para conversas contínuas e contextualizadas.

### Versão 2.0 (Longo Prazo — Planejado)
Foco em escala comercial, descentralização e ecossistema distribuído.
* **Suporte Multi-servidor:** Arquitetar o bot para suportar configurações independentes de canais, provedores e coleções RAG para múltiplos servidores do Discord e múltiplos grupos de Telegram ao mesmo tempo (isolamento de tenants).
* **API REST Pública:** Expor rotas autenticadas (JWT) para que outras aplicações possam consultar o banco de conhecimento (RAG) ou a inteligência do bot programaticamente.
* **Marketplace de Skills:** Permitir o compartilhamento de plugins de IA criados pela comunidade de forma dinâmica no repositório.
