---
marca: smark
tipo: identidade-visual
versao: 1.1
atualizado: 2026-06-14
paleta-ativa: roxo   # roxo #8B3CF7 é o primário (decidido). Lime fica como acento secundário.
tema-padrao: claro   # claro é o tema-padrão da vitrine (2026-06-23). Escuro = secundário, sob pedido.
fonte: site oficial smark.
---

# Identidade Visual — Smark

> **Fonte única da verdade visual.** O `/post-instagram` lê este arquivo a cada geração. Mudou aqui → próximo post já sai com o novo valor. Sem rebuild.

## Paleta ativa

A geração usa SEMPRE a paleta marcada em `paleta-ativa` (frontmatter). Hoje: **verde-limao**.

## Paletas definidas

```yaml
verde-limao:        # atual no site
  base:    "#0B0B0B"   # <<CONFIRMAR HEX>> preto-quase
  acento:  "#C6F24E"   # <<CONFIRMAR HEX>> verde-limão
  texto:   "#FFFFFF"
  apoio:   "#A1A1A1"   # cinza de texto secundário
roxo:               # PRIMÁRIO da Smark (ativo)
  base:    "#0B0B0B"   # escuro (base secundária, sob pedido)
  acento:  "#8B3CF7"   # roxo primário
  brilho:  "#A472FF"   # roxo claro p/ texto-acento sobre escuro
  texto:   "#FFFFFF"
  apoio:   "#A1A1A1"
```

**Para trocar a paleta:** mude `paleta-ativa` no frontmatter. Hoje: **roxo** (primário). Lime fica como acento secundário da mãe.

> Os hex acima são aproximações das telas do site — me passe os valores oficiais quando tiver, eu corrijo aqui (e todo post futuro já sai certo).

## Uso da cor

- **Base escura** domina a arte (fundo).
- **Acento** (cor ativa) só na **palavra-chave da headline** e em CTAs. Não espalhar.
- Texto branco; cinza de apoio para subtítulo/legenda na arte.
- **Nunca** usar cor fora da paleta ativa. Nunca misturar acento de outra marca (lime da Provider Max, roxo da Elever) num post Smark — a menos que o post seja sobre o produto.

## Símbolo & assinatura (v2 — 2026-06-14)

- **Símbolo = APEX:** cursor pra cima (apex + trail + base + *eye*/furo central). Substitui a antiga letra "A". Branco sobre o quadrado, na etiqueta e no avatar do chip. Vetor único em `design-system/tokens/tokens.json` (`marcas.smark.logo_path`) — o compositor desenha automático.
- **Quadrados da moldura em degradé:** etiqueta, avatar do chip, selo ✓ e pílula de CTA usam o **gradiente roxo→azul** `#9A4DFF → #2A1CA8` (mesmo do Elever — **padrão do ecossistema**, dá volume/ar tech). Token `marcas.smark.gradiente`. A palavra-acento do headline segue no roxo claro `#A472FF` (escuro) / `#8B3CF7` (claro).
- **Wordmark = `smark.`** (minúsculo, com o **ponto roxo** — "marca de pontuação"). Aparece no chip como assinatura. Etiqueta vertical = `SMARK.` (caixa-alta).
- **@smark** fica no rodapé (handle, pra atribuição em prints/shares).
- **CTA (estilo V4):** pílula retangular (raio 16) no acento, caixa-alta. Com CTA presente, o headline limita em ~92px pra o bloco respirar. Via `--cta` no compositor.
- Produtos (Provider Max, Elever AI) seguem na **letra** (P / E) até terem símbolo próprio.

## Tipografia

- **Headline (display):** Anton (caixa-alta, condensada), acento na palavra-chave. (Brand book v2 sugere Inter Tight 700 pro wordmark — a subir nas fontes.)
- **Corpo / legenda:** sans grotesca, limpa. <<CONFIRMAR fonte>>
- **Labels / seções:** monoespaçada, caixa-alta, com tracking (ex: "O PADRÃO", "SERVIÇO"). <<CONFIRMAR fonte>>

## Regras de arte

- Logo **"smark."** (minúsculo + ponto) no topo da peça.
- **Pouco texto na arte** — a headline carrega; o resto vai na legenda.
- **Foto real** dos sócios e do trabalho. Grafismo limpo quando não houver foto.
- **Grid consistente** entre posts (mesmo template) → feed coeso.
- Headline curta (até ~8 palavras em display).

## Proibido visualmente (trava de qualidade)

- Imagem de IA dramática/cafona (super-herói, caverna, deadlift épico).
- Stock genérico.
- Poluição de texto na arte.
- Founder em pose de popstar/ostentação.
- Qualquer cor fora da `paleta-ativa`.

## Temas: claro (default) + escuro (secundário)

O feed mistura os dois (~70% claro / 30% escuro) — **claro é o tom-padrão** (vitrine limpa, fundo branco). **Mesmo modelo** — muda só a inversão fundo/texto.

| | Claro (default) | Escuro (secundário) |
|---|---|---|
| Fundo | `#F4F2FB` | `#0B0B0B` |
| Texto | `#100D1C` | `#FFFFFF` |
| Acento | roxo `#8B3CF7` | roxo `#A472FF` |

- **Regra do acento (nos dois temas):** acento é sempre a **palavra-chave colorida** da headline — **nunca** bloco/caixa atrás do texto. Entrelinha apertada.
- **Contraste no claro:** acento claro demais pro fundo branco (ex: lime) **escurece sozinho** (compositor) mantendo o tom. Roxo já tem contraste.
- **Quando usar escuro:** só quando o usuário pedir ("escuro", "dark", "roxo", "fundo escuro") ou como contraponto pontual (UI do produto, bastidor "tech", destaque). **Na dúvida, claro.**
- O compositor já assume `--tema claro` por padrão; cores vêm do `tokens.json` (`tema_claro`). Escuro = `--tema escuro`.

## Tratamento por tipo de conteúdo

Ver o mapa **"Assunto → Modelo → Visual"** em `[[shared/padroes-instagram]]` (seção 2.1). Este arquivo define a paleta e as regras; o playbook define qual formato/tratamento cada assunto pede.

## Geração de fundo (direção de arte)
Todo fundo de IA segue a **direção estruturada nível agência + grade de acabamento** — regra única em [[shared/direcao-de-arte]]. Resumo: conceito por tipo de post, composição guiada pelo layout (texto no terço inferior), cor estrita (roxo/indigo sobre quase-preto; claro = off-white+lavanda) e grade (duotone+vinheta+grão) ligada por padrão no compositor.
