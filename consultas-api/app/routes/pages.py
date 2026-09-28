"""Página HTML interna da recepção: agenda do dia (Ex. 2)."""
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import database as db

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Auto-escape explícito (não dependemos do default implícito do Starlette):
# qualquer {{ valor }} em .html é codificado (< vira &lt; etc.).
_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
templates = Jinja2Templates(env=_env)

router = APIRouter(tags=["recepcao"])


@router.get("/recepcao/agenda", response_class=HTMLResponse)
def agenda_do_dia(request: Request, dia: date | None = None):
    dia = dia or date.today()
    itens = []
    for c in sorted(db.consultas.values(), key=lambda c: c["data_hora"]):
        if c["data_hora"].date() != dia:
            continue
        # Só o necessário para a recepção — sem CPF, sem campos de auditoria.
        itens.append({
            "hora": c["data_hora"].strftime("%H:%M"),
            "paciente": db.pacientes[c["paciente_id"]]["nome"],
            "profissional": db.profissionais[c["profissional_id"]]["nome"],
            "status": c["status"].value,
            "observacoes": c.get("observacoes") or "",
        })
    return templates.TemplateResponse(
        request, "agenda.html", {"dia": dia, "consultas": itens}
    )
