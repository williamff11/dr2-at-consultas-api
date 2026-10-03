"""Ameaça: T04 (JWT forjado/expirado) · README.md, Ex. 4."""
from datetime import datetime, timedelta

import jwt

from app.auth import security


def test_T04_token_expirado(client):
    t = security.criar_access_token("dra_carla", {"papel": "profissional", "profissional_id": 1},
                                    expira_em=timedelta(minutes=-1))
    assert client.get("/consultas", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_T04_assinatura_forjada(client):
    forjado = jwt.encode(
        {"sub": "admin", "papel": "admin", "iss": security.ISSUER, "aud": security.AUDIENCE,
         "iat": int(datetime.now().timestamp()),
         "exp": int((datetime.now() + timedelta(minutes=5)).timestamp())},
        "chave-do-atacante", algorithm="HS256")
    assert client.get("/consultas", headers={"Authorization": f"Bearer {forjado}"}).status_code == 401


def test_T04_aud_errada(client):
    import jwt as _jwt
    t = _jwt.encode(
        {"sub": "dra_carla", "papel": "profissional", "iss": security.ISSUER, "aud": "outra-api",
         "iat": int(datetime.now().timestamp()),
         "exp": int((datetime.now() + timedelta(minutes=5)).timestamp())},
        security.SECRET_KEY, algorithm="HS256")
    assert client.get("/consultas", headers={"Authorization": f"Bearer {t}"}).status_code == 401
