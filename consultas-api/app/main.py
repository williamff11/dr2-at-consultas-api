from fastapi import FastAPI

from app.routes import consultas, pages

app = FastAPI(
    title="API de Agendamento de Consultas",
    version="0.1.0",
    description="DR2 AT — base modular (routes / models / database).",
)

app.include_router(consultas.router)
app.include_router(pages.router)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
