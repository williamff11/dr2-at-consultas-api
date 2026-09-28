"""Ameaça: T01 (BOLA) · Misuse case: MC01 · docs/04_threat_model.md.

Cobre GET, PATCH, DELETE, /prontuario e a página HTML de detalhe: um profissional
não acessa consulta de paciente de outro profissional (ownership centralizado).
"""
from tests.security._helpers import payload


def test_T01_get_bloqueado(client, auth):
    c = client.post("/consultas", json=payload(), headers=auth("dra_carla")).json()
    assert client.get(f"/consultas/{c['id']}", headers=auth("dr_diego")).status_code == 404


def test_T01_prontuario_bloqueado(client, auth):
    c = client.post("/consultas", json=payload(), headers=auth("dra_carla")).json()
    assert client.get(f"/consultas/{c['id']}/prontuario", headers=auth("dr_diego")).status_code == 404


def test_T01_patch_delete_bloqueado(client, auth):
    c = client.post("/consultas", json=payload(), headers=auth("dra_carla")).json()
    assert client.patch(f"/consultas/{c['id']}", json={"status": "confirmada"},
                        headers=auth("dr_diego")).status_code == 404
    assert client.delete(f"/consultas/{c['id']}", headers=auth("dr_diego")).status_code == 404


def test_T01_detalhe_html_bloqueado(client, auth, cookie):
    c = client.post("/consultas", json=payload(), headers=auth("dra_carla")).json()
    assert client.get(f"/recepcao/consultas/{c['id']}", cookies=cookie("dr_diego")).status_code == 404
