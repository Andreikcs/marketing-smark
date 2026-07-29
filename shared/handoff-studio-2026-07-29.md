# Handoff — Smark Studio (estado até 2026-07-29)

Documento para continuar o trabalho com outra IA/sessão. Vault: `/Users/andreik/smark` · Repo: `Andreikcs/marketing-smark` (branch `main`).

---

## 1. O que é o produto

**Smark Studio** — sistema multi-marca de produção de conteúdo social (Instagram/LinkedIn):

- Editor de arte por frame (fundo IA + compositor HTML/CSS com legenda/logo/moldura)
- Painel (galeria de posts), Vitrine, Config (marcas/canais), Status (`/db-status`)
- Postgres multi-tenant no Railway
- OAuth Instagram (Business Login) por marca
- Deploy: https://smark-studio-production.up.railway.app

**Marcas canônicas:** `smark`, `provider-max`, `elever-ai`  
**Clientes no vault/tokens:** alem-do-olhar-chapeco, amosim, deatec, netsul, sul-contabil, track-brasil, v4-company, covatti-2, covatti-4, …

**Regras de conteúdo:** pt-BR; voz em `shared/voz-grupo.md`; não prometer venda no social.

---

## 2. Arquitetura atual

```
Mac local (fonte das artes full PNG)
  editor.json + marcas/**/arte/**/_regen/*.png
  LaunchAgent: com.smark.editor → localhost:8765
  .env (API keys, DATABASE_PUBLIC_URL)
        │
        ▼ sync
Postgres Railway (fonte canônica de posts em prod)
  marca | post | post_frame | canal_conexao | publicacao_log | nota_publicacao
        │
        ▼
Railway app (smark-studio)
  scripts/editor_server.py :8080
  .thumbs/*.jpg (composições HQ ~540px para galeria em prod)
  design-system/dist + logos-perfil
  SEM artes full (limite de upload ~1GB; dockerignore)
```

### URLs / IDs Railway
| Item | Valor |
|------|--------|
| App | https://smark-studio-production.up.railway.app |
| Projeto | `f3bcc859-78c2-4435-ae51-99095dcb3559` |
| Env production | `470b0cbb-b962-49bd-bc8d-743fd43ba4ec` |
| Service app | `83aed1fb-39b6-4638-b69c-bc496e19f97c` (smark-studio) |
| Service Postgres | `d4e5ab1b-b855-44b0-920d-def226020cfe` |
| Proxy DB público | `sakura.proxy.rlwy.net:54314` (via `DATABASE_PUBLIC_URL` no `.env`) |

**UI do banco:** Railway → Postgres → aba **Data**.

