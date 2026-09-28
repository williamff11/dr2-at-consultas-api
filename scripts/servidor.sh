#!/usr/bin/env bash
# Sobe/derruba o uvicorn em background (porta 8000) com banco zerado + seed.
# uso: scripts/servidor.sh start|stop|restart
set -uo pipefail
root="$(git rev-parse --show-toplevel)"; api="$root/consultas-api"
source "$root/scripts/dev_env.sh"
LOG=/tmp/uvicorn.log; PIDF=/tmp/uvicorn_consultas.pid
stop() {
  [ -f "$PIDF" ] && kill "$(cat "$PIDF")" 2>/dev/null
  pkill -f "uvicorn app.main:app" 2>/dev/null; rm -f "$PIDF"; sleep 0.5
}
start() {
  rm -f "$api"/consultas.db
  ( cd "$api" && ENV="${ENV:-dev}" nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG" 2>&1 & echo $! > "$PIDF" )
  for _ in $(seq 1 50); do curl -sf localhost:8000/health >/dev/null && { echo "servidor no ar (pid $(cat "$PIDF"))"; return 0; }; sleep 0.2; done
  echo "ERRO: servidor não respondeu"; cat "$LOG"; return 1
}
case "${1:-}" in start) start;; stop) stop; echo parado;; restart) stop; start;; *) echo "uso: $0 start|stop|restart"; exit 2;; esac
