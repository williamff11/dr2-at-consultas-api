"""Configuração compartilhada dos testes: path, seed e fixtures de autenticação.

As senhas de teste são definidas aqui (fixtures de teste, não código da aplicação —
app/ continua sem senha em texto). Elas devem casar com scripts/dev_env.sh.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Variáveis de seed ANTES de importar a aplicação/seed.
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("SEED_SENHA_ADMIN", "admin-dev-2026!")
os.environ.setdefault("SEED_SENHA_RECEPCAO", "recepcao-dev-2026!")
os.environ.setdefault("SEED_SENHA_CARLA", "carla-dev-2026!")
os.environ.setdefault("SEED_SENHA_DIEGO", "diego-dev-2026!")
os.environ.setdefault("SEED_TOTP_ADMIN", "JBSWY3DPEHPK3PXP")
os.environ.setdefault("LAB_CLIENT_ID", "lab-parceiro")
os.environ.setdefault("LAB_CLIENT_SECRET", "lab-secret-dev-2026!")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import database as db  # noqa: E402
from app.auth import mfa, security  # noqa: E402
from app.auth.dependencies import ESCOPOS_POR_PAPEL  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import semear  # noqa: E402

semear()


@pytest.fixture(autouse=True)
def limpar_banco():
    db.reset()
    yield
    db.reset()


@pytest.fixture
def client():
    return TestClient(app)


def _token(username: str) -> str:
    """Access token direto (sem passar pelo HTTP), para as fixtures."""
    u = db.usuarios[username]
    claims = {"papel": u["papel"], "scope": ESCOPOS_POR_PAPEL.get(u["papel"], "")}
    if "profissional_id" in u:
        claims["profissional_id"] = u["profissional_id"]
    if u.get("totp_secret"):
        claims |= {"mfa": True, "amr": ["pwd", "otp"]}
    return security.criar_access_token(sub=username, claims=claims)


@pytest.fixture
def auth():
    """Fábrica de headers Authorization por usuário: auth('dra_carla')."""
    return lambda username: {"Authorization": f"Bearer {_token(username)}"}


@pytest.fixture
def cookie():
    return lambda username: {"access_token": _token(username)}
