# Relatório de Rastreabilidade — DR2 AT (Capstone, Ex. 13)

**Aluno:** William Felício Freire · **Disciplina:** Desenvolvimento Seguro de Aplicações Web
**Aplicação:** API de Agendamento de Consultas (FastAPI) · **Estado auditado:** tag `ex13`

Este relatório demonstra rastreabilidade **de ponta a ponta**: do threat model (Ex. 4) → vulnerabilidade (Ex. 8) → finding (ZAP e/ou manual) → categoria OWASP → correção (arquivo:linha, tag) → teste que prova → evidência antes/depois → CVSS/prioridade → status.

---

## 1. Comando do scan OWASP ZAP (passivo)

O scan foi rodado duas vezes contra a API em `localhost:8000`: na tag `ex13` (`ex13/02_*`) e de novo no código final, depois das correções do code review (`ex13/11_*`, com print do resumo em `11_zap_codigo_final.png`).

```bash
# na raiz do repositório, com a API rodando em localhost:8000
mkdir -p /tmp/zap && cp .zap/rules.tsv /tmp/zap/ && chmod 777 /tmp/zap
docker run --rm -v /tmp/zap:/zap/wrk:rw ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:8000/openapi.json -c rules.tsv \
  -r report.html -J report.json -w report.md -I \
  -z "-silent -addoninstall pscanrulesBeta"
# relatórios copiados para evidencias/ex13/11_zap_codigo_final.{html,json,md}
```

O `-z "-silent -addoninstall pscanrulesBeta"` evita que o ZAP trave baixando atualizações de add-ons na inicialização, mas mantém o pacote de regras beta. Usando só `-silent`, o scan perde as regras de COEP/COOP/CORP, Permissions-Policy e cache (58 PASS em vez de 61) e aparenta um resultado melhor do que o real.

**Resultado (as duas execuções):** `FAIL-NEW: 0 · WARN-NEW: 6 · PASS: 61`, com os mesmos 10 alertas (3 Medium, 4 Low, 3 Informational). Nenhum alerta de risco **High**. As correções do code review não mudaram a superfície vista pelo ZAP, o que é esperado: eram falhas de autorização, que um scan passivo não enxerga.

---

## 2. Matriz de rastreabilidade (threat model → correção → prova)

