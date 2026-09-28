"""Modelos Pydantic de consultas.

Separação deliberada (Ex. 2):
- ConsultaCreate / ConsultaUpdate: o que o cliente PODE enviar.
- ConsultaPublic: o que o cliente PODE ver (usado como response_model).
- O registro armazenado tem campos internos de auditoria — criado_por, ip_origem,
  criado_em, atualizado_em — que nunca saem na API.

Ownership (Ex. 6): o cliente NÃO envia profissional_id. Ele é derivado do paciente
no servidor (paciente.profissional_id), o que impede o cliente de se apropriar de
uma consulta atribuindo-a a outro profissional (mass assignment, T06).
`extra='forbid'` é adicionado nos modelos de entrada no Ex. 9.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StatusConsulta(str, Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    cancelada = "cancelada"
    realizada = "realizada"


class ConsultaCreate(BaseModel):
    paciente_id: int = Field(gt=0)
    data_hora: datetime
    observacoes: str | None = Field(default=None, max_length=500)
    # TODO Ex. 9: model_config = ConfigDict(extra="forbid") + validação regex


class ConsultaUpdate(BaseModel):
    # VULN-V4 (intencional, Ex. 8): extra="allow" deixa passar campos não declarados
    # (profissional_id, criado_por), que a rota aplica via setattr → mass assignment.
    # Corrigido no Ex. 9 com extra="forbid".
    model_config = ConfigDict(extra="allow")
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
