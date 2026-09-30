# Ex. 12 — Pipeline DevSecOps, CVSS e security gate

**Rubrica:** R19, R20, R21, R22 · **Tag:** `ex12` · Workflow: `.github/workflows/security.yml`

## 1. Testes de segurança rastreáveis ao threat model (R22)

`consultas-api/tests/security/` tem **um arquivo por ameaça** do Ex. 4 (`test_T01_bola.py` … `test_T12`). A docstring de cada arquivo cita a ameaça, o misuse case e `docs/04`. O teste de autorização iniciado no Ex. 6 (`test_recepcionista_nao_acessa_rota_admin`) foi **movido e expandido** para `test_T08_escalada_privilegio.py`, cobrindo: recepção→admin, profissional→admin, admin sem MFA, token M2M em rota humana. Os demais arquivos cobrem BOLA (GET/PATCH/DELETE/prontuário/HTML), SQLi, XSS, JWT forjado/expirado/aud, força bruta (429), mass assignment, escopo M2M, CORS e headers.

Evidência `ex12/04_pytest_security.txt` (nomes `test_T0x` visíveis) e `ex12/06_pytest_completo.txt` (56 testes).

## 2. Priorização por CVSS + impacto de negócio (R20)

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

**Onde o negócio muda a ordem do CVSS:** a **V1 (BOLA)** tem CVSS **6.5 Medium**, abaixo de V4/V5a numericamente próximos, mas **sobe para prioridade crítica**: ela expõe **prontuário de saúde de terceiros**, dado sensível sob LGPD art. 11, com incidente comunicável à ANPD e dano reputacional irreversível. O CVSS não "sabe" que o `C:H` aqui é dado de saúde de outra pessoa. Esse é o exemplo pedido pela rubrica de priorização que combina CVSS **e** impacto de negócio.

## 3. Ferramentas × fase do SDLC, amarradas ao pipeline (R19)

| Tipo | Ferramenta | Fase do SDLC | Job/gatilho (`security.yml`) | Justificativa | Vuln. do histórico que pegaria |
|---|---|---|---|---|---|
| Estática (SAST) | Bandit | Implementação / a cada PR | `sast`, em `pull_request`+`push` | barata e rápida; roda sobre o código sem executá-lo | V2 (B608), T11 segredo (B105) |
| Dependências (SCA) | pip-audit | Build / PR + **agendado** | `sca`, PR + `schedule` semanal | CVEs surgem **sem** mudança no código; por isso o cron semanal | CVEs de pyjwt/python-multipart (achados e corrigidos) |
| Dinâmica (DAST) | OWASP ZAP baseline | Verificação, app **em execução** | `dast`, após subir a API | precisa da aplicação rodando; vê headers, cookies, respostas | V5c (headers), cookies |
| Interativa (IAST) | *não implementada* | Teste/QA em staging (instrumentado) | — | exige agente instrumentado e ambiente de QA dedicado; os testes `tests/security` cobrem parte do que um IAST veria (lógica de negócio/BOLA) | V1 (BOLA, lógica de negócio) |

O `schedule:` semanal roda o SCA mesmo sem commits, porque uma dependência estável pode ganhar um CVE a qualquer momento — foi o que aconteceu com `pyjwt`/`python-multipart` neste Assessment.

## 4. ⚠️ DECISÃO DO WILLIAM — critério de bloqueio do gate (R21)

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

O job `security-gate` tem `needs: [tests, sast, sca, dast]` e consolida os resultados (`.github/workflows/security.yml`).

## 5. Ações que só o William executa (👤)

Registradas em `evidencias/PRINTS_PENDENTES.md` (P2–P4):
1. Criar o repositório no GitHub e `push` da `main` (em plano gratuito, o repo precisa ser **público** para branch protection).
2. Settings → Branches/Rulesets → exigir PR + status check `security-gate`. **Print.**
3. Print do workflow **verde** na `main`.
4. Branch `demo/gate-bloqueio` reintroduzindo a V2 → PR → **print do pipeline vermelho e do merge bloqueado**. Se `gh` autenticado: `gh run view --log-failed > evidencias/ex12/07_gate_bloqueou_log.txt`.

## Evidências

| Arquivo | Prova |
|---|---|
| `ex12/01_cvss_scores.txt` | scores CVSS + prioridade por negócio |
| `ex12/02_bandit_local.txt` | Bandit 0 Medium+ no código atual (gate passa) |
| `ex12/03_pip_audit_local.txt` | SCA limpo após atualizar deps |
| `ex12/04_pytest_security.txt` | testes T0x rastreáveis ao threat model |
| `ex12/05_bandit_contra_ex08.txt` | **gate bloquearia a V2** (Bandit na tag vulnerável) |
| `ex12/06_pytest_completo.txt` | 56 testes verdes |
| `.github/workflows/security.yml` | pipeline com 5 jobs e o gate |
| 👤 `ex12/07..` (William) | prints do PR bloqueado no GitHub |
