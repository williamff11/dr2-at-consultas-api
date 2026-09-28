# Ex. 5 — Arquitetura de segurança, partições e vetores nos três eixos

**Rubrica:** R9 · **Tag:** `ex05`

Complementa o threat model (Ex. 4) com a visão de **partições** e **fronteiras de segurança**, e mapeia vetores nos **três eixos de segurança de APIs**: design, implementação e infraestrutura.

## 1. Partições do sistema

![Partições](img/particoes.png)

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

## 2. Fluxo de dados entre as partições

1. Cliente → **P1**: a borda decide se a origem é aceitável (CORS), impõe limite de taxa e adiciona headers na resposta.
2. **P1 → P2**: rotas protegidas exigem um Bearer válido; a identidade (`sub`, `role`/`scope`, `mfa`) é extraída do JWT.
3. **P2 → P3**: com a identidade conhecida, decide-se o acesso: papel (RBAC), posse do recurso (ownership) ou escopo (M2M).
4. **P3 → P4**: só então o domínio processa; a entrada é validada por Pydantic (`extra='forbid'`, regex) antes de virar ação.
5. **P4 → P5**: escrita/leitura por query parametrizada; credenciais vêm de `BaseSettings`.
6. **P4 → P6**: quando a saída é HTML, o Jinja2 escapa por contexto. Quando é JSON, `response_model` filtra os campos.

## 3. Vetores de ataque nos três eixos

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

## 4. Conclusão que orienta os Ex. 6 e 7

A partição de autenticação (P2) precisa atender **dois tipos de cliente com naturezas diferentes**, e isso define os fluxos OAuth:

- **Humanos (frontend, recepção):** há um usuário e uma senha. Fluxo **Resource Owner Password Credentials** com JWT de vida curta (15 min), papel (RBAC) e checagem de posse (ownership). O admin ganha MFA. → Ex. 6.
- **Laboratório (M2M):** não há usuário nem navegador, apenas duas máquinas com um segredo compartilhado. Fluxo **Client Credentials**, com um único escopo de leitura (`horarios:read`) e **sem** `role`. Mesmo comprometido, o token não alcança PHI, porque as rotas de consulta exigem escopos que nunca são emitidos para ele. → Ex. 7.

## Evidências

| Arquivo | O que prova |
|---|---|
| `docs/img/particoes.png` / `.mmd` | partições e fronteiras de segurança do sistema |
| tabela da seção 3 | vetores mapeados nos três eixos, ligados às ameaças T01–T12 |
