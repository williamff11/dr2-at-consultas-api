"""Rotas de autenticação"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from app.auth import security
from app.auth.dependencies import ESCOPOS_POR_PAPEL
from app.auth.mfa import verificar_codigo
from app.core.rate_limit import LIMITE_LOGIN, limiter
from app.database import get_session
from app.models.tables import ClienteM2M, Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

_LOGIN_INVALIDO = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Usuário ou senha inválidos",
    headers={"WWW-Authenticate": "Bearer"},
)


def _claims_de_sessao(usuario: Usuario) -> dict:
    claims = {
        "papel": usuario.papel,
        "scope": ESCOPOS_POR_PAPEL.get(usuario.papel, ""),
    }
    if usuario.profissional_id is not None:
        claims["profissional_id"] = usuario.profissional_id
    return claims


@router.post("/token")
@limiter.limit(LIMITE_LOGIN)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    if session.get(ClienteM2M, form.username) is not None:
        raise _LOGIN_INVALIDO

    usuario = session.get(Usuario, form.username)
    if usuario is None or not security.verificar_senha(form.password, usuario.senha_hash):
        raise _LOGIN_INVALIDO

    # Contas com MFA (admin)
    if usuario.totp_secret:
        mfa_token = security.criar_access_token(
            sub=usuario.username,
            claims={"scope": "mfa_pending"},
            expira_em=timedelta(minutes=security.MFA_TOKEN_EXPIRE_MINUTES),
        )
        return {"mfa_required": True, "mfa_token": mfa_token, "token_type": "bearer"}

    token = security.criar_access_token(sub=usuario.username, claims=_claims_de_sessao(usuario))
    return {"access_token": token, "token_type": "bearer"}


class MFAVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mfa_token: str
    codigo: str


@router.post("/mfa/verify")
@limiter.limit(LIMITE_LOGIN)
def mfa_verify(request: Request, payload: MFAVerify, session: Session = Depends(get_session)):
    try:
        claims = security.decodificar_token(payload.mfa_token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "mfa_token inválido ou expirado")
    if claims.get("scope") != "mfa_pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token não é um desafio de MFA")

    usuario = session.get(Usuario, claims["sub"])
    if usuario is None or not usuario.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Usuário sem MFA configurado")
    if not verificar_codigo(usuario.totp_secret, payload.codigo):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código MFA inválido")

    token = security.criar_access_token(
        sub=usuario.username,
        claims={**_claims_de_sessao(usuario), "mfa": True, "amr": ["pwd", "otp"]},
    )
    return {"access_token": token, "token_type": "bearer"}