### Variáveis de ambiente (produção)
Já configuradas no serviço app:
- `DATABASE_URL` (interna Railway)
- `PUBLIC_BASE_URL`, `PUBLIC_HOSTS`
- `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, redirect
- `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`

Local: `.env` na raiz (gitignored). `editor_server` carrega `.env` no boot (`_load_dotenv`) porque o LaunchAgent não herda o shell.

---

## 3. Snapshot de dados (2026-07-29)

| Recurso | Qtd |
|---------|-----|
| Posts (`editor.json` + PG) | **46** |
| Frames | **63** |
| Thumbs HQ (`.thumbs/`) | **46** |
| Marcas (tokens) | 12+ |
| Marcas (PG) | 15 |
| canal_conexao | 2 |
| Notas .md | 28 |
| PNGs arte no disco local | ~372 |

**Perfil aproximado dos posts:**
- ~24 com fundo + caption + copy real
- ~12 rascunhos placeholder (`SEU TÍTULO|*AQUI.*`)
- 1 fundo missing local: `smark/construir-em-volta-nao-trocar` (`_regen/01-58ce96.png` sumiu)

**Backups:**
- `editor.json.pre-migrate.bak`
- `editor.json.from-db.json`
- Autosave launchd: `com.smark.autosave` → commit/push a cada 5 min

---

## 4. Stack / arquivos-chave

| Arquivo | Papel |
|---------|--------|
| `scripts/editor_server.py` | HTTP server único (hub, painel, vitrine, config, editor, OAuth, /dados, /preview, /db-status) |
| `scripts/_db.py` | Schema PG, upsert batch, load posts, canais |
| `scripts/_marcas.py` | Registry tokens, `ensure_stub`, logos, `nova_marca` |
| `scripts/compositor.py` | HTML da arte + Chrome headless → PNG |
| `scripts/_provedor.py` | OpenRouter / OpenAI images |
| `scripts/openai_image.py` | Orquestra geração de fundo |
| `scripts/regen_thumbs_hq.py` | Regenera thumbs compostos (Chrome) |
| `scripts/migrate_to_db.py` | Migração editor.json → PG |
| `scripts/tests/test_e2e_preview_flow.py` | E2E preview/compose/DB |
| `scripts/tests/test_db_sync.py` | Perf save/load + openrouter keys |
| `design-system/dist/smark-ds.css` | Tokens UI |
| `design-system/tokens/tokens.json` | Marcas + branding |
| `.thumbs/` | JPEGs da galeria em produção |
| `Dockerfile` + `railway.toml` | Deploy |

### Comportamentos importantes implementados

1. **Save rápido:** grava `editor.json` + cache; Postgres em background (batch, debounce 1.2s). Não bloquear `/salvar` com N upserts síncronos.
2. **Load:** cache memória → arquivo → PG.
3. **Boot `sync_db_boot`:** se PG tem posts → espelha arquivo; se PG vazio e arquivo tem → migra; `ensure_stub` de marcas órfãs.
4. **Galeria:** prioriza `/preview` composto (texto+logo+fundo); fallback thumb HQ; nunca erro vermelho fullscreen.
5. **Marcas órfãs:** `ensure_stub` + compositor com paleta stub se não estiver no tokens.
6. **CSS crítico embutido** em páginas (fallback se `smark-ds.css` 404).
7. **Deploy:** pacote enxuto (~13MB) via `railway up` de pasta slim; **não** `railway up` da raiz (1.3GB artes → 413).

### Deploy enxuto (receita)

```bash
# Montar /tmp/smark-* com: Dockerfile, requirements, railway.toml, editor.json,
# scripts/, .thumbs/, design-system/dist+tokens+assets/logos-perfil,
# marcas/*/branding/assets (logos só)
cd /tmp/smark-...
railway link -p f3bcc859-... -e production -s smark-studio
railway up --detach
```

Comandos úteis:
```bash
python3 scripts/regen_thumbs_hq.py          # thumbs HQ local → editor.json + DB
python3 scripts/tests/test_e2e_preview_flow.py
python3 scripts/tests/test_db_sync.py
python3 scripts/migrate_to_db.py            # com DATABASE_PUBLIC_URL
```

---

## 5. Problemas resolvidos nesta saga

| Problema | Solução |
|----------|---------|
| Posts sumiram no Store prod | Migrar editor.json → PG; load de PG |
| Save travando | Upsert async + batch |
| API key ausente em prod | Vars OPENROUTER/etc no Railway |
| LaunchAgent sem .env | `_load_dotenv()` no boot |
| CSS 404 → layout branco / thumb fullscreen | CSS crítico + deploy do smark-ds.css |
| Cards pretos covatti | ensure_stub + compositor stub |
| Galeria borrada sem legenda | Preview composto + regen thumbs HQ |
| Logo smark 404 | Resolve `design-system/assets/logos-perfil/...` |

---

## 6. Problemas ainda abertos

1. **Produção sem artes full** — estúdio em Railway não tem `_regen/*.png`; só thumbs/preview mesh.
2. **Storage externo** (R2/S3) não implementado — necessário para imagem nítida em prod e publish IG.
3. **1 PNG missing:** `construir-em-volta-nao-trocar`.
4. **Logos** provider-max / elever-ai / covatti sem arquivo de brasão.
5. **Publish Instagram** codificado mas depende de URL pública HTTPS da arte.
6. **App Review Meta** pendente para clientes externos.
7. **Sem:** agendamento, portal de aprovação do cliente, worker de publish.
8. **Deploy frágil:** `railway up` da raiz estoura limite; processo manual de pacote slim.
9. **Local 8765** às vezes lento no boot (sync PG público).

---

## 7. Plano de ação (apresentado; **NÃO implementado** — aguarda aprovação)

Documento de intenção do usuário: fluxo ponta a ponta sem erro + agenda + vitrine para cliente.

### Fase 0 — Estabilizar (3–5 d)
- Volume/storage (R2/S3) para artes
- Pipeline arte → storage → thumb automático
- Gate “marca pronta” (logo/cor)
- Backup PG + arte
- CI e2e

### Fase 1 — Operação interna (4–6 d)
- Status workflow: rascunho → revisão → aprovado → agendado → publicado
- Publish IG estável + log
- Painel por status/marca

### Fase 2 — Portal cliente / vitrine (6–9 d)
- Link mágico por marca `/c/<token>`
- Ver posts, aprovar / pedir ajuste + comentário
- Isolamento multi-tenant
- Notificação ao time smark  
**v1 recomendado:** magic link, não SaaS login completo.

### Fase 3 — Agendamento (4–6 d)
- `scheduled_at` + timezone
- Worker/cron Railway
- Só post aprovado agenda
- Retry + alerta

### Fase 4 — Produto (8–12 d)
- Onboarding marca, pauta mensal, lotes, relatório

**MVP sugerido:** 0 → publish IG → portal v1 → agenda (~15–22 dias).

**Decisões pendentes do usuário:**
- Ordem das fases (A só 0 / B 0+portal / C 0+agenda / D completo)
- Portal: magic link vs login
- Aprovação: por post vs lote
- Agenda v1: só IG ou IG+LinkedIn

---

## 8. Instagram / Meta (contexto)

- App Instagram Business Login (não confundir App ID Facebook com Instagram App ID)
- Secret do app Instagram
- Redirect HTTPS Railway
- Tester role no Meta
- Multi-marca: 1 app, token por marca em `canal_conexao`
- Scopes: basic + content_publish
- Secret vazou em chat antigo → **rotacionar** se ainda for o mesmo

---

## 9. Como a outra IA deve começar

1. Ler este handoff + `Claude.md` / `shared/voz-grupo.md` se for gerar conteúdo.
2. **Não** rodar `railway up` da raiz do vault.
3. Antes de UI: verificar `/db-status` e contagens PG.
4. Após mudar posts/artes: `python3 scripts/regen_thumbs_hq.py` e redeploy slim com `.thumbs/`.
5. Dados sagrados: não apagar `editor.json` sem backup; não `DELETE` em massa no PG.
6. Se usuário pedir portal/agenda: revalidar plano da seção 7 e **esperar aprovação explícita** se ainda não houver.

### Comandos de saúde rápida

```bash
curl -sS https://smark-studio-production.up.railway.app/db-status?json=1 | python3 -m json.tool
curl -sS https://smark-studio-production.up.railway.app/dados | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['posts']), sum(1 for p in d['posts'] if p.get('thumb')))"
python3 scripts/tests/test_e2e_preview_flow.py
```

---

## 10. Commits / mudanças recentes relevantes

- Multi-marca Postgres + migrate
- Save/load async + batch
- CSS crítico + dashboard `/db-status`
- ensure_stub + compositor stub
- Galeria: preview composto + thumbs HQ
- `.env` no boot do editor
- Testes e2e preview

Branch: `main` · working tree pode ter autosave contínuo.

---

## 11. Contato / dono

Workspace do usuário: `andreik` · projeto marketing smark · e-mail Railway login: github@smarktech.com.br (referência de sessão).

---

*Fim do handoff. Atualizar este arquivo ao fechar a próxima fase.*
