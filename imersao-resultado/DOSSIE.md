---
tipo: dossie-imersao
projeto: Smark Vault — Estúdio de Conteúdo Multi-marca
gerado_em: 2026-07-18
status: production (uso interno, single-team)
fonte: leitura direta do repositório (código, editor.json, git, CLAUDE.md/README)
---

# Dossiê de Resultado — Imersão IA (Paris Group)

> Documento honesto e reutilizável sobre o projeto deste repositório. Números marcados com
> **`measured`** têm evidência direta; **`estimated`/`proxy`** têm premissa explícita; **`unknown`**
> ficam em branco com o gap listado. Nada de depoimento inventado, nada de número sem lastro.

---

## 1. O que é (em uma frase)

Um **estúdio de conteúdo local** que roda no Mac do operador: gera carrosséis e posts de
Instagram/LinkedIn **on-brand** para 3 marcas (Smark, Provider Max, Elever AI). **A IA escreve a copy
(Claude) e monta a arte (fundo por OpenAI + tipografia programática); o operador aprova e exporta.**

- **Repo:** `/Users/andreik/smark` · **GitHub:** `Andreikcs/marketing-smark`
- **Deploy:** `local-only` (localhost:8765) + backup automático no GitHub a cada 5 min
- **Status:** `production` — uso interno real, single-team

## 2. Problema de negócio

Produzir conteúdo social **em volume e on-brand para 3 marcas diferentes**, sem depender de designer
no dia a dia e sem quebrar consistência de voz/identidade — evitando também **jargão** e **promessa de
venda** (proibidos pela marca). É uma assessoria de tecnologia que precisa alimentar as redes das
próprias marcas com disciplina de marca.

## 3. Como funciona (ponta a ponta)

```
briefing (linguagem natural)
   └─► Estúdio IA (Claude claude-opus-4-8) ── copy + conceito visual por card (tema claro por padrão)
          └─► Fundo por IA (OpenAI gpt-image-1.5, direção de arte estruturada por _direcao.py)
                 └─► Compositor (HTML/CSS + Chrome headless 2x) ── tipografia nítida + moldura da marca
                        └─► Quality gate (revisar.py) ── bloqueia jargão / promessa de venda
                               └─► Editor (preview ao vivo, card a card) ── aprovar / ajustar
                                      └─► Export PNG 2x ─► Downloads · Autosave ─► GitHub (5/5 min)
```

Telas: **HUB · Editor · Painel de Conteúdo · Vitrine · Config** (ver `screenshots/`).

## 4. Stack (verificado no código)

| Camada | Tecnologia |
|---|---|
| Frontend | HTML/CSS/JS **vanilla** (editor single-file), design-system CSS (tokens claro/escuro), sem framework |
| Backend | **Python 3 stdlib** (`http.server`, `socketserver`, `threading`), sem framework web |
| Store | **JSON flat-file** (`editor.json`) + notas Markdown com frontmatter; sem banco relacional |
| Auth | token de sessão por boot + guarda Host/Origin (CSRF/DNS-rebinding), só localhost |
| IA | **Claude** (copy) · **OpenAI gpt-image-1.5** (imagem) · Gemini (alternativo) |
| Infra | macOS local · **launchd** (commit+push automático) · Chrome headless (render) · Obsidian (vault) |

**Tamanho (measured):** 3.054 LOC em 13 scripts Python (`editor_server.py` 1068 · `compositor.py` 378 ·
`estudio.py` 256 · `revisar.py` 159 …) + editor HTML single-file + design-system. **227 commits** entre
2026-07-04 e 2026-07-18.

## 5. Valor: antes → depois

| Processo | Antes (manual/legado) | Depois (com o sistema) | Métrica | Evidência | Confiança |
|---|---|---|---|---|---|
| Escrever copy on-brand | Copywriter manual; risco de jargão e de prometer venda | Claude gera + gate valida marca e bloqueia jargão/promessa | ~7 checagens de marca automáticas/post | `estudio.py`, `revisar.py` | `measured` |
| Produzir arte do carrossel | Designer monta cada card no Figma/Canva (~2,5h) | Fundo por IA + tipografia programática nítida 2x | tempo/carrossel (proxy ~2,5h→~0,5h) | `compositor.py`, 330 PNGs | `estimated` |
| Versionar / recuperar | Edições sobrescreviam estado; perda possível (ocorreu) | Histórico de versões + autosave git 5 min | recuperação ~5 min | `/historico`+`/restaurar`, 227 commits | `measured` |
| Exportar carrossel | 1 a 1; risco de faltar frame sem aviso | Lote com timeout+retry e aviso de faltas | 5/5 frames em ~32s (teste) | `/exportar`, `render_html_to_png` | `measured` |

