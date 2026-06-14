# Guia de Contribuição (CONTRIBUTING)

Olá! Ficamos muito felizes pelo seu interesse em colaborar com o **DSE.Assist**. Como um projeto de código aberto da comunidade **Data Science Enthusiasts (DSE)**, este repositório é construído de forma colaborativa para ser um ambiente de aprendizado prático e construção de portfólio.

Este guia define as regras do jogo, como configurar o seu ambiente local e a nossa definição de conclusão de tarefas.

---

## 🚀 Rampa de Entrada para Novos Colaboradores

Nosso objetivo é que qualquer pessoa da comunidade consiga realizar sua primeira contribuição em menos de **2 horas**. Para isso, siga o fluxo abaixo:

```text
1. START HERE (Leia este Guia)
      │
      ▼
2. Selecionar uma Issue com a label "good-first-issue"
      │
      ▼
3. Configurar o ambiente de desenvolvimento localmente (<30 min)
      │
      ▼
4. Implementar a alteração e validar com testes locais
      │
      ▼
5. Abrir um Pull Request estruturado seguindo o Template de PR
```

---

## 🛠️ Configuração do Ambiente de Desenvolvimento (<30 minutos)

Siga os passos abaixo para preparar o seu computador para rodar o bot e o dashboard localmente:

### 1. Clonar o Repositório e Criar o Fork
1. Faça um *Fork* deste repositório no seu perfil do GitHub.
2. Clone o seu fork localmente:
   ```bash
   git clone https://github.com/SEU_USUARIO/dse_assist.git
   cd dse_assist
   ```

### 2. Configurar o Ambiente Virtual (venv)
Recomendamos o uso de ambientes virtuais para isolar as dependências do projeto:
```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Linux/macOS:
source venv/bin/activate
```

### 3. Instalar Dependências
Instale todos os pacotes requeridos e os pacotes adicionais de testes:
```bash
pip install -r requirements.txt
pip install pytest
```

### 4. Configurar as Variáveis de Ambiente
Copie o arquivo de exemplo `.env.example` para `.env` e preencha as variáveis locais para testar (você precisará criar tokens de teste no Discord Developer Portal e obter uma API Key de IA):
```bash
cp .env.example .env
```
*(Nota: Nunca comite ou envie seu arquivo `.env` para o Git, ele está bloqueado no `.gitignore`).*

### 5. Executar a Suíte de Testes
Para garantir que tudo está funcionando perfeitamente antes de começar a codificar, execute os testes unitários:
```bash
pytest tests/
```

---

## 📜 Convenções de Código e Commits

Adotamos a especificação de **Conventional Commits** para manter o histórico de commits limpo e fácil de automatizar:

* `feat:` Uma nova funcionalidade (ex: `feat: add platform tracking to dashboard`).
* `fix:` Correção de um bug (ex: `fix: resolve crash when telegram token is missing`).
* `docs:` Alterações na documentação (ex: `docs: update adr list`).
* `refactor:` Alterações de código que não corrigem bugs nem adicionam features.
* `test:` Adição ou correção de testes (ex: `test: add unit tests for regex filters`).
* `chore:` Atualizações de build, dependências ou tarefas administrativas.

---

## 🎯 Definition of Done (DoD)

Uma tarefa (*issue*) é classificada oficialmente como **CONCLUÍDA** (pronta para ser mesclada na branch `main`) apenas quando atende aos seguintes critérios:

* [ ] **Código Implementado:** O código segue as convenções e estilo padrão do Python (PEP 8).
* [ ] **Testes Executados:** A suíte de testes locais (`pytest`) foi executada com sucesso e novos testes foram adicionados para a alteração feita (se aplicável).
* [ ] **Documentação Atualizada:** As alterações foram refletidas no `README.md` (se alterou alguma funcionalidade de interface) ou documentadas no `ARCHITECTURE.md` (se alterou o fluxo da arquitetura). Se houver mudanças de decisões fundamentais, um novo ADR em `docs/adr/` foi registrado.
* [ ] **PR Aprovado:** O Pull Request passou pela revisão de pelo menos um mantenedor do projeto e foi aprovado no GitHub.
