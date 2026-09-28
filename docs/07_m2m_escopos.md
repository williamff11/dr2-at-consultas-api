# Ex. 7 — Integração M2M: fluxo OAuth, escopos e claims

**Rubrica:** R12 · **Tag:** `ex07` · Ameaça coberta: T07

## 1. Qual fluxo OAuth 2.0 e por quê

O laboratório parceiro é uma **máquina**, não um usuário: não há navegador, não há dono de recurso presente para consentir. Isso descarta os demais fluxos:

| Fluxo | Serve aqui? | Por quê |
|---|---|---|
| Authorization Code (+ PKCE) | não | pressupõe um usuário humano num navegador consentindo |
| Resource Owner Password | não | não existe "usuário/senha" do laboratório; usar senha para máquina é antipadrão (credencial de longa vida, sem MFA) |
| Device Code | não | é para dispositivos sem teclado/navegador que ainda representam um usuário |
| **Client Credentials** | **sim** | autenticação de **aplicação para aplicação** com `client_id`/`client_secret`; é exatamente o cenário M2M |

Implementação: `POST /auth/client-token` com `grant_type=client_credentials` (`app/routes/m2m.py:16`). O `client_secret` é guardado com **bcrypt** (`app/seed.py`), nunca em texto. `grant_type` diferente → 400; secret errado → 401.

## 2. Escopos e claims: humano × M2M

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

## 3. Garantia técnica do contrato (o requisito jurídico)

O enunciado exige que a limitação do parceiro seja **tecnicamente garantida**, não só contratual, **mesmo que o token vaze**. Duas barreiras independentes:

1. **Escopo mínimo na emissão:** o laboratório só recebe `horarios:read`. `consultas:read`/`consultas:write` nunca são emitidos para ele. A rota `/horarios-disponiveis` exige `Security(require_scopes, scopes=["horarios:read"])` (`app/routes/m2m.py:44`) e devolve **apenas horários livres, sem nenhum dado de paciente** (evidência `ex07/03`).
2. **Rejeição de token de máquina nas rotas humanas:** `get_current_user` recusa qualquer token com `client_type == "m2m"` (`app/auth/dependencies.py:66`). Assim, mesmo que o token do laboratório seja apresentado a `GET`/`POST /consultas`, a resposta é **403** (`ex07/04`). Um humano, por sua vez, não tem `horarios:read`, então não acessa a rota do parceiro (`test_humano_nao_acessa_horarios_sem_escopo`).

**Princípio do menor privilégio:** cada credencial recebe só o que precisa. O laboratório comprometido não vira um vazamento de PHI — ele alcança, no máximo, a grade de horários livres, que não identifica pacientes. Isso limita o raio de dano do cenário MC04/T07.

- `/auth/token` também rejeita o `client_id` do laboratório (`app/routes/auth.py:41`), evitando que a credencial de máquina seja usada num fluxo humano (`ex07/05`).

## Evidências

| Arquivo | O que prova |
|---|---|
| `ex07/01_client_credentials.txt` | emissão do token M2M com `scope=horarios:read` |
| `ex07/02_claims_humano_vs_m2m.txt` | claims lado a lado (M2M sem papel, exp menor) |
| `ex07/03_lab_horarios_200.txt` | lab lê horários (200), resposta sem paciente |
| `ex07/04_lab_consultas_403.txt` | token do lab barrado em `/consultas` (403) |
| `ex07/05_lab_password_grant_rejeitado.txt` | lab não faz login humano; grant inválido → 400 |
| `ex07/06_pytest.txt` | 7 testes de M2M verdes |
