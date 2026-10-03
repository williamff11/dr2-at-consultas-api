# Índice de evidências (gerado por scripts/evidencia.sh)

| Arquivo | Ex. | Commit | Descrição |
|---|---|---|---|
| `ex01/01_venv.txt` | ex01 | `d996e30` | Ambiente virtual isolado (python3.12 -m venv) + dependências instaladas |
| `ex01/02_estrutura.txt` | ex01 | `d996e30` | Estrutura modular: routes / models / database / templates / tests |
| `ex01/03_uvicorn_startup.txt` | ex01 | `d996e30` | uvicorn subindo a aplicação |
| `ex01/05_pytest.txt` | ex01 | `d996e30` | pytest: caminho de sucesso do Ex. 1 (+ testes do Ex. 2) |
| `ex01/06_swagger.png` | ex01 | `d996e30` | Print do Swagger (/docs) com as rotas documentadas |
| `ex01/04_rotas_curl.txt` | ex01 | `d996e30` | Respostas reais das rotas: health, POST, GET por id, GET lista, PATCH, 404, DELETE e página HTML |
| `ex02/01_sem_response_model_antes.txt` | ex02 | `f3b26ec` | ANTES (branch demo, sem response_model): POST e GET vazam criado_por, ip_origem, criado_em, atualizado_em |
| `ex02/02_com_response_model_depois.txt` | ex02 | `19a8ad9` | DEPOIS (main, response_model=ConsultaPublic): mesmo POST/GET, só os campos públicos |
| `ex02/03_xss_post_payload.txt` | ex02 | `19a8ad9` | Payloads XSS gravados em observacoes (JSON devolve o texto cru, o que é correto para JSON) |
| `ex02/04_agenda_html_escapada.txt` | ex02 | `19a8ad9` | HTML da agenda: payloads aparecem codificados (&lt;script&gt;), nenhuma tag <script>/<img> ativa |
| `ex02/05_agenda_escapada.png` | ex02 | `19a8ad9` | Print da agenda: payload XSS exibido como texto, sem alert (dialogs=0) |
| `ex02/06_pytest.txt` | ex02 | `19a8ad9` | pytest com o teste que demonstra o vazamento sem response_model |
| `ex06/01_senhas_bcrypt.txt` | ex06 | `a8c5c32` | Usuários do seed: apenas hashes bcrypt $2b$12$… (nenhuma senha em texto) |
| `ex06/02_login_e_claims.txt` | ex06 | `a8c5c32` | Login da Dra. Carla + claims decodificadas (sub, papel, aud, iss, exp-iat=900s) |
| `ex06/03_sem_token_401.txt` | ex06 | `a8c5c32` | GET /consultas sem Authorization → 401 |
| `ex06/04_token_expirado_401.txt` | ex06 | `a8c5c32` | Token com exp no passado → 401 (validação de expiração) |
| `ex06/05_mfa_fluxo.txt` | ex06 | `a8c5c32` | Fluxo MFA do admin: senha→mfa_required→(mfa_token barrado 403)→verify TOTP→access→/admin/usuarios 200 |
| `ex06/06_ownership_403.txt` | ex06 | `a8c5c32` | Ownership: Dr. Diego tenta GET/PATCH consulta da Dra. Carla → 404 (não confirma existência); a dona acessa 200 |
| `ex06/07_rbac_recepcao_admin_403.txt` | ex06 | `a8c5c32` | RBAC: recepção em /admin/usuarios → 403 (teste obrigatório do enunciado) |
| `ex06/08_pytest.txt` | ex06 | `a8c5c32` | pytest: 13 testes (autenticação, expiração, MFA, ownership, RBAC) |
| `ex06/09_agenda_autenticada.png` | ex06 | `a8c5c32` | Agenda da recepção acessível só com sessão (cookie); print |
| `ex11/01_segredo_hardcoded_antes.txt` | ex11 | `a8c5c32` | ANTES (Ex.11): segredo hardcoded no código da aplicação (tag ex06) |
| `ex07/01_client_credentials.txt` | ex07 | `521c3d1` | Laboratório obtém token via client_credentials (scope horarios:read) |
| `ex07/02_claims_humano_vs_m2m.txt` | ex07 | `521c3d1` | Claims lado a lado: humano (papel, profissional_id, scope consultas:*) × M2M (client_type m2m, scope horarios:read, sem papel) |
| `ex07/03_lab_horarios_200.txt` | ex07 | `521c3d1` | Lab acessa /horarios-disponiveis (200) — só slots livres, sem paciente |
| `ex07/04_lab_consultas_403.txt` | ex07 | `521c3d1` | Token do laboratório NÃO alcança dados de paciente: GET e POST /consultas → 403 |
| `ex07/05_lab_password_grant_rejeitado.txt` | ex07 | `521c3d1` | Cliente M2M rejeitado no login humano e grant_type inválido rejeitado |
| `ex07/06_pytest.txt` | ex07 | `521c3d1` | pytest completo (20 testes, inclui 7 de M2M) |
| `ex06/10_sem_token_401.png` | ex06 | `521c3d1` | Print HTTP 401: GET /consultas sem sessão |
| `ex06/11_rbac_recepcao_403.png` | ex06 | `521c3d1` | Print HTTP 403: recepção em /admin/usuarios (RBAC) |
| `ex06/12_admin_sem_mfa_403.png` | ex06 | `521c3d1` | Print HTTP 403: admin autenticado SEM MFA em /admin/usuarios |
| `ex06/13_admin_com_mfa_200.png` | ex06 | `521c3d1` | Print HTTP 200: admin com MFA verificado em /admin/usuarios |
| `ex11/02_sem_credenciais_depois.txt` | ex11 | `c6f97e2` | DEPOIS: nenhum segredo hardcoded em app/; segredo vem de Settings/.env |
| `ex11/03_env_example.txt` | ex11 | `c6f97e2` | .env.example (só placeholders) versionado; .env ignorado pelo git |
| `ex11/05_pytest.txt` | ex11 | `c6f97e2` | pytest com banco SQLite em memória (StaticPool) e override de sessão |
| `ex11/04_queries_parametrizadas_log.txt` | ex11 | `c6f97e2` | SQL emitido pelo SQLModel com placeholders (?) e parâmetros separados — não há concatenação |
| `ex11/06_falha_sem_segredo.txt` | ex11 | `c6f97e2` | Fail-fast: sem JWT_SECRET_KEY a aplicação NÃO sobe (nenhum default de segredo) |
| `ex09/01_V1_bola_prontuario_antes.txt` | ex09 | `104f916` | V1 BOLA (ANTES): Dr. Diego lê o prontuário de paciente da Dra. Carla trocando o id → 200 com CPF e observações clínicas |
| `ex09/02_V1irmao_detalhe_html_antes.txt` | ex09 | `104f916` | V1-irmão (ANTES): Dr. Diego abre /recepcao/consultas/1 (paciente da Carla) via cookie → 200 com dados |
| `ex09/03_V2_sqli_antes.txt` | ex09 | `104f916` | V2 SQLi (ANTES): parâmetro nome concatenado altera a query — retorna pacientes fora do filtro e extrai hashes via UNION |
| `ex09/04_V3_xss_antes.png` | ex09 | `104f916` | V3 XSS stored (ANTES): página de detalhe renderiza <img onerror> sem escape (|safe); print captura o alert com document.cookie |
| `ex09/05_V4_mass_assignment_antes.txt` | ex09 | `104f916` | V4 Mass assignment (ANTES): Carla altera a PRÓPRIA consulta enviando profissional_id e criado_por extras → aceitos; a consulta troca de dono |
| `ex09/06_extra_campo_antes.txt` | ex09 | `104f916` | V4/extra (ANTES): POST com campo_inexistente e status='realizada' — campos extras aceitos/ignorados em silêncio (sem extra=forbid) |
| `ex10/01_V5a_cors_antes.txt` | ex10 | `104f916` | V5a CORS (ANTES): preflight de origem maliciosa é aceito (allow-origin ecoa a origem / *) |
| `ex10/02_V5b_bruteforce_antes.txt` | ex10 | `104f916` | V5b Força bruta (ANTES): 10 logins com senha errada — todas 401, nenhum 429 (sem rate limit) |
| `ex10/03_V5c_headers_antes.txt` | ex10 | `104f916` | V5c Headers (ANTES): respostas sem HSTS/X-Frame-Options/X-Content-Type-Options |
| `ex09/01_V1_bola_prontuario_depois.txt` | ex09 | `313e28c` | V1 BOLA (DEPOIS): Dr. Diego no prontuário de paciente da Carla → 404 (ownership no item_router) |
| `ex09/02_V1irmao_detalhe_html_depois.txt` | ex09 | `313e28c` | V1-irmão (DEPOIS): Dr. Diego em /recepcao/consultas/1 → 404 (mesma dependência de ownership) |
| `ex09/03_V2_sqli_depois.txt` | ex09 | `313e28c` | V2 SQLi (DEPOIS): mesmos vetores do antes agora bloqueados; apostrofo legitimo e tratado como literal pela query parametrizada |
| `ex09/04_V3_xss_depois.png` | ex09 | `313e28c` | V3 XSS (DEPOIS): payload com <img onerror> rejeitado na entrada (422); página de detalhe sem alert (dialogs=0) |
| `ex09/05_V4_mass_assignment_depois.txt` | ex09 | `313e28c` | V4 Mass assignment (DEPOIS): PATCH com profissional_id/criado_por extras → 422 extra_forbidden |
| `ex09/06_extra_campo_depois.txt` | ex09 | `313e28c` | extra (DEPOIS): POST com campo_inexistente → 422 extra_forbidden |
| `ex09/07_regex_whitelist.txt` | ex09 | `313e28c` | Whitelist/regex: entradas válidas × inválidas (nome com dígito, status inexistente, transição proibida) |
| `ex09/08_ownership_centralizado.txt` | ex09 | `313e28c` | Ownership centralizado: a decisão de posse (compara profissional_id do objeto) existe só em dependencies.py |
| `ex09/09_pytest.txt` | ex09 | `313e28c` | pytest: 29 testes (correções V1-V4 + endpoint irmão) |
| `ex10/04_cors_origem_permitida.txt` | ex10 | `57e1ca8` | CORS: origem da allowlist (http://localhost:5173) recebe Access-Control-Allow-Origin |
| `ex10/01_V5a_cors_depois.txt` | ex10 | `57e1ca8` | V5a CORS (DEPOIS): preflight de https://evil.example NÃO recebe Access-Control-Allow-Origin (navegador bloqueia) |
| `ex10/03_V5c_headers_depois.txt` | ex10 | `57e1ca8` | V5c Headers (DEPOIS): HSTS/XFO/XCTO em todas as respostas; CSP no GET das páginas HTML |
| `ex10/02_V5b_bruteforce_depois.txt` | ex10 | `57e1ca8` | V5b Força bruta (DEPOIS): 7 logins com senha errada — 5 chegam a 401, a partir da 6ª → 429 (rate limit) |
| `ex10/05_rate_limit_diferenciado.txt` | ex10 | `57e1ca8` | Rate limit diferenciado: 15 GETs numa rota comum (limite global 120/min) → todos 200/OK, sem 429 |
| `ex10/06_pytest.txt` | ex10 | `57e1ca8` | pytest: testes de hardening (headers, CORS, rate limit) |
| `ex12/01_cvss_scores.txt` | ex12 | `d05ddd1` | Scores CVSS 3.1 (lib cvss) e prioridade por impacto de negócio |
| `ex12/02_bandit_local.txt` | ex12 | `d05ddd1` | Bandit (SAST) no código atual: 0 achados de severidade Medium+ (gate passa) |
| `ex12/04_pytest_security.txt` | ex12 | `d05ddd1` | pytest tests/security: testes rastreáveis ao threat model (T0x visíveis) |
| `ex12/05_bandit_contra_ex08.txt` | ex12 | `d05ddd1` | Prova de que o gate teria BLOQUEADO a V2: Bandit -ll no worktree da tag ex08-vulneravel acha a SQLi (B608) e falha |
| `ex12/06_pytest_completo.txt` | ex12 | `d05ddd1` | pytest completo (todos os testes, incluindo tests/security) |
| `ex13/02_zap_resumo.txt` | ex13 | `79a5313` | OWASP ZAP baseline passivo (estado final): 0 FAIL, 6 WARN (Medium/Low), 61 PASS. Relatórios em 02_zap_baseline_depois.{html,json,md} |
| `ex13/03_openapi.txt` | ex13 | `79a5313` | OpenAPI da aplicação (para auditoria) |
| `ex13/04_auditoria_openapi.txt` | ex13 | `79a5313` | Auditoria da OpenAPI: apontamentos de design de segurança (o que foi corrigido e o que fica como risco residual) |
| `ex13/05_pytest_final.txt` | ex13 | `79a5313` | pytest completo final (todos os testes + tests/security + mocking) |
| `ex13/07_checagem_entrega.txt` | ex13 | `6be8141` | Conferências de entrega: tudo commitado, sem .env versionado, sem segredo hardcoded em app/ |
| `ex12/03_pip_audit_local.txt` | ex12 | `e6cc2bd` | pip-audit (SCA): sem vulnerabilidades após pyjwt 2.14.0 (o SCA pegou CVEs em 2.10.1 e depois em 2.13.0) |
| `ex13/08_code_review_antes.txt` | ex13 | `9aaa3d9` | Code review (ANTES): 4 testes dos achados CR1-CR4 falham no código sem correção (MFA contornável no login HTML, login HTML sem rate limit, agenda HTML e busca de pacientes sem ownership) |
| `ex13/09_code_review_depois.txt` | ex13 | `f47f33a` | Code review (DEPOIS): os mesmos 4 testes dos achados CR1-CR4 passam após a correção |
| `ex13/10_pytest_pos_code_review.txt` | ex13 | `f47f33a` | pytest completo após as correções do code review |
| `ex13/11_zap_resumo_codigo_final.txt` | ex13 | `f8476f8` | OWASP ZAP baseline passivo repetido sobre o código final (após o code review): 0 FAIL, 6 WARN, 61 PASS — mesmos alertas do scan anterior. Relatórios e print em 11_zap_codigo_final.{html,json,md,png} |
| `ex12/10_pipeline_verde_main.png` | ex12 | `479be16` | Pipeline verde na main (tests, sast, sca, dast, security-gate) |
| `ex12/11_pr_bloqueado_3_checks.png` | ex12 | `b7ba7a3` | PR #1 (demo/gate-bloqueio, reintroduz a V2): sast, tests e security-gate (Required) falhando, sca e dast passando — merge bloqueado |
| `ex12/12_sast_bandit_b608_log.png` | ex12 | `b7ba7a3` | Log do job sast no PR #1: Bandit acha B608 (SQLi, CWE-89, Severity Medium / Confidence Low) em app/routes/pacientes.py:27 → exit 1 |
