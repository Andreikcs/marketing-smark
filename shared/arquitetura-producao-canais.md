# Arquitetura produção — Smark Studio × Instagram multi-cliente

## Status atual (2026-07-29)

| Capacidade | Status |
|------------|--------|
| OAuth Instagram multi-marca | **OK** (smark @smarkassessoria conectado) |
| 1 app Meta / N clientes | **Modelo correto** |
| Token por marca | Arquivo + **Postgres** (`canal_conexao`) |
| Publicar no feed | Código pronto; exige **URL HTTPS** da arte |
| App Review Advanced Access | **Pendente** (só testers em Development) |
| LinkedIn | Stub |

## Fluxo de publicação

```
Editor → Export PNG → /canais/publicar
  → token da marca (DB/arquivo)
  → image_url pública (PUBLIC_BASE_URL + path)
  → Graph: POST /{ig-user-id}/media
  → Graph: POST /{ig-user-id}/media_publish
  → log em publicacao_log
```

## Gaps para “ativar clientes e postar automático”

1. **App Review** Meta (Advanced Access) — clientes sem ser tester  
2. **PNG público** — export deve ficar em path servido por HTTPS (Railway)  
3. **Volume persistente** opcional p/ artes (Postgres guarda tokens)  
4. **Fila de agendamento** (cron + `publicacao_log` / tabela `fila`)  
5. **Separar** dev local vs production env  

## Stack Railway

- Service `smark-studio` — Super Editor  
- Service `Postgres` — tokens + logs  
- Domain: `smark-studio-production.up.railway.app`  
- Vars: `INSTAGRAM_*`, `DATABASE_URL`, `PUBLIC_BASE_URL`  

## Segurança

- Secrets só em Railway Variables / `.env` local (gitignored)  
- API `/canais` nunca devolve `access_token`  
- Redefinir App Secret se vazou no chat  
