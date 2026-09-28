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
from sqlmodel import Session, select

from app.auth import security
from app.auth.dependencies import (
    ESCOPOS_POR_PAPEL,
    get_consulta_autorizada,
    get_current_user,
)
from app.database import get_session
from app.models.tables import Consulta, Paciente, Profissional, Usuario

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
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    usuario = session.get(Usuario, username)
    if usuario is None or not security.verificar_senha(password, usuario.senha_hash):
        resp = templates.TemplateResponse(
            request, "login.html", {"erro": "Usuário ou senha inválidos"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        return resp
    claims = {"papel": usuario.papel, "scope": ESCOPOS_POR_PAPEL.get(usuario.papel, "")}
    if usuario.profissional_id is not None:
        claims["profissional_id"] = usuario.profissional_id
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
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    dia = dia or date.today()
    consultas = session.exec(select(Consulta).order_by(Consulta.data_hora)).all()
    itens = []
    for c in consultas:
        if c.data_hora.date() != dia:
            continue
        paciente = session.get(Paciente, c.paciente_id)
        profissional = session.get(Profissional, c.profissional_id)
        # Só o necessário para a recepção — sem CPF, sem campos de auditoria.
        itens.append({
            "hora": c.data_hora.strftime("%H:%M"),
            "paciente": paciente.nome if paciente else "?",
            "profissional": profissional.nome if profissional else "?",
            "status": c.status,
            "observacoes": c.observacoes or "",
        })
    return templates.TemplateResponse(
        request, "agenda.html", {"dia": dia, "consultas": itens, "usuario": user.get("sub")}
    )


@router.get("/recepcao/consultas/{consulta_id}", response_class=HTMLResponse)
def detalhe_consulta(
    request: Request,
    consulta: Consulta = Depends(get_consulta_autorizada),
    session: Session = Depends(get_session),
):
    # Corrigido (V1-irmão): esta página compartilhava o padrão da V1 (busca por id sem
    # ownership). Agora usa a MESMA dependência get_consulta_autorizada — a posse é
    # verificada no único lugar de sempre. O template não usa mais |safe (V3).
    paciente = session.get(Paciente, consulta.paciente_id)
    return templates.TemplateResponse(
        request, "detalhe_consulta.html",
        {"consulta": consulta, "paciente": paciente.nome if paciente else "?"},
    )
