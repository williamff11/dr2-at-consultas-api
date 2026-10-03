"""Páginas HTML internas da recepção"""
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
from app.core.rate_limit import LIMITE_LOGIN, limiter
from app.database import get_session
from app.models.tables import Consulta, Paciente, Profissional, Usuario

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
templates = Jinja2Templates(env=_env)

router = APIRouter(tags=["recepcao"])

_COOKIE_SECURE = os.environ.get("ENV", "dev") == "prod"


@router.get("/recepcao/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"erro": None})


@router.post("/recepcao/login")
@limiter.limit(LIMITE_LOGIN)
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
    # Esta tela só confere senha: contas com MFA usam /auth/token + /auth/mfa/verify.
    if usuario.totp_secret:
        return templates.TemplateResponse(
            request, "login.html",
            {"erro": "Esta conta exige MFA: use o login da API (/auth/token)"},
            status_code=status.HTTP_403_FORBIDDEN,
        )
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
    stmt = select(Consulta).order_by(Consulta.data_hora)
    # Profissional só vê a própria agenda (mesmo filtro de GET /consultas).
    if user.get("papel") == "profissional":
        stmt = stmt.where(Consulta.profissional_id == user.get("profissional_id"))
    consultas = session.exec(stmt).all()
    itens = []
    for c in consultas:
        if c.data_hora.date() != dia:
            continue
        paciente = session.get(Paciente, c.paciente_id)
        profissional = session.get(Profissional, c.profissional_id)
        # Só o necessário para a recepção — sem CPF, sem campos de auditoria.
        itens.append({
            "id": c.id,
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
    paciente = session.get(Paciente, consulta.paciente_id)
    return templates.TemplateResponse(
        request, "detalhe_consulta.html",
        {"consulta": consulta, "paciente": paciente.nome if paciente else "?"},
    )
