#!/bin/bash
# AUTO-SAVE do vault Smark → GitHub.
# Rodado pelo launchd (com.smark.autosave) a cada N minutos.
# Faz commit+push só quando há mudança. Respeita .gitignore (nunca sobe .env nem artes-draft).
# Logs: .git/autosave.log  ·  Parar/reativar: veja o final deste arquivo.

set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
VAULT="/Users/andreik/smark"
cd "$VAULT" || exit 1

LOG="$VAULT/.git/autosave.log"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# Lock portável (macOS não tem flock) — evita rodadas sobrepostas.
LOCK="$VAULT/.git/autosave.lock"
if ! mkdir "$LOCK" 2>/dev/null; then exit 0; fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

git add -A

# Nada mudou? sai em silêncio.
if git diff --cached --quiet; then exit 0; fi

git commit -q -m "auto-save $TS" || { echo "$TS  commit falhou" >> "$LOG"; exit 0; }

if git push -q origin main 2>>"$LOG"; then
  echo "$TS  ok — $(git rev-parse --short HEAD)" >> "$LOG"
else
  echo "$TS  push falhou (commit salvo local; tentará de novo no próximo ciclo)" >> "$LOG"
fi