| Ameaça (Ex.4) | Misuse | Vulnerab. (Ex.8) | Finding (ZAP/manual) | OWASP | Correção (arquivo:linha, tag) | Teste (T0x) | Evidência antes→depois | CVSS/prioridade | Status |
|---|---|---|---|---|---|---|---|---|---|
| **T01** | MC01 | V1 BOLA + irmão | manual (scanner não pega lógica) + **code review CR3/CR4** | A01/API1 | `item_router` c/ `get_consulta_autorizada` — `routes/consultas.py`; regra em `auth/dependencies.py` (`ex09`); filtro por `profissional_id` na agenda HTML e na busca de pacientes — `routes/pages.py`, `routes/pacientes.py` (`f47f33a`) | `test_T01_bola` | `ex09/01,02` · `ex13/08→09` | 6.5 Med → **crítica** | ✅ corrigido |
| **T02** | MC02 | V2 SQLi | manual + Bandit B608 | A03 | `select().where(contains)` + regex — `routes/pacientes.py` (`ex09`) | `test_T02_sqli` | `ex09/03` | 8.8 High → crítica | ✅ corrigido |
| **T03** | MC03 | V3 XSS stored | manual + ZAP CSP WARN | A03 | remoção de `\|safe` + regex `^[^<>]*$` — `templates/detalhe_consulta.html`, `models/consulta.py` (`ex09`) | `test_T03_xss` | `ex09/04` | 5.4 Med → alta | ✅ corrigido |
| **T04** | — | (assinatura/exp) | manual | A02/A07 | `decodificar_token` valida exp/iss/aud — `auth/security.py:59` (`ex06`) | `test_T04_jwt` | `ex06/04` | — | ✅ mitigado |
| **T05** | MC05 | V5b força bruta | ZAP Auth Request + **code review CR2** | A07 | rate limit 5/min — `core/rate_limit.py` (`ex10`); estendido a `/recepcao/login` — `routes/pages.py` (`f47f33a`) | `test_T05_bruteforce` | `ex10/02` · `ex13/08→09` | 5.9 Med → alta | ✅ corrigido |
| **T06** | MC06 | V4 mass assign | manual | A08/API3 | `extra='forbid'` + whitelist — `models/consulta.py` (`ex09`) | `test_T06_mass_assignment` | `ex09/05,06` | 6.5 Med → alta | ✅ corrigido |
| **T07** | MC04 | (escopo M2M) | manual | API5 | `Security(scopes)` + bloqueio m2m — `routes/m2m.py`, `auth/dependencies.py:66` (`ex07`) | `test_T07_m2m_escopo` | `ex07/04` | — | ✅ mitigado |
| **T08** | — | (escalada) | manual + **code review CR1** | A01/A07 | RBAC `require_roles` + `require_mfa` (`ex06`); login HTML recusa conta com MFA — `routes/pages.py` (`f47f33a`) | `test_T08_escalada_privilegio` | `ex06/07,11-13` · `ex13/08→09` | — | ✅ corrigido |
| **T09** | — | (repúdio) | — | A09 | `criado_por`/`atualizado_em` (`ex06`) | — | `ex06/*` | — | ⚠️ parcial (risco residual: log central) |
| **T10** | — | V5a CORS | ZAP (headers) | A05 | CORS allowlist + fail-fast — `main.py` (`ex10`) | `test_T10_T12_rede` | `ex10/01,05` | 6.1 Med → alta | ✅ corrigido |
| **T11** | — | segredo hardcoded | Bandit B105 (histórico) | A05/A02 | `BaseSettings`/.env, sem default — `core/config.py` (`ex11`) | `test_T11_segredo` | `ex11/01→02` | 7.4 High → crítica | ✅ corrigido |
| **T12** | — | V5c headers | ZAP (headers) | A05 | `SecurityHeadersMiddleware` (`ex10`) | `test_T10_T12_rede` | `ex10/03` | 4.2 Med | ✅ corrigido |

### 2.1 Achados do code review (estado final)

Depois do ZAP, o código final passou por uma revisão de código manual. Ela achou quatro falhas de **lógica de autorização**, nenhuma visível ao scanner passivo, e todas em superfícies secundárias que repetiam o padrão do "endpoint-irmão" do Ex. 9: a proteção estava na rota principal, mas não na rota vizinha.

| # | Achado | Ameaça | Antes (reproduzido) | Correção | Teste | Status |
|---|---|---|---|---|---|---|
| CR1 | `/recepcao/login` confere só a senha e emite cookie para o **admin sem MFA**; o cookie vale nas rotas da API (`get_current_user` aceita cookie) | T08 | admin abre `/consultas/{id}/prontuario` (CPF) sem 2º fator → 200 | contas com MFA são recusadas no login HTML (403, sem cookie) | `test_T08_login_html_nao_contorna_mfa` | ✅ corrigido |
| CR2 | `/recepcao/login` sem o limite de login, só o global de 120/min | T05 | 7 tentativas erradas → 7×401, nenhum 429 | `@limiter.limit(LIMITE_LOGIN)` (5/min) | `test_T05_login_html_limitado` | ✅ corrigido |
| CR3 | agenda HTML lista consultas de **todos** os profissionais | T01 | `dr_diego` vê paciente e observação clínica da Dra. Carla | filtro por `profissional_id` (o mesmo de `GET /consultas`) | `test_T01_agenda_html_so_mostra_proprias` | ✅ corrigido |
| CR4 | `GET /pacientes` devolve nome e **CPF** de pacientes de outros profissionais | T01 | `dr_diego` busca "Ana" → recebe Ana Souza (paciente da Dra. Carla) | filtro por `profissional_id` para profissionais | `test_T01_busca_pacientes_so_retorna_proprios` | ✅ corrigido |
| CR5 | `PATCH {"data_hora": null}` → erro 500 (NOT NULL no banco) | — | `IntegrityError` | — | — | ⚠️ aberto (baixo impacto: só o dono da consulta alcança) |
| CR6 | `Secure` do cookie lê `os.environ`, não as settings (`.env`) | T12 | com `ENV=prod` só no `.env`, cookie sem `Secure` | — | — | ⚠️ aberto (RR6: TLS no proxy) |
| CR7 | tempo de resposta do login revela usuário inexistente (bcrypt não roda) | T05 | — | — | — | risco residual RR9 |
| CR8 | código TOTP reutilizável dentro da janela (~60–90 s) | T08 | — | — | — | risco residual RR10 |

