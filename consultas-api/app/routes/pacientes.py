"""Busca de pacientes (Ex. 8/9).

ATENÇÃO: contém a vulnerabilidade intencional V2 (SQL injection) do Ex. 8,
claramente marcada. Ela é corrigida no Ex. 9 com query parametrizada + validação.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.get("")
def buscar_pacientes(
    nome: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # VULN-V2 (intencional, Ex. 8): a busca monta o SQL por concatenação de string,
    # então o valor de `nome` altera a estrutura da query (SQL injection). No Ex. 9
    # isto vira select(Paciente).where(Paciente.nome.contains(nome)) + validação regex.
    sql = text(f"SELECT id, nome, cpf, profissional_id FROM paciente WHERE nome LIKE '%{nome}%'")  # noqa: S608
    linhas = session.execute(sql).fetchall()
    return [list(linha) for linha in linhas]
