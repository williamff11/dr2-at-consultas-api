"""Recurso REST de consultas — autenticação, ownership (Ex. 6) e SQLModel (Ex. 11).

A regra de posse vive em app/auth/dependencies.get_consulta_autorizada; aqui as
rotas apenas a declaram. As queries usam select().where() (parametrizadas).
No Ex. 9, GET/PATCH/DELETE/{id} migram para um APIRouter com a dependência de
ownership no prefixo, para que nenhuma rota nova sob /consultas/{id} a esqueça.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app import database as db
from app.auth.dependencies import (
    get_consulta_autorizada,
    get_current_user,
    require_roles,
)
from app.database import get_session
from app.models import ConsultaCreate, ConsultaPublic, ConsultaUpdate, StatusConsulta
from app.models.tables import Consulta, Paciente

router = APIRouter(prefix="/consultas", tags=["consultas"])


@router.get("", response_model=list[ConsultaPublic])
def listar_consultas(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    stmt = select(Consulta)
    if user.get("papel") == "profissional":
        stmt = stmt.where(Consulta.profissional_id == user.get("profissional_id"))
    return session.exec(stmt).all()


@router.get("/{consulta_id}", response_model=ConsultaPublic)
def obter_consulta(consulta: Consulta = Depends(get_consulta_autorizada)):
    return consulta


@router.get("/{consulta_id}/prontuario")
def prontuario(
    consulta_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # VULN-V1 (intencional, Ex. 8): busca por id SEM get_consulta_autorizada → BOLA.
    # Qualquer usuário autenticado lê o prontuário (dados de saúde) de qualquer paciente.
    # Corrigido no Ex. 9 movendo a rota para o item_router (ownership no prefixo).
    consulta = session.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consulta não encontrada")
    paciente = session.get(Paciente, consulta.paciente_id)
    return {
        "consulta_id": consulta.id,
        "paciente": paciente.nome if paciente else None,
        "cpf": paciente.cpf if paciente else None,
        "profissional_id": consulta.profissional_id,
        "observacoes": consulta.observacoes,
    }


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


@router.patch("/{consulta_id}", response_model=ConsultaPublic)
def atualizar_consulta(
    payload: ConsultaUpdate,
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    dados = payload.model_dump(exclude_unset=True)
    # Recepção só pode cancelar (matriz de permissões).
    if user.get("papel") == "recepcao":
        if set(dados) - {"status"} or dados.get("status") != StatusConsulta.cancelada:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Recepção só pode cancelar consultas",
            )
    # VULN-V4 (intencional, Ex. 8): aplica TODOS os campos recebidos, inclusive extras
    # não declarados (profissional_id, criado_por) — mass assignment. Ex. 9 usa whitelist.
    for campo, valor in dados.items():
        setattr(consulta, campo, valor.value if isinstance(valor, StatusConsulta) else valor)
    consulta.atualizado_em = db.now_utc()
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    return consulta


@router.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_consulta(
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if user.get("papel") == "recepcao":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Recepção não remove consultas")
    session.delete(consulta)
    session.commit()
