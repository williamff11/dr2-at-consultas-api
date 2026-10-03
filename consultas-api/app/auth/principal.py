"""Autorização por escopo OAuth2"""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import SecurityScopes

from app.auth import security
from app.auth.dependencies import oauth2_scheme


def get_current_principal(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    if token is None:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Credenciais ausentes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return security.decodificar_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_scopes(
    security_scopes: SecurityScopes,
    principal: dict = Depends(get_current_principal),
) -> dict:
    concedidos = set(principal.get("scope", "").split())
    faltando = [s for s in security_scopes.scopes if s not in concedidos]
    if faltando:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Escopo insuficiente. Requer: {' '.join(security_scopes.scopes)}",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
        )
    return principal
