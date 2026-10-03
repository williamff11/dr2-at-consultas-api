#!/usr/bin/env bash
# Captura a saída REAL de um comando como evidência, com cabeçalho rastreável.
# uso: scripts/evidencia.sh <exNN> <nome_arquivo> "<descrição>" -- '<comando>'
# O comando roda a partir da raiz do repositório.
set -uo pipefail
[ $# -ge 5 ] && [ "$4" = "--" ] || { echo "uso: $0 exNN nome \"descrição\" -- 'comando'"; exit 2; }
ex="$1"; nome="$2"; desc="$3"; shift 4
root="$(git rev-parse --show-toplevel)"
if ! git -C "$root" diff --quiet HEAD -- consultas-api .github; then
  echo "ERRO: há alterações de código não commitadas. Faça commit antes de capturar (a evidência precisa apontar para um commit)."; exit 3
fi
dir="$root/evidencias/$ex"; mkdir -p "$dir"; out="$dir/$nome.txt"
commit="$(git -C "$root" rev-parse --short HEAD)"
ref="$(git -C "$root" describe --tags --exact-match 2>/dev/null || git -C "$root" rev-parse --abbrev-ref HEAD)"
{
  echo "# Evidência : $desc"
  echo "# Exercício : $ex"
  echo "# Commit    : $commit ($ref)"
  echo "# Comando   : $*"
  echo "# ------------------------------------------------------------------"
} > "$out"
(cd "$root" && bash -c "$*") >> "$out" 2>&1; rc=$?
{ echo "# ------------------------------------------------------------------"; echo "# exit code : $rc"; } >> "$out"
idx="$root/evidencias/INDICE.md"
[ -f "$idx" ] || printf '# Índice de evidências (gerado por scripts/evidencia.sh)\n\n| Arquivo | Ex. | Commit | Descrição |\n|---|---|---|---|\n' > "$idx"
tmp="$(mktemp)"; grep -vF "\`$ex/$nome.txt\`" "$idx" > "$tmp"; mv "$tmp" "$idx"
echo "| \`$ex/$nome.txt\` | $ex | \`$commit\` | $desc |" >> "$idx"
echo "evidência salva: evidencias/$ex/$nome.txt (exit $rc)"
