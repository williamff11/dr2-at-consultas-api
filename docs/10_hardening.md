# Ex. 10 — Hardening de rede e proteção contra abuso

**Rubrica:** R17 · **Tag:** `ex10` (corrige V5a/V5b/V5c) · Ameaças: T05, T10, T12

## 1. CORS com allowlist explícita (V5a)

**Como:** `CORSMiddleware` com `allow_origins=settings.cors_origins_list` (`app/main.py`), lido de `CORS_ORIGINS` (env/.env). Métodos e headers são **listas explícitas** (`GET, POST, PATCH, DELETE, OPTIONS`; `Authorization, Content-Type`). **Fail-fast:** se `*` aparecer na lista, a aplicação **não sobe** (`RuntimeError`) — o auditor do enunciado reprova wildcard.

**Por que wildcard + credenciais é proibido:** `allow_origins=["*"]` com `allow_credentials=True` deixaria qualquer site ler respostas autenticadas da API no navegador da vítima (o cookie/o header seguem junto). É a falha exata que reprovou o serviço citado no enunciado.

| | Antes (`ex08-vulneravel`) | Depois (`ex10`) |
|---|---|---|
| Preflight de `evil.example` | `access-control-allow-origin: *` | **sem** allow-origin (bloqueado) |
| Preflight de `localhost:5173` (allowlist) | — | `allow-origin: http://localhost:5173` |
| Evidência | `ex10/01_..._antes` | `ex10/01_..._depois`, `ex10/04_cors_origem_permitida` |

## 2. Cabeçalhos de segurança (V5c)

Middleware `SecurityHeadersMiddleware` (`app/core/security_headers.py`) em toda resposta:

| Header | Valor | O que mitiga |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | downgrade para HTTP / SSL stripping |
| `X-Frame-Options` | `DENY` | clickjacking (embutir a página em iframe) |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing (executar conteúdo com tipo errado) |
| `Referrer-Policy` | `no-referrer` | vazamento da URL interna como referer |
| `Content-Security-Policy` (só HTML) | `script-src 'none'`, `frame-ancestors 'none'`… | defesa extra contra XSS/clickjacking |

Evidência `ex10/03_V5c_headers_depois.txt`: HSTS/XFO/XCTO em `/health`; CSP adicional no GET de `/recepcao/login`.

## 3. Rate limiting diferenciado (V5b)

`slowapi` (`app/core/rate_limit.py`): **5/minuto** nas rotas de autenticação (`/auth/token`, `/auth/mfa/verify`, `/auth/client-token`) e **120/minuto** global. Resposta 429 quando excede.

**Por que o login tem limite mais estrito:** é o alvo de **força bruta** (o enunciado cita tentativas em testes anteriores). Cinco tentativas por minuto por IP inviabilizam a adivinhação de senha sem atrapalhar um usuário legítimo, enquanto as rotas de leitura toleram muito mais requisições.

| | Antes | Depois |
|---|---|---|
| 10 logins errados | 10× 401, nenhum 429 | 5× 401, depois **429** (`ex10/02_..._depois`) |
| 15 GETs em rota comum | — | todos 200, **sem 429** (`ex10/05_rate_limit_diferenciado`) |

**Limitação (risco residual, Ex. 13):** o contador do `slowapi` é **em memória**. Com múltiplas réplicas atrás de um load balancer, cada processo tem seu próprio contador, e o limite efetivo se multiplica. Em produção, usar um storage compartilhado (Redis). Registrado como risco residual no capstone.

## Evidências

| Arquivo (par) | Prova |
|---|---|
| `ex10/01_V5a_cors_*` | CORS: `*` para evil → bloqueado |
| `ex10/04_cors_origem_permitida.txt` | origem da allowlist é aceita |
| `ex10/02_V5b_bruteforce_*` | login: sem 429 → 429 na 6ª |
| `ex10/05_rate_limit_diferenciado.txt` | rota comum tolera 15 GETs |
| `ex10/03_V5c_headers_*` | headers ausentes → presentes (+CSP) |
| `ex10/06_pytest.txt` | testes de hardening |
