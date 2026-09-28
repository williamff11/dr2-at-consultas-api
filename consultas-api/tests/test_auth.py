"""Testes de autenticação e autorização (Ex. 6).

Inclui o teste obrigatório do enunciado (recepcionista barrado em rota de admin),
que é a semente da suíte de segurança expandida no Ex. 12.
"""
from datetime import datetime, timedelta

from app.auth import security
from tests.test_consultas import _payload


# ---------- teste obrigatório do enunciado ----------
def test_recepcionista_nao_acessa_rota_admin(client, auth):
    r = client.get("/admin/usuarios", headers=auth("recepcao"))
    assert r.status_code == 403


# ---------- autenticação ----------
def test_sem_token_401(client):
    assert client.get("/consultas").status_code == 401


def test_token_expirado_401(client):
    token = security.criar_access_token(
        sub="dra_carla",
        claims={"papel": "profissional", "profissional_id": 1},
        expira_em=timedelta(minutes=-1),  # já expirado
    )
    r = client.get("/consultas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_assinado_com_outra_chave_401(client):
    import jwt
    forjado = jwt.encode(
        {"sub": "admin", "papel": "admin", "iss": security.ISSUER,
         "aud": security.AUDIENCE, "iat": int(datetime.now().timestamp()),
         "exp": int((datetime.now() + timedelta(minutes=5)).timestamp())},
        "chave-do-atacante", algorithm="HS256",
    )
    r = client.get("/consultas", headers={"Authorization": f"Bearer {forjado}"})
    assert r.status_code == 401


# ---------- MFA ----------
def test_admin_sem_mfa_barrado_e_com_mfa_liberado(client):
    import os

    from app.auth.mfa import gerar_codigo_atual

    # login → desafio de MFA
    r = client.post("/auth/token", data={"username": "admin", "password": "admin-dev-2026!"})
    assert r.status_code == 200 and r.json().get("mfa_required") is True
    mfa_token = r.json()["mfa_token"]

    # usar o mfa_token direto numa rota admin não vale (scope mfa_pending)
    r = client.get("/admin/usuarios", headers={"Authorization": f"Bearer {mfa_token}"})
    assert r.status_code == 403

    # verificar o 2º fator → access token com mfa=true
    codigo = gerar_codigo_atual(os.environ["SEED_TOTP_ADMIN"])
    r = client.post("/auth/mfa/verify", json={"mfa_token": mfa_token, "codigo": codigo})
    assert r.status_code == 200
    access = r.json()["access_token"]

    r = client.get("/admin/usuarios", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200


def test_mfa_codigo_invalido_401(client):
    r = client.post("/auth/token", data={"username": "admin", "password": "admin-dev-2026!"})
    mfa_token = r.json()["mfa_token"]
    r = client.post("/auth/mfa/verify", json={"mfa_token": mfa_token, "codigo": "000000"})
    assert r.status_code == 401


# ---------- ownership (BOLA) ----------
def test_profissional_nao_acessa_consulta_de_outro(client, auth):
    # Carla cria consulta do paciente dela (paciente 1)
    criada = client.post("/consultas", json=_payload(), headers=auth("dra_carla")).json()

    # Diego (profissional 2) tenta ler/alterar → 404 (não confirma existência)
    assert client.get(f"/consultas/{criada['id']}", headers=auth("dr_diego")).status_code == 404
    r = client.patch(f"/consultas/{criada['id']}", json={"status": "confirmada"}, headers=auth("dr_diego"))
    assert r.status_code == 404

    # a dona acessa normalmente
    assert client.get(f"/consultas/{criada['id']}", headers=auth("dra_carla")).status_code == 200


def test_profissional_so_ve_as_proprias_consultas(client, auth):
    client.post("/consultas", json=_payload(paciente_id=1), headers=auth("dra_carla"))
    # paciente 2 é do Diego; Carla não consegue criar para ele
    r = client.post("/consultas", json=_payload(paciente_id=2), headers=auth("dra_carla"))
    assert r.status_code == 403

    lista_carla = client.get("/consultas", headers=auth("dra_carla")).json()
    assert all(c["profissional_id"] == 1 for c in lista_carla)


def test_login_claims_e_expiracao(client):
    r = client.post("/auth/token", data={"username": "dra_carla", "password": "carla-dev-2026!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    claims = security.decodificar_token(token)
    assert claims["papel"] == "profissional"
    assert claims["profissional_id"] == 1
    assert claims["exp"] - claims["iat"] == security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
