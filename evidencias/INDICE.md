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
