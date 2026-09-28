"""Recurso REST de consultas — protegido por autenticação e ownership (Ex. 6).

A regra de posse vive em app/auth/dependencies.get_consulta_autorizada; aqui as
rotas apenas a declaram. Restrições por papel usam require_roles / o principal.
No Ex. 9, GET/PATCH/DELETE/{id} migram para um APIRouter com a dependência de
ownership no prefixo, para que nenhuma rota nova sob /consultas/{id} a esqueça.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app import database as db
from app.auth.dependencies import (
    get_consulta_autorizada,
    get_current_user,
    require_roles,
)
from app.models import ConsultaCreate, ConsultaPublic, ConsultaUpdate, StatusConsulta

router = APIRouter(prefix="/consultas", tags=["consultas"])


@router.get("", response_model=list[ConsultaPublic])
def listar_consultas(user: dict = Depends(get_current_user)):
    todas = list(db.consultas.values())
    if user.get("papel") == "profissional":
        # profissional só vê as consultas dos seus pacientes
        return [c for c in todas if c["profissional_id"] == user.get("profissional_id")]
    return todas  # admin e recepção veem todas


@router.get("/{consulta_id}", response_model=ConsultaPublic)
def obter_consulta(consulta: dict = Depends(get_consulta_autorizada)):
    return consulta


@router.post("", response_model=ConsultaPublic, status_code=status.HTTP_201_CREATED)
def criar_consulta(
    payload: ConsultaCreate,
    request: Request,
    user: dict = Depends(require_roles("profissional", "admin")),
):
    paciente = db.pacientes.get(payload.paciente_id)
    if paciente is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Paciente inexistente")

    # profissional_id NÃO vem do cliente: é o profissional dono do paciente.
    prof_id = paciente["profissional_id"]
    if user.get("papel") == "profissional" and prof_id != user.get("profissional_id"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Profissional só agenda consultas para os próprios pacientes",
        )

    agora = db.now_utc()
    consulta = {
        "id": db.next_id(),
        "paciente_id": payload.paciente_id,
        "profissional_id": prof_id,
        "data_hora": payload.data_hora,
        "observacoes": payload.observacoes,
        "status": StatusConsulta.agendada,
        # --- auditoria (nunca exposta) ---
        "criado_por": user["sub"],
        "ip_origem": request.client.host if request.client else None,
        "criado_em": agora,
        "atualizado_em": agora,
    }
    db.consultas[consulta["id"]] = consulta
    return consulta


@router.patch("/{consulta_id}", response_model=ConsultaPublic)
def atualizar_consulta(
    payload: ConsultaUpdate,
    consulta: dict = Depends(get_consulta_autorizada),
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
    consulta.update(dados)
    consulta["atualizado_em"] = db.now_utc()
    return consulta


@router.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_consulta(
    consulta: dict = Depends(get_consulta_autorizada),
    user: dict = Depends(get_current_user),
):
    if user.get("papel") == "recepcao":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Recepção não remove consultas")
    del db.consultas[consulta["id"]]
