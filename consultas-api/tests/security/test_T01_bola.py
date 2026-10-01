"""Ameaça: T01 (BOLA) · Misuse case: MC01 · README.md, Ex. 4.

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


def test_T01_agenda_html_so_mostra_proprias(client, auth, cookie):
    p = payload(observacoes="dado clinico da carla")
    client.post("/consultas", json=p, headers=auth("dra_carla"))
    dia = p["data_hora"][:10]
    assert "dado clinico da carla" not in client.get(
        "/recepcao/agenda", params={"dia": dia}, cookies=cookie("dr_diego")).text
    assert "dado clinico da carla" in client.get(
        "/recepcao/agenda", params={"dia": dia}, cookies=cookie("recepcao")).text


def test_T01_busca_pacientes_so_retorna_proprios(client, auth):
    r = client.get("/pacientes", params={"nome": "Ana"}, headers=auth("dr_diego"))
    assert r.status_code == 200 and r.json() == []   # Ana é paciente da Dra. Carla
    r = client.get("/pacientes", params={"nome": "Ana"}, headers=auth("dra_carla"))
    assert [p["nome"] for p in r.json()] == ["Ana Souza"]
