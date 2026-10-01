"""Ameaça: T06 (mass assignment) · Misuse case: MC06 · README.md, Ex. 4."""
from tests.security._helpers import payload


def test_T06_patch_rejeita_extras(client, auth):
    c = client.post("/consultas", json=payload(), headers=auth("dra_carla")).json()
    r = client.patch(f"/consultas/{c['id']}",
                     json={"observacoes": "x", "profissional_id": 2, "criado_por": "hacker"},
                     headers=auth("dra_carla"))
    assert r.status_code == 422


def test_T06_post_rejeita_extras(client, auth):
    assert client.post("/consultas", json=payload(campo_x=1),
                       headers=auth("dra_carla")).status_code == 422
