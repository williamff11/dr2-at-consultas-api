"""Semeia dados iniciais no banco (Ex. 11). Idempotente; só roda com ENV=dev.

Nenhuma senha em texto no código: vêm de Settings (variáveis de ambiente / .env).
"""
from sqlmodel import Session, select

from app.auth.security import hash_senha
from app.core.config import get_settings
from app.database import engine
from app.models.tables import ClienteM2M, Consulta, Paciente, Profissional, Usuario

_s = get_settings()


def semear(session: Session | None = None) -> None:
    if _s.env != "dev":
        return
    own = session is None
    session = session or Session(engine)
    try:
        if session.exec(select(Usuario)).first():
            return  # idempotência

        session.add_all([
            Profissional(id=1, nome="Dra. Carla Mendes", especialidade="Cardiologia"),
            Profissional(id=2, nome="Dr. Diego Rocha", especialidade="Dermatologia"),
            Paciente(id=1, nome="Ana Souza", cpf="111.111.111-11", profissional_id=1),
            Paciente(id=2, nome="Bruno Lima", cpf="222.222.222-22", profissional_id=2),
            Usuario(username="admin", papel="admin",
                    senha_hash=hash_senha(_s.seed_senha_admin), totp_secret=_s.seed_totp_admin),
            Usuario(username="recepcao", papel="recepcao",
                    senha_hash=hash_senha(_s.seed_senha_recepcao)),
            Usuario(username="dra_carla", papel="profissional", profissional_id=1,
                    senha_hash=hash_senha(_s.seed_senha_carla)),
            Usuario(username="dr_diego", papel="profissional", profissional_id=2,
                    senha_hash=hash_senha(_s.seed_senha_diego)),
            ClienteM2M(client_id=_s.lab_client_id,
                       secret_hash=hash_senha(_s.lab_client_secret), scope="horarios:read"),
        ])
        session.commit()
    finally:
        if own:
            session.close()


# Consulta é importada só para garantir o registro da tabela no metadata.
_ = Consulta
