"""Dependências de autenticação e autorização — casa única da lógica de segurança.

Nenhuma rota reimplementa estas regras; elas apenas declaram `Depends(...)`.
- get_current_user      : extrai e valida o principal (Bearer ou cookie de sessão)
- require_roles         : RBAC — falha de papel => 403
- require_mfa           : exige que o token tenha passado pelo 2º fator
- get_consulta_autorizada: ownership (BOLA) — ÚNICA função que compara profissional_id
"""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.auth import security
from app.database import get_session
from app.models.tables import Consulta

# Escopos derivados do papel (usados de forma plena no Ex. 7).
ESCOPOS_POR_PAPEL: dict[str, str] = {
    "admin": "consultas:read consultas:write admin",
    "profissional": "consultas:read consultas:write",
    "recepcao": "consultas:read",
}

# auto_error=False: nas páginas HTML caímos para o cookie quando não há header.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "consultas:read": "Ler consultas",
        "consultas:write": "Criar/alterar consultas",
        "admin": "Operações administrativas",
        "horarios:read": "Ler horários livres (parceiro M2M)",
    },
    auto_error=False,
)

_CRED_INVALIDA = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Credenciais inválidas ou ausentes",
    headers={"WWW-Authenticate": "Bearer"},
)


def _principal_do_token(token: str) -> dict:
    try:
        return security.decodificar_token(token)
    except jwt.PyJWTError:
        raise _CRED_INVALIDA


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    """Principal humano autenticado. Aceita Authorization: Bearer ou, para as
    páginas HTML da recepção, o cookie HttpOnly `access_token`."""
    if token is None:
        token = request.cookies.get("access_token")
    if not token:
        raise _CRED_INVALIDA
    claims = _principal_do_token(token)
    # Tokens de máquina (Ex. 7) não são usuários humanos.
    if claims.get("client_type") == "m2m":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de máquina não pode acessar esta rota")
    # Token intermediário de MFA ainda não é uma sessão válida.
    if claims.get("scope") == "mfa_pending":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "MFA pendente: verifique o segundo fator")
    return claims


def require_roles(*papeis: str):
    """RBAC. Papel ausente/insuficiente => 403 (autenticado, mas sem permissão)."""
    def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user.get("papel") not in papeis:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requer papel: {', '.join(papeis)}",
            )
        return user
    return _dep


def require_mfa(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("mfa"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Esta operação exige autenticação multifator (MFA)",
        )
    return user


def get_consulta_autorizada(
    consulta_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
) -> Consulta:
    """Autorização a NÍVEL DE OBJETO (anti-BOLA). Ponto único de decisão de posse.

    - admin e recepção: acesso a qualquer consulta (papel operacional);
    - profissional: apenas às consultas dos SEUS pacientes (profissional_id do token);
    - caso contrário: 404 (não confirmamos a existência de recurso de terceiro —
      preserva a confidencialidade, decisão registrada em docs/03 e docs/06).
    """
    consulta = session.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consulta não encontrada")

    papel = user.get("papel")
    if papel in ("admin", "recepcao"):
        return consulta
    if papel == "profissional" and consulta.profissional_id == user.get("profissional_id"):
        return consulta

    raise HTTPException(status.HTTP_404_NOT_FOUND, "Consulta não encontrada")
