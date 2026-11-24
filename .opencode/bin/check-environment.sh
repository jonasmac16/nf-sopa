#!/bin/sh
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
REF_DIR="$ROOT/.opencode/skills/data-analysis/references"

ok=0
warn=0
check_cmd() {
  label=$1
  cmd=$2
  if command -v "$cmd" >/dev/null 2>&1; then
    printf 'OK   %-24s %s\n' "$label" "$(command -v "$cmd")"
  else
    printf 'WARN %-24s not found\n' "$label"
    warn=$((warn + 1))
  fi
}

check_cmd "OpenCode" opencode
check_cmd "Git" git
check_cmd "DataLad" datalad
check_cmd "Apptainer" apptainer

if [ -e "$REF_DIR/python.md" ]; then
  check_cmd "Python" python3
fi

if [ -e "$REF_DIR/r.md" ]; then
  check_cmd "R" R
fi

if [ -e "$REF_DIR/julia.md" ]; then
  check_cmd "Julia" julia
fi

printf '\nLanguage support inferred from retained references in:\n  %s\n' "$REF_DIR"
printf 'Warnings: %s\n' "$warn"
exit "$ok"
