from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.database import criar_tabelas
from app.routes import admin, auth, consultas, m2m, pacientes, pages
from app.seed import semear

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()
    semear()
    yield


# Em produção, não expõe Swagger/OpenAPI (reduz superfície de reconhecimento).
_docs = None if settings.env == "prod" else "/docs"
_openapi = None if settings.env == "prod" else "/openapi.json"

app = FastAPI(
    title="API de Agendamento de Consultas",
    version="1.0.0",
    description="DR2 AT — API de agendamento com autenticação, validação, "
                "hardening de rede e persistência segura.",
    lifespan=lifespan,
    docs_url=_docs,
    redoc_url=None,
    openapi_url=_openapi,
)

# --- Rate limiting (Ex. 10) ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- Cabeçalhos de segurança (Ex. 10) ---
app.add_middleware(SecurityHeadersMiddleware)

# --- CORS com allowlist explícita (Ex. 10) ---
# Fail-fast: recusa subir se "*" estiver na lista (o auditor reprova wildcard).
_origins = settings.cors_origins_list
if "*" in _origins:
    raise RuntimeError("CORS_ORIGINS não pode conter '*' (use uma allowlist explícita).")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(consultas.router)
app.include_router(consultas.item_router)
app.include_router(admin.router)
app.include_router(m2m.router)
app.include_router(pacientes.router)
app.include_router(pages.router)


@app.get("/", tags=["infra"])
def root():
    # Raiz mínima (sem dado sensível) — evita 404 do spider do ZAP no CI.
    return {"service": "consultas-api", "status": "ok"}


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
