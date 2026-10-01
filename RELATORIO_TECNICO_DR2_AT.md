# Relatório Técnico — DR2 AT

**Aluno:** William Felício Freire · **Disciplina:** Desenvolvimento Seguro de Aplicações Web
**Aplicação:** API de Agendamento de Consultas (FastAPI + SQLModel)

Este relatório resume as **decisões de segurança** de cada exercício e aponta para as seções detalhadas do `README.md` (uma por exercício) e as evidências (`evidencias/exNN/`). Referências: OWASP Top 10:2021 + OWASP API Security Top 10:2023, NIST SSDF, MITRE.

## Nota metodológica: antecipação do Ex. 11

A migração para SQLModel (Ex. 11) foi **antecipada** e executada antes dos Ex. 8–10. Motivo: a falha de SQL injection do Ex. 8 só é realista e demonstrável sobre uma camada de persistência SQL real — com dados em memória não haveria SQL a injetar. As seções do README seguem a numeração do exercício. Detalhes em [README, Ex. 11](README.md#ex11).

## Decisões por exercício

| Ex. | Decisão de segurança central | Por quê | Detalhe |
|---|---|---|---|
| 1 | venv isolado + módulos routes/models/database | reprodutibilidade, base para SCA, evitar rota-gigante | [README, Ex. 1](README.md#ex01) |
| 2 | `response_model` (allowlist de saída) + Jinja2 auto-escape | não vazar auditoria (API3) e não executar conteúdo de usuário (XSS) | [README, Ex. 2](README.md#ex02) |
| 3 | CIA com confidencialidade priorizada (dado de saúde/LGPD) + DFD | vazamento de PHI é irreversível; fronteiras guiam o threat model | [README, Ex. 3](README.md#ex03) |
| 4 | Threat model STRIDE rastreável (T01–T12) | referência única citada por testes e correções | [README, Ex. 4](README.md#ex04) |
| 5 | Partições + fronteiras + 3 eixos | orienta os fluxos OAuth (humano × M2M) | [README, Ex. 5](README.md#ex05) |
| 6 | OAuth2/JWT curto + bcrypt + **ownership centralizado** + MFA; RBAC + autorização por recurso | BOLA não é resolvido por RBAC; ownership num único lugar | [README, Ex. 6](README.md#ex06) |
| 7 | Client credentials com escopo único `horarios:read` | token do laboratório comprometido não alcança PHI | [README, Ex. 7](README.md#ex07) |
| 11 | SQLModel parametrizado + BaseSettings sem default de segredo | queries seguras; app não sobe sem segredo (fail-fast) | [README, Ex. 11](README.md#ex11) |
| 8 | Vulnerabilidades intencionais marcadas (`# VULN-Vn`) e identificadas lendo código | provar identificação sem scanner; 5 categorias OWASP | [README, Ex. 8](README.md#ex08) |
| 9 | `item_router` com ownership no prefixo; `extra='forbid'`; regex/whitelist; sem `\|safe`; endpoint irmão | correção centralizada, impossível de esquecer | [README, Ex. 9](README.md#ex09) |
| 10 | CORS allowlist (fail-fast se `*`), headers HSTS/XFO/XCTO/CSP, rate limit diferenciado | reprovação por wildcard; força bruta no login | [README, Ex. 10](README.md#ex10) |
| 12 | Pipeline (SAST/SCA/DAST/gate); gate Bandit em severidade Medium+ **sem** filtro de confiança | a SQLi é Medium/conf-Low; filtrar confiança deixaria passar a pior falha | [README, Ex. 12](README.md#ex12) |
| 13 | ZAP passivo interpretado + mocking + auditoria OpenAPI + risco residual | rastreabilidade completa e decisão de deploy | [README, Ex. 13](README.md#ex13), `RELATORIO_RASTREABILIDADE_DR2_AT.md` |

## Princípio transversal: nenhuma lógica de segurança duplicada

Autenticação, autorização, ownership, configuração e headers vivem em `app/auth/` e `app/core/`. As rotas apenas declaram `Depends`/`Security`. A regra de posse (anti-BOLA) existe em **um único ponto** (`app/auth/dependencies.py`), comprovado por `grep` em `evidencias/ex09/08_ownership_centralizado.txt`.

## Mapa de evidências por tema

| Tema | Evidência |
|---|---|
| venv/uvicorn/módulos | `ex01/01–06`, [README, Ex. 1](README.md#ex01) |
| response_model | `ex02/02`, testes |
| justificar exposição | `ex02/01`, [README, Ex. 2](README.md#ex02) |
| Jinja2 auto-escape | `ex02/03–05` |
| CIA + frameworks | [README, Ex. 3](README.md#ex03) |
| DFD trust boundaries | `docs/img/dfd.png` |
| misuse cases | [README, Ex. 4](README.md#ex04) |
| STRIDE rastreável | [README, Ex. 4](README.md#ex04) (T01–T12) |
| 3 eixos | [README, Ex. 5](README.md#ex05) |
| OAuth2+bcrypt+ownership | `ex06/01,02,06` |
| JWT/MFA/RBAC×ABAC | `ex06/02,05,11–13`, [README, Ex. 6](README.md#ex06) |
| M2M escopos/claims | `ex07/*`, [README, Ex. 7](README.md#ex07) |
| identificar OWASP lendo código | [README, Ex. 8](README.md#ex08), `ex09/*_antes` |
| BOLA centralizada | `ex09/01,02,08` |
| whitelist/regex/extra=forbid | `ex09/03,05,06,07` |
| XSS auto-escape | `ex09/04` (+png) |
| CORS/headers/rate limit | `ex10/*` |
| SQLModel/BaseSettings | `ex11/*` |
| fase SDLC no pipeline | [README, Ex. 12](README.md#ex12), `security.yml` |
| CVSS + negócio | `ex12/01`, [README, Ex. 12](README.md#ex12) |
| security gate (critério de bloqueio) | `security.yml`, `ex12/05`, 👤 prints do PR |
| testes rastreáveis ao threat model | `tests/security/`, `ex12/04` |
| ZAP + rastreabilidade + risco residual + decisão | `ex13/02`, `RELATORIO_RASTREABILIDADE` |
| mocking + OpenAPI | `tests/test_unitarios_mock.py`, `ex13/04,05` |

## Pendências manuais (William)

Ver `evidencias/PRINTS_PENDENTES.md`: criação do repositório GitHub e prints do gate bloqueando o merge, validação do critério do gate, decisão sobre o deploy e o vídeo (≤5 min, YouTube não listado).