**Evidência:** os **mesmos** 4 testes falham no commit `9aaa3d9`, antes da correção (`ex13/08_code_review_antes.txt`), e passam no commit `f47f33a`, depois dela (`ex13/09_code_review_depois.txt`). Suíte completa: 67 testes (`ex13/10_pytest_pos_code_review.txt`).

**Lição para o capstone:** o ZAP passivo não acha nenhum desses problemas, e os testes do Ex. 9 também não, porque testavam as rotas principais. A revisão manual focada em "onde mais esse dado sai?" e "onde mais existe login?" fechou a lacuna. Por isso ela passa a valer como etapa do processo, e não só o scanner.

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
| RR9 | **Enumeração de usuário por tempo de resposta** (CR7) | usuário inexistente responde sem rodar bcrypt (~200 ms mais rápido) | Baixa | mensagem genérica + rate limit 5/min tornam a varredura lenta | rodar bcrypt contra um hash fixo quando o usuário não existe |
| RR10 | **Replay do código TOTP** (CR8) | não há registro do último código usado | Baixa | `mfa_token` expira em 5 min; exige a senha antes | guardar o último *time-step* aceito por usuário e recusar repetição |

---

## 5. Decisão: bloquear ou liberar o deploy

**Libero o deploy para um piloto interno, de nó único, usado pela equipe das clínicas. A exposição em produção para pacientes reais fica bloqueada até três condições serem cumpridas.**

**Por que liberar o piloto.** Todas as falhas críticas e altas que encontrei foram corrigidas e têm teste no pipeline: V1–V5 e o segredo no código (T11), mais os quatro achados do code review (CR1–CR4). O caso mais sério do code review, o bypass do MFA pelo login HTML, só apareceu porque revisei o código depois do ZAP. Isso me deixa mais confiante de que a superfície de autorização foi olhada rota por rota, e não só pela ferramenta. O ZAP não achou nenhum alerta High, e o `security-gate` impede que uma regressão dessas falhas chegue na `main`. O que sobrou é, em sua maioria, endurecimento de baixa severidade (RR3, RR6–RR10) ou limitação operacional aceitável enquanto o sistema roda num único nó e com usuários internos (RR1, RR2, RR5).

**Condições para liberar a produção:**

1. **Trilha de auditoria (RR4).** Com dado de saúde sob a LGPD, um incidente precisa ser reconstruível: quem leu ou alterou qual prontuário, e quando. Hoje só existe `criado_por`/`atualizado_em` na própria linha. Sem log estruturado das operações sensíveis, eu não conseguiria responder à ANPD nem aos titulares, e por isso isto bloqueia.
2. **Cookie `Secure` vindo das settings (CR6).** É uma linha de código, mas em produção um cookie de sessão sem `Secure` pode trafegar fora do HTTPS se a configuração vier só do `.env`. Correção barata para um risco que não quero assumir com dado real.
3. **Rate limit distribuído (RR1), antes de qualquer segunda réplica.** Com o contador em memória, cada réplica multiplica o limite de tentativas de login, e a proteção contra força bruta se degrada sem ninguém perceber.

**Fica no backlog, sem bloquear:** CR5 (o erro 500 no `PATCH` com data nula só é alcançável pelo dono da consulta e não expõe dado), MFA com enrollment real (RR2), revogação de JWT (RR5, mitigada pela expiração de 15 min) e os endurecimentos de headers e CSP apontados pelo ZAP (RR7).
