"""Testes da integração M2M (Ex. 7): escopos e separação humano × máquina (T07)."""
from datetime import datetime, timedelta

from tests.test_consultas import _payload

CLIENT = {"grant_type": "client_credentials", "client_id": "lab-parceiro",
          "client_secret": "lab-secret-dev-2026!"}


def _client_token(client):
    return client.post("/auth/client-token", data=CLIENT).json()["access_token"]


def test_client_credentials_emite_token_m2m(client):
    r = client.post("/auth/client-token", data=CLIENT)
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "horarios:read"
    from app.auth import security
    claims = security.decodificar_token(body["access_token"])
    assert claims["client_type"] == "m2m"
    assert "papel" not in claims  # M2M não tem papel humano


def test_grant_type_invalido_rejeitado(client):
    r = client.post("/auth/client-token", data={**CLIENT, "grant_type": "password"})
    assert r.status_code == 400


def test_secret_invalido_401(client):
    r = client.post("/auth/client-token", data={**CLIENT, "client_secret": "errado"})
    assert r.status_code == 401


def test_lab_acessa_horarios(client):
    tok = _client_token(client)
    dia = datetime.now().strftime("%Y-%m-%d")
    r = client.get(f"/horarios-disponiveis?profissional_id=1&dia={dia}",
                   headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert "horarios_livres" in r.json()
    # nenhum dado de paciente na resposta
    assert "paciente" not in r.text.lower()


def test_lab_nao_acessa_consultas(client, auth):
    tok = _client_token(client)
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/consultas", headers=h).status_code == 403
    assert client.post("/consultas", json=_payload(), headers=h).status_code == 403


def test_humano_nao_acessa_horarios_sem_escopo(client, auth):
    # profissional não tem 'horarios:read' → 403
    r = client.get("/horarios-disponiveis?profissional_id=1&dia=2026-09-28",
                   headers=auth("dra_carla"))
    assert r.status_code == 403


def test_lab_nao_faz_login_humano(client):
    r = client.post("/auth/token", data={"username": "lab-parceiro", "password": "lab-secret-dev-2026!"})
    assert r.status_code == 401
