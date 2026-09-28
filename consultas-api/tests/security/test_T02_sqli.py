"""Ameaça: T02 (SQL injection) · Misuse case: MC02 · docs/04_threat_model.md."""
from tests.security._helpers import payload  # noqa: F401


def test_T02_injecao_rejeitada_na_borda(client, auth):
    r = client.get("/pacientes", params={"nome": "' OR 1=1"}, headers=auth("recepcao"))
    assert r.status_code == 422


def test_T02_valor_tratado_como_literal(client, auth):
    # apóstrofo legítimo passa a whitelist mas é ligado como parâmetro (sem UNION)
    r = client.get("/pacientes", params={"nome": "O'Brien"}, headers=auth("recepcao"))
    assert r.status_code == 200
    assert r.json() == []
    assert "$2b$" not in r.text  # nenhum hash vazado
