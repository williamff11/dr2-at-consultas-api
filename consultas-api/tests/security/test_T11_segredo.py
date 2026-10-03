"""Ameaça: T11 (segredo hardcoded) · README.md, Ex. 4.

Garante que a aplicação exige o segredo do ambiente (não há default).
"""
import os

import pytest


def test_T11_sem_jwt_secret_falha(monkeypatch):
    from app.core.config import Settings
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(Exception):
        Settings(_env_file=None)
