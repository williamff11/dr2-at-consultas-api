# Ex. 6 — Autenticação e autorização

**Rubrica:** R10, R11 · **Tag:** `ex06` · Ameaças cobertas: T01, T04, T05, T08, T09

## 1. Autenticação OAuth2 + bcrypt + JWT

- **Fluxo:** `OAuth2PasswordBearer(tokenUrl="/auth/token")` (`app/auth/dependencies.py:35`). O login recebe `username`/`password` como form OAuth2 (`app/routes/auth.py:44`).
- **Hashing bcrypt:** `hash_senha`/`verificar_senha` em `app/auth/security.py:26-36`, usando `bcrypt` diretamente (o `passlib` está sem manutenção e quebra com `bcrypt>=4`). Custo 12 rounds. Nenhuma senha em texto no código: o seed (`app/seed.py`) lê as senhas de variáveis de ambiente e só guarda o **hash**. Evidência `ex06/01_senhas_bcrypt.txt` mostra apenas hashes `$2b$12$…`.
- **JWT com expiração:** `criar_access_token` (`app/auth/security.py:41`) assina HS256 com claims `sub`, `iss`, `aud`, `iat`, `exp`. Tokens humanos expiram em **15 min** (`ACCESS_TOKEN_EXPIRE_MINUTES`). `decodificar_token` (`:59`) valida assinatura, expiração, emissor e audiência e exige a presença dessas claims. Evidência `ex06/02_login_e_claims.txt`: `exp - iat = 900s`. `ex06/04`: token expirado → 401.
- **Resposta genérica de login** (`app/routes/auth.py:37`): não distingue "usuário inexistente" de "senha errada", para não permitir enumeração de usuários (T05).

**Por que 15 minutos.** Um JWT é *stateless*: não há revogação sem infraestrutura extra (blocklist). Uma janela curta limita o dano de um token vazado. O frontend renova via novo login/refresh (o refresh token completo fica como evolução; ver risco residual no Ex. 13). Para o admin, o segundo fator reduz ainda mais o risco.

## 2. MFA simulado (TOTP)

Contas com `totp_secret` (admin) têm login em duas etapas (`app/routes/auth.py:56-67`, `app/auth/mfa.py`):

1. `POST /auth/token` com senha correta → **não** devolve o access token; devolve `{"mfa_required": true, "mfa_token": ...}`, um JWT de 5 min com `scope: mfa_pending`.
2. `POST /auth/mfa/verify` com `{mfa_token, codigo}` → valida o TOTP (`pyotp`) e só então emite o access token, com `mfa: true` e `amr: ["pwd","otp"]`.

O `mfa_token` sozinho não abre nada: `get_current_user` rejeita `scope == "mfa_pending"` (`app/auth/dependencies.py:70`) e `/admin/usuarios` exige `require_mfa`. Evidência `ex06/05_mfa_fluxo.txt`: com o `mfa_token` a rota admin dá **403**; após o TOTP, **200**.

**O que o torna "simulado".** O algoritmo TOTP (RFC 6238) é o de produção. Falta o *enrollment* real (o segredo é semeado, não provisionado por um app autenticador escaneando um QR), o armazenamento do segredo por usuário num cofre, e códigos de recuperação. Trocar isso não muda a lógica de verificação.

## 3. Autorização: RBAC + ownership (por que essa combinação)

Adotamos **RBAC para capacidades** e **autorização por recurso (ownership) para dados clínicos** — as duas juntas, cada uma no que faz melhor.

- **RBAC** (`require_roles`, `app/auth/dependencies.py:75`): três papéis fixos (recepcao, profissional, admin) governam *o que a pessoa pode fazer* (ex.: só admin lista usuários). Papel insuficiente → **403**. É simples e cobre bem um conjunto pequeno e estável de capacidades.
- **Ownership** (`get_consulta_autorizada`, `:96`): governa *sobre quais objetos*. Um profissional só acessa consultas dos seus pacientes (`consulta.profissional_id == token.profissional_id`). É a defesa direta contra **BOLA** (T01), que o RBAC sozinho não pega — ambos os profissionais têm o mesmo papel; o que muda é o dono do dado.

**Por que não ABAC puro.** ABAC (política sobre atributos arbitrários) seria complexidade sem ganho para 3 papéis e uma regra de posse. É o caminho de evolução natural se entrarem atributos como unidade/clínica, turno, ou consentimento do paciente — aí uma engine de políticas (ex.: OPA) se paga. Hoje, não.

**Centralização (exigência do enunciado).** A regra de posse existe em **um único lugar** (`get_consulta_autorizada`). As rotas só declaram `Depends(...)`. No Ex. 9 isso vira um `APIRouter` com a dependência no prefixo, de modo que nenhuma rota nova sob `/consultas/{id}` possa esquecê-la. O `grep` do Ex. 9 comprova que `profissional_id ==` aparece só em `dependencies.py`.

### Matriz de permissões

| Rota | recepção | profissional | admin (+MFA) | laboratório (Ex. 7) |
|---|---|---|---|---|
| `GET /consultas` | todas | só as suas | todas | ✗ |
| `GET /consultas/{id}` | ✓ | só as suas | ✓ | ✗ |
| `PATCH /consultas/{id}` | só cancelar | só as suas | ✓ | ✗ |
| `DELETE /consultas/{id}` | ✗ | só as suas | ✓ | ✗ |
| `POST /consultas` | ✗ | só p/ pacientes próprios; `profissional_id` do paciente, não do body | ✓ | ✗ |
| `GET /recepcao/agenda` | ✓ (cookie) | ✓ | ✓ | ✗ |
| `GET /admin/usuarios` | ✗ | ✗ | ✓ | ✗ |

**Decisão 403 × 404.** Falha de **papel** (RBAC) → **403** (você está autenticado, mas não tem essa capacidade). Falha de **posse** de objeto (BOLA) → **404** (não confirmamos sequer a existência de um recurso de terceiro). Isso evita que um profissional descubra, pela diferença entre 403 e 404, quais IDs de consulta existem. Registrado em `docs/03` (a confidencialidade prevalece).

## 4. Detalhes que fecham lacunas anteriores

- `criado_por` passa a ser o usuário autenticado (`app/routes/consultas.py:60`), fechando o `TODO` do Ex. 2 e dando trilha de autoria (T09, parcial).
- `profissional_id` é derivado do paciente no servidor (`:47`), não aceito do cliente — pré-mitiga mass assignment (T06), tratado a fundo no Ex. 9.
- A sessão da recepção usa cookie `HttpOnly`, `SameSite=Strict`, `Secure` em produção (`app/routes/pages.py:44-49`): `HttpOnly` impede que um XSS leia o cookie; `SameSite=Strict` reduz CSRF. A agenda exige sessão (evidência `ex06/09`: sem cookie → 401).
- **CORS provisório** `allow_origins=["*"]` (`app/main.py:24`) com comentário de revisão: é o estado "antes" da V5a, corrigido no Ex. 10.
- **Segredo hardcoded** em `security.py:17` (`# TODO Ex.11`): é o "antes" do Ex. 11, capturado em `ex11/01_segredo_hardcoded_antes.txt`.

## Evidências

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
| `ex11/01_segredo_hardcoded_antes.txt` | segredo no código (antes do Ex. 11) |
