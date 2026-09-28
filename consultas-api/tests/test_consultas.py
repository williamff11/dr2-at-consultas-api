"""Suíte de testes — iniciada no Ex. 1, expandida nos Ex. 6, 12 e 13.

Os testes do Ex. 1/2 foram preservados (R24) e apenas passaram a autenticar via
fixture, já que as rotas agora exigem sessão (Ex. 6).
"""
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database as db

CAMPOS_INTERNOS = {"criado_por", "ip_origem", "criado_em", "atualizado_em"}


def _payload(**extra):
    base = {
        "paciente_id": 1,  # paciente da Dra. Carla (profissional 1)
        "data_hora": (datetime.now() + timedelta(hours=1)).replace(microsecond=0).isoformat(),
        "observacoes": "Retorno",
    }
    base.update(extra)
    return base


# ---------- Ex. 1: caminho de sucesso (agora autenticado) ----------
def test_criar_e_obter_consulta_sucesso(client, auth):
    r = client.post("/consultas", json=_payload(), headers=auth("dra_carla"))
    assert r.status_code == 201
    criada = r.json()
    assert criada["status"] == "agendada"
    assert criada["profissional_id"] == 1  # derivado do paciente, não do corpo

    r = client.get(f"/consultas/{criada['id']}", headers=auth("dra_carla"))
    assert r.status_code == 200
    assert r.json()["paciente_id"] == 1


# ---------- Ex. 2: response_model não vaza auditoria ----------
def test_resposta_nao_expoe_campos_internos(client, auth):
    criada = client.post("/consultas", json=_payload(), headers=auth("dra_carla")).json()
    assert CAMPOS_INTERNOS.isdisjoint(criada)
    assert CAMPOS_INTERNOS <= db.consultas[criada["id"]].keys()

    lista = client.get("/consultas", headers=auth("dra_carla")).json()
    assert all(CAMPOS_INTERNOS.isdisjoint(item) for item in lista)


# ---------- Ex. 2/R3: sem response_model o registro inteiro vazaria ----------
def test_sem_response_model_vazaria_campos_internos(client, auth):
    criada = client.post("/consultas", json=_payload(), headers=auth("dra_carla")).json()
    registro = db.consultas[criada["id"]]

    app_sem_filtro = FastAPI()
    app_sem_filtro.add_api_route("/raw", lambda: registro)  # sem response_model
    vazado = TestClient(app_sem_filtro).get("/raw").json()

    assert CAMPOS_INTERNOS <= vazado.keys()          # sem filtro: vaza
    assert vazado["ip_origem"] is not None
    # a rota real, com response_model, não vaza:
    real = client.get(f"/consultas/{criada['id']}", headers=auth("dra_carla")).json()
    assert CAMPOS_INTERNOS.isdisjoint(real)


# ---------- Ex. 2: XSS stored neutralizado pelo auto-escape ----------
def test_agenda_html_escapa_payload_xss(client, auth, cookie):
    ataque = "<script>alert('xss')</script>"
    client.post("/consultas", json=_payload(observacoes=ataque), headers=auth("dra_carla"))

    r = client.get("/recepcao/agenda", cookies=cookie("recepcao"))
    assert r.status_code == 200
    assert ataque not in r.text
    assert "&lt;script&gt;" in r.text
