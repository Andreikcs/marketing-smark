#!/usr/bin/env bash
# Registra um post na planilha de controle e sincroniza pro Drive (raiz "Smark — Posts").
# A planilha é o índice/vínculo de tudo: marca, datas, headline, imagem, status, LINK da pasta.
# Uso: registrar.sh <marca> <pasta-do-post> <headline> <nome-imagem> [status]
set -euo pipefail

MARCA="${1:?marca}"; POST="${2:?pasta-do-post}"; HEAD="${3:?headline}"; IMG="${4:?imagem}"; STATUS="${5:-draft}"
CSV="/Users/andreik/smark/controle-posts.csv"
REMOTE="gdrive"

GEN=$(date "+%Y-%m-%d %H:%M")
DPOST=$(printf '%s' "$POST" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' || date +%F)

# Link da pasta do post (via ID, sem tornar público)
FID=$(rclone lsf --tpslimit 4 --retries 5 --dirs-only --format "ip" "${REMOTE}:Smark — Posts/${MARCA}/" 2>/dev/null | awk -F';' -v p="${POST}/" '$2==p{print $1}')
LINK=""; [ -n "$FID" ] && LINK="https://drive.google.com/drive/folders/${FID}"

# Cabeçalho na primeira vez
[ -f "$CSV" ] || echo "marca,data_post,data_geracao,headline,imagem,status,link_pasta" > "$CSV"

HEAD_ESC=$(printf '%s' "$HEAD" | sed 's/"/""/g')
echo "\"${MARCA}\",\"${DPOST}\",\"${GEN}\",\"${HEAD_ESC}\",\"${IMG}\",\"${STATUS}\",\"${LINK}\"" >> "$CSV"

rclone copy --tpslimit 4 --retries 5 "$CSV" "${REMOTE}:Smark — Posts/"
echo "Registrado na planilha: ${MARCA} · ${POST} · ${IMG}"
