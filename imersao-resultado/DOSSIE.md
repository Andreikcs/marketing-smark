# Dossiê de Resultado — Imersão IA Paris Group

**Projeto:** Smark Vault — Motor de Marketing Multi-marca  
**Gerado em:** 2026-07-26  
**Schema:** `resultado.json` v1.0  
**Repo:** https://github.com/Andreikcs/marketing-smark  
**Deploy:** apenas local (`http://127.0.0.1:8765`)

---

## 1. O que é

Sistema **local** (Python + vault Obsidian + Super Editor web) que produz **copy + arte** para as marcas **smark**, **provider-max** e **elever-ai**, com:

- governança de voz (sem jargão / sem promessa de venda na vitrine social)
- design system e compositor tipográfico
- IA de imagem via **OpenRouter** (Gemini final, Seedream rascunho)
- IA de copy via **Claude** (Estúdio)
- **ledger de custos** em USD e BRL (cotação ao vivo)

**Não é** um SaaS multi-tenant publicado. É ferramenta de operação de marketing + laboratório de motor de imagem/custo.

---

## 2. Segmentação

| Campo | Valor |
|-------|--------|
| industry | tech |
| company_size | 2-10 |
| user_type | internal-team |
| primary_job | content |
| ai_usage | agentic |
| maturity | pilot |
| deployment | local-only |
| stack_family | internal-tool |

---

## 3. Antes → Depois

| Processo | Antes | Depois | Métrica | Confiança |
|----------|-------|--------|---------|-----------|
| Post Instagram multi-marca | Freela/agência ou Canva; horas/dias; R$50–150/arte | Estúdio + Editor + compositor; minutos | tempo + COGS | estimated |
| Iterar fundo “não gostei” | Nova rodada cara ou re-prompt cego | Rascunho Seedream **US$0,04** + final Gemini **US$0,24** | US$/tentativa | **measured** |
| Controle de gasto de IA | Billing opaco | Ledger imagem+copy, BRL ao vivo, relatório CLI | rastreabilidade | **measured** |
| Consistência de voz | Risco de jargão/hype | `revisar.py` + regras CLAUDE.md | qualidade de marca | proxy |

---

## 4. Números com honestidade

### Medidos (`confidence: measured`)

| Métrica | Valor | Evidência |
|---------|-------|-----------|
| Custo arte final Gemini 4K | **~US$ 0,243** | `geracoes.jsonl` (6 eventos) |
| Custo rascunho Seedream | **US$ 0,04** | ledger 2026-07-26 |
| Gasto imagem no ledger (amostra) | **US$ 1,50** (~R$ 7,61 @ 5,0785) | 7 gerações ok |
| Testes automatizados | **86 passed** | `pytest tests/` |
| Arte no vault | **~357 PNGs** | contagem `marcas/**/arte` |
| Posts no editor | **41 posts / 84 frames** | `editor.json` |
| Publicações markdown | **~28** | `marcas/**/publicacoes` |

### Estimados (`confidence: estimated`)

| Métrica | Base | Low–High |
|---------|------|----------|
| Horas economizadas / mês | 22,5 h (30 posts × 35 min salvos) | 12–40 h |
| Economia R$/mês vs freela R$80 | ~R$ 2.100 (30×(80−3,5)) | 900–4.200 |
| Redução tempo de ciclo | ~78% (45→10 min) | 60–85% |
| Valor de construção do sistema | ~R$ 48.000 (160 h × R$300) | 25k–90k |
| COGS post completo (img+copy Opus) | **~US$ 0,65–0,73 · ~R$ 3,3–3,7** | depende de tokens Claude |

### Desconhecido

- Taxa de erro/retrabalho pré vs pós (sem baseline)
- Horas reais de stopwatch por post
- Ledger de copy Claude histórico (**n=0** até o deploy do tracker)

---

## 5. Stack (real)

- **Frontend:** HTML/CSS/JS do Super Editor + design system  
- **Backend:** `editor_server.py` (stdlib HTTP)  
- **Dados:** Markdown Obsidian, `editor.json`, JSONL de custos  
- **IA:** OpenRouter images, Anthropic Messages, OpenAI fallback  
- **Câmbio:** AwesomeAPI USD-BRL  
- **Testes:** pytest (86)  
- **Infra:** local + GitHub autosave  

---

## 6. Screenshots

| Arquivo | O que prova | Status |
|---------|-------------|--------|
| `screenshots/01-hub.png` | Hub do sistema local | captured |
| `screenshots/02-editor.png` | Super Editor / produção | captured |
| `screenshots/03-painel.png` | Painel de publicações | captured |
| `screenshots/04-vitrine.png` | Vitrine por marca | captured |
| `screenshots/05-config.png` | Configurações do sistema | captured |

**Opcional pendente:** recaptura do Estúdio mostrando bloco de custo copy + total do post (após hard refresh pós-deploy do ledger de copy).

---

## 7. Marketing (uso interno — não publicar sem revisão)

**Headline candidata:**  
*Do brief à arte on-brand em minutos — com custo de IA rastreado em dólar e real*

**3 bullets:**
1. Multi-marca com voz e visual governados  
2. Final Gemini ~US$0,24 · rascunho Seedream US$0,04 — só o final publica  
3. Ledger imagem + copy + cotação USD/BRL para precificar operação  

`can_publish_publicly: false` · `anonymize: true` · **sem depoimento inventado**

---

## 8. Gaps (para virar case “measured”)

1. Ligar analytics simples: tempo por post, nº de regenerações, taxa de aprovação  
2. Encher ledger de copy com uso real do Estúdio  
3. Stopwatch de 10 posts (antes/depois) com o mesmo operador  
4. Opcional: deploy demo read-only (Vercel/static) só vitrine  

---

## 9. Quality score

| Dimensão | Nota |
|----------|------|
| Completeness | **78**/100 |
| Evidence strength | **72**/100 |

Forte em produto técnico e custo de imagem; fraco em ROI humano medido e histórico de copy.

---

## 10. Como regenerar

```bash
cd /Users/andreik/smark
python3 scripts/custos_relatorio.py
python3 -m pytest tests/ -q
# screenshots: Chrome headless em http://127.0.0.1:8765
```

Arquivo máquina: [`resultado.json`](./resultado.json)
