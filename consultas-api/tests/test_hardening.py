"""Testes do hardening do Ex. 10: headers de segurança, CORS e rate limit (T05, T10, T12)."""
import pytest

from app.core.rate_limit import limiter


def test_headers_de_seguranca_presentes(client):
    r = client.get("/health")
    assert r.headers["strict-transport-security"].startswith("max-age=31536000")
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"


def test_csp_nas_paginas_html(client, cookie):
    r = client.get("/recepcao/login")
    assert "content-security-policy" in r.headers
    assert "script-src 'none'" in r.headers["content-security-policy"]


def test_cors_origem_fora_da_allowlist(client):
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    # origem não permitida → sem header de allow-origin ecoando a origem maliciosa
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"


@pytest.fixture
def rate_limit_ativo():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()
    limiter.enabled = False


def test_rate_limit_login(client, rate_limit_ativo):
    codigos = [
        client.post("/auth/token", data={"username": "x", "password": "y"}).status_code
        for _ in range(7)
    ]
    assert 429 in codigos                     # a partir da 6ª tentativa
    assert codigos.count(401) <= 5            # só as 5 primeiras chegam a validar
