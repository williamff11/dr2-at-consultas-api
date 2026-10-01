"""Ameaça: T07 (token M2M além do escopo) · Misuse case: MC04 · README.md, Ex. 4."""
CLIENT = {"grant_type": "client_credentials", "client_id": "lab-parceiro",
          "client_secret": "lab-secret-dev-2026!"}


def _m2m(client):
    return client.post("/auth/client-token", data=CLIENT).json()["access_token"]


def test_T07_m2m_nao_acessa_consultas(client):
    h = {"Authorization": f"Bearer {_m2m(client)}"}
    assert client.get("/consultas", headers=h).status_code == 403
    assert client.post("/consultas", json={"paciente_id": 1, "data_hora": "2026-09-28T10:00:00"},
                       headers=h).status_code == 403


def test_T07_humano_sem_escopo_horarios(client, auth):
    assert client.get("/horarios-disponiveis?profissional_id=1&dia=2026-09-28",
                      headers=auth("dra_carla")).status_code == 403
