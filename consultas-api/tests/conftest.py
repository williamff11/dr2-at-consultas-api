"""Configuração dos testes: banco SQLite em memória (StaticPool) e override da sessão.

As senhas/segredos de teste são definidos aqui (fixtures, não código da aplicação —
app/ continua sem segredo em texto). Devem casar com scripts/dev_env.sh.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# A suíte é AUTÔNOMA: fixa as credenciais de seed que os testes usam, sobrescrevendo
# qualquer valor herdado do ambiente (ex.: variáveis do CI). Sem isto, um SEED_SENHA_*
# diferente no CI faria os logins dos testes retornarem 401. Fixadas ANTES de importar
# a aplicação (config/security leem o ambiente no import).
os.environ["ENV"] = "dev"
os.environ["JWT_SECRET_KEY"] = "test-secret-nao-usar-em-producao-0011"
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory (engine da app; testes usam o próprio)
os.environ["SEED_SENHA_ADMIN"] = "admin-dev-2026!"
os.environ["SEED_SENHA_RECEPCAO"] = "recepcao-dev-2026!"
os.environ["SEED_SENHA_CARLA"] = "carla-dev-2026!"
os.environ["SEED_SENHA_DIEGO"] = "diego-dev-2026!"
os.environ["SEED_TOTP_ADMIN"] = "JBSWY3DPEHPK3PXP"
os.environ["LAB_CLIENT_ID"] = "lab-parceiro"
os.environ["LAB_CLIENT_SECRET"] = "lab-secret-dev-2026!"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.auth import security  # noqa: E402
from app.auth.dependencies import ESCOPOS_POR_PAPEL  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402

# Rate limiting desligado por padrão nos testes (isolamento). O teste dedicado de
# rate limit reativa e reseta o contador explicitamente.
limiter.enabled = False
from app.models.tables import Consulta, Usuario  # noqa: E402
from app.seed import semear  # noqa: E402

# Um único engine em memória compartilhado por toda a sessão de testes.
_test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
# Schema + seed uma única vez (bcrypt é caro; usuários/base não mudam entre testes).
SQLModel.metadata.create_all(_test_engine)
with Session(_test_engine) as _s:
    semear(session=_s)


@pytest.fixture(autouse=True)
def _banco_limpo():
    """Isola cada teste apagando só as consultas (base semeada permanece)."""
    with Session(_test_engine) as s:
        for c in s.exec(__import__("sqlmodel").select(Consulta)).all():
            s.delete(c)
        s.commit()
    yield


@pytest.fixture
def session():
    with Session(_test_engine) as s:
        yield s


def _get_session_override():
    with Session(_test_engine) as session:
        yield session


app.dependency_overrides[get_session] = _get_session_override


@pytest.fixture
def client():
    return TestClient(app)


def _token(username: str) -> str:
    with Session(_test_engine) as s:
        u = s.get(Usuario, username)
        claims = {"papel": u.papel, "scope": ESCOPOS_POR_PAPEL.get(u.papel, "")}
        if u.profissional_id is not None:
            claims["profissional_id"] = u.profissional_id
        if u.totp_secret:
            claims |= {"mfa": True, "amr": ["pwd", "otp"]}
    return security.criar_access_token(sub=username, claims=claims)


@pytest.fixture
def auth():
    return lambda username: {"Authorization": f"Bearer {_token(username)}"}


@pytest.fixture
def cookie():
    return lambda username: {"access_token": _token(username)}
