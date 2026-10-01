# DR2 AT — API de Agendamento de Consultas

**Aluno:** William Felício Freire
**Disciplina:** Desenvolvimento Seguro de Aplicações Web
**Vídeo (YouTube, não listado):** `<!-- COLAR O LINK DO VÍDEO AQUI -->`

API REST de agendamento de consultas médicas (dado de saúde, LGPD), construída em FastAPI + SQLModel, com autenticação OAuth2/JWT, autorização RBAC + ownership, integração M2M por escopos, correção de vulnerabilidades OWASP, hardening de rede, pipeline DevSecOps e auditoria final.

## Como executar

```bash
cd consultas-api
python3.12 -m venv .venv && source .venv/bin/activate   # Python >= 3.10
pip install -r requirements.txt

# variáveis (DEV): a partir da raiz do repositório
source ../scripts/dev_env.sh        # exporta segredos fictícios de desenvolvimento
uvicorn app.main:app --reload       # ou: ../scripts/servidor.sh start
```

- Swagger: http://localhost:8000/docs (desabilitado quando `ENV=prod`)
- Agenda da recepção: http://localhost:8000/recepcao/login
- Testes: `pytest -v` (67 testes, inclui `tests/security/`)

> **Segredos:** nenhum segredo real é versionado. `.env` está no `.gitignore`; use `.env.example`. Em DEV, `scripts/dev_env.sh` exporta valores fictícios.

## Usuários de demonstração (seed)

| Usuário | Papel | Observação |
|---|---|---|
| `admin` | admin | exige MFA (TOTP): login pela API (`/auth/token` → `/auth/mfa/verify`) |
| `recepcao` | recepção | páginas HTML |
| `dra_carla` | profissional | pacientes: Ana (id 1) |
| `dr_diego` | profissional | pacientes: Bruno (id 2) |
| `lab-parceiro` | M2M | escopo `horarios:read` |

(senhas de DEV em `scripts/dev_env.sh`)

## Estrutura da entrega

```
William_Felicio_Freire_DR2_AT/
├── README.md                             ← este documento (como rodar + os 13 exercícios)
├── RELATORIO_TECNICO_DR2_AT.md           ← decisões de segurança por exercício + mapa de evidências por tema
├── RELATORIO_RASTREABILIDADE_DR2_AT.md   ← capstone (Ex. 13): ZAP, matriz T01–T12, code review, risco residual
├── .github/workflows/security.yml        ← pipeline DevSecOps
├── docs/img/                             ← DFD e partições (.mmd + .png)
├── evidencias/                           ← ex01/ … ex13/ + INDICE.md
├── scripts/                              ← evidencia.sh, servidor.sh, token.sh, cvss_scores.py, …
└── consultas-api/                        ← código (app/, tests/, requirements.txt, .env.example)
```

Índice das evidências: `evidencias/INDICE.md`. Cada evidência `.txt` traz no cabeçalho o commit e o comando que a gerou. Tags git `ex00`…`ex14` marcam o estado de cada exercício; `ex08-vulneravel` marca o código deliberadamente vulnerável do Ex. 8.

## Exercícios

