"""Helpers da suíte de segurança (rastreável ao threat model, README.md, Ex. 4)."""
from datetime import datetime, timedelta


def payload(**extra):
    base = {
        "paciente_id": 1,
        "data_hora": (datetime.now() + timedelta(hours=1)).replace(microsecond=0).isoformat(),
        "observacoes": "consulta",
    }
    base.update(extra)
    return base
