#!/usr/bin/env bash
# Imprime um access token válido de um usuário do seed. Para admin, resolve o MFA.
# uso: export TOKEN_CARLA=$(scripts/token.sh dra_carla)
set -uo pipefail
root="$(git rev-parse --show-toplevel)"; source "$root/scripts/dev_env.sh"
u="${1:?uso: token.sh <admin|recepcao|dra_carla|dr_diego>}"
case "$u" in
  admin) senha="$SEED_SENHA_ADMIN";; recepcao) senha="$SEED_SENHA_RECEPCAO";;
  dra_carla) senha="$SEED_SENHA_CARLA";; dr_diego) senha="$SEED_SENHA_DIEGO";;
  *) echo "usuario desconhecido: $u" >&2; exit 2;;
esac
resp="$(curl -s -X POST localhost:8000/auth/token -d "username=$u&password=$senha")"
if echo "$resp" | grep -q '"mfa_required"'; then
  mfa_token="$(echo "$resp" | "$root/consultas-api/.venv/bin/python" -c 'import sys,json;print(json.load(sys.stdin)["mfa_token"])')"
  codigo="$("$root/consultas-api/.venv/bin/python" -c "import pyotp,os;print(pyotp.TOTP(os.environ['SEED_TOTP_ADMIN']).now())")"
  resp="$(curl -s -X POST localhost:8000/auth/mfa/verify -H 'content-type: application/json' -d "{\"mfa_token\":\"$mfa_token\",\"codigo\":\"$codigo\"}")"
fi
echo "$resp" | "$root/consultas-api/.venv/bin/python" -c 'import sys,json;print(json.load(sys.stdin)["access_token"])'
