# Plano de Eficiência — Sistema de Conteúdo Smark

## Camada de marca conectada + Compositor (FEITO em 2026-06-11)

- ✅ **`shared/arquitetura-marca.md`** — regra principal: modelo endossado "uma plataforma smark", fio condutor "IA que deixa marcos na operação", cores oficiais (PM lime, Elever roxo, smark lime). Lida primeiro por todos os comandos (CLAUDE.md precedência).
- ✅ Branding **Provider Max** e **Elever AI** atualizados (v2.0, novo posicionamento) + `herda-de: arquitetura-marca` + identidade-visual com endosso.
- ✅ **`scripts/compositor.py`** — motor de qualidade: fundo (IA) + tipografia real (HTML/CSS, Chrome headless 2x). Texto nítido, cor exata, selo automático.
- ✅ Comandos (`post-instagram`, `post-linkedin`, `pauta`) leem arquitetura-marca e usam o pipeline de 2 camadas.



Objetivo: o sistema deve **automatizar o dia a dia** e **substituir uma agência** para posts de Instagram e LinkedIn das 3 marcas, com engenharia de contexto preservada (cada peça rastreável, contexto conectado).

## Fase 0 — Fundamentos (FEITO em 2026-06-10)

- ✅ **Ficha de metadados por imagem** (`scripts/_sidecar.py`): toda arte gerada cria uma `.md` ao lado com marca, canal, formato, modelo, qualidade, tamanho, proporção, data de geração, paleta, headline, legenda e o **prompt usado**. Backfill das 3 artes existentes feito.
- ✅ **Integração das notas**: READMEs de marca agora linkam `identidade-visual` + sistema de geração; `voz-grupo` cruza com pilares/glossário/playbook. Grafo conectado.
- ✅ `.gitignore` mantém as fichas `.md` versionadas e ignora só os PNGs.

## Arquitetura arquivo-único (FEITO em 2026-06-10)

- ✅ Scripts **não criam ficha separada** — imprimem bloco de metadados pra embutir na nota.
- ✅ Cada post é **1 nota** que embute a imagem (`![[arte/<slug>.png]]`) + metadados `arte-*` + legenda + prompt. As 4 artes existentes consolidadas.

## Fase 1 — Paridade LinkedIn (FEITO)

- ✅ `/post-linkedin` reescrito com classificação, playbook, `identidade-visual`, geração de imagem (Passo 6) e nota única.

## Fase 2 — Presets de formato (FEITO)

- ✅ `shared/formatos-canais.md` — mapa canal/formato → `--size`. Comandos consultam.

## Fase 3 — Modo agência (FEITO)

- ✅ `shared/calendario-conteudo.md` — pauta + painel Dataview de produção.
- ✅ `/pauta <marca> <canal>` — sugere pauta e gera N posts em lote (texto + arte), fluxo híbrido.

## Fase 4 — Enriquecimento de contexto

- ✅ Swipe file consolidado em `marcas/smark/referencias/swipe-file.md` (3 contas + 9 marcas, com tags).
- ⏳ Fixar **hex oficiais** (pendente do usuário).
- ⏳ Completar branding da **Elever AI** (pendente do usuário).

## Pendências de segurança

- 🔐 Rotacionar as chaves Gemini e OpenAI (foram coladas em texto aberto).
- Billing Gemini em pós-pagamento (se quiser usar o gerador barato pra fundos).