- [Ex. 1 — Fundação da API de agendamento](#ex01)
- [Ex. 2 — Controle de exposição de dados e templates seguros](#ex02)
- [Ex. 3 — Tríade CIA, frameworks de referência e DFD](#ex03)
- [Ex. 4 — Misuse cases, STRIDE e threat model consolidado](#ex04)
- [Ex. 5 — Arquitetura de segurança, partições e vetores nos três eixos](#ex05)
- [Ex. 6 — Autenticação e autorização](#ex06)
- [Ex. 7 — Integração M2M: fluxo OAuth, escopos e claims](#ex07)
- [Ex. 8 — Identificação de vulnerabilidades OWASP Top 10](#ex08)
- [Ex. 9 — Correção de vulnerabilidades de entrada e saída](#ex09)
- [Ex. 10 — Hardening de rede e proteção contra abuso](#ex10)
- [Ex. 11 — Persistência segura (SQLModel + BaseSettings)](#ex11)
- [Ex. 12 — Pipeline DevSecOps, CVSS e security gate](#ex12)
- [Ex. 13 — Capstone: auditoria final, mocking e OpenAPI](#ex13)

> **Ordem de execução:** o Ex. 11 (persistência) foi feito antes dos Ex. 8–10, para que a SQL injection do Ex. 8 fosse real (ver [Ex. 11](#ex11)). As seções seguem a numeração do enunciado. Referências de `arquivo:linha` apontam para o código na tag do exercício correspondente.

<a id="ex01"></a>

### Ex. 1 — Fundação da API de agendamento

#### Ambiente virtual isolado

A API roda em um `venv` próprio (`consultas-api/.venv`, criado com Python 3.12). Motivos:

- **Isolamento de dependências:** as versões fixadas em `requirements.txt` (FastAPI, Pydantic v2, Jinja2…) não conflitam com outros projetos nem com o Python do sistema (a máquina tem 3.9 como padrão, que nem suporta a sintaxe `str | None` usada no código).
- **Reprodutibilidade:** o mesmo `requirements.txt` é instalado no CI (Ex. 12). Versões fixas também são pré-requisito para a análise de dependências (SCA) com `pip-audit`: só é possível dizer "esta versão tem CVE" se a versão for conhecida.
- **Superfície mínima:** apenas o que a aplicação usa é instalado; ferramentas auxiliares (Playwright, para os prints) ficam em outro venv (`scripts/.venv-tools`).

A evidência `ex01/01_venv.txt` mostra `sys.prefix != sys.base_prefix` (= ambiente isolado) e o `pip list` resultante.

#### Organização em módulos

| Módulo            | Responsabilidade                                                                                       | Por que separado                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `app/main.py`     | cria o `FastAPI` e registra os routers                                                                 | ponto único de composição; middlewares de segurança (Ex. 10) entram aqui uma única vez |
| `app/routes/`     | um `APIRouter` por recurso (`consultas.py`) + páginas HTML (`pages.py`)                                | evita a "rota gigante" citada no enunciado; cada recurso cresce no seu arquivo         |
| `app/models/`     | modelos Pydantic de **entrada** (`ConsultaCreate`, `ConsultaUpdate`) e de **saída** (`ConsultaPublic`) | contrato da API separado do armazenamento (base do Ex. 2)                              |
| `app/database.py` | armazenamento (em memória até o Ex. 11)                                                                | trocar a persistência por SQLModel não obriga reescrever as rotas                      |
| `app/templates/`  | Jinja2 com herança (`base.html` → `agenda.html`)                                                       | apresentação isolada do domínio                                                        |
| `tests/`          | pytest                                                                                                 | arquivo iniciado aqui e expandido nos Ex. 6, 12 e 13                                   |

Nas próximas etapas entram `app/auth/` (autenticação/autorização) e `app/core/` (configuração, headers, rate limit): a lógica de segurança fica **centralizada** nesses módulos e as rotas só as _usam_.

#### Recurso RESTful completo: consultas

| Método   | Rota              | Resposta de sucesso     |
| -------- | ----------------- | ----------------------- |
| `POST`   | `/consultas`      | 201 + `ConsultaPublic`  |
| `GET`    | `/consultas`      | 200 + lista             |
| `GET`    | `/consultas/{id}` | 200 (404 se não existe) |
| `PATCH`  | `/consultas/{id}` | 200                     |
| `DELETE` | `/consultas/{id}` | 204                     |

#### Como rodar

```bash
cd consultas-api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # ou, da raiz do repo: scripts/servidor.sh start
pytest -v
```

#### Teste automatizado

`consultas-api/tests/test_consultas.py::test_criar_e_obter_consulta_sucesso` cobre o caminho de sucesso (POST 201 → GET 200). Esse teste é **preservado** ao longo de todo o Assessment e continua existindo no Ex. 13.

#### Evidências

| Arquivo                                  | O que prova                                                     |
| ---------------------------------------- | --------------------------------------------------------------- |
| `evidencias/ex01/01_venv.txt`            | venv isolado criado e dependências instaladas                   |
| `evidencias/ex01/02_estrutura.txt`       | árvore de arquivos com `routes/`, `models/`, `database.py`      |
| `evidencias/ex01/03_uvicorn_startup.txt` | uvicorn subindo e respondendo `/health`                         |
| `evidencias/ex01/04_rotas_curl.txt`      | respostas HTTP reais de todas as operações do recurso consultas |
| `evidencias/ex01/05_pytest.txt`          | teste de sucesso passando                                       |
| `evidencias/ex01/06_swagger.png`         | rotas documentadas no Swagger                                   |

---

<a id="ex02"></a>

### Ex. 2 — Controle de exposição de dados e templates seguros

**Tag:** `ex02` · **Branch de demonstração:** `demo/ex02-sem-response-model` (commit `f3b26ec`)

#### 1. response_model controla exatamente os campos expostos

O registro armazenado de cada consulta tem campos internos de auditoria: `criado_por`, `ip_origem`, `criado_em`, `atualizado_em` (`consultas-api/app/routes/consultas.py`, no `criar_consulta`). O contrato público é outro modelo:

- `consultas-api/app/models/consulta.py:40`: `ConsultaPublic` (id, paciente_id, profissional_id, data_hora, status, observacoes). É uma **allowlist** de saída.
- `consultas-api/app/routes/consultas.py:16,21,27,49`: todas as rotas que devolvem consulta declaram `response_model=ConsultaPublic` (ou `list[ConsultaPublic]`).

O FastAPI valida e **filtra** o objeto retornado pela rota através do `response_model`: um campo que não está declarado em `ConsultaPublic` não sai na resposta, mesmo que exista no registro. Também separamos os modelos de **entrada** (`ConsultaCreate`/`ConsultaUpdate`: o que o cliente pode enviar) dos de **saída** (o que ele pode ver). Assim, nenhum dos dois contratos é derivado do modelo de persistência.

#### 2. Por que é arriscado não definir response_model

**Mecanismo.** Sem `response_model`, o FastAPI serializa *tudo* o que a função retorna (`jsonable_encoder` do objeto inteiro). A resposta passa a ser definida pelo **modelo de persistência**, não pelo contrato da API. Com isso:

1. **Todo campo interno vaza hoje.** Na evidência `ex02/01_sem_response_model_antes.txt`, o mesmo POST/GET devolve `criado_por`, `ip_origem` (IP de quem cadastrou) e os carimbos de data/hora.
2. **Todo campo adicionado no futuro também vaza.** Se amanhã alguém acrescentar `cpf`, `senha_hash` ou `anotacoes_clinicas` ao registro, eles aparecem na API sem nenhuma mudança na rota. Esse vazamento é silencioso e não é detectado em code review da rota, porque a rota não mudou.
3. **O filtro vira responsabilidade do cliente.** Confiar que o frontend "não mostra" o campo não adianta: o dado já trafegou e está visível no DevTools, em proxies e em logs.

**Por que isso é grave aqui.** O IP de origem, somado ao autor da operação e aos horários, permite **correlacionar e identificar** o paciente e a recepção/unidade que o atendeu, a partir do momento em que ele passou pelo sistema. Isso é o que o enunciado descreve no "caso público" ("um campo interno vazado facilitou a identificação de usuários por terceiros não autorizados"). O IP é dado pessoal (LGPD, art. 5º, I). Associado a uma consulta médica, ele passa a revelar dado **sensível** de saúde (art. 5º, II, e art. 11), que exige tratamento com salvaguardas reforçadas. Um vazamento assim é incidente comunicável à ANPD (art. 48).

**Classificação.**
- OWASP API Security Top 10:2023 → **API3:2023, Broken Object Property Level Authorization** (antiga "Excessive Data Exposure"): o cliente recebe propriedades do objeto que não deveria ver.
- OWASP Top 10:2021 → **A01:2021, Broken Access Control** (exposição de informação a ator não autorizado).
- **CWE-213** (Exposure of Sensitive Information Due to Incompatible Policies) / **CWE-200**.

**Prova executável.** `consultas-api/tests/test_consultas.py::test_sem_response_model_vazaria_campos_internos` registra a **mesma função de rota** em um app auxiliar *sem* `response_model` e verifica que os quatro campos de auditoria aparecem. No app real, eles não aparecem. A justificativa deixa de ser só texto e passa a ser um teste que falha se o comportamento mudar.

#### 3. Jinja2 com herança e auto-escape

- **Herança:** `consultas-api/app/templates/base.html:5,14,15` define o layout e os blocos `title`, `heading` e `content`. `agenda.html:1` faz `{% extends "base.html" %}` e só preenche os blocos. Cabeçalho, rodapé (aviso LGPD) e, depois, a CSP ficam em um único lugar.
- **Auto-escape explícito:** `consultas-api/app/routes/pages.py:16-19` cria o `Environment` com `autoescape=select_autoescape(["html"])`. Não dependemos do default implícito do Starlette: se alguém trocar o loader ou a forma de instanciar, o escape continua declarado no código.
- **O que o escape faz:** `{{ c.observacoes }}` (`agenda.html:21`) converte `<`, `>`, `&`, `"` e `'` em entidades HTML. O navegador exibe `<script>` como **texto** e não o executa.
- **Por que `|safe` nunca deve ser usado em conteúdo de usuário:** `|safe` (ou `Markup()`) marca a string como "HTML confiável" e **desliga o escape** naquele ponto. Um único `|safe` sobre `observacoes` basta para transformar o campo em XSS **stored**: o payload fica gravado no banco e executa no navegador de *toda* recepcionista que abrir a agenda, com acesso à sessão dela. Esse é o segundo incidente citado no enunciado. No Ex. 8 isso é demonstrado de propósito (V3).
- **Minimização na página:** `pages.py` monta um dicionário só com hora, nome, profissional, status e observações. CPF e campos de auditoria nem chegam ao template.

**JSON sem escape é o correto.** Em `ex02/03_xss_post_payload.txt`, a API JSON devolve `observacoes` com `<script>` cru. Isso não é falha. O encoding de saída depende do **contexto** em que o dado é renderizado: JSON é dado, não markup. Quem insere o valor em HTML (o Jinja2 aqui, ou o frontend via `textContent`) é que deve codificar para aquele contexto. Escapar no JSON corromperia o dado para outros consumidores e daria falsa sensação de segurança (a mesma string pode ir para um atributo, uma URL ou JS, e cada um exige um encoding diferente). A validação na **entrada** (rejeitar `<`/`>` em `observacoes`) entra no Ex. 9 como defesa em profundidade, não como substituto do escape.

#### Evidências

| Arquivo | O que prova |
|---|---|
| `evidencias/ex02/01_sem_response_model_antes.txt` | commit `f3b26ec` (branch demo): sem response_model, POST e GET vazam os 4 campos de auditoria |
| `evidencias/ex02/02_com_response_model_depois.txt` | **mesmo comando** em `main`: só os campos de `ConsultaPublic` |
| `evidencias/ex02/03_xss_post_payload.txt` | payloads `<script>` e `<img onerror>` gravados (JSON devolve cru, correto) |
| `evidencias/ex02/04_agenda_html_escapada.txt` | HTML contém `&lt;script&gt;`; contagem de `<script` = 0 |
| `evidencias/ex02/05_agenda_escapada.png` (+ `.txt`) | página exibe o payload como texto, `dialogs=0` (nenhum alert disparado) |
| `evidencias/ex02/06_pytest.txt` | 4 testes verdes, incluindo o teste do vazamento sem response_model |

---

<a id="ex03"></a>

### Ex. 3 — Tríade CIA, frameworks de referência e DFD

**Tag:** `ex03` · **Estado analisado:** tag `ex02` (API sem autenticação, persistência em memória)

> Referências usadas em toda a entrega: **OWASP Top 10:2021**, **OWASP API Security Top 10:2023**, **NIST SSDF (SP 800-218)** e **MITRE CAPEC / ATT&CK / CWE**.

#### 1. Tríade CIA aplicada à API de consultas

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

#### 2. Frameworks de referência → controles concretos

| Framework | Item | Controle concreto nesta aplicação | Onde (código / exercício) |
|---|---|---|---|
| OWASP API Top 10:2023 | **API3** Broken Object Property Level Authorization | `response_model=ConsultaPublic` (saída) e modelos de entrada sem campos sensíveis | `app/routes/consultas.py:16-49`, `app/models/consulta.py:34-47` · reforço com `extra='forbid'` no Ex. 9 |
| OWASP API Top 10:2023 | **API1** Broken Object Level Authorization | *lacuna*: ownership centralizado em `get_consulta_autorizada` | Ex. 6 e Ex. 9 |
| OWASP API Top 10:2023 | **API2** Broken Authentication | *lacuna*: OAuth2 + bcrypt + JWT curto + MFA | Ex. 6 |
| OWASP API Top 10:2023 | **API4** Unrestricted Resource Consumption | `max_length` já existe; rate limit | `app/models/consulta.py:26` · Ex. 10 |
| OWASP Top 10:2021 | **A03** Injection (inclui XSS) | auto-escape Jinja2; tipagem Pydantic; SQL parametrizado | `app/routes/pages.py:16-19` · Ex. 11 |
| OWASP Top 10:2021 | **A05** Security Misconfiguration | CORS com allowlist, headers de segurança | Ex. 10 |
| NIST SSDF | **PO.1** Definir requisitos de segurança | requisitos derivados do threat model (Ex. 4) | [Ex. 4](#ex04) |
| NIST SSDF | **PW.1** Projetar software para atender requisitos e mitigar riscos | threat model + DFD + partições | Ex. 3, Ex. 4, Ex. 5 |
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

#### 3. DFD — fronteiras de confiança e fluxos sensíveis

![DFD](docs/img/dfd.png)

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

#### Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/dfd.png` / `docs/img/dfd.mmd` | DFD com as 3 trust boundaries e os fluxos PHI destacados |
| `evidencias/ex02/*` | os controles de C (response_model, auto-escape) citados na tabela CIA funcionam |

---

<a id="ex04"></a>

### Ex. 4 — Misuse cases, STRIDE e threat model consolidado

**Tag:** `ex04`

> Documento de referência oficial da entrega. Os IDs `MCxx` (misuse cases) e `Txx` (ameaças) são **estáveis** e citados depois:
> - nas vulnerabilidades do Ex. 8 ([Ex. 8](#ex08));
> - nas docstrings dos testes `consultas-api/tests/security/test_Txx_*.py` (Ex. 12);
> - no relatório de rastreabilidade do capstone (`RELATORIO_RASTREABILIDADE_DR2_AT.md`).
>
> As colunas **"Teste que prova"** e **"Evidência"** da tabela da seção 4 começam como `(pendente)` e são preenchidas conforme cada mitigação é implementada. É isso que torna o modelo rastreável de ponta a ponta.
>
> **Nota sobre payloads:** este documento descreve os vetores de forma conceitual. As strings de exploração concretas ficam apenas onde têm função de prova — nos comandos capturados por `scripts/evidencia.sh` (Ex. 8/9) e nos testes automatizados — nunca transcritas na prosa.

Base: DFD do Ex. 3 (`docs/img/dfd.png`). Superfícies consideradas: as rotas atuais e as já decididas para os próximos exercícios (`/auth/*`, `/pacientes`, `/consultas/{id}/prontuario`, `/horarios-disponiveis`, `/admin/*`, `/recepcao/*`).

---

#### 1. Misuse cases

Formato: **ator · objetivo · pré-condição · passos (conceituais) · rota real · STRIDE → ameaça**.

##### MC01 — Troca de identificador para ler dados clínicos de terceiro (BOLA)
- **Ator:** usuário autenticado (ex.: o profissional Dr. Diego) com um token legítimo.
- **Objetivo:** ler prontuário/anotações de um paciente que não está sob seus cuidados.
- **Passos:** obtém um JWT válido; acessa uma consulta própria; substitui o identificador do recurso na URL por outros valores sequenciais; a API responde com dados de pacientes de outro profissional, por não checar posse do recurso.
- **Rotas:** `GET /consultas/{id}`, `GET /consultas/{id}/prontuario`, `PATCH`/`DELETE /consultas/{id}`, página de detalhe da recepção.
- **STRIDE:** Information Disclosure, Elevation of Privilege → **T01**.

##### MC02 — Injeção na busca textual de pacientes
- **Ator:** usuário autenticado com acesso à busca (recepção/profissional).
- **Objetivo:** contornar o filtro da busca para ler registros fora do escopo e, no limite, extrair credenciais.
- **Passos:** usa o parâmetro de busca por nome como ponto de entrada; em vez de um nome, envia conteúdo que altera a estrutura da consulta ao banco, aproveitando que o valor é concatenado direto na query em vez de parametrizado.
- **Rota:** `GET /pacientes?nome=`.
- **STRIDE:** Tampering, Information Disclosure → **T02**.

##### MC03 — Comentário malicioso persistido que executa no navegador da recepção (XSS stored)
- **Ator:** quem consegue gravar o campo livre `observacoes` (usuário autenticado; ou, antes da autenticação, qualquer um).
- **Objetivo:** executar script no navegador de toda recepcionista que abrir a agenda, sequestrando a sessão.
- **Passos:** grava markup ativo no campo de observações; a página de detalhe renderiza esse campo sem escape (uso indevido de `|safe`), e o script roda no contexto da recepção.
- **Rotas:** `POST /consultas` (gravação) → página de detalhe/agenda da recepção (execução).
- **STRIDE:** Tampering, Elevation of Privilege → **T03**.

##### MC04 — Token do laboratório usado para alcançar dados de paciente
- **Ator:** quem obtém o token M2M do laboratório parceiro (vazamento/comprometimento).
- **Objetivo:** ler ou criar consultas (PHI) com uma credencial que deveria ver só horários livres.
- **Passos:** apresenta o token M2M às rotas de consultas; se o escopo não for verificado, a credencial ultrapassa o combinado em contrato.
- **Rotas:** `GET/POST /consultas*` com token de escopo `horarios:read`.
- **STRIDE:** Elevation of Privilege, Information Disclosure → **T07** (escopo) e reforça **T01**.

##### MC05 — Força bruta no login
- **Ator:** atacante externo não autenticado.
- **Objetivo:** descobrir a senha de um profissional/admin por tentativa e erro.
- **Passos:** repete requisições ao endpoint de token com muitas combinações de senha, sem qualquer limite de taxa.
- **Rota:** `POST /auth/token`.
- **STRIDE:** Spoofing, Denial of Service → **T05** e **T10**.

##### MC06 — Campos extras no corpo para se apropriar de uma consulta (mass assignment)
- **Ator:** usuário autenticado.
- **Objetivo:** alterar campos que não deveriam ser editáveis pelo cliente (ex.: dono da consulta, autor do registro).
- **Passos:** inclui no corpo do PATCH/POST campos além dos declarados; se o modelo aceitar chaves extras e fizer atribuição em massa, o cliente sobrescreve `profissional_id`/`criado_por`.
- **Rota:** `PATCH /consultas/{id}`, `POST /consultas`.
- **STRIDE:** Tampering, Elevation of Privilege → **T06**.

---

#### 2. STRIDE por componente

Ameaça concreta ou "n/a" com o motivo. Componentes escolhidos: os quatro processos do DFD.

##### 2.1 `/auth/*` (login, MFA, token M2M)
| STRIDE | Ameaça nesta API |
|---|---|
| **S** poofing | passar-se por um usuário: força bruta de senha (**T05**), token forjado/assinatura inválida (**T04**) |
| **T** ampering | alterar claims do JWT (papel, sub) se a assinatura não for verificada (**T04**) |
| **R** epudiation | login sem trilha de auditoria — não se sabe quem tentou/entrou (**T09**) |
| **I** nfo disclosure | mensagem de erro que distingue "usuário não existe" de "senha errada" (enumeração) → mitigado por resposta genérica (**T05**) |
| **D** oS | flood no login sem rate limit (**T10**) |
| **E** levation | conta comum obtém privilégio de admin sem MFA (**T08**) |

##### 2.2 `/consultas/{id}` e `/consultas/{id}/prontuario`
| STRIDE | Ameaça |
|---|---|
| **S** | acesso sem token (rota hoje aberta) → mitigado por `OAuth2PasswordBearer` (**T01**) |
| **T** | mass assignment via campos extras no PATCH (**T06**) |
| **R** | alteração de consulta sem registro de autor (**T09**) |
| **I** | **BOLA**: ler consulta/prontuário de terceiro (**T01**) |
| **D** | enumeração de IDs sequenciais para varrer a base (**T01**, risco residual no Ex. 13) |
| **E** | profissional agindo sobre paciente de outro profissional (**T01**) |

##### 2.3 `/recepcao/*` (páginas HTML)
| STRIDE | Ameaça |
|---|---|
| **S** | acesso à agenda sem autenticação da recepção → cookie de sessão (**T01**) |
| **T** | **XSS stored** via `observacoes` renderizado sem escape (**T03**) |
| **R** | n/a direto (páginas são leitura); a gravação ocorre em `/consultas` |
| **I** | agenda expõe mais dado do que o necessário (CPF) → minimização no `pages.py` |
| **D** | página pesada sob flood → rate limit global (**T10**) |
| **E** | recepcionista alcançar rota de admin (**T08**) |

##### 2.4 Integração M2M (`/auth/client-token`, `/horarios-disponiveis`)
| STRIDE | Ameaça |
|---|---|
| **S** | cliente M2M sem `client_secret` forte / secret em texto (**T07**) |
| **T** | trocar `grant_type` para obter um token humano (**T07**) |
| **R** | ações do parceiro sem correlação (`client_type: m2m` nas claims) (**T09**) |
| **I** | token M2M alcançar PHI (**T07** + **T01**) |
| **D** | parceiro consumindo a API sem limite (**T10**) |
| **E** | escopo amplo demais concedido ao parceiro (**T07**) |

---

#### 3. Ativos

| Ativo | Sensibilidade | Onde vive |
|---|---|---|
| Dados de saúde (consultas, prontuário, observações) | **PHI / LGPD art. 11** | Banco, respostas JSON, agenda HTML |
| Credenciais e hashes de senha | crítico | Banco (bcrypt) |
| `JWT_SECRET_KEY` | crítico (assina todos os tokens) | `.env` (Ex. 11) |
| `client_secret` do laboratório | alto | Banco (bcrypt) |
| Segredo TOTP do admin | alto | Banco / `.env` |
| Logs / trilha de auditoria | médio (integridade) | `criado_por`, `atualizado_em` |

---

#### 4. Threat model consolidado (tabela rastreável)

STRIDE: S/T/R/I/D/E. As duas últimas colunas são preenchidas nas Etapas 10, 12 e 13.

| ID | Ameaça | STRIDE | Ativo | Superfície (rota) | Mitigação | Exercício | Teste que prova | Evidência |
|---|---|---|---|---|---|---|---|---|
| **T01** | BOLA em consulta/prontuário | I, E | dados de saúde | `GET/PATCH/DELETE /consultas/{id}`, `/prontuario`, detalhe HTML, **agenda HTML, `GET /pacientes`** | ownership centralizado (`get_consulta_autorizada`) num único `APIRouter`; **listagens filtradas por `profissional_id`** (CR3/CR4) | 6, 9, 13 | `test_correcoes::test_prontuario_bloqueia_outro_profissional`, `test_detalhe_html_bloqueia_outro_profissional`, `test_T01_agenda_html_so_mostra_proprias`, `test_T01_busca_pacientes_so_retorna_proprios` | `ex09/01,02` · `ex13/08→09` |
| **T02** | SQL injection na busca | T, I | dados de saúde, hashes | `GET /pacientes?nome=` | query parametrizada SQLModel + validação regex do parâmetro | 9, 11 | `test_correcoes::test_busca_pacientes_rejeita_injecao` | `ex09/03 antes→depois` |
| **T03** | XSS stored em `observacoes` | T, E | sessão da recepção | `POST /consultas` → agenda/detalhe HTML | auto-escape Jinja2 (sem `\|safe`) + rejeição de `<`/`>` na entrada | 2, 9 | `test_correcoes::test_observacoes_com_html_rejeitada_na_entrada`, `test_detalhe_html_escapa_conteudo` | `ex09/04 antes→depois` |
| **T04** | JWT forjado / expirado aceito | S, T | todas as sessões | qualquer rota autenticada | assinatura HS256 verificada + validação de `exp`/`iss`/`aud` | 6 | `test_auth::test_token_expirado_401`, `test_token_assinado_com_outra_chave_401` | `ex06/04` |
| **T05** | Força bruta de senha | S, D | credenciais | `POST /auth/token`, **`POST /recepcao/login`** | rate limit dedicado nas **duas** telas de login (CR2) + resposta genérica + MFA no admin | 10, 13 | `test_hardening::test_rate_limit_login`, `test_T05_login_html_limitado` | `ex10/02` · `ex13/08→09` |
| **T06** | Mass assignment | T, E | integridade da consulta | `POST`/`PATCH /consultas` | `extra='forbid'` + whitelist de campos; `profissional_id` vem do token | 9 | `test_correcoes::test_patch_rejeita_campos_extras`, `test_post_rejeita_campo_inexistente` | `ex09/05,06 antes→depois` |
| **T07** | Token M2M além do escopo | E, I | dados de saúde | `/consultas*` com token de laboratório | escopos OAuth (`horarios:read`) verificados por `Security(scopes=...)` | 7 | `test_m2m::test_lab_nao_acessa_consultas` | `ex07/04` |
| **T08** | Escalada de privilégio (recepção/prof → admin; admin sem MFA) | E | funções administrativas | `/admin/*`, **`POST /recepcao/login`** | RBAC (`require_roles`) + `require_mfa`; **login HTML recusa conta com MFA** (CR1) | 6, 13 | `test_auth::test_recepcionista_nao_acessa_rota_admin`, `test_admin_sem_mfa_barrado_e_com_mfa_liberado`, `test_T08_login_html_nao_contorna_mfa` | `ex06/07`, `ex06/11-13` · `ex13/08→09` |
| **T09** | Repúdio: ação sem trilha | R | integridade/auditoria | escrita em `/consultas`, `/auth` | `criado_por`=usuário autenticado, `atualizado_em`; log centralizado = risco residual | 6, 13 | (parcial) | `ex06/*` · RR4 no relatório |
| **T10** | DoS por volume / CORS permissivo | D, (S) | disponibilidade | toda a API; preflight CORS | rate limit global + CORS allowlist + headers | 10 | `test_hardening::test_cors_origem_fora_da_allowlist` | `ex10/01,05 antes→depois` |
| **T11** | Segredo hardcoded no código | I | `JWT_SECRET_KEY`, credenciais | código-fonte | `BaseSettings` + `.env` (fora do git); sem defaults para segredos | 11 | `test_T11_segredo` + `ex11/06` | `ex11/01→02` |
| **T12** | Falta de headers de segurança (clickjacking, sniffing, downgrade) | T, I | sessão da recepção | respostas HTTP | HSTS, X-Frame-Options, X-Content-Type-Options, CSP | 10 | `test_hardening::test_headers_de_seguranca_presentes`, `test_csp_nas_paginas_html` | `ex10/03 antes→depois` |

> **Atualização do Ex. 13 (code review).** A revisão de código do estado final achou superfícies de T01, T05 e T08 que esta tabela não listava: a agenda HTML e a busca de pacientes sem filtro de posse, e o login HTML (`/recepcao/login`) sem rate limit e sem MFA. Os quatro achados (CR1–CR4) foram corrigidos com teste. Detalhes em `RELATORIO_RASTREABILIDADE_DR2_AT.md` §2.1.

#### Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/dfd.png` | superfícies e fronteiras que embasam os componentes STRIDE |
| tabela da seção 4 | ativos, superfícies e mitigações com colunas de rastreio (preenchidas nos Ex. 9–13) |

---

<a id="ex05"></a>

### Ex. 5 — Arquitetura de segurança, partições e vetores nos três eixos

**Tag:** `ex05`

Complementa o threat model (Ex. 4) com a visão de **partições** e **fronteiras de segurança**, e mapeia vetores nos **três eixos de segurança de APIs**: design, implementação e infraestrutura.

#### 1. Partições do sistema

![Partições](docs/img/particoes.png)

Fonte: `docs/img/particoes.mmd`. Cada requisição atravessa as partições de cima para baixo; uma partição só confia no que a anterior já validou.

| Partição | Responsabilidade | Fronteira de segurança | Módulo (destino) |
|---|---|---|---|
| **P1 · Borda** | CORS allowlist, headers de segurança, rate limit | fronteira de rede: tudo que entra é não confiável | `app/core/` (Ex. 10) |
| **P2 · Autenticação** | provar identidade: OAuth2 + JWT + bcrypt + MFA | fronteira de identidade: separa anônimo de autenticado | `app/auth/security.py`, `app/auth/dependencies.py` (Ex. 6) |
| **P3 · Autorização** | decidir o que o principal pode: RBAC + ownership + escopos | fronteira de privilégio: separa "autenticado" de "autorizado para *este* recurso" | `app/auth/dependencies.py` (Ex. 6/7/9) |
| **P4 · Domínio** | regra de negócio de consultas/pacientes/horários + validação de entrada | — (já dentro da zona confiável) | `app/routes/`, `app/models/` |
| **P5 · Persistência** | acesso a dados com queries parametrizadas; segredos fora do código | fronteira API ↔ banco: onde a injeção se concretiza | `app/database.py`, `app/core/config.py` (Ex. 11) |
| **P6 · Apresentação** | renderizar HTML com escape por contexto | fronteira de saída: separa dado de markup | `app/templates/`, `app/routes/pages.py` |

**Princípio central: nenhuma lógica de segurança duplicada.** Autenticação, autorização, ownership, configuração e headers vivem em `app/auth/` e `app/core/`. As rotas do domínio (P4) apenas *declaram* de quais dependências precisam (`Depends`, `Security`). Uma rota nunca reimplementa a checagem de posse — ela herda `get_consulta_autorizada`. Isso é o que o enunciado exige e o que o Ex. 9 comprova com `grep` (a regra de ownership existe em um único arquivo).

#### 2. Fluxo de dados entre as partições

1. Cliente → **P1**: a borda decide se a origem é aceitável (CORS), impõe limite de taxa e adiciona headers na resposta.
2. **P1 → P2**: rotas protegidas exigem um Bearer válido; a identidade (`sub`, `role`/`scope`, `mfa`) é extraída do JWT.
3. **P2 → P3**: com a identidade conhecida, decide-se o acesso: papel (RBAC), posse do recurso (ownership) ou escopo (M2M).
4. **P3 → P4**: só então o domínio processa; a entrada é validada por Pydantic (`extra='forbid'`, regex) antes de virar ação.
5. **P4 → P5**: escrita/leitura por query parametrizada; credenciais vêm de `BaseSettings`.
6. **P4 → P6**: quando a saída é HTML, o Jinja2 escapa por contexto. Quando é JSON, `response_model` filtra os campos.

#### 3. Vetores de ataque nos três eixos

| Eixo | Vetor | Partição | Ameaça (Ex. 4) | Mitigação planejada (exercício) |
|---|---|---|---|---|
| **Design** | ausência de ownership → BOLA | P3 | T01 | `get_consulta_autorizada` centralizada (Ex. 6/9) |
| **Design** | exposição excessiva de propriedades | P4/P6 | (API3) | `response_model` de saída (Ex. 2) |
| **Design** | escopo amplo demais para o parceiro | P3 | T07 | um único escopo `horarios:read` (Ex. 7) |
| **Design** | IDs sequenciais previsíveis (enumeração) | P4 | T01 | ownership barra o acesso; UUID = risco residual (Ex. 13) |
| **Design** | admin sem segundo fator | P2 | T08 | MFA TOTP obrigatório no admin (Ex. 6) |
| **Implementação** | SQL injection na busca | P5 | T02 | query parametrizada + regex no parâmetro (Ex. 9/11) |
| **Implementação** | XSS stored | P6 | T03 | auto-escape sem `\|safe` + rejeição de `<`/`>` (Ex. 9) |
| **Implementação** | mass assignment | P4 | T06 | `extra='forbid'` + whitelist; `profissional_id` do token (Ex. 9) |
| **Implementação** | validação fraca de entrada | P4 | T02/T06 | regex/whitelist, enum de status, transições validadas (Ex. 9) |
| **Implementação** | JWT forjado/expirado aceito | P2 | T04 | assinatura HS256 + `exp`/`iss`/`aud` (Ex. 6) |
| **Infraestrutura** | CORS `*` | P1 | T10 | allowlist explícita; falha se `*` (Ex. 10) |
| **Infraestrutura** | falta de HSTS/headers | P1 | T12 | HSTS, XFO, XCTO, CSP (Ex. 10) |
| **Infraestrutura** | segredos no código | P5 | T11 | `BaseSettings` + `.env` no `.gitignore` (Ex. 11) |
| **Infraestrutura** | ausência de rate limit (brute force/DoS) | P1 | T05/T10 | rate limit dedicado no login + global (Ex. 10) |

#### 4. Conclusão que orienta os Ex. 6 e 7

A partição de autenticação (P2) precisa atender **dois tipos de cliente com naturezas diferentes**, e isso define os fluxos OAuth:

- **Humanos (frontend, recepção):** há um usuário e uma senha. Fluxo **Resource Owner Password Credentials** com JWT de vida curta (15 min), papel (RBAC) e checagem de posse (ownership). O admin ganha MFA. → Ex. 6.
- **Laboratório (M2M):** não há usuário nem navegador, apenas duas máquinas com um segredo compartilhado. Fluxo **Client Credentials**, com um único escopo de leitura (`horarios:read`) e **sem** `role`. Mesmo comprometido, o token não alcança PHI, porque as rotas de consulta exigem escopos que nunca são emitidos para ele. → Ex. 7.

#### Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/particoes.png` / `.mmd` | partições e fronteiras de segurança do sistema |
| tabela da seção 3 | vetores mapeados nos três eixos, ligados às ameaças T01–T12 |

---

<a id="ex06"></a>

### Ex. 6 — Autenticação e autorização

**Tag:** `ex06` · Ameaças cobertas: T01, T04, T05, T08, T09

#### 1. Autenticação OAuth2 + bcrypt + JWT

- **Fluxo:** `OAuth2PasswordBearer(tokenUrl="/auth/token")` (`app/auth/dependencies.py:35`). O login recebe `username`/`password` como form OAuth2 (`app/routes/auth.py:44`).
- **Hashing bcrypt:** `hash_senha`/`verificar_senha` em `app/auth/security.py:26-36`, usando `bcrypt` diretamente (o `passlib` está sem manutenção e quebra com `bcrypt>=4`). Custo 12 rounds. Nenhuma senha em texto no código: o seed (`app/seed.py`) lê as senhas de variáveis de ambiente e só guarda o **hash**. Evidência `ex06/01_senhas_bcrypt.txt` mostra apenas hashes `$2b$12$…`.
- **JWT com expiração:** `criar_access_token` (`app/auth/security.py:41`) assina HS256 com claims `sub`, `iss`, `aud`, `iat`, `exp`. Tokens humanos expiram em **15 min** (`ACCESS_TOKEN_EXPIRE_MINUTES`). `decodificar_token` (`:59`) valida assinatura, expiração, emissor e audiência e exige a presença dessas claims. Evidência `ex06/02_login_e_claims.txt`: `exp - iat = 900s`. `ex06/04`: token expirado → 401.
- **Resposta genérica de login** (`app/routes/auth.py:37`): não distingue "usuário inexistente" de "senha errada", para não permitir enumeração de usuários (T05).

**Por que 15 minutos.** Um JWT é *stateless*: não há revogação sem infraestrutura extra (blocklist). Uma janela curta limita o dano de um token vazado. O frontend renova via novo login/refresh (o refresh token completo fica como evolução; ver risco residual no Ex. 13). Para o admin, o segundo fator reduz ainda mais o risco.

#### 2. MFA simulado (TOTP)

Contas com `totp_secret` (admin) têm login em duas etapas (`app/routes/auth.py:56-67`, `app/auth/mfa.py`):

1. `POST /auth/token` com senha correta → **não** devolve o access token; devolve `{"mfa_required": true, "mfa_token": ...}`, um JWT de 5 min com `scope: mfa_pending`.
2. `POST /auth/mfa/verify` com `{mfa_token, codigo}` → valida o TOTP (`pyotp`) e só então emite o access token, com `mfa: true` e `amr: ["pwd","otp"]`.

O `mfa_token` sozinho não abre nada: `get_current_user` rejeita `scope == "mfa_pending"` (`app/auth/dependencies.py:70`) e `/admin/usuarios` exige `require_mfa`. Evidência `ex06/05_mfa_fluxo.txt`: com o `mfa_token` a rota admin dá **403**; após o TOTP, **200**.

**O que o torna "simulado".** O algoritmo TOTP (RFC 6238) é o de produção. Falta o *enrollment* real (o segredo é semeado, não provisionado por um app autenticador escaneando um QR), o armazenamento do segredo por usuário num cofre, e códigos de recuperação. Trocar isso não muda a lógica de verificação.

#### 3. Autorização: RBAC + ownership (por que essa combinação)

Adotamos **RBAC para capacidades** e **autorização por recurso (ownership) para dados clínicos** — as duas juntas, cada uma no que faz melhor.

- **RBAC** (`require_roles`, `app/auth/dependencies.py:75`): três papéis fixos (recepcao, profissional, admin) governam *o que a pessoa pode fazer* (ex.: só admin lista usuários). Papel insuficiente → **403**. É simples e cobre bem um conjunto pequeno e estável de capacidades.
- **Ownership** (`get_consulta_autorizada`, `:96`): governa *sobre quais objetos*. Um profissional só acessa consultas dos seus pacientes (`consulta.profissional_id == token.profissional_id`). É a defesa direta contra **BOLA** (T01), que o RBAC sozinho não pega — ambos os profissionais têm o mesmo papel; o que muda é o dono do dado.

**Por que não ABAC puro.** ABAC (política sobre atributos arbitrários) seria complexidade sem ganho para 3 papéis e uma regra de posse. É o caminho de evolução natural se entrarem atributos como unidade/clínica, turno, ou consentimento do paciente — aí uma engine de políticas (ex.: OPA) se paga. Hoje, não.

**Centralização (exigência do enunciado).** A regra de posse existe em **um único lugar** (`get_consulta_autorizada`). As rotas só declaram `Depends(...)`. No Ex. 9 isso vira um `APIRouter` com a dependência no prefixo, de modo que nenhuma rota nova sob `/consultas/{id}` possa esquecê-la. O `grep` do Ex. 9 comprova que `profissional_id ==` aparece só em `dependencies.py`.

##### Matriz de permissões

| Rota | recepção | profissional | admin (+MFA) | laboratório (Ex. 7) |
|---|---|---|---|---|
| `GET /consultas` | todas | só as suas | todas | ✗ |
| `GET /consultas/{id}` | ✓ | só as suas | ✓ | ✗ |
| `PATCH /consultas/{id}` | só cancelar | só as suas | ✓ | ✗ |
| `DELETE /consultas/{id}` | ✗ | só as suas | ✓ | ✗ |
| `POST /consultas` | ✗ | só p/ pacientes próprios; `profissional_id` do paciente, não do body | ✓ | ✗ |
| `GET /recepcao/agenda` | ✓ (cookie) | só as suas | ✓ (Bearer com MFA; o login HTML recusa conta com MFA) | ✗ |
| `GET /admin/usuarios` | ✗ | ✗ | ✓ | ✗ |

**Decisão 403 × 404.** Falha de **papel** (RBAC) → **403** (você está autenticado, mas não tem essa capacidade). Falha de **posse** de objeto (BOLA) → **404** (não confirmamos sequer a existência de um recurso de terceiro). Isso evita que um profissional descubra, pela diferença entre 403 e 404, quais IDs de consulta existem. Registrado em [Ex. 3](#ex03) (a confidencialidade prevalece).

#### 4. Detalhes que fecham lacunas anteriores

- `criado_por` passa a ser o usuário autenticado (`app/routes/consultas.py:60`), fechando o `TODO` do Ex. 2 e dando trilha de autoria (T09, parcial).
- `profissional_id` é derivado do paciente no servidor (`:47`), não aceito do cliente — pré-mitiga mass assignment (T06), tratado a fundo no Ex. 9.
- A sessão da recepção usa cookie `HttpOnly`, `SameSite=Strict`, `Secure` em produção (`app/routes/pages.py:44-49`): `HttpOnly` impede que um XSS leia o cookie; `SameSite=Strict` reduz CSRF. A agenda exige sessão (evidência `ex06/09`: sem cookie → 401).
- **CORS provisório** `allow_origins=["*"]` (`app/main.py:24`) com comentário de revisão: é o estado "antes" da V5a, corrigido no Ex. 10.
- **Segredo hardcoded** em `security.py:17` (`# TODO Ex.11`): é o "antes" do Ex. 11, capturado em `ex11/01_segredo_hardcoded_antes.txt`.

#### Evidências

| Arquivo | O que prova |
|---|---|
| `ex06/01_senhas_bcrypt.txt` | só hashes `$2b$12$…` |
| `ex06/02_login_e_claims.txt` | claims + `exp-iat = 900s` |
| `ex06/03_sem_token_401.txt` | rota protegida sem token → 401 |
| `ex06/04_token_expirado_401.txt` | token expirado → 401 |
| `ex06/05_mfa_fluxo.txt` | mfa_token barrado (403) → TOTP → access (200) |
| `ex06/06_ownership_403.txt` | BOLA bloqueado: Diego → 404; Carla → 200 |
| `ex06/07_rbac_recepcao_admin_403.txt` | teste obrigatório: recepção → admin → 403 |
| `ex06/08_pytest.txt` | 13 testes verdes |
| `ex06/09_agenda_autenticada.png` | agenda só com sessão (sem cookie → 401) |
| `ex06/10_sem_token_401.png` | print HTTP **401**: `/consultas` sem sessão |
| `ex06/11_rbac_recepcao_403.png` | print HTTP **403** (RBAC): recepção em `/admin/usuarios` |
| `ex06/12_admin_sem_mfa_403.png` | print HTTP **403**: admin autenticado sem MFA em `/admin/usuarios` |
| `ex06/13_admin_com_mfa_200.png` | print HTTP **200**: mesmo admin após verificar o TOTP |
| `ex11/01_segredo_hardcoded_antes.txt` | segredo no código (antes do Ex. 11) |

Os prints 10–13 renderizam a **resposta HTTP real** no navegador com um banner do status (verde 2xx / vermelho 4xx), gerado por `scripts/print_tela.py`. Foram capturados sobre o código já no estado do Ex. 7 (o comportamento 401/403 do Ex. 6 permanece idêntico); o commit exato consta no cabeçalho de cada `.txt` correspondente.

---

<a id="ex07"></a>

### Ex. 7 — Integração M2M: fluxo OAuth, escopos e claims

**Tag:** `ex07` · Ameaça coberta: T07

#### 1. Qual fluxo OAuth 2.0 e por quê

O laboratório parceiro é uma **máquina**, não um usuário: não há navegador, não há dono de recurso presente para consentir. Isso descarta os demais fluxos:

| Fluxo | Serve aqui? | Por quê |
|---|---|---|
| Authorization Code (+ PKCE) | não | pressupõe um usuário humano num navegador consentindo |
| Resource Owner Password | não | não existe "usuário/senha" do laboratório; usar senha para máquina é antipadrão (credencial de longa vida, sem MFA) |
| Device Code | não | é para dispositivos sem teclado/navegador que ainda representam um usuário |
| **Client Credentials** | **sim** | autenticação de **aplicação para aplicação** com `client_id`/`client_secret`; é exatamente o cenário M2M |

Implementação: `POST /auth/client-token` com `grant_type=client_credentials` (`app/routes/m2m.py:16`). O `client_secret` é guardado com **bcrypt** (`app/seed.py`), nunca em texto. `grant_type` diferente → 400; secret errado → 401.

#### 2. Escopos e claims: humano × M2M

O token do laboratório (`app/routes/m2m.py:36`) carrega:
- `sub: "lab-parceiro"`, `client_type: "m2m"`, `scope: "horarios:read"`, **sem `role`/`papel`**, `exp` de **10 min**.

O token humano carrega `papel`, `profissional_id` e `scope` derivado do papel (`consultas:read consultas:write`). Comparação lado a lado em `ex07/02_claims_humano_vs_m2m.txt`.

| Claim | Humano (profissional) | M2M (laboratório) |
|---|---|---|
| `sub` | username | client_id |
| `papel` | profissional/recepcao/admin | — (ausente) |
| `scope` | `consultas:read consultas:write` | `horarios:read` |
| `client_type` | — | `m2m` |
| `profissional_id` | sim | — |
| `exp` | 15 min | 10 min |

#### 3. Garantia técnica do contrato (o requisito jurídico)

O enunciado exige que a limitação do parceiro seja **tecnicamente garantida**, não só contratual, **mesmo que o token vaze**. Duas barreiras independentes:

1. **Escopo mínimo na emissão:** o laboratório só recebe `horarios:read`. `consultas:read`/`consultas:write` nunca são emitidos para ele. A rota `/horarios-disponiveis` exige `Security(require_scopes, scopes=["horarios:read"])` (`app/routes/m2m.py:44`) e devolve **apenas horários livres, sem nenhum dado de paciente** (evidência `ex07/03`).
2. **Rejeição de token de máquina nas rotas humanas:** `get_current_user` recusa qualquer token com `client_type == "m2m"` (`app/auth/dependencies.py:66`). Assim, mesmo que o token do laboratório seja apresentado a `GET`/`POST /consultas`, a resposta é **403** (`ex07/04`). Um humano, por sua vez, não tem `horarios:read`, então não acessa a rota do parceiro (`test_humano_nao_acessa_horarios_sem_escopo`).

**Princípio do menor privilégio:** cada credencial recebe só o que precisa. O laboratório comprometido não vira um vazamento de PHI — ele alcança, no máximo, a grade de horários livres, que não identifica pacientes. Isso limita o raio de dano do cenário MC04/T07.

- `/auth/token` também rejeita o `client_id` do laboratório (`app/routes/auth.py:41`), evitando que a credencial de máquina seja usada num fluxo humano (`ex07/05`).

#### Evidências

| Arquivo | O que prova |
|---|---|
| `ex07/01_client_credentials.txt` | emissão do token M2M com `scope=horarios:read` |
| `ex07/02_claims_humano_vs_m2m.txt` | claims lado a lado (M2M sem papel, exp menor) |
| `ex07/03_lab_horarios_200.txt` | lab lê horários (200), resposta sem paciente |
| `ex07/04_lab_consultas_403.txt` | token do lab barrado em `/consultas` (403) |
| `ex07/05_lab_password_grant_rejeitado.txt` | lab não faz login humano; grant inválido → 400 |
| `ex07/06_pytest.txt` | 7 testes de M2M verdes |

---

<a id="ex08"></a>

### Ex. 8 — Identificação de vulnerabilidades OWASP Top 10

**Tag do estado vulnerável:** `ex08-vulneravel` · Referência: [Ex. 4](#ex04)

Este documento identifica padrões vulneráveis **lendo o código** (sem scanner), cobrindo mais de três categorias distintas do OWASP. Cada falha foi introduzida de propósito e marcada no código com `# VULN-Vn (intencional, Ex. 8)`. As correções são o Ex. 9 (entrada/saída) e o Ex. 10 (rede/abuso). As strings de exploração completas estão nas evidências `_antes` (capturadas sobre a tag `ex08-vulneravel`), não transcritas aqui.

> Cobertura de categorias: **A01** (BOLA), **A03** (SQLi e XSS), **A05** (CORS/headers), **A07** (brute force), **A08/API3** (mass assignment) — cinco categorias distintas, acima do mínimo de três.

#### V1 — BOLA em `GET /consultas/{id}/prontuario` (A01:2021 / API1:2023)

- **Local:** `app/routes/consultas.py` (rota `prontuario`, marcada `# VULN-V1`).
- **Padrão que chama atenção lendo o código:** a rota faz `session.get(Consulta, consulta_id)` e devolve os dados **sem** depender de `get_consulta_autorizada`. Ela usa `get_current_user` (exige estar logado) mas **não verifica posse do objeto**. Toda vez que uma rota recebe um id de recurso direto da URL e não passa pela dependência de ownership, é candidata a BOLA.
- **Impacto:** um profissional autenticado lê o prontuário (nome, CPF, observações clínicas) de paciente de **outro** profissional só trocando o id. É o cenário exato descrito no enunciado.
- **Ameaça:** **T01** · Misuse case **MC01**.
- **Evidência:** `ex09/01_V1_bola_prontuario_antes.txt` (Diego lê a consulta da Carla → 200 com CPF e observações).

#### V2 — SQL injection em `GET /pacientes?nome=` (A03:2021)

- **Local:** `app/routes/pacientes.py` (`# VULN-V2`).
- **Padrão:** o SQL é montado com **f-string** (`text(f"... LIKE '%{nome}%'")`). O valor do parâmetro entra no **texto** da query, não como parâmetro ligado. Qualquer `text(f"...")`/concatenação com entrada do usuário é sinal de injeção.
- **Impacto:** o parâmetro `nome` altera a estrutura da query. Nas evidências: (a) burla o filtro e retorna pacientes fora do escopo; (b) via `UNION SELECT` extrai `username` e `senha_hash` da tabela `usuario`. Vazamento de dados de saúde e de credenciais.
- **Ameaça:** **T02** · **MC02** · CAPEC-66.
- **Evidência:** `ex09/03_V2_sqli_antes.txt`.

#### V3 — XSS stored no detalhe da consulta (A03:2021 — XSS)

- **Local:** `app/templates/detalhe_consulta.html` (`# VULN-V3`), renderizado por `app/routes/pages.py` (`detalhe_consulta`).
- **Padrão:** o template aplica `| safe` sobre `observacoes` ("para manter quebras de linha"). `| safe` **desliga o auto-escape**. Conteúdo livre de usuário renderizado com `| safe` é XSS stored quase garantido.
- **Impacto:** markup ativo gravado em `observacoes` executa no navegador de quem abrir o detalhe. A evidência `ex09/04_V3_xss_antes.png` mostra o `alert()` **executando** (banner vermelho do print).
  - *Nota honesta sobre o `document.cookie`:* o print exibe o token porque o cookie injetado pelo Playwright não é `HttpOnly`. O cookie real da recepção **é** `HttpOnly` (`app/routes/pages.py`, `set_cookie(httponly=True)`), o que bloquearia **essa** exfiltração específica. Mas o XSS continua crítico: o script executa como a vítima (ações no lugar dela, captura de teclas, pivô). `HttpOnly` é defesa em profundidade, não desculpa para o XSS.
- **Ameaça:** **T03** · **MC03** · CAPEC-63.
- **Evidência:** `ex09/04_V3_xss_antes.txt` + `.png`.

#### V4 — Mass assignment em `PATCH /consultas/{id}` (A08:2021 / API3:2023, CWE-915)

- **Local:** `app/models/consulta.py` (`ConsultaUpdate` com `extra="allow"`, `# VULN-V4`) + `app/routes/consultas.py` (loop `setattr` sobre todos os campos recebidos).
- **Padrão:** o modelo de entrada aceita campos não declarados (`extra="allow"`) e a rota os aplica em massa com `setattr`. Modelo de entrada sem `extra="forbid"` + atribuição por loop é a assinatura de mass assignment.
- **Impacto:** o cliente envia `profissional_id`/`criado_por` no corpo e **sobrescreve** o dono e o autor da consulta. Na evidência, Carla reatribui a própria consulta para o profissional 2. Também: `POST` com `campo_inexistente` e `status` forçado é aceito sem erro (deveria ser 422).
- **Ameaça:** **T06** · **MC06**.
- **Evidência:** `ex09/05_V4_mass_assignment_antes.txt`, `ex09/06_extra_campo_antes.txt`.

#### V5 — Configuração de rede e abuso (corrigidas no Ex. 10)

| ID | Falha | Local | Categoria | Evidência |
|---|---|---|---|---|
| **V5a** | CORS `allow_origins=["*"]` — aceita qualquer origem | `app/main.py` (`# provisório`) | A05:2021 | `ex10/01_V5a_cors_antes.txt` (preflight de `evil.example` → `allow-origin: *`) |
| **V5b** | `POST /auth/token` sem rate limit → força bruta | `app/routes/auth.py` | A07:2021 | `ex10/02_V5b_bruteforce_antes.txt` (10× 401, nenhum 429) |
| **V5c** | Respostas sem HSTS / X-Frame-Options / X-Content-Type-Options | ausência de middleware | A05:2021 | `ex10/03_V5c_headers_antes.txt` (nenhum header presente) |

Ameaças: **T05**, **T10**, **T12**.

#### Resumo (rastreabilidade)

| V | Rota/arquivo | OWASP | Ameaça | Corrigida em |
|---|---|---|---|---|
| V1 | `/consultas/{id}/prontuario` | A01 / API1 | T01 | Ex. 9 |
| V2 | `/pacientes?nome=` | A03 | T02 | Ex. 9 |
| V3 | `detalhe_consulta.html` | A03 (XSS) | T03 | Ex. 9 |
| V4 | `ConsultaUpdate` / PATCH | A08 / API3 | T06 | Ex. 9 |
| V5a | CORS | A05 | T10 | Ex. 10 |
| V5b | `/auth/token` | A07 | T05 | Ex. 10 |
| V5c | headers | A05 | T12 | Ex. 10 |

---

<a id="ex09"></a>

### Ex. 9 — Correção de vulnerabilidades de entrada e saída

**Tag:** `ex09` (correção) sobre `ex08-vulneravel` (falha) · Ameaças: T01, T02, T03, T06

Cada correção usa o **mesmo comando/payload** do "antes"; só o commit muda. O corretor compara `_antes` (tag `ex08-vulneravel`) com `_depois` (tag `ex09`).

#### V1 — BOLA corrigida de forma centralizada

**Como:** as rotas de item migraram para um `item_router` cujo **prefixo** `/consultas/{consulta_id}` carrega `dependencies=[Depends(get_consulta_autorizada)]` (`app/routes/consultas.py`). `GET`, `PATCH`, `DELETE` e `/prontuario` herdam a checagem de posse. **Qualquer rota nova** sob esse prefixo é obrigada a passar pela verificação — é impossível esquecer, que era a causa da V1.

A regra de posse continua num **único lugar** (`app/auth/dependencies.py:113`), o que a evidência `ex09/08_ownership_centralizado.txt` comprova: a comparação `consulta.profissional_id == user...` só existe ali. As duas outras ocorrências de `profissional_id ==` são **filtros de listagem** (escopar a coleção que um profissional vê) — não decisões de posse sobre um objeto, e não reimplementam a regra.

| | Antes (`ex08-vulneravel`) | Depois (`ex09`) |
|---|---|---|
| Diego → `/consultas/1/prontuario` | 200 com CPF e observações | **404** |
| Evidência | `ex09/01_..._antes.txt` | `ex09/01_..._depois.txt` |

#### Endpoint irmão descoberto (exigência do enunciado)

**Como foi encontrado:** procurando no código o **mesmo padrão** da V1 — "rota que busca um recurso por id vindo da URL e o devolve sem passar por `get_consulta_autorizada`". O `grep` por `session.get(Consulta, ...)` fora do `item_router` revelou `GET /recepcao/consultas/{id}` (página de detalhe HTML), acessível ao papel profissional. Ele **não foi citado** no doc do Ex. 8 de propósito: é o achado do Ex. 9.

**Correção:** a página passou a usar a **mesma** dependência `get_consulta_autorizada` (`app/routes/pages.py`). Evidência `ex09/02`: Diego → **404**, Carla (dona) → **200**. Como as rotas de item herdam ownership do `item_router`, futuras páginas/rotas sob esse recurso não repetem a falha.

#### V2 — SQL injection corrigida

**Como:** a busca virou `select(Paciente).where(Paciente.nome.contains(nome))` (query parametrizada, `app/routes/pacientes.py`) **e** o parâmetro é validado por **whitelist/regex** `^[A-Za-zÀ-ÿ' ]{2,60}$` na borda (`Query(pattern=...)`).

Evidência `ex09/03_V2_sqli_depois.txt` (mesmos vetores do antes):
- payload com `=`/dígitos (`' OR 1=1`) → **422** (fora da whitelist);
- `UNION SELECT ...` longo → **422** (excede `max_length`);
- um nome legítimo com apóstrofo (`O'Brien`) → **200** e resultado `[]`: o valor é **literal**, ligado como parâmetro, não altera a estrutura da query. A extração de hashes via UNION do Ex. 8 deixou de funcionar.

Duas camadas: a regex barra a maioria dos vetores na borda; a parametrização garante que, mesmo um valor que passe pela regex (apóstrofo é válido em nomes), seja tratado como dado.

#### V3 — XSS stored corrigido

**Como:** removido o `| safe` do template (`app/templates/detalhe_consulta.html`); as quebras de linha agora vêm de CSS (`white-space: pre-line`), não de HTML. O auto-escape do Jinja2 volta a tratar `<`, `>` como texto. Camada extra: a entrada rejeita `<`/`>` (regex `^[^<>]*$` em `observacoes`).

| | Antes | Depois |
|---|---|---|
| POST `observacoes=<img onerror=...>` | aceito (200) | **422** (regex) |
| Página de detalhe | `alert()` **executa** (`ex09/04_..._antes.png`) | conteúdo como texto, **`dialogs=0`** (`ex09/04_..._depois.png`) |

#### V4 — Mass assignment corrigido

**Como:** `model_config = ConfigDict(extra="forbid")` em `ConsultaCreate` e `ConsultaUpdate` (`app/models/consulta.py`). Campos não declarados são **rejeitados** (422 `extra_forbidden`), não mais aplicados. `profissional_id` e `criado_por` não são campos de entrada. Somado: transições de status por **whitelist** (`TRANSICOES_VALIDAS`) e `status` só pelo enum.

| | Antes | Depois |
|---|---|---|
| PATCH com `profissional_id`, `criado_por` | aceito; consulta troca de dono | **422 extra_forbidden** (`ex09/05_..._depois`) |
| POST com `campo_inexistente` | aceito em silêncio | **422** (`ex09/06_..._depois`) |
| `status` inexistente / transição proibida | — | **422** (`ex09/07_regex_whitelist`) |

#### Evidências

| Arquivo (par antes/depois) | Prova |
|---|---|
| `ex09/01_V1_bola_prontuario_*` | BOLA: 200 → 404 |
| `ex09/02_V1irmao_detalhe_html_*` | endpoint irmão: 200 → 404 (dona 200) |
| `ex09/03_V2_sqli_*` | SQLi: extração → 422 / literal |
| `ex09/04_V3_xss_*` (.txt + .png) | XSS: alert executa → rejeitado/escapado |
| `ex09/05_V4_mass_assignment_*` | mass assignment: aceito → 422 |
| `ex09/06_extra_campo_*` | campo extra: aceito → 422 |
| `ex09/07_regex_whitelist.txt` | válido × inválido (nome, status, transição) |
| `ex09/08_ownership_centralizado.txt` | posse decidida só em `dependencies.py` |
| `ex09/09_pytest.txt` | 29 testes verdes |

---

<a id="ex10"></a>

### Ex. 10 — Hardening de rede e proteção contra abuso

**Tag:** `ex10` (corrige V5a/V5b/V5c) · Ameaças: T05, T10, T12

#### 1. CORS com allowlist explícita (V5a)

**Como:** `CORSMiddleware` com `allow_origins=settings.cors_origins_list` (`app/main.py`), lido de `CORS_ORIGINS` (env/.env). Métodos e headers são **listas explícitas** (`GET, POST, PATCH, DELETE, OPTIONS`; `Authorization, Content-Type`). **Fail-fast:** se `*` aparecer na lista, a aplicação **não sobe** (`RuntimeError`) — o auditor do enunciado reprova wildcard.

**Por que wildcard + credenciais é proibido:** `allow_origins=["*"]` com `allow_credentials=True` deixaria qualquer site ler respostas autenticadas da API no navegador da vítima (o cookie/o header seguem junto). É a falha exata que reprovou o serviço citado no enunciado.

| | Antes (`ex08-vulneravel`) | Depois (`ex10`) |
|---|---|---|
| Preflight de `evil.example` | `access-control-allow-origin: *` | **sem** allow-origin (bloqueado) |
| Preflight de `localhost:5173` (allowlist) | — | `allow-origin: http://localhost:5173` |
| Evidência | `ex10/01_..._antes` | `ex10/01_..._depois`, `ex10/04_cors_origem_permitida` |

#### 2. Cabeçalhos de segurança (V5c)

Middleware `SecurityHeadersMiddleware` (`app/core/security_headers.py`) em toda resposta:

| Header | Valor | O que mitiga |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | downgrade para HTTP / SSL stripping |
| `X-Frame-Options` | `DENY` | clickjacking (embutir a página em iframe) |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing (executar conteúdo com tipo errado) |
| `Referrer-Policy` | `no-referrer` | vazamento da URL interna como referer |
| `Content-Security-Policy` (só HTML) | `script-src 'none'`, `frame-ancestors 'none'`… | defesa extra contra XSS/clickjacking |

Evidência `ex10/03_V5c_headers_depois.txt`: HSTS/XFO/XCTO em `/health`; CSP adicional no GET de `/recepcao/login`.

#### 3. Rate limiting diferenciado (V5b)

`slowapi` (`app/core/rate_limit.py`): **5/minuto** nas rotas de autenticação (`/auth/token`, `/auth/mfa/verify`, `/auth/client-token`) e **120/minuto** global. Resposta 429 quando excede.

**Por que o login tem limite mais estrito:** é o alvo de **força bruta** (o enunciado cita tentativas em testes anteriores). Cinco tentativas por minuto por IP inviabilizam a adivinhação de senha sem atrapalhar um usuário legítimo, enquanto as rotas de leitura toleram muito mais requisições.

| | Antes | Depois |
|---|---|---|
| 10 logins errados | 10× 401, nenhum 429 | 5× 401, depois **429** (`ex10/02_..._depois`) |
| 15 GETs em rota comum | — | todos 200, **sem 429** (`ex10/05_rate_limit_diferenciado`) |

**Limitação (risco residual, Ex. 13):** o contador do `slowapi` é **em memória**. Com múltiplas réplicas atrás de um load balancer, cada processo tem seu próprio contador, e o limite efetivo se multiplica. Em produção, usar um storage compartilhado (Redis). Registrado como risco residual no capstone.

#### Evidências

| Arquivo (par) | Prova |
|---|---|
| `ex10/01_V5a_cors_*` | CORS: `*` para evil → bloqueado |
| `ex10/04_cors_origem_permitida.txt` | origem da allowlist é aceita |
| `ex10/02_V5b_bruteforce_*` | login: sem 429 → 429 na 6ª |
| `ex10/05_rate_limit_diferenciado.txt` | rota comum tolera 15 GETs |
| `ex10/03_V5c_headers_*` | headers ausentes → presentes (+CSP) |
| `ex10/06_pytest.txt` | testes de hardening |

---

<a id="ex11"></a>

### Ex. 11 — Persistência segura (SQLModel + BaseSettings)

**Tag:** `ex11` · Ameaças cobertas: T11 (segredo), pré-requisito de T02 (SQLi) · Ameaça associada ao commit ordenado: `ex11`

#### Por que este exercício foi antecipado (executado como Etapa 8)

O plano executou o Ex. 11 **antes** dos Ex. 8–10. Motivo: a vulnerabilidade de **SQL injection** do Ex. 8 (V2) só é realista, e só pode ser demonstrada, sobre uma **camada de persistência SQL real**. Com o armazenamento em dicionários Python (Ex. 1–7), não há SQL para injetar — uma "SQLi" ali seria encenação. Migrando a persistência primeiro, a falha do Ex. 8 é introduzida e explorada sobre o banco de verdade, e a correção do Ex. 9 (parametrização) passa a ter significado. Os documentos seguem numerados pelo exercício.

#### 1. Migração para SQLModel com queries parametrizadas

- **Tabelas** (`app/models/tables.py`): `Profissional`, `Paciente`, `Consulta` (com os campos de auditoria), `Usuario`, `ClienteM2M`. Os schemas Pydantic de entrada/saída (`app/models/consulta.py`) continuam **separados** das tabelas — o contrato da API não é o modelo do banco.
- **Engine e sessão** (`app/database.py`): `create_engine` a partir de `Settings.database_url`; `get_session()` injeta a sessão via `Depends` com `yield` (abre/fecha por request). `criar_tabelas()` roda no `lifespan`.
- **Queries parametrizadas:** todo acesso usa `select(...).where(...)` ou `session.get(...)`. **Nenhum `text()` com f-string.** A evidência `ex11/04_queries_parametrizadas_log.txt` (com `DB_ECHO=1`) mostra o SQL emitido como `WHERE paciente.nome = ?` e os valores em uma tupla separada (`('Ana Souza',)`): o valor nunca vira parte do texto da query, então não pode alterar sua estrutura. É o oposto do que o Ex. 8/V2 fará de propósito.
- **Injeção de sessão nas rotas:** todas as rotas passaram a receber `session: Session = Depends(get_session)`; a lógica de negócio não mudou, só a origem dos dados. `get_consulta_autorizada` agora faz `session.get(Consulta, id)` mantendo-se como ponto único de ownership.

#### 2. Credenciais fora do código (BaseSettings + .env)

- `app/core/config.py`: `class Settings(BaseSettings)` com `model_config = SettingsConfigDict(env_file=".env")`. Todos os parâmetros vêm do ambiente.
- **Sem default para segredos:** `jwt_secret_key`, `seed_senha_*` e `lab_client_secret` **não têm valor padrão**. Se faltarem, o `Settings()` lança `ValidationError` e a aplicação **não sobe** (evidência `ex11/06_falha_sem_segredo.txt`). Falhar cedo é melhor do que rodar com um segredo previsível — um `JWT_SECRET_KEY` default permitiria a qualquer pessoa forjar tokens válidos (T04).
- **Segredo removido do código:** o `SECRET_KEY` hardcoded que existia em `security.py` (Ex. 6, capturado em `ex11/01_segredo_hardcoded_antes.txt`) foi substituído por `get_settings().jwt_secret_key`. A evidência `ex11/02_sem_credenciais_depois.txt` mostra o `grep` por segredo em `app/` **vazio** e o segredo vindo de `Settings`.
- **`.env` nunca versionado:** só `.env.example` (placeholders) vai no repositório/ZIP. `ex11/03_env_example.txt` mostra `git check-ignore` confirmando que `.env` está no `.gitignore` e que nenhum `.env` está versionado. Em DEV, `scripts/dev_env.sh` exporta valores fictícios equivalentes.

#### 3. Antes × depois

| Aspecto | Antes (Ex. 6, tag `ex06`) | Depois (Ex. 11, tag `ex11`) |
|---|---|---|
| Persistência | dicts em memória (`db.consultas`, …) | SQLModel + SQLite (`select().where()`) |
| Sessão | — | `Depends(get_session)` com `yield` |
| Segredo JWT | hardcoded em `security.py:17` | `Settings.jwt_secret_key` (env/.env) |
| Falta de segredo | app subia com segredo fraco | app **não sobe** (fail-fast) |
| Evidência | `ex11/01_segredo_hardcoded_antes.txt` | `ex11/02..06` |

#### Evidências

| Arquivo | O que prova |
|---|---|
| `ex11/01_segredo_hardcoded_antes.txt` | segredo no código (estado do Ex. 6) |
| `ex11/02_sem_credenciais_depois.txt` | `grep` de segredo em `app/` vazio; segredo vem de Settings |
| `ex11/03_env_example.txt` | `.env.example` com placeholders; `.env` ignorado |
| `ex11/04_queries_parametrizadas_log.txt` | SQL com `?` e parâmetros separados |
| `ex11/05_pytest.txt` | 20 testes verdes com SQLite em memória |
| `ex11/06_falha_sem_segredo.txt` | app recusa subir sem `JWT_SECRET_KEY` |

---

<a id="ex12"></a>

### Ex. 12 — Pipeline DevSecOps, CVSS e security gate

**Tag:** `ex12` · Workflow: `.github/workflows/security.yml`

#### 1. Testes de segurança rastreáveis ao threat model

`consultas-api/tests/security/` tem **um arquivo por ameaça** do Ex. 4 (`test_T01_bola.py` … `test_T12`). A docstring de cada arquivo cita a ameaça, o misuse case e [Ex. 4](#ex04). O teste de autorização iniciado no Ex. 6 (`test_recepcionista_nao_acessa_rota_admin`) foi **movido e expandido** para `test_T08_escalada_privilegio.py`, cobrindo: recepção→admin, profissional→admin, admin sem MFA, token M2M em rota humana. Os demais arquivos cobrem BOLA (GET/PATCH/DELETE/prontuário/HTML), SQLi, XSS, JWT forjado/expirado/aud, força bruta (429), mass assignment, escopo M2M, CORS e headers.

Evidência `ex12/04_pytest_security.txt` (nomes `test_T0x` visíveis) e `ex12/06_pytest_completo.txt` (56 testes).

#### 2. Priorização por CVSS + impacto de negócio

`scripts/cvss_scores.py` calcula os scores com a biblioteca `cvss` (evidência `ex12/01_cvss_scores.txt`).

| V-ID | Vetor CVSS 3.1 | Score | Sev. CVSS | Impacto de negócio | **Prioridade final** |
|---|---|---|---|---|---|
| V2 SQLi | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` | **8.8** | High | vaza pacientes **e** hashes → tomada de conta | **1 – Crítica** |
| T11 Segredo hardcoded | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` | 7.4 | High | forjar qualquer token | **2 – Crítica** |
| **V1 BOLA** | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` | **6.5** | **Medium** | **prontuário de terceiros (LGPD art. 11)** | **3 – Crítica ↑** |
| V4 Mass assignment | `AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N` | 6.5 | Medium | reatribuição de consultas | 4 – Alta |
| V5a CORS | `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` | 6.1 | Medium | leitura cross-origin autenticada | 5 – Alta |
| V5b Força bruta | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` | 5.9 | Medium | adivinhação de senha | 6 – Alta |
| V3 XSS | `AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N` | 5.4 | Medium | sessão da recepção | 7 – Média |
| V5c Headers | `AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N` | 4.2 | Medium | clickjacking/downgrade | 8 – Média |

**Onde o negócio muda a ordem do CVSS:** a **V1 (BOLA)** tem CVSS **6.5 Medium**, abaixo de V4/V5a numericamente próximos, mas **sobe para prioridade crítica**: ela expõe **prontuário de saúde de terceiros**, dado sensível sob LGPD art. 11, com incidente comunicável à ANPD e dano reputacional irreversível. O CVSS não "sabe" que o `C:H` aqui é dado de saúde de outra pessoa. É uma priorização que combina CVSS **e** impacto de negócio.

#### 3. Ferramentas × fase do SDLC, amarradas ao pipeline

| Tipo | Ferramenta | Fase do SDLC | Job/gatilho (`security.yml`) | Justificativa | Vuln. do histórico que pegaria |
|---|---|---|---|---|---|
| Estática (SAST) | Bandit | Implementação / a cada PR | `sast`, em `pull_request`+`push` | barata e rápida; roda sobre o código sem executá-lo | V2 (B608), T11 segredo (B105) |
| Dependências (SCA) | pip-audit | Build / PR + **agendado** | `sca`, PR + `schedule` semanal | CVEs surgem **sem** mudança no código; por isso o cron semanal | CVEs de pyjwt/python-multipart (achados e corrigidos) |
| Dinâmica (DAST) | OWASP ZAP baseline | Verificação, app **em execução** | `dast`, após subir a API | precisa da aplicação rodando; vê headers, cookies, respostas | V5c (headers), cookies |
| Interativa (IAST) | *não implementada* | Teste/QA em staging (instrumentado) | — | exige agente instrumentado e ambiente de QA dedicado; os testes `tests/security` cobrem parte do que um IAST veria (lógica de negócio/BOLA) | V1 (BOLA, lógica de negócio) |

O `schedule:` semanal roda o SCA mesmo sem commits, porque uma dependência estável pode ganhar um CVE a qualquer momento — foi o que aconteceu com `pyjwt`/`python-multipart` neste Assessment.

#### 4. ⚠️ DECISÃO DO WILLIAM — critério de bloqueio do gate

> **Proposta (a validar e reescrever por você, e explicar no vídeo).** O `security-gate` **bloqueia o merge** se:
> - (a) **qualquer teste** falhar (`tests`, inclui `tests/security`);
> - (b) **Bandit** reportar achado de **severidade ≥ MEDIUM em qualquer confiança** (`bandit -r app -ll`);
> - (c) **pip-audit** encontrar **qualquer CVE com correção disponível**;
> - **ZAP (DAST) é advisory:** roda como `continue-on-error` e **não** entra na decisão do `security-gate`. Um alerta **High** é triado a partir do artefato e vira correção priorizada; Medium/Low são ruído esperado num baseline passivo.
>
> **Justificativa amarrada ao histórico deste Assessment:**
> 1. **Por que Bandit sem filtro de confiança.** Descobri, medindo, que esta versão do Bandit reporta a nossa SQLi (V2, `B608`) como **severidade Medium mas confiança Low**. Um gate "Medium severidade **e** Medium confiança" (o `-ll -ii` que eu havia proposto no início) **teria deixado passar a V2**, que é a falha mais grave do Assessment (CVSS 8.8). Por isso o gate usa `-ll` (severidade Medium+, qualquer confiança). Evidência: `ex12/05_bandit_contra_ex08.txt` — Bandit no worktree da tag `ex08-vulneravel` acha o B608 e o gate sai com código ≠ 0. No código corrigido (`ex10`+), Bandit acha 0 Medium+ e o gate passa (`ex12/02`).
> 2. **Por que SCA bloqueia qualquer CVE com fix.** Se existe correção, o custo de aplicá-la é baixo e o risco de não aplicá-la é conhecido. Foi o caso de `pyjwt`/`python-multipart`: o SCA apontou, eu atualizei, e o `pip-audit` ficou limpo (`ex12/03`).
> 3. **Por que ZAP é advisory (não bloqueia).** Num baseline passivo de API, os Medium/Low típicos são headers extras (COEP/COOP/CORP, Permissions-Policy) e anti-CSRF — que já temos teste cobrindo (`tests/security/test_T10_T12_rede.py`). Além disso, o alcance de rede do container do ZAP no runner é frágil. Bloquear o merge por isso geraria falso-negativo de produtividade sem ganho de segurança, então o ZAP informa (artefato) e um eventual **High** é triado manualmente. Os bloqueios determinísticos ficam com `tests`, `sast` e `sca`.

O job `security-gate` tem `needs: [tests, sast, sca]` (o DAST roda em paralelo, como advisory) e consolida os resultados (`.github/workflows/security.yml`).

#### 5. Demonstração no GitHub

- Repositório `williamff11/dr2-at-consultas-api` com o ruleset `protect-main`: merge na `main` só por PR com o check `security-gate` verde (`ex12/08`, `ex12/09`).
- Pipeline verde na `main` (`ex12/10`).
- Branch `demo/gate-bloqueio` reintroduz a V2 (SQLi) → PR #1 com `sast`, `tests` e `security-gate` vermelhos e **merge bloqueado** (`ex12/07`, `ex12/11`). O log do `sast` mostra o Bandit achando o B608 (`ex12/12`). A falha do `tests` vem dos testes de regressão da T02 (`test_T02_valor_tratado_como_literal`): duas camadas independentes barram a mesma falha.

#### Evidências

| Arquivo | Prova |
|---|---|
| `ex12/01_cvss_scores.txt` | scores CVSS + prioridade por negócio |
| `ex12/02_bandit_local.txt` | Bandit 0 Medium+ no código atual (gate passa) |
| `ex12/03_pip_audit_local.txt` | SCA limpo após atualizar deps |
| `ex12/04_pytest_security.txt` | testes T0x rastreáveis ao threat model |
| `ex12/05_bandit_contra_ex08.txt` | **gate bloquearia a V2** (Bandit na tag vulnerável) |
| `ex12/06_pytest_completo.txt` | 56 testes verdes |
| `.github/workflows/security.yml` | pipeline com 5 jobs e o gate |
| `ex12/07`, `ex12/11`, `ex12/12` | PR #1 bloqueado pelo gate + log do Bandit (B608) |
| `ex12/08`, `ex12/09` | ruleset `protect-main` exigindo o `security-gate` |
| `ex12/10` | pipeline verde na `main` |

---

<a id="ex13"></a>

### Ex. 13 — Capstone: auditoria final, mocking e OpenAPI

**Tag:** `ex13` · Relatório principal: `RELATORIO_RASTREABILIDADE_DR2_AT.md`

#### 1. Testes unitários com mocking

`consultas-api/tests/test_unitarios_mock.py` isola a lógica das dependências externas:
- **`dependency_overrides[get_current_user]`**: simula papéis (recepção, profissional) sem gerar JWT real — testa RBAC/criação direto na lógica.
- **`patch` em `verificar_senha`**: login testado sem bcrypt real.
- **`patch` em `verificar_codigo` (TOTP)**: fluxo MFA sem depender do relógio TOTP.
- **controle do relógio** via `expira_em` negativo: expiração do JWT.
- **mock da sessão** (`SimpleNamespace`): a regra de ownership (`get_consulta_autorizada`) é testada **sem tocar o banco**, provando que ela decide só pelo `profissional_id`.
- **teste de sucesso do Ex. 1 preservado** (`test_ex1_criar_e_obter_sucesso`).

Evidência: `ex13/05_pytest_final.txt` (63 testes).

#### 2. Auditoria da especificação OpenAPI

`scripts/auditar_openapi.py` lê o `openapi.json` e aponta falhas de design (`ex13/04_auditoria_openapi.txt`). O que foi **corrigido** e o que ficou como **risco residual**:

| Apontamento | Ação |
|---|---|
| `/docs` e `/openapi.json` expostos | **corrigido**: `docs_url=None`, `redoc_url=None`, `openapi_url=None` quando `ENV=prod` (`app/main.py`) |
| Rotas de item sem 401/403 documentados | **corrigido**: `responses=` nos routers de consultas, admin, pacientes |
| Modelos de entrada sem `additionalProperties:false` | já garantido pelo `extra='forbid'` (Ex. 9) |
| `/horarios-disponiveis` e páginas HTML sem 401/403 na spec | **parcial**: protegidas por `Depends`; documentação da spec é risco baixo |
| `dia` (string) sem `pattern` em `/horarios-disponiveis` | risco residual baixo (validação de data feita na lógica) |
| **IDs inteiros sequenciais** | **risco residual aceito**: ownership já barra o acesso; UUID seria defesa extra contra enumeração |

#### 3. OWASP ZAP baseline passivo

Executado com Docker contra o estado final (comando em `RELATORIO_RASTREABILIDADE`). Resultado: **0 FAIL, 6 WARN (Medium/Low), 61 PASS**. Cada alerta é interpretado no relatório de rastreabilidade (verdadeiro/falso positivo, categoria OWASP, correção/decisão). Relatórios: `ex13/02_zap_baseline_depois.{html,json,md}`; resumo em `ex13/02_zap_resumo.txt`.

Nenhum alerta de risco **High** — coerente com as correções dos Ex. 9–10. Os WARN são majoritariamente headers extras (COEP/COOP/CORP, Permissions-Policy) e anti-CSRF na página de login, analisados no relatório.

#### 4. Regressão final das evidências

`scripts/regerar_evidencias_finais.sh` reexecuta os ataques dos Ex. 9–10 contra o **código final** e confirma que todas as correções seguem válidas (`ex13/regressao/regressao.txt`): BOLA→404, SQLi→422, XSS→422, mass assignment→422, CORS malicioso→sem allow-origin, HSTS presente.

#### 5. Revisão de código do estado final

Uma revisão manual do código final achou 8 pontos (CR1–CR8). Os quatro de maior impacto foram corrigidos com teste:
- **CR1:** admin contornava o MFA pelo login HTML.
- **CR2:** login HTML sem rate limit.
- **CR3:** agenda HTML sem ownership.
- **CR4:** busca de pacientes expunha CPF de outros profissionais.

O par antes/depois usa o mesmo comando: `ex13/08_code_review_antes.txt` (4 falham) e `ex13/09_code_review_depois.txt` (4 passam). A suíte completa tem 67 testes (`ex13/10_pytest_pos_code_review.txt`). Os demais pontos estão em aberto ou viraram risco residual (RR9, RR10). A tabela completa está em `RELATORIO_RASTREABILIDADE_DR2_AT.md` §2.1.

#### Evidências

| Arquivo | Prova |
|---|---|
| `ex13/02_zap_baseline_depois.{html,json,md}` + `02_zap_resumo.txt` | scan ZAP passivo |
| `ex13/03_openapi.json` | spec auditada |
| `ex13/04_auditoria_openapi.txt` | apontamentos de design |
| `ex13/05_pytest_final.txt` | 63 testes (mocking + segurança + Ex.1) |
| `ex13/regressao/regressao.txt` | correções válidas no código final |
| `ex13/08_code_review_antes.txt` → `09_code_review_depois.txt` | achados CR1–CR4: 4 testes falham antes e passam depois |
| `ex13/10_pytest_pos_code_review.txt` | 67 testes após as correções do code review |
