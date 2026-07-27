# Backup pré multi-marca / clientes externos

**Data:** 2026-07-27  
**Motivo:** ponto de volta seguro antes de abrir o vault para marcas de clientes (onda 1 B2B).  
**Commit:** `ce82461fc95e9483a5d2e13ec13f62b37f1d4f20`  
**Mensagem:** `auto-save 2026-07-27 17:48:01`

---

## O que foi salvo

| Artefato | Nome | Onde |
|----------|------|------|
| **Branch** | `backup/pre-multimarca-2026-07-27` | local + `origin` |
| **Tag anotada** | `backup/pre-multimarca-2026-07-27` | local + `origin` |
| **Repo remoto** | `https://github.com/Andreikcs/marketing-smark` | GitHub |

Inclui o estado versionado do vault naquele commit: scripts, design-system, docs, marcas (conforme o que estava no git), editor, testes, protótipo white studio, motor Seedream/Gemini, ledger, ROI.

**Não versionado (nunca no git):** `.env`, segredos.  
Se precisar das chaves de API, mantenha backup separado e seguro do `.env` (fora do repositório).

---

## Como restaurar (voltar tudo)

### Opção A — descartar mudanças locais e voltar a `main` para o backup

```bash
cd /Users/andreik/smark

# 1) Ver o ponto de backup
git fetch origin
git log -1 backup/pre-multimarca-2026-07-27

# 2a) Restaurar main para o backup (CUIDADO: perde commits posteriores em main)
git checkout main
git reset --hard backup/pre-multimarca-2026-07-27

# 2b) Ou só inspecionar sem mexer em main
git checkout backup/pre-multimarca-2026-07-27
```

### Opção B — criar uma branch de trabalho a partir do backup

```bash
git checkout -b restore/pre-multimarca backup/pre-multimarca-2026-07-27
```

### Opção C — pela tag

```bash
git checkout backup/pre-multimarca-2026-07-27
# detached HEAD — use -b se for trabalhar em cima
git switch -c restore/from-tag
```

### Depois de restaurar

1. Confirme: `git log -1 --oneline` → deve mostrar `ce82461`  
2. Rode: `python3 -m pytest tests/ -q`  
3. Suba o editor: `python3 scripts/editor_server.py`  
4. Recoloque `.env` se necessário  

**Não force-push em `main` no remoto** sem combinar — o autosave e o histórico compartilhado dependem disso.

---

## Checklist do que estava “bom” neste snapshot

- [x] Marcas: smark, provider-max, elever-ai  
- [x] Motor: Seedream (rascunho padrão) + Gemini (final)  
- [x] Super Editor + Estúdio + compositor  
- [x] Ledger de custos + cotação USD/BRL  
- [x] ROI humano (ciclos)  
- [x] Protótipo white studio em `docs/estudo-agencias/prototipo-white-studio/`  
- [x] Suíte de testes (ordem de 90 passed no período da implementação)  

---

## Qualidade fiel ao multi-marcar

Ver também: **`QUALIDADE-FIDELIDADE-MULTIMARCA.md`** (regras para não degradar o craft quando entrar cliente externo).
