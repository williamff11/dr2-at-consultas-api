---
titulo: "DR2 AT — API de Agendamento de Consultas"
aluno: "William Felício Freire"
disciplina: "Desenvolvimento Seguro de Aplicações Web"
data: "2026-09-30"
video: "<!-- LINK DO VÍDEO YOUTUBE (não listado) -->"
---

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
| `admin` | admin | exige MFA (TOTP) |
| `recepcao` | recepção | páginas HTML |
| `dra_carla` | profissional | pacientes: Ana (id 1) |
| `dr_diego` | profissional | pacientes: Bruno (id 2) |
| `lab-parceiro` | M2M | escopo `horarios:read` |

(senhas de DEV em `scripts/dev_env.sh`)

## Estrutura da entrega

```
William_Felicio_Freire_DR2_AT/
├── William_Felicio_Freire_DR2_AT.md      ← este documento
├── RELATORIO_TECNICO_DR2_AT.md           ← decisões de segurança por exercício
├── RELATORIO_RASTREABILIDADE_DR2_AT.md   ← capstone (Ex. 13)
├── .github/workflows/security.yml        ← pipeline DevSecOps
├── docs/                                  ← 01_*.md … 13_*.md + img/ (DFD, partições)
├── evidencias/                            ← ex01/ … ex13/ + INDICE.md + PRINTS_PENDENTES.md
├── scripts/                              ← evidencia.sh, servidor.sh, token.sh, cvss_scores.py, …
└── consultas-api/                        ← código (app/, tests/, requirements.txt, .env.example)
```

## Índice dos documentos

| Doc | Exercício | Rubricas |
|---|---|---|
| `docs/01_fundacao.md` | 1 | R1 |
| `docs/02_exposicao_templates.md` | 2 | R2, R3, R4 |
| `docs/03_cia_frameworks_dfd.md` | 3 | R5, R6 |
| `docs/04_threat_model.md` | 4 | R7, R8 |
| `docs/05_arquitetura.md` | 5 | R9 |
| `docs/06_autenticacao_autorizacao.md` | 6 | R10, R11 |
| `docs/07_m2m_escopos.md` | 7 | R12 |
| `docs/08_vulnerabilidades.md` | 8 | R13 |
| `docs/09_correcoes.md` | 9 | R14, R15, R16 |
| `docs/10_hardening.md` | 10 | R17 |
| `docs/11_persistencia.md` | 11 | R18 |
| `docs/12_pipeline_devsecops.md` | 12 | R19, R20, R21, R22 |
| `docs/13_capstone.md` | 13 | R23, R24 |

Índice das evidências: `evidencias/INDICE.md`. Rastreabilidade completa: `RELATORIO_RASTREABILIDADE_DR2_AT.md`.

## Roteiro do vídeo (≤ 5 min)

1. **0:00–0:30** estrutura e DFD (`docs/img/dfd.png`).
2. **0:30–1:30** login com MFA, BOLA bloqueada (Diego → 404), token do laboratório barrado.
3. **1:30–2:30** antes × depois de uma falha (SQLi ou XSS).
4. **2:30–3:45** pipeline e **critério do gate** (explicado com suas palavras — R21).
5. **3:45–5:00** capstone: ZAP, risco residual e **decisão de deploy** (R23).
