"""Modelos Pydantic de consultas.

Separação deliberada (Ex. 2):
- ConsultaCreate / ConsultaUpdate: o que o cliente PODE enviar.
- ConsultaPublic: o que o cliente PODE ver (usado como response_model).
- O registro armazenado (dict em database.py) tem campos internos de auditoria
  — criado_por, ip_origem, criado_em, atualizado_em — que nunca saem na API.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StatusConsulta(str, Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    cancelada = "cancelada"
    realizada = "realizada"


class ConsultaBase(BaseModel):
    paciente_id: int = Field(gt=0)
    profissional_id: int = Field(gt=0)
    data_hora: datetime
    observacoes: str | None = Field(default=None, max_length=500)


class ConsultaCreate(ConsultaBase):
    pass
    # TODO Ex. 9: model_config = ConfigDict(extra="forbid") + validação regex/whitelist


class ConsultaUpdate(BaseModel):
    data_hora: datetime | None = None
    status: StatusConsulta | None = None
    observacoes: str | None = Field(default=None, max_length=500)


class ConsultaPublic(BaseModel):
    """Único formato exposto ao cliente. Campos de auditoria ficam de fora."""
    id: int
    paciente_id: int
    profissional_id: int
    data_hora: datetime
    status: StatusConsulta
    observacoes: str | None = None
