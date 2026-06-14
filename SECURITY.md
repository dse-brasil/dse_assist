# Política de Segurança (SECURITY)

Este documento define a nossa política de reporte de vulnerabilidades de segurança, as diretrizes para divulgação responsável (*responsible disclosure*) e os compromissos de resposta dos mantenedores do **DSE.Assist**.

Dado que este projeto implementa camadas ativas de proteção para LLMs e RAG, levamos a segurança da informação muito a sério.

---

## 🛡️ Escopo e Vulnerabilidades Cobertas

Encorajamos a análise de segurança e testes de intrusão éticos no código do bot. Estamos particularmente interessados em relatórios sobre:
* Métodos de *bypass* ou evasão de comandos que burlem o **Filtro de Entrada Ativo** (Prompt Injections inéditos).
* Técnicas de *Indirect Prompt Injection* capazes de sequestrar a sessão do LLM através de arquivos ingeridos na base vetorial.
* Falhas na validação de saída (**Zero Trust RAG**) que permitam à IA citar ou inventar referências não fornecidas.
* Modificações não autorizadas que permitam quebrar a integridade criptográfica da cadeia de hashes do ledger local (`security_audit.jsonl`).
* Vulnerabilidades clássicas de aplicações web no Dashboard administrativo (XSS, CSRF, Injection, etc.).

---

## 📬 Como Reportar uma Vulnerabilidade?

**NÃO abra uma issue pública no GitHub para reportar uma vulnerabilidade de segurança.** Fazer isso expõe o bot da comunidade ativa a explorações imediatas.

Por favor, reporte qualquer vulnerabilidade de forma privada através de um dos seguintes métodos:
1. **GitHub Private Vulnerability Reporting:** Se disponível no repositório, utilize a aba de segurança do GitHub para reportar privadamente.
2. **Contato Privado:** Envie um relatório detalhado para o e-mail dos mantenedores (listados na seção de contatos do repositório) ou envie uma mensagem direta para a moderação da comunidade **Data Science Enthusiasts (DSE)**.

### O que incluir no relatório:
* Uma descrição detalhada do problema de segurança encontrado.
* Passos claros e reproduzíveis para explorar a vulnerabilidade (incluindo o prompt exato ou payload HTTP utilizado).
* O impacto potencial da vulnerabilidade.
* Ideias ou sugestões de como mitigar ou corrigir o problema (opcional).

---

## 🤝 Diretrizes para Divulgação Responsável

Ao reportar e investigar problemas, pedimos que você siga as seguintes diretrizes:
* Dê aos mantenedores um prazo razoável para corrigir a vulnerabilidade antes de divulgá-la publicamente (geralmente **90 dias** a partir do reporte privado).
* Evite acessar ou destruir dados de outros usuários durante os seus testes.
* Não utilize as vulnerabilidades encontradas para fins maliciosos, extorsão ou spam.

---

## ⏱️ Compromisso e Tempo de Resposta

Os mantenedores se comprometem a:
* Reconhecer o recebimento do seu relatório de segurança em até **48 horas**.
* Fornecer uma avaliação preliminar da gravidade do problema em até **5 dias úteis**.
* Manter o relator informado sobre o progresso e o desenvolvimento da correção.
* Dar o devido crédito de segurança (*credit recognition*) nas notas de release da nova versão, a menos que o relator prefira permanecer anônimo.
