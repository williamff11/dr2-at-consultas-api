"""Modelos Pydantic de consultas.

Separação deliberada (Ex. 2):
- ConsultaCreate / ConsultaUpdate: o que o cliente PODE enviar.
- ConsultaPublic: o que o cliente PODE ver (usado como response_model).

Correções do Ex. 9:
- extra="forbid" em todos os modelos de entrada (rejeita campos não declarados →
  mata mass assignment). O cliente não envia profissional_id/criado_por.
- observacoes com max_length e regex que rejeita < e > (defesa em profundidade
  contra XSS, além do auto-escape na saída).
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# Rejeita os metacaracteres de HTML na entrada (defesa em profundidade; o escape
# de saída continua sendo a proteção principal contra XSS).
_SEM_HTML = r"^[^<>]*$"


class StatusConsulta(str, Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    cancelada = "cancelada"
    realizada = "realizada"


# Transições de status permitidas (whitelist). O que não está aqui é rejeitado.
TRANSICOES_VALIDAS: dict[StatusConsulta, set[StatusConsulta]] = {
    StatusConsulta.agendada: {StatusConsulta.confirmada, StatusConsulta.cancelada},
    StatusConsulta.confirmada: {StatusConsulta.realizada, StatusConsulta.cancelada},
    StatusConsulta.cancelada: set(),
    StatusConsulta.realizada: set(),
}


class ConsultaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paciente_id: int = Field(gt=0)
    data_hora: datetime
    observacoes: str | None = Field(default=None, max_length=500, pattern=_SEM_HTML)


class ConsultaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_hora: datetime | None = None
    status: StatusConsulta | None = None
    observacoes: str | None = Field(default=None, max_length=500, pattern=_SEM_HTML)


class ConsultaPublic(BaseModel):
    """Único formato exposto ao cliente. Campos de auditoria ficam de fora."""
    id: int
    paciente_id: int
    profissional_id: int
    data_hora: datetime
    status: StatusConsulta
    observacoes: str | None = None
