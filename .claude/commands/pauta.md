---
description: Modo agência — sugere uma pauta e gera vários posts em lote (texto + arte) numa marca/canal
argument-hint: <marca> <canal> [quantidade] [temas opcionais]
---

Modo agência: planejar e produzir conteúdo em lote. Argumentos: `$ARGUMENTS`.

## Passo 1 — Parsear

Primeiro token = marca (`smark|provider-max|elever-ai`). Segundo = canal (`instagram|linkedin`). Terceiro (opcional) = quantidade (default 5). O resto, se houver, são temas que o usuário já quer.

Marca/canal inválidos → pergunte.

## Passo 2 — Carregar contexto (uma vez)

Leia: **`shared/arquitetura-marca.md`** (regra principal), `shared/voz-grupo.md`, `shared/pilares-gerais.md`, `shared/glossario.md`, `shared/padroes-instagram.md`, `shared/formatos-canais.md`, todos os `branding/*.md` da marca (incl. `identidade-visual.md`), e as últimas publicações do canal (variar ângulos).

Arte (se pedida) usa o pipeline de 2 camadas com **direção de arte** (`shared/direcao-de-arte.md`): fundo via `scripts/openai_image.py --direcao --tipo <tipo> --tema <...>` + composição via `scripts/compositor.py` (texto nítido, grade de acabamento automática, selo "uma plataforma smark"). **Tema-padrão = CLARO.** Gere a arte clara por default (o compositor já assume `--tema claro`) — mire ~70% claro / 30% escuro no lote. Só use `--tema escuro` quando o usuário pedir explicitamente com palavras como **"escuro", "dark", "roxo", "fundo escuro", "preto", "noturno"** ou algo que remeta a tons escuros. Na dúvida, claro.

## Passo 3 — Propor a PAUTA (não gerar ainda)

Monte uma tabela com `quantidade` linhas, distribuindo entre os **pilares** da marca e variando formato/hook:

| # | Tema | Pilar | Formato | Hook (rascunho) |

Se o usuário deu temas, use-os primeiro e complete o resto. **Mostre a pauta e pergunte:** "Aprova a pauta? Quer trocar algum tema?"

## Passo 4 — Gerar em lote (após aprovação)

Para CADA item aprovado, execute o fluxo do post (igual `/post-instagram` ou `/post-linkedin`):
1. Classifique → escolha formato/visual.
2. Escreva legenda + hook (varie entre os itens — nada repetido).
3. Se o usuário pediu arte, gere a imagem (script) e **embuta na nota única** (frontmatter `arte-*` + `![[arte/<slug>.png]]`).
4. Salve a **nota única** em `.../publicacoes/social/<canal>/<YYYY-MM-DD>-<slug>.md`, `status: draft`.
5. **Envie pro Drive + registre (1 pasta por post):** se gerou arte, legenda em `/tmp/legenda.txt`, então `bash scripts/to_drive.sh <MARCA> "<YYYY-MM-DD>-<slug>" <imagem> /tmp/legenda.txt` e `bash scripts/registrar.sh <MARCA> "<YYYY-MM-DD>-<slug>" "<HEADLINE>" "<slug>.png" draft`. Cada peça vira sua pasta + 1 linha na planilha.

Trabalhe um item por vez, mas **sem pausar pra confirmar cada um** — gere o lote todo e só então apresente o resumo.

## Passo 5 — Resumo + atualizar calendário

Liste os arquivos criados (link + tema + formato). Acrescente as linhas na pauta de `shared/calendario-conteudo.md`.

Pergunte ao usuário quais quer **revisar/ajustar** (mude status pra `revisado` quando aprovar).

## Regras invioláveis

- Sempre pt-BR. Linha vermelha (playbook seção 5) em cada peça. Nota = arquivo único.
- Não publica em rede social. Não inventa dado (marcar como exemplo).
- Custo de imagem: avise o total estimado antes de gerar arte em lote (≈ R$0,70/imagem alta).
