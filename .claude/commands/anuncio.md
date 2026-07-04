---
description: Gera anúncio (headline + copy + CTA) com 3 variações A/B/C, salva em marcas/<marca>/publicacoes/marketing/anuncios/
argument-hint: <marca> <produto-ou-objetivo>
---

Você vai gerar um anúncio. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

Primeiro token = marca (`smark`, `provider-max`, `elever-ai`). Resto = objetivo/produto a anunciar. Se a marca não bater, pergunte. Se o objetivo for vago demais, pergunte (ex: "anúncio de qual produto? com qual objetivo — awareness, conversão, recrutamento?").

## Passo 2 — Carregar contexto

1. `shared/voz-grupo.md`, `pilares-gerais.md`, `glossario.md`
2. Todos os arquivos em `marcas/<MARCA>/branding/`
3. 3-5 referências relevantes em `marcas/<MARCA>/referencias/` (priorize referências com tag `obj-conversao`, `tipo: anuncio`, `copy-curto`)
4. Os 3 anúncios mais recentes em `marcas/<MARCA>/publicacoes/marketing/anuncios/` (evitar repetir headline)

## Passo 3 — Gerar preview com variações

Entregue 3 variações **estruturalmente diferentes** (não só sinônimo):

- **Variação A — Dor-direta:** abre nomeando a dor.
- **Variação B — Resultado-prometido:** abre com o resultado concreto.
- **Variação C — Provocação-contraintuitiva:** abre virando uma crença.

Para cada variação:
- **Headline** (5-10 palavras)
- **Copy primário** (1-3 frases, 50-120 caracteres)
- **Copy secundário/descrição** (1 frase de reforço)
- **CTA** (verbo + benefício — não "Saiba mais" puro)

Mais:
- **Persona-alvo** dominante (qual persona do `branding/personas.md` cada variação ataca melhor)
- **Briefing visual** comum (composição, cor dominante, elementos)

**Não salve ainda.** Pergunte: "Qual variação seguimos? Posso salvar com as 3 pra você decidir depois?"

## Passo 4 — Iterar conforme feedback

## Passo 5 — Salvar quando confirmado

Salve em:
`/Users/andreik/smark/marcas/<MARCA>/publicacoes/marketing/anuncios/<YYYY-MM-DD>-<slug>.md`

Use template `shared/_templates/publicacao.md`, com as 3 variações na seção "Variações" e a escolhida (se houver) destacada em "Versão final".

Frontmatter:
```yaml
marca: <MARCA>
canal: anuncio
formato: headline-ad
status: draft
data: <YYYY-MM-DD>
tags: [obj-conversao, ...]
referencias-usadas: [...]
pilares: [...]
```

Confirme caminho ao usuário.

## Regras invioláveis

- Sempre pt-BR.
- Sem palavras-proibidas.
- Headline nunca passa de 10 palavras.
- CTA nunca é só "Saiba mais" — sempre verbo + benefício.
- Não gere imagem.
