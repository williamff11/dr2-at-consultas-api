"""Middleware de cabeçalhos de segurança (Ex. 10).

Aplica os headers padrão da empresa a todas as respostas. CSP e Referrer-Policy
são reforços; HSTS/XFO/XCTO são os exigidos pela rubrica.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        h = response.headers
        # HSTS: força HTTPS por 1 ano, incluindo subdomínios (evita downgrade).
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        # Anti-clickjacking: a página não pode ser embutida em iframe de terceiros.
        h.setdefault("X-Frame-Options", "DENY")
        # Impede MIME sniffing (execução de conteúdo com content-type errado).
        h.setdefault("X-Content-Type-Options", "nosniff")
        # Não vaza a URL interna como referer para terceiros.
        h.setdefault("Referrer-Policy", "no-referrer")
        # CSP nas páginas HTML: sem scripts inline/externos (defesa extra contra XSS).
        if response.headers.get("content-type", "").startswith("text/html"):
            h.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; "
                "frame-ancestors 'none'; base-uri 'none'",
            )
        return response
