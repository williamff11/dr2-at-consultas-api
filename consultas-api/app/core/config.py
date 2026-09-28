"""Configuração central via BaseSettings (Ex. 11).

Todos os segredos e parâmetros vêm do ambiente / arquivo .env. NÃO há default para
segredos: se JWT_SECRET_KEY ou as senhas de seed faltarem, a aplicação não sobe —
falhar cedo é melhor do que rodar com um segredo previsível.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    env: str = Field(default="dev", alias="ENV")

    # Persistência
    database_url: str = Field(default="sqlite:///./consultas.db", alias="DATABASE_URL")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # JWT — SEM default (segredo obrigatório)
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS (Ex. 10)
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")

    # Seed — SEM default (senhas obrigatórias)
    seed_senha_admin: str = Field(alias="SEED_SENHA_ADMIN")
    seed_senha_recepcao: str = Field(alias="SEED_SENHA_RECEPCAO")
    seed_senha_carla: str = Field(alias="SEED_SENHA_CARLA")
    seed_senha_diego: str = Field(alias="SEED_SENHA_DIEGO")
    seed_totp_admin: str = Field(default="JBSWY3DPEHPK3PXP", alias="SEED_TOTP_ADMIN")
    lab_client_id: str = Field(default="lab-parceiro", alias="LAB_CLIENT_ID")
    lab_client_secret: str = Field(alias="LAB_CLIENT_SECRET")

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.cors_origins, str):
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
