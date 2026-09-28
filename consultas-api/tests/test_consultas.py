"""Suíte de testes — iniciada no Ex. 1, expandida nos Ex. 6, 12 e 13."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import database as db
from app.main import app

client = TestClient(app)

CAMPOS_INTERNOS = {"criado_por", "ip_origem", "criado_em", "atualizado_em"}


@pytest.fixture(autouse=True)
def limpar_banco():
    db.reset()
    yield
    db.reset()


def _payload(**extra):
    base = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": (datetime.now() + timedelta(hours=1)).replace(microsecond=0).isoformat(),
        "observacoes": "Retorno",
    }
    base.update(extra)
    return base


# ---------- Ex. 1: caminho de sucesso ----------
def test_criar_e_obter_consulta_sucesso():
    r = client.post("/consultas", json=_payload())
    assert r.status_code == 201
    criada = r.json()
    assert criada["status"] == "agendada"

    r = client.get(f"/consultas/{criada['id']}")
    assert r.status_code == 200
    assert r.json()["paciente_id"] == 1


# ---------- Ex. 2: response_model não vaza auditoria ----------
def test_resposta_nao_expoe_campos_internos():
    criada = client.post("/consultas", json=_payload()).json()
    assert CAMPOS_INTERNOS.isdisjoint(criada)
    # o registro interno TEM os campos; a resposta não
    assert CAMPOS_INTERNOS <= db.consultas[criada["id"]].keys()

    lista = client.get("/consultas").json()
    assert all(CAMPOS_INTERNOS.isdisjoint(item) for item in lista)


# ---------- Ex. 2: XSS stored neutralizado pelo auto-escape ----------
def test_agenda_html_escapa_payload_xss():
    ataque = "<script>alert('xss')</script>"
    client.post("/consultas", json=_payload(observacoes=ataque))

    r = client.get("/recepcao/agenda")
    assert r.status_code == 200
    assert ataque not in r.text
    assert "&lt;script&gt;" in r.text
