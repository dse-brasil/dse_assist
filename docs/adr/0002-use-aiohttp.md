# ADR 0002: Utilização de Servidor Web Integrado Baseado em aiohttp para o Dashboard

## Status
Aceito

## Data
2026-06-13

## Contexto
O **DSE.Assist** necessita de um painel web administrativo (dashboard) para gerenciar variáveis do `.env`, monitorar o uptime/latência da instância, auditar a integridade criptográfica do ledger local de logs, e analisar gráficos estatísticos de interações. Precisamos que esse servidor rode de forma integrada ao bot, sem exigir que o usuário gerencie múltiplos processos em paralelo.

## Alternativas Consideradas

* **FastAPI + Uvicorn em Processo Separado:**
  * *Prós:* FastAPI é moderno, rápido, possui documentação automática Swagger e tipagem estrita com Pydantic.
  * *Contras:* Rodar um processo separado via Uvicorn exigiria orquestração de infraestrutura adicional (como Docker Compose) ou inicialização manual de múltiplos terminais, o que complica o deploy do bot.
* **Flask (WSGI Síncrono):**
  * *Prós:* Extremamente comum e familiar para desenvolvedores Python.
  * *Contras:* Por ser síncrono por padrão, exige execução em threads separadas para não bloquear o loop de eventos assíncronos (`asyncio`) do bot Discord, adicionando complexidade e risco de concorrência.

## Decisão
Decidimos utilizar a biblioteca **aiohttp** para construir nosso servidor web integrado de APIs e entrega de arquivos estáticos.

## Justificativa
1. **Loop de Eventos Compartilhado:** `aiohttp` é totalmente assíncrono. Isso nos permite rodar o servidor web e o bot do Discord em paralelo sob o **mesmo** loop de eventos ativo, usando apenas `asyncio.create_task(start_dashboard(bot))`.
2. **Compartilhamento de Estado em Memória:** Por rodar no mesmo processo e thread, o servidor web tem acesso direto ao objeto global `bot`. Isso viabiliza o Hot Reload (reinicialização dinâmica do provedor de IA na memória) e a leitura de propriedades vivas do bot (latência, uptime, lista de servidores) sem a necessidade de APIs IPC ou bancos de dados intermediários.
3. **Leveza:** O `aiohttp` é leve e fornece exatamente as primitivas necessárias para servir rotas JSON (APIs REST) e uma Single Page Application (SPA).

## Consequências
* **Positivas:** Deploy extremamente simples (basta digitar `python bot.py` e tudo funciona), consumo mínimo de memória RAM (sem processos duplicados) e facilidade de comunicação entre o painel e o bot.
* **Negativas:** Se o loop de eventos principal sofrer um bloqueio severo por processamento síncrono pesado de CPU, tanto o bot quanto o dashboard ficarão temporariamente indisponíveis (evitamos isso rodando I/O pesado de disco ou rede em executors de thread adicionais).
