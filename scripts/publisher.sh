#!/bin/bash
# WORKER DE AGENDADOS do Smark Studio.
# Rodado pelo launchd (com.smark.publisher) a cada 5 min: bate em /agenda/rodar
# e o servidor publica o que já venceu. Toda a regra (gate, fluxo, log) vive no
# servidor — este arquivo é só o despertador.
#
# Só publica post em `agendado` cuja data passou, e só se o gate liberar.
# Se o Mac estiver dormindo ou o servidor fora do ar, nada sai — e nada sai errado.
# Logs: .git/publisher.log  ·  Parar: launchctl bootout gui/$UID/com.smark.publisher

set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
VAULT="/Users/andreik/smark"
cd "$VAULT" || exit 1

LOG="$VAULT/.git/publisher.log"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
BASE="http://127.0.0.1:8765"

# Lock portável (macOS não tem flock) — duas passadas juntas poderiam tentar
# publicar o mesmo post. O servidor também trava, mas barato é barrar aqui.
LOCK="$VAULT/.git/publisher.lock"
if ! mkdir "$LOCK" 2>/dev/null; then exit 0; fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

TOKEN_FILE="$VAULT/.editor-token"
[ -r "$TOKEN_FILE" ] || { echo "$TS  sem .editor-token — servidor nunca subiu?" >> "$LOG"; exit 0; }
TOK="$(cat "$TOKEN_FILE")"

# Servidor no ar? Silêncio se não — é o caso normal com o Mac dormindo.
curl -sf --max-time 5 -o /dev/null "$BASE/" 2>/dev/null || exit 0

# SMARK_PUBLISHER_DRY=1 simula: percorre a fila inteira, chama o gate, e não
# posta nem mexe no status. É como se confere o worker sem gastar feed.
DRY="false"; [ "${SMARK_PUBLISHER_DRY:-0}" = "1" ] && DRY="true"

RESP="$(curl -s --max-time 300 -X POST "$BASE/agenda/rodar" \
  -H 'Content-Type: application/json' -H "X-Editor-Token: $TOK" \
  -d "{\"limite\":5,\"dry_run\":$DRY,\"por\":\"agenda-launchd\"}" 2>>"$LOG")"

# Nada venceu é o caso comum: não polui o log.
python3 -c '
import json, sys
ts, resp = sys.argv[1], sys.argv[2]
try:
    d = json.loads(resp or "{}")
except Exception:
    print(ts, " resposta ilegível:", (resp or "")[:200]); raise SystemExit
if d.get("rodando"):
    print(ts, " outra passada em andamento"); raise SystemExit
if not d.get("venceram"):
    raise SystemExit          # nada venceu: silêncio
feitos, pulados = d.get("feitos") or [], d.get("pulados") or []
print(ts, "%s venceram %d · publicados %d · pulados %d"
      % (" [SIMULAÇÃO]" if d.get("dry_run") else "", d["venceram"], len(feitos), len(pulados)))
for f in feitos:
    print("      ok   %s/%s → %s" % (f.get("marca"), f.get("slug"),
                                     f.get("media_id") or ("modo " + (f.get("modo") or "?"))))
for p in pulados:
    motivo = p.get("erro") or ", ".join(p.get("faltas") or [])
    print("      pula %s/%s — %s" % (p.get("marca"), p.get("slug"), motivo[:160]))
' "$TS" "$RESP" >> "$LOG" 2>&1
