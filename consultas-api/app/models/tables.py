"""Tabelas SQLModel (Ex. 11). Separadas dos schemas Pydantic de entrada/saída.

As rotas recebem/entregam ConsultaCreate/Update/Public (app/models/consulta.py);
estas classes são apenas o mapeamento objeto-relacional. Toda consulta ao banco é
parametrizada via select().where() — nunca concatenação de string.
"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class Profissional(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str
    especialidade: str


class Paciente(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    cpf: str
    profissional_id: int = Field(foreign_key="profissional.id")


class Consulta(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    paciente_id: int = Field(foreign_key="paciente.id")
    profissional_id: int = Field(foreign_key="profissional.id")
    data_hora: datetime
    status: str = Field(default="agendada")
    observacoes: str | None = None
    # auditoria (nunca exposta via response_model)
    criado_por: str
    ip_origem: str | None = None
    criado_em: datetime
    atualizado_em: datetime


class Usuario(SQLModel, table=True):
    username: str = Field(primary_key=True)
    papel: str
    senha_hash: str
    profissional_id: int | None = Field(default=None, foreign_key="profissional.id")
    totp_secret: str | None = None


class ClienteM2M(SQLModel, table=True):
    client_id: str = Field(primary_key=True)
    secret_hash: str
    scope: str
