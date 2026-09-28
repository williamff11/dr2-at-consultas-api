"""Rate limiting com slowapi (Ex. 10).

Limite global generoso + limite estrito nas rotas de autenticação (força bruta).
O limiter é único e centralizado; as rotas sensíveis o aplicam via decorator.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limite global padrão; as rotas de login endurecem para 5/minute.
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

LIMITE_LOGIN = "5/minute"
