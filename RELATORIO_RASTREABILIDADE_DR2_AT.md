# Relatório de Rastreabilidade — DR2 AT (Capstone, Ex. 13)

**Aluno:** William Felício Freire · **Disciplina:** Desenvolvimento Seguro de Aplicações Web
**Aplicação:** API de Agendamento de Consultas (FastAPI) · **Estado auditado:** tag `ex13`

Este relatório demonstra rastreabilidade **de ponta a ponta**: do threat model (Ex. 4) → vulnerabilidade (Ex. 8) → finding (ZAP e/ou manual) → categoria OWASP → correção (arquivo:linha, tag) → teste que prova → evidência antes/depois → CVSS/prioridade → status.

---

## 1. Comando do scan OWASP ZAP (passivo)

```bash
# API no estado final rodando em localhost:8000
docker run --rm -v "$PWD/evidencias/ex13:/zap/wrk:rw" -t \
  ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:8000/openapi.json \
  -r 02_zap_baseline_depois.html -J 02_zap_baseline_depois.json \
  -w 02_zap_baseline_depois.md -I
```

**Resultado:** `FAIL-NEW: 0 · WARN-NEW: 6 · PASS: 61`. Nenhum alerta de risco **High**.

---

## 2. Matriz de rastreabilidade (threat model → correção → prova)

| Ameaça (Ex.4) | Misuse | Vulnerab. (Ex.8) | Finding (ZAP/manual) | OWASP | Correção (arquivo:linha, tag) | Teste (T0x) | Evidência antes→depois | CVSS/prioridade | Status |
|---|---|---|---|---|---|---|---|---|---|
| **T01** | MC01 | V1 BOLA + irmão | manual (scanner não pega lógica) | A01/API1 | `item_router` c/ `get_consulta_autorizada` — `routes/consultas.py`; regra em `auth/dependencies.py:113` (`ex09`) | `test_T01_bola` | `ex09/01,02` | 6.5 Med → **crítica** | ✅ corrigido |
| **T02** | MC02 | V2 SQLi | manual + Bandit B608 | A03 | `select().where(contains)` + regex — `routes/pacientes.py` (`ex09`) | `test_T02_sqli` | `ex09/03` | 8.8 High → crítica | ✅ corrigido |
| **T03** | MC03 | V3 XSS stored | manual + ZAP CSP WARN | A03 | remoção de `\|safe` + regex `^[^<>]*$` — `templates/detalhe_consulta.html`, `models/consulta.py` (`ex09`) | `test_T03_xss` | `ex09/04` | 5.4 Med → alta | ✅ corrigido |
| **T04** | — | (assinatura/exp) | manual | A02/A07 | `decodificar_token` valida exp/iss/aud — `auth/security.py:59` (`ex06`) | `test_T04_jwt` | `ex06/04` | — | ✅ mitigado |
| **T05** | MC05 | V5b força bruta | ZAP Auth Request | A07 | rate limit 5/min — `core/rate_limit.py` (`ex10`) | `test_T05_bruteforce` | `ex10/02` | 5.9 Med → alta | ✅ corrigido |
| **T06** | MC06 | V4 mass assign | manual | A08/API3 | `extra='forbid'` + whitelist — `models/consulta.py` (`ex09`) | `test_T06_mass_assignment` | `ex09/05,06` | 6.5 Med → alta | ✅ corrigido |
| **T07** | MC04 | (escopo M2M) | manual | API5 | `Security(scopes)` + bloqueio m2m — `routes/m2m.py`, `auth/dependencies.py:66` (`ex07`) | `test_T07_m2m_escopo` | `ex07/04` | — | ✅ mitigado |
| **T08** | — | (escalada) | manual | A01 | RBAC `require_roles` + `require_mfa` (`ex06`) | `test_T08_escalada_privilegio` | `ex06/07,11-13` | — | ✅ mitigado |
| **T09** | — | (repúdio) | — | A09 | `criado_por`/`atualizado_em` (`ex06`) | — | `ex06/*` | — | ⚠️ parcial (risco residual: log central) |
| **T10** | — | V5a CORS | ZAP (headers) | A05 | CORS allowlist + fail-fast — `main.py` (`ex10`) | `test_T10_T12_rede` | `ex10/01,05` | 6.1 Med → alta | ✅ corrigido |
| **T11** | — | segredo hardcoded | Bandit B105 (histórico) | A05/A02 | `BaseSettings`/.env, sem default — `core/config.py` (`ex11`) | `test_T11_segredo` | `ex11/01→02` | 7.4 High → crítica | ✅ corrigido |
| **T12** | — | V5c headers | ZAP (headers) | A05 | `SecurityHeadersMiddleware` (`ex10`) | `test_T10_T12_rede` | `ex10/03` | 4.2 Med | ✅ corrigido |

---

## 3. Interpretação de cada alerta do ZAP

O baseline é **passivo** (só observa respostas; não ataca). Por isso ele vê headers e cookies, mas **não** detecta BOLA/SQLi/mass assignment (que dependem de contexto de negócio) — esses foram cobertos por análise manual + `tests/security`. Isso, por si, é uma conclusão do capstone: **scanner passivo não substitui revisão de autorização**.

