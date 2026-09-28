#!/usr/bin/env bash
# Credenciais de DESENVOLVIMENTO/TESTE (valores fictícios — NÃO são segredos reais).
# Ficam FORA do código da aplicação (app/ não contém senha em texto). Em produção,
# estas variáveis viriam de um cofre / secret manager, nunca de um arquivo versionado.
# Uso: source scripts/dev_env.sh
export ENV="${ENV:-dev}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./consultas.db}"
# Segredo JWT de DEV (fictício). Em produção: gere com secrets.token_urlsafe e use um cofre.
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-dev-jwt-secret-3f9a1c8e2b7d4a6f-nao-usar-em-producao}"
export SEED_SENHA_ADMIN="admin-dev-2026!"
export SEED_SENHA_RECEPCAO="recepcao-dev-2026!"
export SEED_SENHA_CARLA="carla-dev-2026!"
export SEED_SENHA_DIEGO="diego-dev-2026!"
export SEED_TOTP_ADMIN="JBSWY3DPEHPK3PXP"
# Cliente M2M do laboratório (Ex. 7)
export LAB_CLIENT_ID="lab-parceiro"
export LAB_CLIENT_SECRET="lab-secret-dev-2026!"
