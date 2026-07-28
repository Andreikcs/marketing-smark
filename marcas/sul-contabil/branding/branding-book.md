---
marca: sul-contabil
tipo: branding-book
versao: 1.0
gerado: auto
---

# Branding Book — Sul Contábil

> Documento vivo da marca no vault Smark. Fonte: `tokens.json` + branding.

## Essência

| Campo | Valor |
|-------|-------|
| Nome | Sul Contábil |
| Slug | `sul-contabil` |
| Handle | @sulcontabil |
| Wordmark | Sul Contábil |
| Glyph | S |
| Segmento | contabilidade |
| Site | https://revoecontabil.com.br/ |
| Logo | marcas/sul-contabil/branding/assets/logo.png |

## Paleta

| Papel | Hex |
|-------|-----|
| Acento | `#1CA5B2` |
| Acento claro | `#3DC4D0` |
| Base escura | `#001A34` |
| Gradiente | `linear-gradient(155deg,#1CA5B2 0%,#001A34 100%)` |

```
■ #1CA5B2  acento
■ #3DC4D0  acento claro
■ #001A34  base escura
```

## Mood (direção de arte)

premium B2B accounting and tax advisory brand — deep navy and teal, clean corporate photography, geometric curves, trustworthy and modern Contabilidade de Resultado style

## Regras de aplicação

1. **Tema-padrão = claro** (fundo branco/lavanda, texto escuro, acento na palavra-chave).
2. Escuro só sob pedido explícito.
3. Fundo de IA **sem texto** — tipografia e logo vêm do compositor.
4. Logo na tab/chip: preferir marca limpa (PNG com transparência ou SVG). Foto de feed **não** vira brasão.
5. Sem jargão vazio; sem promessa de venda/faturamento no social.

## Identidade visual (resumo)

# Identidade Visual — Sul Contábil

Absorvida da referência **Revoe Contabilidade de Resultado** (site + feed). Padrão de qualidade: contabilidade premium B2B, navy + teal, fotografia corporativa e UI fiscal.

## Paleta ativa

```yaml
primaria:
  base_escuro: "#001A34"      # navy oficial (site #001a34)
  base_deep:   "#000F1F"      # fundos mais densos do feed
  base_claro:  "#F4F8FA"      # cards claros pontuais
  acento:      "#1CA5B2"      # teal oficial (site #1ca5b2)
  acento_claro: "#3DC4D0"
  ouro_sutil:  "#B78139"      # raro — só detalhes/premium
  texto_escuro: "#FFFFFF"
  texto_claro:  "#001A34"
  apoio:       "#6C757D"
```

## Hierarquia visual (padrão do feed)

1. **Fundo** navy profundo ou fotografia corporativa com overlay navy/teal.
2. **Curvas geométricas** teal (arcos, waves) no canto ou divisória diagonal.
3. **Logo** no topo (wordmark branco ou bloco com S).
4. **Headline** bold, 1–2 linhas; **palavra-chave em teal** (`*acento*` no compositor).
5. **Apoio** curto em cinza/branco 80%.
6. **CTA** opcional em pill teal ou outline.
7. Terço inferior com respiro para tipografia (quando fundo IA).

## Temas

| Tema | Quando |
|------|--------|
| **Escuro (padrão da marca)** | 70%+ do feed — autoridade fiscal, riscos, leis, UI |
| **Claro** | Avisos, feriados, MEI “alerta”, calendário, educacionais leves |

No compositor: para peçasescuro do feed → `--tema escuro`. Claro só se o briefing pedir.

## Tipografia

- Display/headline: bold sans (Anton/Archivo no sistema smark).
- Apoio: regular, legível.
- Números grandes (anos, prazos, “5 erros”) em teal ou branco com peso máximo.

## Fotografia / cena

- Empresário(a) em escritório, laptop, gráficos, reunões.
- Props fiscais: calculadora, documentos, martelo (lei), calendário, NF-e, celular com app.
- Evitar stock genérico “aperto de mão feliz” sem contexto fiscal.
- Fundo IA: abstrato tech navy/teal **ou** cena editorial limpa — nunca poluição de texto na imagem.

## Proibido

- Roxo smark / lime Provider Max nesta marca
- Arco-íris, neon genérico, glassmorphism sem navy
- Texto tipografado pela IA no fundo
- Humor cafona com imposto
- Promessa de “zero imposto” / resultado financeiro inventado

## Arquivos

- Logo placeholder: `branding/assets/logo.png` (substituir pelo oficial quando chegar)
- Refs de feed: `referencias/feed/feed-01.jpg` … `feed-03.jpg`
- Site fonte: https://revoecontabil.com.br/

## Como usar neste sistema

1. Config → Marcas → Editar → confira cores, logo e referências.
2. Editor → selecione a marca no post → Estúdio IA gera copy + fundo na paleta.
3. Referências em `referencias/feed` e `referencias/acervo` guiam o fundo.

---
*Gerado pelo smark studio · edite este arquivo se o cliente tiver book oficial.*
