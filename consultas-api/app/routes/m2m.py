"""Integração máquina-a-máquina (Ex. 7): client credentials + escopo restrito.

O laboratório parceiro obtém um token que só enxerga horários livres. Mesmo que
esse token vaze, ele não alcança dados de paciente: as rotas de consulta exigem
escopos `consultas:*` que nunca são emitidos para um cliente M2M (T07).
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Security, status

from app import database as db
from app.auth import security
from app.auth.principal import require_scopes

router = APIRouter(tags=["m2m"])


@router.post("/auth/client-token")
def client_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    if grant_type != "client_credentials":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "grant_type não suportado neste endpoint (use client_credentials)",
        )
    cliente = db.clientes_m2m.get(client_id)
    if cliente is None or not security.verificar_senha(client_secret, cliente["secret_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "client_id ou client_secret inválidos")

    token = security.criar_access_token(
        sub=client_id,
        claims={
            "client_type": "m2m",
            "scope": cliente["scope"],   # ex.: "horarios:read" — sem 'role'
        },
        expira_em=timedelta(minutes=security.M2M_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "scope": cliente["scope"]}


@router.get("/horarios-disponiveis")
def horarios_disponiveis(
    profissional_id: int,
    dia: str,
    principal: dict = Security(require_scopes, scopes=["horarios:read"]),
):
    """Slots livres de um profissional num dia. NÃO expõe paciente (só horários)."""
    if profissional_id not in db.profissionais:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profissional inexistente")

    grade = [f"{h:02d}:00" for h in range(8, 18)]  # 08:00..17:00
    ocupados = {
        c["data_hora"].strftime("%H:%M")
        for c in db.consultas.values()
        if c["profissional_id"] == profissional_id
        and c["data_hora"].strftime("%Y-%m-%d") == dia
        and c["status"] != "cancelada"
    }
    livres = [h for h in grade if h not in ocupados]
    return {"profissional_id": profissional_id, "dia": dia, "horarios_livres": livres}
