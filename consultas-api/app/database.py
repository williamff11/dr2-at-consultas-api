"""Camada de persistência com SQLModel (Ex. 11).

Substitui o armazenamento em memória dos Ex. 1–10. A sessão é injetada nas rotas
via Depends(get_session); as queries usam select().where() (parametrizadas).
"""
from collections.abc import Iterator
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import tables  # noqa: F401 — registra as tabelas no metadata

_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
engine = create_engine(_settings.database_url, echo=_settings.db_echo, connect_args=_connect_args)


def criar_tabelas() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
