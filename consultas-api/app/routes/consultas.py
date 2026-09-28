"""Recurso REST de consultas — autenticação, ownership (Ex. 6), SQLModel (Ex. 11)
e correções do Ex. 9.

Ownership impossível de esquecer (Ex. 9): as rotas de item vivem em `item_router`,
cujo prefixo `/consultas/{consulta_id}` já carrega `Depends(get_consulta_autorizada)`.
Qualquer rota nova sob esse prefixo herda a checagem de posse — inclusive /prontuario,
que na V1 era vulnerável. A regra de posse continua num único lugar (dependencies.py).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from app import database as db
from app.auth.dependencies import (
    get_consulta_autorizada,
    get_current_user,
    require_roles,
)
from app.database import get_session
from app.models import ConsultaCreate, ConsultaPublic, ConsultaUpdate, StatusConsulta
from app.models.consulta import TRANSICOES_VALIDAS
from app.models.tables import Consulta, Paciente

# Respostas de erro documentadas na OpenAPI (auditoria do Ex. 13).
_ERRO_AUTH = {401: {"description": "Não autenticado"}, 403: {"description": "Sem permissão"}}
_ERRO_ITEM = {**_ERRO_AUTH, 404: {"description": "Não encontrada ou sem posse"}}

# Coleção: /consultas
router = APIRouter(prefix="/consultas", tags=["consultas"], responses=_ERRO_AUTH)

# Item: /consultas/{consulta_id} — ownership aplicado no prefixo (Ex. 9).
item_router = APIRouter(
    prefix="/consultas/{consulta_id}",
    tags=["consultas"],
    dependencies=[Depends(get_consulta_autorizada)],
    responses=_ERRO_ITEM,
)


@router.get("", response_model=list[ConsultaPublic])
def listar_consultas(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    stmt = select(Consulta)
    if user.get("papel") == "profissional":
        stmt = stmt.where(Consulta.profissional_id == user.get("profissional_id"))
    return session.exec(stmt).all()


@router.post("", response_model=ConsultaPublic, status_code=status.HTTP_201_CREATED)
def criar_consulta(
    payload: ConsultaCreate,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(require_roles("profissional", "admin")),
):
    paciente = session.get(Paciente, payload.paciente_id)
    if paciente is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Paciente inexistente")

    # profissional_id NÃO vem do cliente: é o profissional dono do paciente.
    prof_id = paciente.profissional_id
    if user.get("papel") == "profissional" and prof_id != user.get("profissional_id"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Profissional só agenda consultas para os próprios pacientes",
        )

    agora = db.now_utc()
    consulta = Consulta(
        paciente_id=payload.paciente_id,
        profissional_id=prof_id,
        data_hora=payload.data_hora,
        observacoes=payload.observacoes,
        status=StatusConsulta.agendada.value,
        criado_por=user["sub"],
        ip_origem=request.client.host if request.client else None,
        criado_em=agora,
        atualizado_em=agora,
    )
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    return consulta


@item_router.get("", response_model=ConsultaPublic)
def obter_consulta(consulta: Consulta = Depends(get_consulta_autorizada)):
    return consulta


@item_router.get("/prontuario")
def prontuario(
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
):
    # Corrigido (V1): a rota herda o ownership do item_router; só o dono/admin/recepção
    # chega aqui. A busca por id sem checagem foi eliminada.
    paciente = session.get(Paciente, consulta.paciente_id)
    return {
        "consulta_id": consulta.id,
        "paciente": paciente.nome if paciente else None,
        "cpf": paciente.cpf if paciente else None,
        "profissional_id": consulta.profissional_id,
        "observacoes": consulta.observacoes,
    }


@item_router.patch("", response_model=ConsultaPublic)
def atualizar_consulta(
    payload: ConsultaUpdate,
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # extra="forbid" no modelo já rejeita profissional_id/criado_por (mass assignment).
    dados = payload.model_dump(exclude_unset=True)

    # Recepção só pode cancelar (matriz de permissões).
    if user.get("papel") == "recepcao":
        if set(dados) - {"status"} or dados.get("status") != StatusConsulta.cancelada:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Recepção só pode cancelar consultas")

    # Transição de status por whitelist.
    novo_status = dados.get("status")
    if novo_status is not None:
        atual = StatusConsulta(consulta.status)
        if novo_status != atual and novo_status not in TRANSICOES_VALIDAS[atual]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Transição de status inválida: {atual.value} → {novo_status.value}",
            )

    if "data_hora" in dados:
        consulta.data_hora = dados["data_hora"]
    if "observacoes" in dados:
        consulta.observacoes = dados["observacoes"]
    if novo_status is not None:
        consulta.status = novo_status.value
    consulta.atualizado_em = db.now_utc()

    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    return consulta


@item_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remover_consulta(
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user.get("papel") == "recepcao":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Recepção não remove consultas")
    session.delete(consulta)
    session.commit()
