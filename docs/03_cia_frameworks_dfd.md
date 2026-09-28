# Ex. 3 — Tríade CIA, frameworks de referência e DFD

**Rubrica:** R5, R6 · **Tag:** `ex03` · **Estado analisado:** tag `ex02` (API sem autenticação, persistência em memória)

> Referências usadas em toda a entrega: **OWASP Top 10:2021**, **OWASP API Security Top 10:2023**, **NIST SSDF (SP 800-218)** e **MITRE CAPEC / ATT&CK / CWE**.

## 1. Tríade CIA aplicada à API de consultas

**Por que a confidencialidade pesa mais aqui.** O ativo principal é **dado pessoal sensível de saúde** (LGPD, art. 5º, II): saber que "Ana Souza tem consulta de cardiologia às 14h30" já revela uma condição de saúde. Um vazamento gera obrigação de comunicar à ANPD e aos titulares (art. 48), sanções (art. 52) e dano reputacional que não se desfaz. Uma falha de integridade (consulta remarcada indevidamente) ou de disponibilidade (agenda fora do ar) é grave, mas normalmente recuperável. Um vazamento de dado de saúde é **irreversível**. Por isso, nas decisões de trade-off desta entrega, a confidencialidade prevalece: por exemplo, responder 404 em vez de 403 para não confirmar a existência de uma consulta de terceiro (Ex. 9) e tratar BOLA como prioridade crítica mesmo com CVSS médio (Ex. 12).

| Pilar | Ativo / fluxo (DFD) | Ameaça concreta nesta API | Controle já implementado (arquivo:linha, tag `ex02`) | Lacuna → onde será tratada |
|---|---|---|---|---|
| **C** | Resposta JSON de consultas (F4) | vazamento de campos de auditoria (`ip_origem`, `criado_por`) | `ConsultaPublic` como allowlist de saída: `app/models/consulta.py:40`; `response_model` em `app/routes/consultas.py:16,21,27,49` | — |
| **C** | Agenda HTML (F6) | XSS stored que rouba a sessão da recepção e lê a página | auto-escape explícito: `app/routes/pages.py:16-19`; `{{ c.observacoes }}` sem `\|safe`: `app/templates/agenda.html:21` | CSP no Ex. 10 |
| **C** | Agenda HTML (F6) | exposição desnecessária de CPF na tela | minimização: `app/routes/pages.py:32-39` monta só hora, nome, profissional, status e observações | — |
| **C** | Todas as rotas | **qualquer pessoa lê qualquer consulta** (sem autenticação) | nenhum: o comentário `TODO Ex. 6/9` em `app/routes/consultas.py:23` registra a lacuna | Ex. 6 (JWT + ownership), Ex. 9 (centralização) |
| **C** | Segredos (JWT, banco) | segredo no código-fonte | ainda não há segredos; `.env.example` já prevê as variáveis | Ex. 11 (BaseSettings + `.env`) |
| **I** | Criação de consulta (F3) | ids inválidos ou negativos, texto gigante | `Field(gt=0)`: `app/models/consulta.py:23-24`; `max_length=500`: `:26,37`; checagem de existência (422): `app/routes/consultas.py:29-32` | regex/whitelist no Ex. 9 |
| **I** | Status da consulta | valor arbitrário de status | enum `StatusConsulta`: `app/models/consulta.py:15`; status inicial imposto pelo servidor: `app/routes/consultas.py:38` | transições de status por whitelist no Ex. 9 |
| **I** | Atualização (PATCH) | cliente troca `profissional_id` (se apropria da consulta) | `ConsultaUpdate` não declara `profissional_id`: `app/models/consulta.py:34-37` (campo extra é **ignorado**) | `extra='forbid'` no Ex. 9 (rejeitar, não ignorar) |
| **I** | Auditoria | não dá para saber quem alterou (repúdio) | campos `criado_por`/`atualizado_em` gravados: `app/routes/consultas.py:39-43` (mas `criado_por="anonimo"`) | usuário autenticado no Ex. 6; log centralizado = risco residual (Ex. 13) |
| **A** | Todas as rotas | flood de requisições / força bruta | nenhum controle | rate limit no Ex. 10 |
| **A** | Persistência | reinício do processo apaga tudo (memória) | nenhum: `app/database.py` é em memória por design do Ex. 1 | Ex. 11 (banco relacional) |
| **A** | Payload | corpo gigante em `observacoes` | `max_length=500`: `app/models/consulta.py:26` | — |

## 2. Frameworks de referência → controles concretos

