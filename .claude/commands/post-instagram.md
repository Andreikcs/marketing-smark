---
description: Gera post de Instagram para uma marca, salva em marcas/<marca>/publicacoes/social/instagram/
argument-hint: <marca> <briefing>
---

Você vai gerar um post de Instagram. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

O primeiro token de `$ARGUMENTS` é a marca. O restante é o briefing.

Marcas válidas: `smark`, `provider-max`, `elever-ai`. Se a primeira palavra não bater com nenhuma, **pare e pergunte ao usuário qual marca**. Não assuma.

## Passo 0 — Estratégia primeiro (obrigatório, camada acima da copy)

**Antes de qualquer copy**, para a smark leia `marcas/smark/branding/estrategia.md` + `site-oficial.md`:
1. Escolha **1 dos 3 Ângulos** (produtividade · medo/método · contexto econômico).
2. Aplique o **Filtro dos 3 Testes** (DONO≠ferramenta · CONSEQUÊNCIA≠função · MADUREZA≠hype) ao gancho. Se falhar em qualquer um, reescreva o ângulo.
3. Se for citar número de mercado, use **só** os dados ✅ verificados de `shared/dados-mercado.md` (e registre o uso lá).
4. CTA de fundo de funil = **diagnóstico gratuito do site**.

## Passo 2 — Carregar contexto na ordem

Leia, nesta ordem:

0. **`/Users/andreik/smark/shared/arquitetura-marca.md`** (REGRA PRINCIPAL — endosso "uma plataforma smark" se for produto, fio condutor, cores oficiais)
1. `/Users/andreik/smark/shared/voz-grupo.md`
2. `/Users/andreik/smark/shared/pilares-gerais.md`
3. `/Users/andreik/smark/shared/glossario.md`
4. `/Users/andreik/smark/shared/padroes-instagram.md` (playbook: hooks, formatos, mapa assunto→modelo, linha vermelha)
5. Todos os arquivos `.md` em `/Users/andreik/smark/marcas/<MARCA>/branding/` — **incluindo `identidade-visual.md`** (paleta ativa, tipografia, regras de arte).
6. Liste `/Users/andreik/smark/marcas/<MARCA>/referencias/` e identifique 3-5 referências cujas tags no frontmatter melhor casem com palavras-chave do briefing. Leia o conteúdo dessas.
7. Liste as 3 publicações mais recentes em `/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/instagram/` (por data no nome do arquivo) e leia-as para evitar repetir hook/ângulo.

Se a marca tiver marcadores `<<COMPLETAR COM USUÁRIO>>` em branding, **avise o usuário antes de gerar** — pergunte se quer completar primeiro ou seguir com o que tem.

## Passo 2.5 — Classificar e recomendar o modelo

Antes de escrever, decida o formato com critério (não aleatório):

1. **Classifique o assunto** do briefing (processo/operação, IA/automação, vendas/autoridade, legado, capacitação, bastidor…).
2. Use o mapa **"Assunto → Modelo → Visual"** (`shared/padroes-instagram.md`, seção 2.1) para escolher o **formato ideal** e o **tratamento visual default**.
3. Pegue a **paleta ativa** e as regras de arte de `identidade-visual.md`.
4. **Recomende a melhor opção + 1-2 alternativas**, com 1 linha de justificativa cada. Se desviar do mapa, explique por quê.

Apresente essa recomendação curta ao usuário no topo do preview (ele pode trocar o formato antes de você detalhar).

## Passo 3 — Gerar preview na conversa

Apresente:

- **Modelo recomendado** (formato + por quê) + alternativas consideradas
- **Ângulo escolhido** (1-2 linhas — qual insight guiou)
- **Pilar de conteúdo** que esse post ataca
- **Referências usadas** (slug + 1 linha do que extraiu)
- **Hook** (do banco da seção 3 do playbook, adaptado — não repetir o dos 3 últimos posts)
- **Copy da legenda** (versão final pronta pra publicar)
- **Sugestão de carrossel** se aplicável (frame por frame)
- **Briefing visual** (descrição pra arte) — **usando a paleta ativa e as regras de `identidade-visual.md`**
- **Hashtags** (5-8, relevantes — não spam)

**Antes de apresentar, passe o rascunho pela "linha vermelha"** (playbook, seção 5): se algo soaria como V4/Weagle no *tom* (vanity metric, insulto, hype, promessa absoluta), reescreva.

**Não salve nada ainda.** Pergunte: "Quer ajustar algo ou já pode salvar como draft?"

## Passo 4 — Iterar conforme feedback

Ajuste o que o usuário pedir. Não regere tudo — só o que mudou.

## Passo 5 — Salvar quando o usuário confirmar

Salve em:
`/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/instagram/<YYYY-MM-DD>-<slug-do-tema>.md`

Onde `<YYYY-MM-DD>` é a data de hoje e `<slug-do-tema>` é um slug em kebab-case curto derivado do tema (ex: `churn-invisivel-isps`).

Use o template `/Users/andreik/smark/shared/_templates/publicacao.md` como base (padrão do **painel**). Frontmatter:

```yaml
marca: <MARCA>
canal: instagram
formato: <post|carrossel>
status: draft
data: <YYYY-MM-DD>
tema: <título curto>          # vira o título do card no painel
arte: arte/<slug>/            # o painel puxa o thumbnail daqui
drive: "Smark — Posts/<MARCA>/<pasta>/"
alt: <alt-text da imagem>     # acessibilidade/SEO
tags: [<tags-relevantes>]
referencias-usadas: [<wikilinks-pras-refs>]
pilares: [<wikilinks-pros-pilares>]
url-publicado:
```

