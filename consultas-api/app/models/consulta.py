"""Modelos Pydantic de consultas.

- ConsultaCreate / ConsultaUpdate: o que o cliente PODE enviar.
- ConsultaPublic: o que o cliente PODE ver .

Correções do Ex. 9:
- extra="forbid" em todos os modelos de entrada
- observacoes com max_length e regex que rejeita < e >
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# Rejeita os metacaracteres de HTML na entrada.
_SEM_HTML = r"^[^<>]*$"


class StatusConsulta(str, Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    cancelada = "cancelada"
    realizada = "realizada"


# Transições de status permitidas (whitelist).
TRANSICOES_VALIDAS: dict[StatusConsulta, set[StatusConsulta]] = {
    StatusConsulta.agendada: {StatusConsulta.confirmada, StatusConsulta.cancelada},
    StatusConsulta.confirmada: {StatusConsulta.realizada, StatusConsulta.cancelada},
    StatusConsulta.cancelada: set(),
    StatusConsulta.realizada: set(),
}


class ConsultaCreate(BaseModel):
    # json_schema_extra define o "Example Value" do Swagger (senão ele gera um texto
    # aleatório que casa com a regex de observacoes).
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "paciente_id": 1,
                "data_hora": "2026-10-01T14:00:00",
                "observacoes": "Retorno para avaliar pressão arterial",
            }
        },
    )
    paciente_id: int = Field(gt=0, examples=[1])
    data_hora: datetime = Field(examples=["2026-10-01T14:00:00"])
    observacoes: str | None = Field(
        default=None, max_length=500, pattern=_SEM_HTML,
        examples=["Retorno para avaliar pressão arterial"],
    )


class ConsultaUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "confirmada"}},
    )
    data_hora: datetime | None = Field(default=None, examples=["2026-10-01T15:30:00"])
    status: StatusConsulta | None = None
    observacoes: str | None = Field(
        default=None, max_length=500, pattern=_SEM_HTML,
        examples=["Paciente confirmou presença"],
    )


class ConsultaPublic(BaseModel):
    id: int
    paciente_id: int
    profissional_id: int
    data_hora: datetime
    status: StatusConsulta
    observacoes: str | None = None
