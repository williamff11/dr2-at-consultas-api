"""Camada de dados em memória (Ex. 1–10).

Isolada neste módulo de propósito: no Ex. 11 este arquivo é substituído por
SQLModel + sessão via Depends, sem mudar as rotas além da assinatura.
"""
from datetime import datetime, timezone
from itertools import count

# "Tabelas" em memória
pacientes: dict[int, dict] = {
    1: {"id": 1, "nome": "Ana Souza", "cpf": "111.111.111-11"},
    2: {"id": 2, "nome": "Bruno Lima", "cpf": "222.222.222-22"},
}
profissionais: dict[int, dict] = {
    1: {"id": 1, "nome": "Dra. Carla Mendes", "especialidade": "Cardiologia"},
    2: {"id": 2, "nome": "Dr. Diego Rocha", "especialidade": "Dermatologia"},
}
consultas: dict[int, dict] = {}

_seq = count(1)


def next_id() -> int:
    return next(_seq)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def reset() -> None:
    """Usado pelos testes para começar de um estado limpo."""
    global _seq
    consultas.clear()
    _seq = count(1)
