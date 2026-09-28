"""Rotas administrativas. Exigem papel admin E MFA (dois fatores)."""
from fastapi import APIRouter, Depends

from app import database as db
from app.auth.dependencies import require_mfa, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/usuarios", dependencies=[Depends(require_roles("admin")), Depends(require_mfa)])
def listar_usuarios():
    """Lista usuários sem expor hashes de senha nem segredos TOTP."""
    return [
        {
            "username": u["username"],
            "papel": u["papel"],
            "profissional_id": u.get("profissional_id"),
            "mfa_habilitado": bool(u.get("totp_secret")),
        }
        for u in db.usuarios.values()
    ]
