"""Páginas HTML internas da recepção (Ex. 2) — agora com sessão por cookie (Ex. 6).

As páginas são somente leitura. A recepção autentica em /recepcao/login, que grava
um cookie HttpOnly (não acessível a JavaScript, mitiga roubo de sessão via XSS).
"""
import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import database as db
from app.auth import security
from app.auth.dependencies import ESCOPOS_POR_PAPEL, get_current_user

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Auto-escape explícito: qualquer {{ valor }} em .html é codificado (< vira &lt;).
_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
templates = Jinja2Templates(env=_env)

router = APIRouter(tags=["recepcao"])

# Secure só em produção (em DEV o cookie precisa funcionar sobre http).
_COOKIE_SECURE = os.environ.get("ENV", "dev") == "prod"


@router.get("/recepcao/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"erro": None})


@router.post("/recepcao/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    usuario = db.usuarios.get(username)
    if usuario is None or not security.verificar_senha(password, usuario["senha_hash"]):
        resp = templates.TemplateResponse(
            request, "login.html", {"erro": "Usuário ou senha inválidos"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        return resp
    claims = {"papel": usuario["papel"], "scope": ESCOPOS_POR_PAPEL.get(usuario["papel"], "")}
    if "profissional_id" in usuario:
        claims["profissional_id"] = usuario["profissional_id"]
    token = security.criar_access_token(sub=username, claims=claims)
    resp = RedirectResponse("/recepcao/agenda", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(
        "access_token", token,
        httponly=True, samesite="strict", secure=_COOKIE_SECURE,
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return resp


@router.get("/recepcao/agenda", response_class=HTMLResponse)
def agenda_do_dia(
    request: Request,
    dia: date | None = None,
    user: dict = Depends(get_current_user),
):
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
        request, "agenda.html", {"dia": dia, "consultas": itens, "usuario": user.get("sub")}
    )
