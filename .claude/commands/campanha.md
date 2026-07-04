---
description: Gera campanha completa (conceito + posts sociais + anúncios + cronograma) numa pasta em marcas/<marca>/publicacoes/marketing/campanhas/
argument-hint: <marca> <tema>
---

Você vai gerar uma campanha. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

Primeiro token = marca. Resto = tema. Se a marca não bater, pergunte. Se o tema for muito vago (< 6 palavras ou genérico), pergunte por ângulo, objetivo e prazo.

## Passo 2 — Carregar contexto

1. `shared/voz-grupo.md`, `pilares-gerais.md`, `glossario.md`
2. Todos os arquivos em `marcas/<MARCA>/branding/`
3. 5-8 referências relevantes em `marcas/<MARCA>/referencias/`
4. Listar últimas 5 publicações em `marcas/<MARCA>/publicacoes/` (qualquer canal) pra ter contexto recente.

## Passo 3 — Gerar preview do conceito primeiro

Apresente ao usuário **só o conceito** antes de gerar peças:

- **Big idea** (1 frase — a ideia-síntese)
- **Pilares acionados** (quais do `branding/pilares-de-conteudo.md`)
- **Narrativa** (3-5 frases — como a campanha se desenvolve do início ao fim)
- **Canais sugeridos** (Instagram, LinkedIn, anúncios — qual mix)
- **Duração sugerida** (1 semana? 2 semanas? mês?)

Pergunte: "Esse conceito está alinhado? Posso desdobrar nas peças?"

## Passo 4 — Quando aprovado, gerar peças

Para cada peça:

- **3 posts sociais** (mix Instagram + LinkedIn): briefing curto de cada, com headline e ângulo
- **2 variações de anúncio** (estruturalmente diferentes — dor vs resultado)
- **Cronograma sugerido** (ordem de publicação, intervalo)

Apresente tudo numa estrutura clara. Pergunte: "Posso salvar?"

## Passo 5 — Salvar quando confirmado

Crie a pasta:
`/Users/andreik/smark/marcas/<MARCA>/publicacoes/marketing/campanhas/<YYYY-MM-DD>-<slug>/`

Com 4 arquivos:

- `00-conceito.md` — big idea, pilares, narrativa, canais, duração
- `01-posts-social.md` — os 3 posts sugeridos (cada um com ângulo, copy, briefing visual)
- `02-anuncios.md` — as 2 variações
- `03-cronograma.md` — ordem + intervalo + responsabilidades (se especificadas)

Cada arquivo com frontmatter:
```yaml
marca: <MARCA>
canal: campanha
status: draft
data: <YYYY-MM-DD>
campanha: <slug>
```

`00-conceito.md` adicionalmente tem:
```yaml
pilares: [...]
referencias-usadas: [...]
duracao-sugerida: <ex: "2 semanas">
```

Confirme caminho ao usuário.

## Regras invioláveis

- Sempre pt-BR.
- Big idea **nunca** é um clichê do tipo "transforme seu negócio".
- Conceito vai sempre antes das peças — não pular o passo 3.
- Não gere imagem.
