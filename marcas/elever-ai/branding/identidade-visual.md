---
marca: elever-ai
tipo: identidade-visual
versao: 1.0
atualizado: 2026-06-11
paleta-ativa: roxo
tema-padrao: claro   # claro é o tema-padrão da vitrine (2026-06-23). Escuro = secundário, sob pedido.
herda-de: "[[shared/arquitetura-marca]]"
---

# Identidade Visual — Elever AI

> **uma plataforma smark.** Compartilha o DNA visual da casa (ver [[shared/arquitetura-marca]]); muda só o acento.

## Paleta ativa: roxo

```yaml
roxo:
  base:    "#0B0B0B"   # escuro (base secundária, sob pedido)
  acento:  "#8B3CF7"   # roxo (acento da marca)
  brilho:  "#A472FF"   # roxo claro p/ texto-acento (mais vívido sobre escuro)
  texto:   "#FFFFFF"
  apoio:   "#A1A1A1"
```

## Temas: claro (default) + escuro (secundário)

O feed mistura os dois (~70% claro / 30% escuro) — **claro é o tom-padrão**. **Mesmo modelo** — muda só a inversão fundo/texto.

| | Claro (default) | Escuro (secundário) |
|---|---|---|
| Fundo | `#F4F2FB` | `#0B0B0B` |
| Texto | `#100D1C` | `#FFFFFF` |
| Acento | roxo `#8B3CF7` | roxo `#A472FF` |

- **Regra do acento (nos dois temas):** palavra-chave **colorida** da headline, **nunca** bloco/caixa atrás do texto. Entrelinha apertada.
- **Contraste no claro:** roxo já tem contraste; fica como está. (Acentos claros demais escurecem sozinhos.)
- **Quando usar escuro:** só sob pedido ("escuro", "dark", "roxo", "fundo escuro") ou contraponto pontual. **Na dúvida, claro.**
- O compositor já assume `--tema claro` por padrão; cores vêm do `tokens.json` (`tema_claro`). Escuro = `--tema escuro`.

## Símbolo & assinatura (v2 — 2026-06-14)

- **Símbolo = SPARKLE:** estrela de 4 pontas côncava (da logo original do Elever). Substitui a letra "E". Branco sobre o quadrado, na etiqueta e no avatar do chip. Vetor único em `tokens.json` (`marcas.elever-ai.logo_path`).
- **Gradiente roxo→azul** (`#9A4DFF → #2A1CA8`) = assinatura cromática do Elever (dentro da família roxa). Vai nos **quadrados da moldura** (etiqueta, chip, selo) e na **pílula de CTA**. Fonte: `tokens.json` (`marcas.elever-ai.gradiente`).
- **Wordmark = "Elever AI"** no chip — "AI" no roxo claro `#A472FF` (eco do badge da logo). Etiqueta vertical = `ELEVER`.
- **Acento da headline** = roxo claro `#A472FF` (escuro) / `#8B3CF7` (claro) — palavra colorida, nunca bloco.
- **Rodapé:** `@eleverai` + **`@copywriting2026`** (padrão de todas as marcas). O selo "uma plataforma smark." vai na **legenda** (produto).

## Regras de arte
Herda o sistema da casa (tipografia, malha, foto/realismo) renderizado pelo **compositor** (`scripts/compositor.py`). Rodapé sempre com o selo **"uma plataforma smark."**.

## Tratamento por tipo de conteúdo
Ver [[shared/padroes-instagram]] (seção 2.1) e [[shared/formatos-canais]].

## Geração de fundo (direção de arte)
Todo fundo de IA segue a **direção estruturada nível agência + grade de acabamento** — regra única em [[shared/direcao-de-arte]]. Resumo: conceito por tipo de post, composição guiada pelo layout (texto no terço inferior), cor estrita (roxo/indigo sobre quase-preto; claro = off-white+lavanda) e grade (duotone+vinheta+grão) ligada por padrão no compositor.
