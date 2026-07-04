---
tipo: shared
titulo: Direção de Arte — geração de fundos nível agência
atualizado: 2026-06-21
---

# Direção de Arte (fundos de IA)

Regra de qualidade pra **todo fundo gerado por IA** (gpt-image via `scripts/openai_image.py`). Substitui o prompt genérico de uma linha por **direção estruturada nível agência** + uma **grade de acabamento** aplicada no compositor. Objetivo: somar qualidade sem quebrar o que já existe.

> Validado em A/B/C com o usuário (2026-06-21): direção estruturada + composição guiada pelo layout + grade venceram o prompt genérico. Esta é a mescla aprovada.

## As duas camadas

1. **Construtor de prompt** — `scripts/_direcao.py` → `construir(marca, tipo, tema, headline, conceito)`. Monta o prompt em blocos:
   `CONCEITO · COMPOSIÇÃO (guiada pelo layout) · LUZ · LENTE (85mm) · COR (hex estritos) · MATERIAL · MOOD · ACABAMENTO · NEGATIVOS`.
   - **Composição guiada pelo layout:** o texto vive no **terço inferior** → o prompt reserva essa zona limpa e joga o visual pro topo. Garante legibilidade e zero colisão.
   - **Biblioteca de conceitos por tipo** (`CONCEITOS`): cada tipo de post tem uma metáfora visual própria → variedade com coerência:
     `manifesto · nucleo · dor · provoca · educativo · antihype · prova · autoridade · diferencial · cta`.
   - **Cor estrita** (espelha `design-system/tokens/tokens.json`): no **claro** (default), off-white/lavanda `#F4F2FB` base + lavanda `#E7DCFF`, texto `#100D1C` e violeta de acento `#8B3CF7` na palavra-chave; no **escuro** (secundário), base quase-preta `#0B0B0B`, indigo `#2A1CA8` → violeta `#9A4DFF`. Sem outros matizes, sem tons quentes.
   - **Tema-padrão = CLARO** (decisão 2026-06-23). O **escuro** virou paleta **secundária**: use só sob pedido ("escuro/dark/roxo/fundo escuro") ou como contraponto pontual. Ritmo de feed alvo ~70% claro / 30% escuro.
   - Reforçado pela **trava de paleta** (`_paleta.py`, `--paleta roxo`).

2. **Grade de acabamento** — `scripts/compositor.py` (ligada por padrão; `--no-grade` desliga). Camadas CSS sobre o fundo, antes do texto: **duotone** (soft-light roxo) + **vinheta** + **grão de filme**. Sutil numa imagem; o ganho real é **coesão de feed** — todas as artes parecem uma marca só.
   - **No claro (default), a grade fica LEVE/sutil** — duotone, vinheta e grão bem discretos. A intensidade cheia é coisa do escuro; no claro ela não pode escurecer/sujar o fundo, senão volta o ar "escuro/datado" que o brief de 2026-06-23 justamente critica.

## Como usar

- **Fundo dirigido:** `python3 scripts/openai_image.py --out <bg.png> --direcao --marca <marca> --tipo <tipo> --tema <claro|escuro> --headline "..." [--conceito "override p/ tema especial"]` — **claro é o default**; só passe `--tema escuro` sob pedido.
- **Compor (grade automática):** `python3 scripts/compositor.py --marca <marca> --out <arte.png> --bg <bg.png> --tema <...> --headline "..." --sub "..."`
- **Lançamento:** o `lancamento_server.py` (Gerar oficiais) já usa essa direção por tipo/tema de cada quadro.

## Temas especiais

Use `--conceito` (ou o param `conceito`) pra sobrescrever a metáfora **mantendo a paleta**. Ex.: Copa → estádio à noite com feixes de luz violeta e gramado em grade brilhante, **tudo em roxo** (nunca verde/amarelo — quebraria a marca).

## Roadmap (opcional, não implementado)

- **Âncora de estilo** (imagem de referência pro gpt-image) → consistência de campanha.
- **Multi-candidato** (gera 3, escolhe a melhor) → padrão de agência.
