# Ex. 1 — Fundação da API de agendamento

**Rubrica:** R1 · **Tag:** `ex01`

## Ambiente virtual isolado

A API roda em um `venv` próprio (`consultas-api/.venv`, criado com Python 3.12). Motivos:

- **Isolamento de dependências:** as versões fixadas em `requirements.txt` (FastAPI, Pydantic v2, Jinja2…) não conflitam com outros projetos nem com o Python do sistema (a máquina tem 3.9 como padrão, que nem suporta a sintaxe `str | None` usada no código).
- **Reprodutibilidade:** o mesmo `requirements.txt` é instalado no CI (Ex. 12). Versões fixas também são pré-requisito para a análise de dependências (SCA) com `pip-audit`: só é possível dizer "esta versão tem CVE" se a versão for conhecida.
- **Superfície mínima:** apenas o que a aplicação usa é instalado; ferramentas auxiliares (Playwright, para os prints) ficam em outro venv (`scripts/.venv-tools`).

A evidência `ex01/01_venv.txt` mostra `sys.prefix != sys.base_prefix` (= ambiente isolado) e o `pip list` resultante.

## Organização em módulos

| Módulo | Responsabilidade | Por que separado |
|---|---|---|
| `app/main.py` | cria o `FastAPI` e registra os routers | ponto único de composição; middlewares de segurança (Ex. 10) entram aqui uma única vez |
| `app/routes/` | um `APIRouter` por recurso (`consultas.py`) + páginas HTML (`pages.py`) | evita a "rota gigante" citada no enunciado; cada recurso cresce no seu arquivo |
| `app/models/` | modelos Pydantic de **entrada** (`ConsultaCreate`, `ConsultaUpdate`) e de **saída** (`ConsultaPublic`) | contrato da API separado do armazenamento (base do Ex. 2) |
| `app/database.py` | armazenamento (em memória até o Ex. 11) | trocar a persistência por SQLModel não obriga reescrever as rotas |
| `app/templates/` | Jinja2 com herança (`base.html` → `agenda.html`) | apresentação isolada do domínio |
| `tests/` | pytest | arquivo iniciado aqui e expandido nos Ex. 6, 12 e 13 |

Nas próximas etapas entram `app/auth/` (autenticação/autorização) e `app/core/` (configuração, headers, rate limit): a lógica de segurança fica **centralizada** nesses módulos e as rotas só as *usam*.

## Recurso RESTful completo: consultas

| Método | Rota | Resposta de sucesso |
|---|---|---|
| `POST` | `/consultas` | 201 + `ConsultaPublic` |
| `GET` | `/consultas` | 200 + lista |
| `GET` | `/consultas/{id}` | 200 (404 se não existe) |
| `PATCH` | `/consultas/{id}` | 200 |
| `DELETE` | `/consultas/{id}` | 204 |

## Como rodar

```bash
cd consultas-api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # ou, da raiz do repo: scripts/servidor.sh start
pytest -v
```

## Teste automatizado

`consultas-api/tests/test_consultas.py::test_criar_e_obter_consulta_sucesso` cobre o caminho de sucesso (POST 201 → GET 200). Esse teste é **preservado** ao longo de todo o Assessment (o R24 exige que ele continue existindo no Ex. 13).

## Evidências

| Arquivo | O que prova |
|---|---|
| `evidencias/ex01/01_venv.txt` | venv isolado criado e dependências instaladas |
| `evidencias/ex01/02_estrutura.txt` | árvore de arquivos com `routes/`, `models/`, `database.py` |
| `evidencias/ex01/03_uvicorn_startup.txt` | uvicorn subindo e respondendo `/health` |
| `evidencias/ex01/04_rotas_curl.txt` | respostas HTTP reais de todas as operações do recurso consultas |
| `evidencias/ex01/05_pytest.txt` | teste de sucesso passando |
| `evidencias/ex01/06_swagger.png` | rotas documentadas no Swagger |