## 6. Impacto quantificado (com fórmula e premissa)

> ⚠️ **Sem telemetria embarcada.** Tempos e volume mensal são **`estimated`/`proxy`**, nunca cronometrados.
> O mais defensável é o **custo de construção** e o **tempo por carrossel vs. fluxo manual**.

**Economia de tempo — `estimated`**
`horas_economizadas_mes = (tempo_antes_min − tempo_depois_min) × volume_mes / 60`
Premissas: `tempo_antes=210min` (design 2,5h + copy 1h, proxy de mercado), `tempo_depois=30min`,
`volume_mes=20`.
→ base **60 h/mês** · faixa **18–143 h/mês**

**Economia financeira — `estimated`**
`economia_R$_mes = horas_economizadas_mes × custo_hora` · `custo_hora=R$80/h` (blended freelance BR)
→ base **R$ 4.800/mês** · faixa **R$ 1.080 – 17.160/mês**

**Redução do tempo de ciclo — `estimated`**
`(210−30)/210 = 85,7%` → **~86%** · faixa 70–90%

**Redução de erro/retrabalho — `proxy` (valor `null`)**
Sem baseline medido. Proxy: o gate automatiza ~7 checagens e **bloqueia** promessa de venda.
Para virar `measured`: logar quantos posts o gate reprovou/corrigiu ao longo de N publicações.

**Valor de construção do sistema — `estimated`**
`build_value = horas_dev_estimadas × custo_hora_dev` · base `250h × R$130`
→ base **R$ 32.500** · faixa **R$ 15.000 – 63.000**
(esforço de reconstrução do zero; boa parte foi feita com assistência de IA.)

## 7. Ganhos qualitativos

- Consistência de marca em **multi-marca** (paleta e voz herdadas de um DNA de grupo).
- **Compliance automatizado**: impede jargão e promessa de venda antes de publicar.
- **Recuperação de trabalho**: o histórico de versões já resgatou um carrossel de 5 cards perdido.
- Produção **sem designer** no fluxo diário.
- **Backup versionado** automático (git a cada 5 min).
- Tema por card (template **roxo** ou **verde lima**) respeitando a paleta oficial.

## 8. Segmentação (taxonomia fechada)

| Campo | Valor |
|---|---|
| industry | `tech` |
| company_size | `2-10` |
| user_type | `internal-team` |
| primary_job | `content` |
| ai_usage | `core-feature` |
| maturity | `production` (interno, single-team) |
| deployment | `local-only` |
| stack_family | `internal-tool` |

## 9. Evidência produzida (measured)

- **31 posts** / **80 cards** no `editor.json` (Smark 20 · Elever 8 · Provider Max 3)
- **330 PNGs** de arte em `marcas/*/publicacoes/*/arte`
- **28 notas** de publicação `.md` + **26 notas** de branding
- **227 commits** (autosave) em ~2 semanas
- 5 screenshots das telas principais em `screenshots/`

## 10. Gaps (o que falta para virar `measured`)

1. Instrumentar **telemetria** de tempo real de produção por post.
2. Rodar **baseline cronometrado** "com vs. sem sistema" (elimina o proxy de tempo).
3. Medir **volume steady-state mensal** (os 31 posts foram de ~2 semanas de construção).
4. Logar **custo de API por post** (Claude + OpenAI) — hoje `unknown`, é estimável.
5. Registrar **taxa de reprovação do quality gate** de forma agregável.
6. Sem dados de **conversão/engajamento** dos posts (o sistema não publica nem mede resultado).

## 11. Marketing (com evidência, anonimizável)

- **Headline:** "Um estúdio de conteúdo multi-marca que roda no seu Mac: a IA escreve a copy e monta a arte; você aprova e exporta."
- **3 bullets:**
  1. Copy on-brand pelo Claude + gate que bloqueia jargão e promessa de venda.
  2. Arte de carrossel em 2 camadas (fundo por IA + tipografia nítida 2x) sem designer no fluxo diário.
  3. Histórico de versões estilo Google Docs + backup automático no GitHub a cada 5 min.
- **Depoimento:** nenhum (não inventar).
- `can_publish_publicly: false` · `anonymize: true` (contém estratégia de marca; o operador decide expor).

## 12. Qualidade do dossiê

- **Completude:** 80/100 — descoberta de produto/stack forte e verificada no código.
- **Força de evidência:** 55/100 — impacto financeiro/tempo é honestamente estimado por falta de telemetria.

---

_Arquivos deste pacote: `resultado.json` (máquina), `DOSSIE.md` (humano), `screenshots/` (5 telas)._
