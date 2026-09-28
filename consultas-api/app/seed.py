"""Semeia usuários e o cliente M2M em memória a partir de variáveis de ambiente.

Idempotente: chamar duas vezes não duplica. Nenhuma senha em texto no código —
as senhas vêm do ambiente (ver scripts/dev_env.sh para os valores de DEV, e
.env.example para os nomes das variáveis). Em produção, viriam do cofre/secret manager.

Papéis: admin (com MFA/TOTP), recepcao, profissional (dra_carla=1, dr_diego=2).
"""
import os

from app import database as db
from app.auth.security import hash_senha

# Segredo TOTP de DEV do admin (base32). Em produção seria provisionado por usuário.
_TOTP_ADMIN = os.environ.get("SEED_TOTP_ADMIN", "JBSWY3DPEHPK3PXP")


def _senha(var: str) -> str:
    valor = os.environ.get(var)
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente {var} ausente. "
            f"Rode `source scripts/dev_env.sh` (DEV) ou configure o .env."
        )
    return valor


def semear() -> None:
    if db.usuarios:  # idempotência
        return
    db.usuarios.update({
        "admin": {
            "username": "admin",
            "papel": "admin",
            "senha_hash": hash_senha(_senha("SEED_SENHA_ADMIN")),
            "totp_secret": _TOTP_ADMIN,
        },
        "recepcao": {
            "username": "recepcao",
            "papel": "recepcao",
            "senha_hash": hash_senha(_senha("SEED_SENHA_RECEPCAO")),
        },
        "dra_carla": {
            "username": "dra_carla",
            "papel": "profissional",
            "profissional_id": 1,
            "senha_hash": hash_senha(_senha("SEED_SENHA_CARLA")),
        },
        "dr_diego": {
            "username": "dr_diego",
            "papel": "profissional",
            "profissional_id": 2,
            "senha_hash": hash_senha(_senha("SEED_SENHA_DIEGO")),
        },
    })
