# Ex. 8 — Identificação de vulnerabilidades OWASP Top 10

**Rubrica:** R13 · **Tag do estado vulnerável:** `ex08-vulneravel` · Referência: `docs/04_threat_model.md`

Este documento identifica padrões vulneráveis **lendo o código** (sem scanner), cobrindo mais de três categorias distintas do OWASP. Cada falha foi introduzida de propósito e marcada no código com `# VULN-Vn (intencional, Ex. 8)`. As correções são o Ex. 9 (entrada/saída) e o Ex. 10 (rede/abuso). As strings de exploração completas estão nas evidências `_antes` (capturadas sobre a tag `ex08-vulneravel`), não transcritas aqui.

> Cobertura de categorias: **A01** (BOLA), **A03** (SQLi e XSS), **A05** (CORS/headers), **A07** (brute force), **A08/API3** (mass assignment) — cinco categorias distintas, acima do mínimo de três.

## V1 — BOLA em `GET /consultas/{id}/prontuario` (A01:2021 / API1:2023)

- **Local:** `app/routes/consultas.py` (rota `prontuario`, marcada `# VULN-V1`).
- **Padrão que chama atenção lendo o código:** a rota faz `session.get(Consulta, consulta_id)` e devolve os dados **sem** depender de `get_consulta_autorizada`. Ela usa `get_current_user` (exige estar logado) mas **não verifica posse do objeto**. Toda vez que uma rota recebe um id de recurso direto da URL e não passa pela dependência de ownership, é candidata a BOLA.
- **Impacto:** um profissional autenticado lê o prontuário (nome, CPF, observações clínicas) de paciente de **outro** profissional só trocando o id. É o cenário exato descrito no enunciado.
- **Ameaça:** **T01** · Misuse case **MC01**.
- **Evidência:** `ex09/01_V1_bola_prontuario_antes.txt` (Diego lê a consulta da Carla → 200 com CPF e observações).

## V2 — SQL injection em `GET /pacientes?nome=` (A03:2021)

- **Local:** `app/routes/pacientes.py` (`# VULN-V2`).
- **Padrão:** o SQL é montado com **f-string** (`text(f"... LIKE '%{nome}%'")`). O valor do parâmetro entra no **texto** da query, não como parâmetro ligado. Qualquer `text(f"...")`/concatenação com entrada do usuário é sinal de injeção.
- **Impacto:** o parâmetro `nome` altera a estrutura da query. Nas evidências: (a) burla o filtro e retorna pacientes fora do escopo; (b) via `UNION SELECT` extrai `username` e `senha_hash` da tabela `usuario`. Vazamento de dados de saúde e de credenciais.
- **Ameaça:** **T02** · **MC02** · CAPEC-66.
- **Evidência:** `ex09/03_V2_sqli_antes.txt`.

## V3 — XSS stored no detalhe da consulta (A03:2021 — XSS)

- **Local:** `app/templates/detalhe_consulta.html` (`# VULN-V3`), renderizado por `app/routes/pages.py` (`detalhe_consulta`).
- **Padrão:** o template aplica `| safe` sobre `observacoes` ("para manter quebras de linha"). `| safe` **desliga o auto-escape**. Conteúdo livre de usuário renderizado com `| safe` é XSS stored quase garantido.
- **Impacto:** markup ativo gravado em `observacoes` executa no navegador de quem abrir o detalhe. A evidência `ex09/04_V3_xss_antes.png` mostra o `alert()` **executando** (banner vermelho do print).
  - *Nota honesta sobre o `document.cookie`:* o print exibe o token porque o cookie injetado pelo Playwright não é `HttpOnly`. O cookie real da recepção **é** `HttpOnly` (`app/routes/pages.py`, `set_cookie(httponly=True)`), o que bloquearia **essa** exfiltração específica. Mas o XSS continua crítico: o script executa como a vítima (ações no lugar dela, captura de teclas, pivô). `HttpOnly` é defesa em profundidade, não desculpa para o XSS.
- **Ameaça:** **T03** · **MC03** · CAPEC-63.
- **Evidência:** `ex09/04_V3_xss_antes.txt` + `.png`.

## V4 — Mass assignment em `PATCH /consultas/{id}` (A08:2021 / API3:2023, CWE-915)

- **Local:** `app/models/consulta.py` (`ConsultaUpdate` com `extra="allow"`, `# VULN-V4`) + `app/routes/consultas.py` (loop `setattr` sobre todos os campos recebidos).
- **Padrão:** o modelo de entrada aceita campos não declarados (`extra="allow"`) e a rota os aplica em massa com `setattr`. Modelo de entrada sem `extra="forbid"` + atribuição por loop é a assinatura de mass assignment.
- **Impacto:** o cliente envia `profissional_id`/`criado_por` no corpo e **sobrescreve** o dono e o autor da consulta. Na evidência, Carla reatribui a própria consulta para o profissional 2. Também: `POST` com `campo_inexistente` e `status` forçado é aceito sem erro (deveria ser 422).
- **Ameaça:** **T06** · **MC06**.
- **Evidência:** `ex09/05_V4_mass_assignment_antes.txt`, `ex09/06_extra_campo_antes.txt`.

## V5 — Configuração de rede e abuso (corrigidas no Ex. 10)

| ID | Falha | Local | Categoria | Evidência |
|---|---|---|---|---|
| **V5a** | CORS `allow_origins=["*"]` — aceita qualquer origem | `app/main.py` (`# provisório`) | A05:2021 | `ex10/01_V5a_cors_antes.txt` (preflight de `evil.example` → `allow-origin: *`) |
| **V5b** | `POST /auth/token` sem rate limit → força bruta | `app/routes/auth.py` | A07:2021 | `ex10/02_V5b_bruteforce_antes.txt` (10× 401, nenhum 429) |
| **V5c** | Respostas sem HSTS / X-Frame-Options / X-Content-Type-Options | ausência de middleware | A05:2021 | `ex10/03_V5c_headers_antes.txt` (nenhum header presente) |

Ameaças: **T05**, **T10**, **T12**.

## Resumo (rastreabilidade)

| V | Rota/arquivo | OWASP | Ameaça | Corrigida em |
|---|---|---|---|---|
| V1 | `/consultas/{id}/prontuario` | A01 / API1 | T01 | Ex. 9 |
| V2 | `/pacientes?nome=` | A03 | T02 | Ex. 9 |
| V3 | `detalhe_consulta.html` | A03 (XSS) | T03 | Ex. 9 |
| V4 | `ConsultaUpdate` / PATCH | A08 / API3 | T06 | Ex. 9 |
| V5a | CORS | A05 | T10 | Ex. 10 |
| V5b | `/auth/token` | A07 | T05 | Ex. 10 |
| V5c | headers | A05 | T12 | Ex. 10 |
