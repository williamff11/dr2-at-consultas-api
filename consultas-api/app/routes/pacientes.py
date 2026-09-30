"""Busca de pacientes (Ex. 8/9) — corrigida no Ex. 9.

A V2 (SQL injection) foi eliminada: a query é parametrizada via SQLModel e o
parâmetro `nome` é validado por regex (whitelist de caracteres) na borda.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.tables import Paciente

router = APIRouter(prefix="/pacientes", tags=["pacientes"],
    responses={401: {"description": "Não autenticado"}, 422: {"description": "Parâmetro inválido"}})


@router.get("")
def buscar_pacientes(
    # Whitelist: letras (com acento), espaço e apóstrofo; 2 a 60 caracteres.
    nome: str = Query(pattern=r"^[A-Za-zÀ-ÿ' ]{2,60}$", min_length=2, max_length=60),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # DEMO: reintrodução da V2 (SQL por concatenação) para provar que o security-gate
    # bloqueia o merge. NÃO deve ser mesclado (branch demo/gate-bloqueio).
    sql = text(f"SELECT id, nome, cpf, profissional_id FROM paciente WHERE nome LIKE '%{nome}%'")  # noqa: S608
    linhas = session.execute(sql).fetchall()
    return [list(linha) for linha in linhas]
