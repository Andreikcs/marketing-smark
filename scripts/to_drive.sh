#!/usr/bin/env bash
# Envia uma publicação pro Google Drive como MINI-PROJETO: 1 pasta por post.
# Uso: to_drive.sh <marca> <pasta-do-post> <arquivo1> [arquivo2 ...]
#   <pasta-do-post>: ex. 2026-06-13-receita-parada  (use o mesmo slug datado da nota)
#   arquivos: imagem(ns) + legenda.txt (a legenda deve se chamar legenda.txt)
# Requer remote "gdrive": rclone config create gdrive drive scope=drive
set -euo pipefail

MARCA="${1:?marca}"; POST="${2:?pasta-do-post}"; shift 2
[ "$#" -ge 1 ] || { echo "ERRO: informe ao menos 1 arquivo"; exit 1; }
REMOTE="gdrive"
DEST="Smark — Posts/${MARCA}/${POST}"

rclone listremotes | grep -q "^${REMOTE}:" || { echo "ERRO: remote '${REMOTE}' não configurado. Rode: rclone config create gdrive drive scope=drive"; exit 1; }

RFLAGS="--tpslimit 4 --retries 5 --low-level-retries 10"
n=0
for f in "$@"; do
  if [ -f "$f" ]; then rclone copy $RFLAGS "$f" "${REMOTE}:${DEST}/"; n=$((n+1)); fi
done
echo "OK Drive: ${DEST}/  (${n} arquivo(s))"
