"""Ameaça: T05 (força bruta no login) · Misuse case: MC05 · docs/04_threat_model.md."""
import pytest

from app.core.rate_limit import limiter


@pytest.fixture
def rate_limit_ativo():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()
    limiter.enabled = False


def test_T05_login_limitado(client, rate_limit_ativo):
    codigos = [client.post("/auth/token", data={"username": "x", "password": "y"}).status_code
               for _ in range(7)]
    assert 429 in codigos
    assert codigos.count(401) <= 5
