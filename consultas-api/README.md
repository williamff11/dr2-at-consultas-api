# API de Agendamento de Consultas — DR2 AT

## Rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger: http://localhost:8000/docs
- Agenda da recepção: http://localhost:8000/recepcao/agenda

## Testes

```bash
pytest -q
```

## Estrutura

```
app/
  main.py            # cria o FastAPI e registra os routers
  database.py        # armazenamento (em memória até o Ex. 11)
  models/            # Pydantic: entrada (Create/Update) e saída (Public)
  routes/            # APIRouter por recurso + páginas HTML
  templates/         # Jinja2 com herança (base.html → agenda.html)
tests/
docs/                # relatórios e evidências por exercício
```

Veja `ROADMAP.md` para o plano completo dos 13 exercícios.
