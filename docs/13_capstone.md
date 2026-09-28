# Ex. 13 — Capstone: auditoria final, mocking e OpenAPI

**Rubrica:** R23, R24 · **Tag:** `ex13` · Relatório principal: `RELATORIO_RASTREABILIDADE_DR2_AT.md`

## 1. Testes unitários com mocking (R24)

`consultas-api/tests/test_unitarios_mock.py` isola a lógica das dependências externas:
- **`dependency_overrides[get_current_user]`**: simula papéis (recepção, profissional) sem gerar JWT real — testa RBAC/criação direto na lógica.
- **`patch` em `verificar_senha`**: login testado sem bcrypt real.
- **`patch` em `verificar_codigo` (TOTP)**: fluxo MFA sem depender do relógio TOTP.
- **controle do relógio** via `expira_em` negativo: expiração do JWT.
- **mock da sessão** (`SimpleNamespace`): a regra de ownership (`get_consulta_autorizada`) é testada **sem tocar o banco**, provando que ela decide só pelo `profissional_id`.
- **teste de sucesso do Ex. 1 preservado** (`test_ex1_criar_e_obter_sucesso`), como a R24 exige explicitamente.

Evidência: `ex13/05_pytest_final.txt` (63 testes).

## 2. Auditoria da especificação OpenAPI (R24)

`scripts/auditar_openapi.py` lê o `openapi.json` e aponta falhas de design (`ex13/04_auditoria_openapi.txt`). O que foi **corrigido** e o que ficou como **risco residual**:

| Apontamento | Ação |
|---|---|
| `/docs` e `/openapi.json` expostos | **corrigido**: `docs_url=None`, `redoc_url=None`, `openapi_url=None` quando `ENV=prod` (`app/main.py`) |
| Rotas de item sem 401/403 documentados | **corrigido**: `responses=` nos routers de consultas, admin, pacientes |
| Modelos de entrada sem `additionalProperties:false` | já garantido pelo `extra='forbid'` (Ex. 9) |
| `/horarios-disponiveis` e páginas HTML sem 401/403 na spec | **parcial**: protegidas por `Depends`; documentação da spec é risco baixo |
| `dia` (string) sem `pattern` em `/horarios-disponiveis` | risco residual baixo (validação de data feita na lógica) |
| **IDs inteiros sequenciais** | **risco residual aceito**: ownership já barra o acesso; UUID seria defesa extra contra enumeração |

## 3. OWASP ZAP baseline passivo (R23)

Executado com Docker contra o estado final (comando em `RELATORIO_RASTREABILIDADE`). Resultado: **0 FAIL, 6 WARN (Medium/Low), 61 PASS**. Cada alerta é interpretado no relatório de rastreabilidade (verdadeiro/falso positivo, categoria OWASP, correção/decisão). Relatórios: `ex13/02_zap_baseline_depois.{html,json,md}`; resumo em `ex13/02_zap_resumo.txt`.

Nenhum alerta de risco **High** — coerente com as correções dos Ex. 9–10. Os WARN são majoritariamente headers extras (COEP/COOP/CORP, Permissions-Policy) e anti-CSRF na página de login, analisados no relatório.

## 4. Regressão final das evidências

`scripts/regerar_evidencias_finais.sh` reexecuta os ataques dos Ex. 9–10 contra o **código final** e confirma que todas as correções seguem válidas (`ex13/regressao/regressao.txt`): BOLA→404, SQLi→422, XSS→422, mass assignment→422, CORS malicioso→sem allow-origin, HSTS presente.

## Evidências

| Arquivo | Prova |
|---|---|
| `ex13/02_zap_baseline_depois.{html,json,md}` + `02_zap_resumo.txt` | scan ZAP passivo |
| `ex13/03_openapi.json` | spec auditada |
| `ex13/04_auditoria_openapi.txt` | apontamentos de design |
| `ex13/05_pytest_final.txt` | 63 testes (mocking + segurança + Ex.1) |
| `ex13/regressao/regressao.txt` | correções válidas no código final |
