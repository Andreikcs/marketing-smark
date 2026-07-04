---
description: Normaliza uma referência (screenshot, URL, PDF, texto livre) em nota estruturada em marcas/<marca>/referencias/
argument-hint: <marca> <url-ou-descricao-ou-caminho-de-arquivo>
---

Você vai normalizar uma referência. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

Primeiro token = marca. Resto = input cru (URL, descrição em texto livre, ou caminho de arquivo já em `referencias/inbox/`).

Identifique o tipo de input:
- **URL** (começa com `http`) — busque o conteúdo via WebFetch.
- **Caminho de arquivo** (começa com `/` ou contém `inbox/`) — leia o arquivo (PDF, imagem).
- **Texto livre** — trate como descrição direta.

Se ambíguo, pergunte.

## Passo 2 — Extrair padrões

Quando o input já estiver carregado, identifique:

- **Tipo da referência** (post, anuncio, artigo, video, site, email)
- **Fonte** (URL canônica ou descrição da origem)
- **Tom usado** (mapeie pra tags em `shared/glossario.md` — `tom-proximo`, `tom-ironico`, etc)
- **Estrutura** (como abre, desenvolve, fecha)
- **Visual** (cor, tipografia, composição, peso de texto)
- **Copy-chave** (transcreva 1-3 trechos memoráveis)
- **CTA** (verbo + benefício)

## Passo 3 — Aplicabilidade

Sugira uma nota de aplicabilidade (alta/média/baixa) baseado em:
- alinhamento de tom com `marcas/<MARCA>/branding/tom-de-voz.md`
- se a estrutura é replicável no contexto da marca
- se o conteúdo viola palavras-proibidas

Justifique em 1 frase.

## Passo 4 — Como aplicar / o que evitar

- **Como aplicar na <marca>:** 2-4 frases de adaptação contextual
- **O que evitar:** 1-2 armadilhas se imitar mal

## Passo 5 — Preview e confirmação

Apresente o resumo na conversa antes de salvar. Pergunte: "Tags estão certas? Aplicabilidade está certa? Posso salvar?"

## Passo 6 — Salvar quando confirmado

Decida o slug (kebab-case, derivado do tema da referência, curto: `magalu-post-black-friday`).

Salve em:
`/Users/andreik/smark/marcas/<MARCA>/referencias/<slug>.md`

Use template `shared/_templates/referencia.md`. Frontmatter:
```yaml
marca: <MARCA>
tipo: <post|anuncio|artigo|video|site|email>
fonte: <url ou descrição>
data-salvo: <YYYY-MM-DD>
tags: [<3-6 tags de shared/glossario>]
aplicabilidade: <alta|media|baixa>
arquivo-original: <caminho relativo a inbox/ se houver, senão vazio>
```

**Se houve arquivo original** (PDF, imagem):
- Mova-o para `/Users/andreik/smark/marcas/<MARCA>/referencias/inbox/<slug>.<ext>` (se não estava lá).
- Preencha `arquivo-original: inbox/<slug>.<ext>` no frontmatter.

Confirme caminho ao usuário.

## Regras invioláveis

- Sempre pt-BR (mesmo se a referência for em inglês — traduzir trechos).
- Tags vindas de `shared/glossario.md` — se precisar de uma tag nova, avise o usuário e pergunte se quer adicionar ao glossário.
- Não inventar dados que a referência não tem.
