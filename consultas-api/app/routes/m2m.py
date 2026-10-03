"""Integração máquina-a-máquina"""
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Security, status
from sqlmodel import Session, select

from app.auth import security
from app.auth.principal import require_scopes
from app.core.rate_limit import LIMITE_LOGIN, limiter
from app.database import get_session
from app.models.tables import ClienteM2M, Consulta, Profissional

router = APIRouter(tags=["m2m"])


@router.post("/auth/client-token")
@limiter.limit(LIMITE_LOGIN)
def client_token(
    request: Request,
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    session: Session = Depends(get_session),
):
    if grant_type != "client_credentials":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "grant_type não suportado neste endpoint (use client_credentials)",
        )
    cliente = session.get(ClienteM2M, client_id)
    if cliente is None or not security.verificar_senha(client_secret, cliente.secret_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "client_id ou client_secret inválidos")

    token = security.criar_access_token(
        sub=client_id,
        claims={
            "client_type": "m2m",
            "scope": cliente.scope,   # ex.: "horarios:read" — sem 'role'
        },
        expira_em=timedelta(minutes=security.M2M_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "scope": cliente.scope}


@router.get("/horarios-disponiveis")
def horarios_disponiveis(
    profissional_id: int,
    dia: str,
    session: Session = Depends(get_session),
    principal: dict = Security(require_scopes, scopes=["horarios:read"]),
):
    if session.get(Profissional, profissional_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profissional inexistente")

    grade = [f"{h:02d}:00" for h in range(8, 18)]  # 08:00..17:00
    consultas = session.exec(
        select(Consulta).where(Consulta.profissional_id == profissional_id)
    ).all()
    ocupados = {
        c.data_hora.strftime("%H:%M")
        for c in consultas
        if c.data_hora.strftime("%Y-%m-%d") == dia and c.status != "cancelada"
    }
    livres = [h for h in grade if h not in ocupados]
    return {"profissional_id": profissional_id, "dia": dia, "horarios_livres": livres}
