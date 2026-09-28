"""Camada de dados em memória (Ex. 1–10).

Isolada neste módulo de propósito: no Ex. 11 este arquivo é substituído por
SQLModel + sessão via Depends, sem mudar as rotas além da assinatura.

Nenhuma senha em texto vive aqui: os hashes bcrypt são gerados pelo seed a partir
de variáveis de ambiente (ver app/seed.py).
"""
from datetime import datetime, timezone
from itertools import count

# "Tabelas" em memória ------------------------------------------------------
# paciente.profissional_id define de quem é o paciente (usado no ownership).
pacientes: dict[int, dict] = {
    1: {"id": 1, "nome": "Ana Souza", "cpf": "111.111.111-11", "profissional_id": 1},
    2: {"id": 2, "nome": "Bruno Lima", "cpf": "222.222.222-22", "profissional_id": 2},
}
profissionais: dict[int, dict] = {
    1: {"id": 1, "nome": "Dra. Carla Mendes", "especialidade": "Cardiologia"},
    2: {"id": 2, "nome": "Dr. Diego Rocha", "especialidade": "Dermatologia"},
}
consultas: dict[int, dict] = {}

# usuarios[username] = {username, papel, senha_hash, profissional_id?, totp_secret?}
usuarios: dict[str, dict] = {}
# clientes_m2m[client_id] = {client_id, secret_hash, scope} (preenchido no Ex. 7)
clientes_m2m: dict[str, dict] = {}

_seq = count(1)


def next_id() -> int:
    return next(_seq)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def reset() -> None:
    """Usado pelos testes para começar de um estado limpo (só as consultas)."""
    global _seq
    consultas.clear()
    _seq = count(1)