A copy vai em seções (o painel mostra cada canal): **`## Legenda Instagram`**, **`## Legenda LinkedIn`** (se também for pro LinkedIn), **`## Hashtags`** e **`## Frames`** (carrossel).

## Passo 5.1 — Quality gate (obrigatório antes de confirmar)

Rode o gate na nota salva e mostre o resultado ao usuário:
```bash
cd /Users/andreik/smark && python3 scripts/revisar.py "marcas/<MARCA>/publicacoes/social/instagram/<arquivo>.md"
```
- **❌ REPROVADO** (palavra-proibida, promessa absoluta): corrija a copy e rode de novo antes de seguir.
- **⚠️ REVISAR** (sem CTA, sem selo, sem alt-text, hashtags fora de 3–8): ajuste o que fizer sentido.
- **✅ APROVADO:** segue.

## Passo 5.2 — Atualizar o painel
```bash
cd /Users/andreik/smark && python3 scripts/painel.py
```
Confirme ao usuário o **caminho do arquivo salvo**, o **veredito do quality gate** e que o **painel foi atualizado** (`painel.html`).

## Passo 6 — (opcional) Gerar a arte com QUALIDADE PROFISSIONAL → nota única

Só execute se o usuário pedir ("gera a arte"). Custa por imagem.

> **ARQUITETURA ARQUIVO-ÚNICO:** nunca crie ficha `.md` separada. PNG em `.../arte/<slug>.png`; a nota do post embute imagem + metadados + legenda + prompt juntos.

**Pipeline de 2 camadas (padrão — texto sempre nítido, cor exata):**

1. **Gere só o FUNDO** com IA (**sem texto**) pela **direção de arte** (`shared/direcao-de-arte.md`) — conceito por tipo + composição guiada pelo layout (a zona do texto já é reservada automaticamente, não precisa instruir manualmente):
   ```bash
   cd /Users/andreik/smark && python3 scripts/openai_image.py \
     --out "marcas/<MARCA>/publicacoes/social/instagram/arte/<slug>-bg.png" \
     --direcao --marca <MARCA> --tipo <manifesto|dor|provoca|educativo|antihype|prova|autoridade|diferencial|cta|nucleo> \
     --tema <escuro|claro> --headline "..." --size 1024x1536 --quality high
   ```
   **Tema-padrão = CLARO.** Gere a arte clara por default (o compositor já assume `--tema claro`). Só use `--tema escuro` quando o usuário pedir explicitamente com palavras como **"escuro", "dark", "roxo", "fundo escuro", "preto", "noturno"** ou algo que remeta a tons escuros. Na dúvida, claro.
   (Tema especial → `--conceito "metáfora, mantendo a paleta roxa"`. Prompt 100% manual → troque `--direcao` por `--prompt-file /tmp/bg.txt`.)
2. **Componha a arte** com o template da marca (tipografia real + acento + selo "uma plataforma smark"):
   ```bash
   cd /Users/andreik/smark && python3 scripts/compositor.py \
     --marca <MARCA> --bg "marcas/<MARCA>/publicacoes/social/instagram/arte/<slug>-bg.png" \
     --out "marcas/<MARCA>/publicacoes/social/instagram/arte/<slug>.png" \
     --headline "LINHA 1\n*PALAVRA NO ACENTO*\nLINHA 3" --sub "subtítulo opcional"
   ```
   (`\n` = quebra de linha · `*texto*` = palavra no acento da marca · selo de produto e **grade de acabamento** automáticos; `--no-grade` desliga a grade)
3. O compositor imprime os metadados `arte-*` — cole no frontmatter da nota e o `![[arte/<slug>.png]]` no corpo.
4. **Abra a arte (Read)** e confira. Texto nítido e cor exata vêm do compositor; o fundo vem da IA.
5. **Envie pro Drive (automático · 1 pasta por post):** escreva a legenda final em `/tmp/legenda.txt` e rode:
   ```bash
   cd /Users/andreik/smark && bash scripts/to_drive.sh <MARCA> "<YYYY-MM-DD>-<slug>" \
     "marcas/<MARCA>/publicacoes/social/instagram/arte/<slug>.png" /tmp/legenda.txt
   ```
   → cai em `Smark — Posts/<MARCA>/<YYYY-MM-DD>-<slug>/` com **imagem + legenda juntas** (mini-projeto). Carrossel: passe vários PNGs no fim. Confirme o caminho ao usuário.
6. **Registre na planilha-índice** (controle + vínculo de tudo):
   ```bash
   cd /Users/andreik/smark && bash scripts/registrar.sh <MARCA> "<YYYY-MM-DD>-<slug>" "<HEADLINE>" "<slug>.png" draft
   ```
   → adiciona a linha (marca, datas, headline, imagem, status, link da pasta) em `controle-posts.csv` e sincroniza pra raiz do Drive.

**Formatos (ver [[shared/formatos-canais]]):** feed `--size 1080x1350` · story `--size 1080x1920` · anúncio `--cta "..."` · **carrossel** = N frames (capa com chip + `--page "01/0N"`; internos `--no-chip --page`), todos na pasta `arte/<slug>/` e subindo juntos pro Drive.

**Atalho (sem texto crítico / meme / estilo solto):** dá pra usar `scripts/openai_image.py` direto com o texto no prompt — mais rápido, porém o texto sai menos nítido. Prefira o pipeline de 2 camadas para peças finais.

## Regras invioláveis

- Sempre pt-BR.
- Nunca use palavras-proibidas listadas em `shared/voz-grupo.md`.
- Não gere arte/imagem — só briefing visual em texto.
- Se a marca não existir ou o briefing for vago demais (< 5 palavras), pergunte antes.