| Framework | Item | Controle concreto nesta aplicação | Onde (código / exercício) |
|---|---|---|---|
| OWASP API Top 10:2023 | **API3** Broken Object Property Level Authorization | `response_model=ConsultaPublic` (saída) e modelos de entrada sem campos sensíveis | `app/routes/consultas.py:16-49`, `app/models/consulta.py:34-47` · reforço com `extra='forbid'` no Ex. 9 |
| OWASP API Top 10:2023 | **API1** Broken Object Level Authorization | *lacuna*: ownership centralizado em `get_consulta_autorizada` | Ex. 6 e Ex. 9 |
| OWASP API Top 10:2023 | **API2** Broken Authentication | *lacuna*: OAuth2 + bcrypt + JWT curto + MFA | Ex. 6 |
| OWASP API Top 10:2023 | **API4** Unrestricted Resource Consumption | `max_length` já existe; rate limit | `app/models/consulta.py:26` · Ex. 10 |
| OWASP Top 10:2021 | **A03** Injection (inclui XSS) | auto-escape Jinja2; tipagem Pydantic; SQL parametrizado | `app/routes/pages.py:16-19` · Ex. 11 |
| OWASP Top 10:2021 | **A05** Security Misconfiguration | CORS com allowlist, headers de segurança | Ex. 10 |
| NIST SSDF | **PO.1** Definir requisitos de segurança | requisitos derivados do threat model (Ex. 4) | `docs/04_threat_model.md` |
| NIST SSDF | **PW.1** Projetar software para atender requisitos e mitigar riscos | threat model + DFD + partições | este documento, Ex. 4, Ex. 5 |
| NIST SSDF | **PW.5** Criar código seguro seguindo práticas | separação entrada/saída, validação declarativa, escape por contexto | `app/models/consulta.py`, `app/routes/pages.py:16-19` |
| NIST SSDF | **PW.7** Revisar/analisar o código | revisão manual (Ex. 8) + SAST Bandit no pipeline | Ex. 8, Ex. 12 |
| NIST SSDF | **PW.8** Testar o código executável | pytest cobrindo vazamento e XSS | `tests/test_consultas.py` (4 testes) · ampliado no Ex. 12 |
| NIST SSDF | **PS.1** Proteger o código contra alteração | repositório git com tags por exercício; proteção de branch | Ex. 12 |
| NIST SSDF | **RV.1** Identificar e confirmar vulnerabilidades continuamente | SCA agendado + DAST (ZAP) | Ex. 12, Ex. 13 |
| MITRE CAPEC | **CAPEC-63** Cross-Site Scripting | auto-escape (sem `\|safe`) | `app/templates/agenda.html:21` |
| MITRE CAPEC | **CAPEC-66** SQL Injection | queries parametrizadas SQLModel | Ex. 11 (e antes/depois nos Ex. 8/9) |
| MITRE CAPEC | **CAPEC-49** Password Brute Forcing | rate limit no login | Ex. 10 |
| MITRE CAPEC | **CAPEC-122** Privilege Abuse | RBAC + ownership | Ex. 6 |
| MITRE ATT&CK | **T1190** Exploit Public-Facing Application | toda a superfície HTTP: validação de entrada, autenticação, headers e rate limit | Ex. 6–10 |
| MITRE ATT&CK | **T1110** Brute Force | rate limit + MFA para admin | Ex. 6, Ex. 10 |
| MITRE CWE | **CWE-213 / CWE-200** Exposição de informação | `ConsultaPublic` | `app/models/consulta.py:40` |
| MITRE CWE | **CWE-79** XSS | auto-escape | `app/routes/pages.py:16-19` |

## 3. DFD — fronteiras de confiança e fluxos sensíveis

![DFD](img/dfd.png)

Fonte: `docs/img/dfd.mmd` (Mermaid), renderizado com `scripts/render_mermaid.py`. O DFD já inclui os componentes que entram nos Ex. 6–7 (Auth e Horários), porque ele é a base de todas as análises de ameaça seguintes (o próprio enunciado pede isso).

**Elementos**

| Tipo | Elemento |
|---|---|
| Entidade externa | Frontend SPA (JSON), Recepção (navegador/HTML), Laboratório parceiro (M2M) |
| Processo | 1. Auth, 2. Consultas/Pacientes, 3. Páginas da recepção, 4. Horários disponíveis |
| Depósito | Banco (pacientes, profissionais, consultas, usuários, clientes M2M) |

**Trust boundaries (tracejadas em vermelho)**

| # | Fronteira | O que cruza | Por que é fronteira |
|---|---|---|---|
| TB1 | Internet / rede das clínicas ↔ API | F1–F6 | origem do dado não é confiável: toda entrada precisa ser autenticada, autorizada e validada |
| TB2 | Rede do laboratório ↔ API | F7–F10 | outra organização, outro nível de controle; um token vazado lá não pode alcançar PHI |
| TB3 | API ↔ Banco | F11–F14 | é onde a injeção se concretiza; credencial do banco não pode estar no código |

**Fluxos com dado de paciente ([PHI], em vermelho grosso):** F3/F4 (consultas e prontuário JSON), F6 (agenda HTML), F12/F13 (leitura e escrita no banco). O laboratório (F9/F10/F14) recebe **apenas horários livres, sem identificação de paciente**. Essa é uma decisão de desenho que o Ex. 7 torna técnica por escopo.

## Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/dfd.png` / `docs/img/dfd.mmd` | DFD com as 3 trust boundaries e os fluxos PHI destacados |
| `evidencias/ex02/*` | os controles de C (response_model, auto-escape) citados na tabela CIA funcionam |
