---
description: Gera post de LinkedIn para uma marca, salva em marcas/<marca>/publicacoes/social/linkedin/
argument-hint: <marca> <briefing>
---

Você vai gerar um post de LinkedIn. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

Primeiro token = marca. Resto = briefing. Marcas válidas: `smark`, `provider-max`, `elever-ai`. Se não bater, **pare e pergunte qual marca**.

## Passo 2 — Carregar contexto na ordem

0. **`/Users/andreik/smark/shared/arquitetura-marca.md`** (REGRA PRINCIPAL — endosso "uma plataforma smark", fio condutor, cores)
1. `/Users/andreik/smark/shared/voz-grupo.md`
2. `/Users/andreik/smark/shared/pilares-gerais.md`
3. `/Users/andreik/smark/shared/glossario.md`
4. `/Users/andreik/smark/shared/padroes-instagram.md` (hooks/formatos/linha vermelha — valem p/ LinkedIn também)
5. Todos os `.md` em `/Users/andreik/smark/marcas/<MARCA>/branding/` — **incluindo `identidade-visual.md`**.
6. 3-5 referências em `/Users/andreik/smark/marcas/<MARCA>/referencias/` por tags do briefing.
7. As 3 publicações mais recentes em `.../publicacoes/social/linkedin/` (variar hook/ângulo).

Se houver `<<COMPLETAR>>` em branding, avise antes de gerar.

## Passo 2.5 — Classificar e recomendar

Classifique o assunto e use o mapa **"Assunto → Modelo → Visual"** (`padroes-instagram.md`, seção 2.1). Recomende formato + 1-2 alternativas com justificativa.

## Passo 3 — Preview otimizado p/ LinkedIn

- **Hook nos 2 primeiros parágrafos** (corta com "ver mais").
- Texto **150-400 palavras**, parágrafos de 1-3 frases.
- **3-5 hashtags** no fim. Máx 1-2 emojis funcionais.

Apresente: modelo recomendado + alternativas · ângulo · pilar · referências · copy completo · (se imagem) briefing visual · hashtags.

**Antes de apresentar, passe pela "linha vermelha"** (playbook seção 5). **Não salve ainda.** Pergunte: "Quer ajustar ou já salvo como draft?"

## Passo 4 — Iterar conforme feedback

## Passo 5 — Salvar na NOTA ÚNICA quando confirmado

Salve em `/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/linkedin/<YYYY-MM-DD>-<slug>.md`.
Base: `shared/_templates/publicacao.md` (padrão do **painel**). Frontmatter:

```yaml
marca: <MARCA>
canal: linkedin
formato: post
status: draft
data: <YYYY-MM-DD>
tema: <título curto>          # título do card no painel
arte: arte/<slug>/            # thumbnail do painel
drive: "Smark — Posts/<MARCA>/<pasta>/"
alt: <alt-text da imagem>
tags: [...]
referencias-usadas: [...]
pilares: [...]
url-publicado:
```

A copy do LinkedIn vai na seção **`## Legenda LinkedIn`** (o painel mostra o preview em formato LinkedIn). Hashtags em `## Hashtags` (3–5 no LinkedIn).

## Passo 5.1 — Quality gate (obrigatório antes de confirmar)
```bash
cd /Users/andreik/smark && python3 scripts/revisar.py "marcas/<MARCA>/publicacoes/social/linkedin/<arquivo>.md"
```
❌ REPROVADO → corrija e rode de novo. ⚠️ REVISAR → ajuste o que fizer sentido. ✅ → segue.

## Passo 5.2 — Atualizar o painel
```bash
cd /Users/andreik/smark && python3 scripts/painel.py
```
Confirme: caminho salvo + veredito do gate + painel atualizado.

## Passo 6 — (opcional) Gerar a arte → tudo na NOTA ÚNICA

Só se o usuário pedir. **Arquivo único:** PNG em `.../linkedin/arte/<slug>.png`, e a nota embute a imagem + metadados + copy + prompt. Nunca crie ficha separada.

1. Prompt em inglês = regras de `identidade-visual.md` + conteúdo. Salve em `/tmp/frame.txt`.
2. **Pipeline de 2 camadas (qualidade profissional):** gere o FUNDO sem texto com `scripts/openai_image.py --direcao --marca <MARCA> --tipo <tipo> --tema <escuro|claro> --headline "..." --size 1024x1024` (direção de arte, ver `shared/direcao-de-arte.md`) e componha com `scripts/compositor.py --marca <MARCA> --size 1080x1080 --bg <fundo> --headline "..." --sub "..."` (grade de acabamento automática). Texto nítido + acento exato + selo "uma plataforma smark" (produtos). **Tema-padrão = CLARO.** Gere a arte clara por default (o compositor já assume `--tema claro`). Só use `--tema escuro` quando o usuário pedir explicitamente com palavras como **"escuro", "dark", "roxo", "fundo escuro", "preto", "noturno"** ou algo que remeta a tons escuros. Na dúvida, claro.
3. Cole os `arte-*` impressos no frontmatter da nota e o `![[arte/<slug>.png]]` no corpo.
4. **Abra a imagem (Read)** e confira.
5. **Envie pro Drive (1 pasta por post):** legenda em `/tmp/legenda.txt` + `bash scripts/to_drive.sh <MARCA> "<YYYY-MM-DD>-<slug>" "marcas/<MARCA>/publicacoes/social/linkedin/arte/<slug>.png" /tmp/legenda.txt` → `Smark — Posts/<MARCA>/<YYYY-MM-DD>-<slug>/`.
6. **Registre na planilha:** `bash scripts/registrar.sh <MARCA> "<YYYY-MM-DD>-<slug>" "<HEADLINE>" "<slug>.png" draft`.

## Regras invioláveis

- Sempre pt-BR. Sem palavras-proibidas de `shared/voz-grupo.md`.
- Marca inválida ou briefing vago → pergunte.
- Nota é **arquivo único** (imagem embutida + tudo junto).
