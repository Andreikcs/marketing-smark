---
tipo: formatos-canais
escopo: todas-as-marcas
versao: 1.0
atualizado: 2026-06-10
---

# Formatos e Tamanhos por Canal

Mapa que os comandos (`/post-instagram`, `/post-linkedin`, `/pauta`) usam pra decidir o `--size` da geração de imagem.

> Os modelos `gpt-image-*` aceitam **apenas** `1024x1024`, `1024x1536` (retrato), `1536x1024` (paisagem) ou `auto`. Não há 9:16 nativo — para story usamos retrato 1024x1536 e cortamos/adicionamos margem no template.

| Canal | Formato | Proporção alvo | `--size` | Nota |
|---|---|---|---|---|
| Instagram | feed (post/carrossel) | 4:5 | `1024x1536` | retrato 2:3, recorta pra 4:5 |
| Instagram | quadrado | 1:1 | `1024x1024` | |
| Instagram | story / reels capa | 9:16 | `1024x1536` | sem 9:16 nativo — recorte/margem no template |
| LinkedIn | feed | 1:1 ou 4:5 | `1024x1024` (ou `1024x1536`) | 1:1 rende melhor no feed do LinkedIn |
| LinkedIn | imagem de link | 1.91:1 | `1536x1024` | paisagem |
| Anúncio | feed | 4:5 | `1024x1536` | |

## Como gerar cada formato (compositor)

Todos via `scripts/compositor.py` (fundo IA opcional + moldura da marca):

- **Feed (post único):** `--size 1080x1350`.
- **Quadrado:** `--size 1080x1080`.
- **Story / Reels-capa:** `--size 1080x1920` (fundo IA 1024x1536 preenche por cover).
- **Anúncio:** `--size 1080x1350 --cta "Diagnóstico gratuito →"` (renderiza o botão no acento).
- **Carrossel:** gere N frames no mesmo post; cada frame é uma chamada:
  - **Capa** (frame 1): com chip + `--page "01/05"` + hook forte.
  - **Internos** (2..N): `--no-chip --page "0X/05"`, 1 ideia por frame.
  - Saída: `arte/<slug>/01.png … 0N.png`; suba TODOS na mesma pasta do post no Drive (`to_drive.sh` aceita vários arquivos).

## Regras de copy por canal

- **Instagram:** headline carrega a arte; legenda curta-média; 5-8 hashtags.
- **LinkedIn:** hook nos 2 primeiros parágrafos; texto 150-400 palavras; 3-5 hashtags; imagem opcional (1:1).

Ver também: [[shared/padroes-instagram]] (hooks/formatos/linha vermelha) e `identidade-visual.md` de cada marca (paleta/arte).
