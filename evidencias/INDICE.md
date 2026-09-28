# Índice de evidências (gerado por scripts/evidencia.sh)

| Arquivo | Ex. | Rubrica | Commit | Descrição |
|---|---|---|---|---|
| `ex01/01_venv.txt` | ex01 | R1 | `d996e30` | Ambiente virtual isolado (python3.12 -m venv) + dependências instaladas |
| `ex01/02_estrutura.txt` | ex01 | R1 | `d996e30` | Estrutura modular: routes / models / database / templates / tests |
| `ex01/03_uvicorn_startup.txt` | ex01 | R1 | `d996e30` | uvicorn subindo a aplicação |
| `ex01/05_pytest.txt` | ex01 | R1 | `d996e30` | pytest: caminho de sucesso do Ex. 1 (+ testes do Ex. 2) |
| `ex01/06_swagger.txt` | ex01 | R1 | `d996e30` | Print do Swagger (/docs) com as rotas documentadas → 06_swagger.png |
| `ex01/04_rotas_curl.txt` | ex01 | R1 | `d996e30` | Respostas reais das rotas: health, POST, GET por id, GET lista, PATCH, 404, DELETE e página HTML |
| `ex02/01_sem_response_model_antes.txt` | ex02 | R2,R3 | `f3b26ec` | ANTES (branch demo, sem response_model): POST e GET vazam criado_por, ip_origem, criado_em, atualizado_em |
| `ex02/02_com_response_model_depois.txt` | ex02 | R2 | `19a8ad9` | DEPOIS (main, response_model=ConsultaPublic): mesmo POST/GET, só os campos públicos |
| `ex02/03_xss_post_payload.txt` | ex02 | R4 | `19a8ad9` | Payloads XSS gravados em observacoes (JSON devolve o texto cru, o que é correto para JSON) |
| `ex02/04_agenda_html_escapada.txt` | ex02 | R4 | `19a8ad9` | HTML da agenda: payloads aparecem codificados (&lt;script&gt;), nenhuma tag <script>/<img> ativa |
| `ex02/05_agenda_escapada.txt` | ex02 | R4 | `19a8ad9` | Print da agenda: payload XSS exibido como texto, sem alert (dialogs=0) → 05_agenda_escapada.png |
| `ex02/06_pytest.txt` | ex02 | R2,R3,R4 | `19a8ad9` | pytest com o teste que demonstra o vazamento sem response_model |
| `ex06/01_senhas_bcrypt.txt` | ex06 | R10 | `a8c5c32` | Usuários do seed: apenas hashes bcrypt $2b$12$… (nenhuma senha em texto) |
| `ex06/02_login_e_claims.txt` | ex06 | R10,R11 | `a8c5c32` | Login da Dra. Carla + claims decodificadas (sub, papel, aud, iss, exp-iat=900s) |
| `ex06/03_sem_token_401.txt` | ex06 | R10 | `a8c5c32` | GET /consultas sem Authorization → 401 |
| `ex06/04_token_expirado_401.txt` | ex06 | R11 | `a8c5c32` | Token com exp no passado → 401 (validação de expiração) |
| `ex06/05_mfa_fluxo.txt` | ex06 | R11 | `a8c5c32` | Fluxo MFA do admin: senha→mfa_required→(mfa_token barrado 403)→verify TOTP→access→/admin/usuarios 200 |
| `ex06/06_ownership_403.txt` | ex06 | R10 | `a8c5c32` | Ownership: Dr. Diego tenta GET/PATCH consulta da Dra. Carla → 404 (não confirma existência); a dona acessa 200 |
| `ex06/07_rbac_recepcao_admin_403.txt` | ex06 | R10,R11 | `a8c5c32` | RBAC: recepção em /admin/usuarios → 403 (teste obrigatório do enunciado) |
| `ex06/08_pytest.txt` | ex06 | R10,R11 | `a8c5c32` | pytest: 13 testes (autenticação, expiração, MFA, ownership, RBAC) |
| `ex06/09_agenda_autenticada.txt` | ex06 | R10 | `a8c5c32` | Agenda da recepção acessível só com sessão (cookie); print → 09_agenda_autenticada.png |
| `ex11/01_segredo_hardcoded_antes.txt` | ex11 | R18 | `a8c5c32` | ANTES (Ex.11): segredo hardcoded no código da aplicação (tag ex06) |