| Alerta ZAP | Risco (ZAP) | Verdadeiro/falso positivo | OWASP | Correção / decisão |
|---|---|---|---|---|
| CSP: Failure to Define Directive with No Fallback | Medium | **Parcial-VP**: a CSP existe nas páginas HTML mas não define todas as diretivas com fallback | A05 | CSP já restringe `script-src 'none'`; refinar `default-src`/`object-src` é melhoria de baixo custo (backlog) |
| CSP: style-src unsafe-inline | Medium | **VP aceito**: o CSS inline do `base.html` exige `unsafe-inline` em `style-src` | A05 | risco baixo (sem script inline); mover CSS para arquivo removeria o `unsafe-inline` (backlog) |
| Absence of Anti-CSRF Tokens (`/recepcao/login`) | Medium | **VP mitigado**: o cookie de sessão é `SameSite=Strict`, o que mitiga CSRF; um token anti-CSRF seria defesa adicional | A01 | aceito com `SameSite=Strict`; token CSRF no formulário = backlog |
| COEP/COOP/CORP Header Missing | Low | **VP baixo**: headers de isolamento de origem ausentes | A05 | baixo impacto para uma API/HTML interna; adicionáveis no middleware (backlog) |
| Permissions-Policy Header Not Set | Low | **VP baixo** | A05 | adicionável ao `SecurityHeadersMiddleware` (backlog) |
| Non-Storable / Storable Content | Informational | **FP**: comportamento normal de cache de respostas | — | nenhuma ação |
| Authentication Request Identified | Informational | **FP**: o ZAP apenas identificou a rota de login | — | nenhuma ação |

Nenhum alerta **High**; nenhum corresponde às vulnerabilidades críticas (V1–V4), que já foram corrigidas e são cobertas por teste. Os WARN são endurecimentos incrementais de headers.

---

## 4. Risco residual

| # | Risco residual | Por que permanece | Severidade | Mitigação atual | Recomendação |
|---|---|---|---|---|---|
| RR1 | **Rate limit em memória** (`slowapi`) | não é distribuído; com múltiplas réplicas o limite se multiplica | Média | protege o cenário single-node | storage compartilhado (Redis) antes de escalar horizontalmente |
| RR2 | **MFA simulado** (TOTP semeado) | falta enrollment real e cofre por usuário | Média | algoritmo TOTP é o de produção | provisionamento por app autenticador + cofre |
| RR3 | **IDs sequenciais** (enumeração) | inteiros previsíveis | Baixa | ownership barra o acesso a terceiros | UUID como defesa em profundidade |
| RR4 | **Sem log de auditoria central + alertas** (T09) | só há `criado_por`/`atualizado_em` na linha | Média | trilha mínima de autoria | logging estruturado + SIEM/alertas |
| RR5 | **Revogação de JWT inexistente** | token stateless vale até expirar | Média | expiração curta (15 min) | blocklist/refresh tokens com rotação |
| RR6 | **TLS terminado fora da app** | HSTS assume HTTPS no proxy | Baixa | HSTS já enviado | garantir terminação TLS no ingress |
| RR7 | **Headers COEP/COOP/CORP e CSP refináveis** (ZAP WARN) | endurecimento incremental | Baixa | HSTS/XFO/XCTO/CSP-parcial presentes | completar no middleware |
| RR8 | **IAST não implementado** | exige ambiente instrumentado | Baixa | `tests/security` cobre parte | avaliar IAST em staging |

---

## 5. ⚠️ DECISÃO DO WILLIAM — bloquear ou liberar o deploy

> **Proposta do agente (a validar, reescrever com suas palavras e explicar no vídeo).**
>
> **Recomendação: liberar o deploy do MVP interno, condicionado a duas correções antes de qualquer exposição pública.**
>
> **Justificativa.** Todas as vulnerabilidades **críticas e altas** (V1–V5, T11) foram corrigidas, têm teste automatizado no pipeline e evidência antes/depois. O scan ZAP não achou nenhum alerta **High**. Os riscos residuais são, na maioria, endurecimentos de baixa severidade (RR3, RR6, RR7, RR8) ou limitações operacionais aceitáveis num primeiro deploy **interno** de nó único (RR1, RR2).
>
> **Condicionantes antes de liberar (bloqueiam a exposição pública, não o piloto interno):**
> 1. **RR4 (trilha de auditoria):** para dado de saúde sob LGPD, um incidente precisa ser reconstruível. Adicionar logging estruturado das operações sensíveis antes de expor a pacientes reais.
> 2. **RR1 (rate limit distribuído):** obrigatório antes de escalar para múltiplas réplicas, senão a proteção contra força bruta se degrada.
>
> Os demais (RR2, RR3, RR5, RR6, RR7, RR8) entram no backlog priorizado, sem bloquear o piloto.

*(William: revise cada linha, decida se concorda, e reescreva esta seção 5 com as suas próprias palavras — a rubrica R23 exige que a decisão seja sua.)*
