---
marca: provider-max
tipo: identidade-visual
versao: 2.0
atualizado: 2026-06-16
paleta-ativa: roxo
tema-padrao: claro   # claro é o tema-padrão da vitrine (2026-06-23). Escuro = secundário, sob pedido.
herda-de: "[[shared/arquitetura-marca]]"
---

# Identidade Visual — Provider Max

> **uma plataforma smark.** Compartilha o DNA visual da casa (ver [[shared/arquitetura-marca]]); diferencia pelo **símbolo**, não pela cor.

## Paleta ativa: roxo (padrão do ecossistema)

```yaml
roxo:
  base:    "#0B0B0B"   # escuro (base secundária, sob pedido)
  acento:  "#8B3CF7"   # roxo (padrão das 3 marcas)
  brilho:  "#A472FF"   # roxo claro p/ texto-acento ("Max", sobre escuro)
  degradé: "#9A4DFF → #2A1CA8"   # quadrados da moldura
  texto:   "#FFFFFF"
  apoio:   "#A1A1A1"
```

> Decisão (2026-06-16): o PM **adota o roxo padrão** do ecossistema (lime aposentado). As 3 marcas ficam roxas; a distinção é pelo **símbolo** (PM = sinal). O IG antigo navy/vermelho continua descartado.

## Temas: claro (default) + escuro (secundário)

O feed mistura os dois (~70% claro / 30% escuro) — **claro é o tom-padrão**. **Mesmo modelo** — muda só a inversão fundo/texto.

| | Claro (default) | Escuro (secundário) |
|---|---|---|
| Fundo | `#F4F2FB` | `#0B0B0B` |
| Texto | `#100D1C` | `#FFFFFF` |
| Acento | roxo `#8B3CF7` | roxo `#A472FF` |

- **Regra do acento (nos dois temas):** palavra-chave **colorida** da headline, **nunca** bloco/caixa atrás do texto. Entrelinha apertada.
- **Contraste:** roxo já tem contraste nos dois temas (sem necessidade de escurecer).
- **Quando usar escuro:** só sob pedido ("escuro", "dark", "roxo", "fundo escuro") ou contraponto pontual. **Na dúvida, claro.**
- O compositor já assume `--tema claro` por padrão; cores vêm do `tokens.json` (`tema_claro`). Escuro = `--tema escuro`.

## Símbolo & assinatura (v2 — 2026-06-16)

- **Símbolo = SINAL:** ondas de WiFi/sinal subindo (ponto + 3 arcos), **centralizado** no quadrado. Lê na hora pro dono de provedor = **conectividade que vira crescimento**. Substitui a letra "P". **Branco** sobre o quadrado em degradé roxo. Vetor único em `tokens.json` (`marcas.provider-max.logo_svg`, `currentColor`).
- **Quadrado em degradé roxo→azul** `#9A4DFF → #2A1CA8` — **mesmo padrão das 3 marcas**. Token `marcas.provider-max.gradiente`.
- **Wordmark = "Provider Max"** no chip, com **"Max" em roxo** (como o "AI" do Elever e o ponto da smark) — `wordmark: "Provider *Max*"`. Etiqueta vertical = `PROVIDER`; `@providermax` no rodapé.
- **Acento da headline:** roxo `#A472FF` (escuro) / `#8B3CF7` (claro) — palavra colorida, nunca bloco.
- **Rodapé:** `@providermax` + **`@copywriting2026`** (padrão). O selo "uma plataforma smark." vai na **legenda** (produto).
- **Diferenciação:** o PM se distingue das outras pelo **símbolo (sinal)**, não pela cor — todas são roxas.

## Regras de arte
Herda o sistema da casa (tipografia, malha, foto/realismo) renderizado pelo **compositor** (`scripts/compositor.py`). Rodapé sempre com o selo **"uma plataforma smark."**.

## Tratamento por tipo de conteúdo
Ver [[shared/padroes-instagram]] (seção 2.1) e [[shared/formatos-canais]].

## Geração de fundo (direção de arte)
Todo fundo de IA segue a **direção estruturada nível agência + grade de acabamento** — regra única em [[shared/direcao-de-arte]]. Resumo: conceito por tipo de post, composição guiada pelo layout (texto no terço inferior), cor estrita (roxo/indigo sobre quase-preto; claro = off-white+lavanda) e grade (duotone+vinheta+grão) ligada por padrão no compositor.
