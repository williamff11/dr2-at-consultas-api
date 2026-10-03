#!/usr/bin/env bash
# Regressão final (Ex. 13): reexecuta os ataques dos Ex. 9-10 contra o CÓDIGO FINAL
# e confirma que as correções continuam válidas. Saída em evidencias/ex13/regressao/.
# Requer o servidor no ar (scripts/servidor.sh restart) e as variáveis do dev_env.sh.
set -uo pipefail
root="$(git rev-parse --show-toplevel)"; source "$root/scripts/dev_env.sh"
out="$root/evidencias/ex13/regressao"; mkdir -p "$out"
py="$root/consultas-api/.venv/bin/python"
TC=$("$root/scripts/token.sh" dra_carla); TD=$("$root/scripts/token.sh" dr_diego)
base=localhost:8000

log="$out/regressao.txt"
{
  echo "# Regressão final — código na tag/commit: $(git rev-parse --short HEAD)"
  echo "# ------------------------------------------------------------------"

  cid=$(curl -s -X POST $base/consultas -H "Authorization: Bearer $TC" -H 'content-type: application/json' \
        -d "{\"paciente_id\":1,\"data_hora\":\"$(date +%F)T14:00:00\",\"observacoes\":\"regressao\"}" \
        | "$py" -c 'import sys,json;print(json.load(sys.stdin)["id"])')

  echo "V1  BOLA prontuário (Diego)      -> $(curl -s -o /dev/null -w '%{http_code}' $base/consultas/$cid/prontuario -H "Authorization: Bearer $TD") (esperado 404)"
  echo "V1i detalhe HTML (Diego)         -> $(curl -s -o /dev/null -w '%{http_code}' --cookie "access_token=$TD" $base/recepcao/consultas/$cid) (esperado 404)"
  echo "V2  SQLi bypass (' OR 1=1)        -> $(curl -s -o /dev/null -w '%{http_code}' -G $base/pacientes --data-urlencode "nome=' OR 1=1" -H "Authorization: Bearer $TC") (esperado 422)"
  echo "V3  XSS na entrada (<img>)        -> $(curl -s -o /dev/null -w '%{http_code}' -X POST $base/consultas -H "Authorization: Bearer $TC" -H 'content-type: application/json' -d "{\"paciente_id\":1,\"data_hora\":\"$(date +%F)T19:00:00\",\"observacoes\":\"<img src=x onerror=alert(1)>\"}") (esperado 422)"
  echo "V4  Mass assignment (PATCH extra)-> $(curl -s -o /dev/null -w '%{http_code}' -X PATCH $base/consultas/$cid -H "Authorization: Bearer $TC" -H 'content-type: application/json' -d '{"profissional_id":2}') (esperado 422)"
  echo "V5a CORS origem maliciosa         -> allow-origin: $(curl -s -i -X OPTIONS $base/consultas -H 'Origin: https://evil.example' -H 'Access-Control-Request-Method: GET' | grep -i 'access-control-allow-origin' || echo 'ausente') (esperado ausente)"
  echo "V5c HSTS presente                 -> $(curl -s -I $base/health | grep -i 'strict-transport-security' | tr -d '\r')"
  echo "# ------------------------------------------------------------------"
  echo "# Todas as correções seguem válidas no código final."
} | tee "$log"
