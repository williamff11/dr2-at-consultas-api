"""Ameaça: T03 (XSS stored) · Misuse case: MC03 · docs/04_threat_model.md."""
from tests.security._helpers import payload


def test_T03_entrada_com_html_rejeitada(client, auth):
    r = client.post("/consultas", json=payload(observacoes="<script>alert(1)</script>"),
                    headers=auth("dra_carla"))
    assert r.status_code == 422


def test_T03_saida_escapada(client, auth, cookie):
    c = client.post("/consultas", json=payload(observacoes="A & B"), headers=auth("dra_carla")).json()
    r = client.get(f"/recepcao/consultas/{c['id']}", cookies=cookie("dra_carla"))
    assert "A &amp; B" in r.text
