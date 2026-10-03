"""Rotas administrativas. Exigem papel admin e MFA (dois fatores)."""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.dependencies import require_mfa, require_roles
from app.database import get_session
from app.models.tables import Usuario

router = APIRouter(prefix="/admin", tags=["admin"],
    responses={401: {"description": "Não autenticado"}, 403: {"description": "Requer admin+MFA"}})


@router.get("/usuarios", dependencies=[Depends(require_roles("admin")), Depends(require_mfa)])
def listar_usuarios(session: Session = Depends(get_session)):
    """Lista usuários sem expor hashes de senha nem segredos TOTP."""
    usuarios = session.exec(select(Usuario)).all()
    return [
        {
            "username": u.username,
            "papel": u.papel,
            "profissional_id": u.profissional_id,
            "mfa_habilitado": bool(u.totp_secret),
        }
        for u in usuarios
    ]
