"""Testes unitários com mocking (Ex. 13, R24).

Isolam a lógica de autorização/entrada de suas dependências externas:
- dependency_overrides[get_current_user] simula papéis sem gerar JWT;
- patch em verificar_senha / pyotp.TOTP.verify / relógio;
- mock da sessão para testar ownership isoladamente.
Inclui o teste de sucesso do Ex. 1 (R24 cita o teste inicial explicitamente).
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app
from tests.test_consultas import _payload


# ---------- teste de sucesso do Ex. 1 (preservado, R24) ----------
def test_ex1_criar_e_obter_sucesso(client, auth):
    r = client.post("/consultas", json=_payload(), headers=auth("dra_carla"))
    assert r.status_code == 201
    cid = r.json()["id"]
    assert client.get(f"/consultas/{cid}", headers=auth("dra_carla")).status_code == 200


# ---------- mocking do principal via dependency_overrides ----------
def _override_user(**claims):
    def _dep():
        return {"sub": "mock", "papel": "profissional", "profissional_id": 1, **claims}
    return _dep


def test_mock_papel_recepcao_barrado_em_admin():
    app.dependency_overrides[get_current_user] = _override_user(papel="recepcao")
    try:
        r = TestClient(app).get("/admin/usuarios")
        assert r.status_code == 403   # RBAC decide pelo papel mockado, sem JWT real
    finally:
        del app.dependency_overrides[get_current_user]


def test_mock_profissional_cria_para_proprio_paciente():
    app.dependency_overrides[get_current_user] = _override_user(papel="profissional", profissional_id=1)
    try:
        r = TestClient(app).post("/consultas", json=_payload())
        assert r.status_code == 201
    finally:
        del app.dependency_overrides[get_current_user]


# ---------- mock de verificar_senha (login sem bcrypt real) ----------
def test_mock_login_sem_bcrypt(client):
    with patch("app.routes.auth.security.verificar_senha", return_value=True):
        r = client.post("/auth/token", data={"username": "dra_carla", "password": "qualquer"})
    assert r.status_code == 200
    assert "access_token" in r.json()


# ---------- mock do TOTP (MFA) ----------
def test_mock_mfa_verify_com_totp_mockado(client):
    login = client.post("/auth/token", data={"username": "admin", "password": "admin-dev-2026!"})
    mfa_token = login.json()["mfa_token"]
    with patch("app.routes.auth.verificar_codigo", return_value=True):
        r = client.post("/auth/mfa/verify", json={"mfa_token": mfa_token, "codigo": "000000"})
    assert r.status_code == 200
    assert r.json().get("access_token")


# ---------- controle do relógio via timedelta (expiração do JWT) ----------
def test_relogio_token_expirado(client):
    from app.auth import security
    # controla o "tempo" do token com expira_em negativo → já expirado
    expirado = security.criar_access_token(
        "dra_carla", {"papel": "profissional", "profissional_id": 1},
        expira_em=timedelta(seconds=-1),
    )
    r = client.get("/consultas", headers={"Authorization": f"Bearer {expirado}"})
    assert r.status_code == 401


# ---------- mock da sessão: ownership isolado do banco ----------
def test_mock_ownership_sem_banco():
    from types import SimpleNamespace

    from app.auth.dependencies import get_consulta_autorizada
    from fastapi import HTTPException

    consulta_de_outro = SimpleNamespace(id=9, profissional_id=2)
    fake_session = SimpleNamespace(get=lambda model, cid: consulta_de_outro)
    user = {"papel": "profissional", "profissional_id": 1}

    with pytest.raises(HTTPException) as exc:
        get_consulta_autorizada(consulta_id=9, session=fake_session, user=user)
    assert exc.value.status_code == 404   # não é dono → 404, sem tocar o banco real
