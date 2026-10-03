"""MFA simulado via TOTP (RFC 6238), usando pyotp.

Simulado porque o segredo TOTP fica no seed em vez de ser provisionado por um app
autenticador real (Google Authenticator etc.). O algoritmo de verificação é o mesmo
de produção; o que falta é o enrollment do dispositivo e o armazenamento por usuário
num cofre. Ver README.md, Ex. 6 para o que separaria isto de um MFA de produção.
"""
import pyotp


def gerar_codigo_atual(segredo_totp: str) -> str:
    """Gera o código TOTP do instante (usado pelos testes/scripts para simular o app)."""
    return pyotp.TOTP(segredo_totp).now()


def verificar_codigo(segredo_totp: str, codigo: str) -> bool:
    # valid_window=1 tolera o relógio deslocado em ±30s (uma janela).
    return pyotp.TOTP(segredo_totp).verify(codigo, valid_window=1)
