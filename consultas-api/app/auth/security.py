"""Primitivas de segurança: hashing de senha e emissão/validação de JWT.

Centralizado aqui (nenhuma rota reimplementa hash ou decodificação de token).
Usa `bcrypt` diretamente — o `passlib` está sem manutenção e quebra com bcrypt>=4.

Ex. 11: o segredo vem de BaseSettings/.env (get_settings). Não há mais segredo
hardcoded no código-fonte.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

_s = get_settings()

SECRET_KEY = _s.jwt_secret_key
ALGORITHM = _s.jwt_algorithm
ISSUER = "consultas-api"
AUDIENCE = "api-consultas"

ACCESS_TOKEN_EXPIRE_MINUTES = _s.access_token_expire_minutes  # tokens humanos
MFA_TOKEN_EXPIRE_MINUTES = 5       # token intermediário "mfa_pending"
M2M_TOKEN_EXPIRE_MINUTES = 10      # tokens de máquina (Ex. 7)


# ---------- senhas ----------
def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())
    except (ValueError, TypeError):
        return False


# ---------- JWT ----------
def criar_access_token(
    sub: str,
    claims: dict | None = None,
    expira_em: timedelta | None = None,
) -> str:
    agora = datetime.now(timezone.utc)
    exp = agora + (expira_em or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict = {
        "sub": sub,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": int(agora.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Valida assinatura, expiração, emissor e audiência.

    Lança jwt.PyJWTError (ExpiredSignatureError, InvalidTokenError, ...) em falha —
    quem chama traduz para 401. Nunca retorna um payload não verificado.
    """
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        audience=AUDIENCE,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
