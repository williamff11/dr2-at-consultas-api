"""Busca de pacientes"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.tables import Paciente

router = APIRouter(prefix="/pacientes", tags=["pacientes"],
    responses={401: {"description": "Não autenticado"}, 422: {"description": "Parâmetro inválido"}})


@router.get("")
def buscar_pacientes(
    # Whitelist: letras (com acento), espaço e apóstrofo; 2 a 60 caracteres.
    nome: str = Query(pattern=r"^[A-Za-zÀ-ÿ' ]{2,60}$", min_length=2, max_length=60, examples=["Ana"]),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    stmt = select(Paciente).where(Paciente.nome.contains(nome))
    pacientes = session.exec(stmt).all()
    return [
        {"id": p.id, "nome": p.nome, "cpf": p.cpf, "profissional_id": p.profissional_id}
        for p in pacientes
    ]
