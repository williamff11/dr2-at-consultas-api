from fastapi import APIRouter, HTTPException, Request, status

from app import database as db
from app.models import ConsultaCreate, ConsultaPublic, ConsultaUpdate, StatusConsulta

router = APIRouter(prefix="/consultas", tags=["consultas"])


def _get_or_404(consulta_id: int) -> dict:
    consulta = db.consultas.get(consulta_id)
    if consulta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consulta não encontrada")
    return consulta


@router.get("", response_model=list[ConsultaPublic])
def listar_consultas():
    return list(db.consultas.values())


@router.get("/{consulta_id}", response_model=ConsultaPublic)
def obter_consulta(consulta_id: int):
    # TODO Ex. 6/9: verificar ownership (BOLA) — hoje qualquer id é retornado
    return _get_or_404(consulta_id)


@router.post("", response_model=ConsultaPublic, status_code=status.HTTP_201_CREATED)
def criar_consulta(payload: ConsultaCreate, request: Request):
    if payload.paciente_id not in db.pacientes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Paciente inexistente")
    if payload.profissional_id not in db.profissionais:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Profissional inexistente")

    agora = db.now_utc()
    consulta = {
        "id": db.next_id(),
        **payload.model_dump(),
        "status": StatusConsulta.agendada,
        # --- campos internos de auditoria (nunca expostos) ---
        "criado_por": "anonimo",  # TODO Ex. 6: usuário autenticado
        "ip_origem": request.client.host if request.client else None,
        "criado_em": agora,
        "atualizado_em": agora,
    }
    db.consultas[consulta["id"]] = consulta
    return consulta


@router.patch("/{consulta_id}", response_model=ConsultaPublic)
def atualizar_consulta(consulta_id: int, payload: ConsultaUpdate):
    consulta = _get_or_404(consulta_id)
    consulta.update(payload.model_dump(exclude_unset=True))
    consulta["atualizado_em"] = db.now_utc()
    return consulta


@router.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_consulta(consulta_id: int):
    _get_or_404(consulta_id)
    del db.consultas[consulta_id]
