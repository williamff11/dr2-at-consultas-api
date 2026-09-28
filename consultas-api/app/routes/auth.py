"""Rotas de autenticação: login (senha), verificação de MFA e sessão da recepção.

Fluxo humano:
  POST /auth/token           (form OAuth2)  -> access token, OU desafio de MFA (admin)
  POST /auth/mfa/verify      {mfa_token, codigo} -> access token com mfa=true
O fluxo M2M (client credentials) fica em routes/m2m.py (Ex. 7).
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict

from app import database as db
from app.auth import security
from app.auth.dependencies import ESCOPOS_POR_PAPEL
from app.auth.mfa import verificar_codigo

router = APIRouter(prefix="/auth", tags=["auth"])

# Erro deliberadamente genérico: não distingue "usuário inexistente" de "senha
# errada", para não permitir enumeração de usuários (T05).
_LOGIN_INVALIDO = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Usuário ou senha inválidos",
    headers={"WWW-Authenticate": "Bearer"},
)


def _claims_de_sessao(usuario: dict) -> dict:
    claims = {
        "papel": usuario["papel"],
        "scope": ESCOPOS_POR_PAPEL.get(usuario["papel"], ""),
    }
    if "profissional_id" in usuario:
        claims["profissional_id"] = usuario["profissional_id"]
    return claims


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    # Um client_id de máquina nunca faz login humano (Ex. 7 / T07).
    if form.username in db.clientes_m2m:
        raise _LOGIN_INVALIDO

    usuario = db.usuarios.get(form.username)
    if usuario is None or not security.verificar_senha(form.password, usuario["senha_hash"]):
        raise _LOGIN_INVALIDO

    # Contas com MFA (admin): a senha só libera um token intermediário.
    if usuario.get("totp_secret"):
        mfa_token = security.criar_access_token(
            sub=usuario["username"],
            claims={"scope": "mfa_pending"},
            expira_em=timedelta(minutes=security.MFA_TOKEN_EXPIRE_MINUTES),
        )
        return {"mfa_required": True, "mfa_token": mfa_token, "token_type": "bearer"}

    token = security.criar_access_token(sub=usuario["username"], claims=_claims_de_sessao(usuario))
    return {"access_token": token, "token_type": "bearer"}


class MFAVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mfa_token: str
    codigo: str


@router.post("/mfa/verify")
def mfa_verify(payload: MFAVerify):
    try:
        claims = security.decodificar_token(payload.mfa_token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "mfa_token inválido ou expirado")
    if claims.get("scope") != "mfa_pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token não é um desafio de MFA")

    usuario = db.usuarios.get(claims["sub"])
    if usuario is None or not usuario.get("totp_secret"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Usuário sem MFA configurado")
    if not verificar_codigo(usuario["totp_secret"], payload.codigo):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código MFA inválido")

    token = security.criar_access_token(
        sub=usuario["username"],
        claims={**_claims_de_sessao(usuario), "mfa": True, "amr": ["pwd", "otp"]},
    )
    return {"access_token": token, "token_type": "bearer"}
