from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import admin, auth, consultas, m2m, pages
from app.seed import semear


@asynccontextmanager
async def lifespan(app: FastAPI):
    semear()
    yield


app = FastAPI(
    title="API de Agendamento de Consultas",
    version="0.2.0",
    description="DR2 AT — autenticação, autorização e ownership (Ex. 6).",
    lifespan=lifespan,
)

# CORS provisório — revisar no Ex. 10 (allow_origins=["*"] é o "antes" da V5a).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(consultas.router)
app.include_router(admin.router)
app.include_router(m2m.router)
app.include_router(pages.router)



@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
