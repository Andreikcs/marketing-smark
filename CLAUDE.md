# Smark Vault — Instruções do Claude Code

Este diretório é o **vault Obsidian do grupo Smark**, usado para gerar publicações sociais e materiais de marketing com contexto de marca consistente.

## Regras invioláveis

1. **Sempre escreva em pt-BR** (Brasil). Sem anglicismos desnecessários.
2. **Nunca use jargão financeiro vazio** ("alavancar", "sinergia", "exponencial sem dado", "transformação digital", "disrupção"). Veja `shared/voz-grupo.md` → palavras-proibidas.
3. **Marcas válidas:** `smark`, `provider-max`, `elever-ai`. Recuse a operação se receber slug diferente — peça correção.
4. **Tudo é markdown.** Saídas vão para arquivos `.md` com frontmatter YAML. Nunca gere HTML, JSON ou outros formatos como artefato principal.
5. **Voz herda do grupo.** Toda publicação começa lendo `shared/voz-grupo.md`. A marca específica refina, não substitui inteiramente.
6. **Arquivo único por post.** Cada publicação é UMA nota `.md` que embute a imagem (`![[arte/<slug>.png]]`) e traz metadados, legenda, hashtags e prompt juntos. **Nunca** crie ficha de metadados separada. O PNG fica em `.../arte/<slug>.png`; a nota é a fonte única.
7. **Imagem via script.** A arte é **pipeline de 2 camadas**: o FUNDO (sem texto) por `scripts/openai_image.py` e o TEXTO/moldura por `scripts/compositor.py` (HTML/CSS nítido a 2x). Tamanho por canal em `shared/formatos-canais.md`. Cor/estilo por `marcas/<marca>/branding/identidade-visual.md` (paleta ativa).
8. **Qualidade de fundo = direção de arte.** Todo fundo de IA usa a **direção estruturada nível agência** (`scripts/_direcao.py`: conceito por tipo + composição guiada pelo layout + cor estrita) via `openai_image.py --direcao`, e o compositor aplica a **grade de acabamento** (duotone+vinheta+grão, ligada por padrão). Regra completa em `shared/direcao-de-arte.md`. Nunca volte ao prompt genérico de uma linha.
9. **Tema-padrão = CLARO.** Toda arte sai **clara por default** (fundo branco/lavanda, texto escuro, acento roxo na palavra-chave). O compositor já assume `--tema claro`. **Só gere escuro** quando o usuário disser **"escuro", "dark", "roxo", "fundo escuro", "preto", "noturno"** ou qualquer coisa que remeta a **tons escuros** — aí passe `--tema escuro` (paleta secundária). Na dúvida, claro. Fonte: `design-system/tokens/tokens.json` → `tema_padrao`.
10. **Posicionamento = híbrido, alinhado ao SITE** (revisão 2026-07-04; o site `smarktech.com.br` é a fonte canônica e não muda — o resto do sistema se alinha a ele). **smark (mãe) = a assessoria que coloca um funcionário de IA em cada departamento** — headline oficial "Cada departamento pode ganhar um novo funcionário de IA · redução de custos, eficiência e escala". Duas portas: **o método** (diagnóstico gratuito / assessoria, cara = **Marta**, "a mãe de todos"; `marcas/smark/branding/metodo-maia.md`) e **o funcionário de IA** nomeado (**Nina**→Elever, **Clara**→Provider Max, **Téo**→prospecção; ver `marcas/smark/branding/funcionarios-ia.md`). A mãe **fronta os funcionários** como sua "seleção", conduzindo com método — não é mais "só método". **Camada estratégica** (ângulo + Filtro dos 3 Testes) em `marcas/smark/branding/estrategia.md`; fatos do site em `site-oficial.md`; dados em `shared/dados-mercado.md`. **Voz da vitrine social continua disciplinada:** sem jargão (tradutor DE→PARA em `shared/voz-grupo.md`), **nunca prometer venda/faturamento**, criança de 7 anos. **O SITE é exceção** — mantém a linguagem de conversão própria (SDR, "5× mais leads" etc.); o social não copia isso. Gate: `python3 scripts/revisar.py <post>` sinaliza jargão (⚠️) e bloqueia promessa de venda (❌).

## Arquitetura do vault

```
smark/
├── shared/             # DNA: voz-grupo, pilares-gerais, glossario, padroes-instagram,
│                       #       formatos-canais, calendario-conteudo, _templates/
├── marcas/<slug>/      # uma pasta por marca, autocontida
│   ├── branding/       # 7 notas: posicionamento, brand-voice, tom-de-voz, personas,
│   │                   #          pilares-de-conteudo, do-and-dont, identidade-visual
│   ├── referencias/    # swipe-file.md + notas por referência + inbox/
│   └── publicacoes/    # social/{instagram,linkedin}/{*.md + arte/*.png} + marketing/
├── scripts/            # gemini_image.py, openai_image.py, _sidecar.py
├── .claude/commands/   # post-instagram, post-linkedin, anuncio, campanha, nova-referencia, pauta
└── .env                # chaves de API (gitignored)
```

**Geração de conteúdo:** avulso (`/post-instagram`, `/post-linkedin`) ou em lote (`/pauta` = modo agência). Painel de produção em `shared/calendario-conteudo.md`.

## Precedência de contexto

**`shared/arquitetura-marca.md` é regra principal e SEMPRE se aplica** (lida antes de tudo): define que cada produto é "uma plataforma smark", o fio condutor do grupo e as cores oficiais. Produto nunca é gerado isolado da mãe.

Fora isso, quando há conflito, **o mais específico vence**:

```
arquitetura-marca (sempre)  ·  referências do briefing  >  branding da marca  >  shared/voz-grupo  >  CLAUDE.md
```

## Quando o usuário invoca um slash command

Cada slash command em `.claude/commands/` já especifica a ordem de carregamento. O padrão é:

1. Validar a marca (`smark`, `provider-max` ou `elever-ai`).
2. Ler **`shared/arquitetura-marca.md`** (regra principal) + `shared/voz-grupo.md` + `shared/pilares-gerais.md`.
3. Ler todos os arquivos em `marcas/<marca>/branding/`.
4. Buscar 3-5 referências relevantes em `marcas/<marca>/referencias/` por tags do briefing.
5. Ler as 3 últimas publicações do mesmo canal em `marcas/<marca>/publicacoes/<canal>/` para variar abertura/ângulo.
6. Gerar preview na conversa.
7. **Esperar confirmação do usuário antes de salvar.**
8. Ao confirmar, salvar com nome `YYYY-MM-DD-<slug>.md` no destino do canal, frontmatter completo, `status: draft`.

## Conversação livre (sem slash command)

Se o usuário pedir conteúdo sem usar slash command (ex: "cria um post sobre X"), pergunte qual marca antes de gerar. Não assuma Smark por padrão.

## Convenções de nome

- Slugs em `kebab-case` (`provider-max`, `churn-invisivel-isps`).
- Arquivos de publicação: `YYYY-MM-DD-<slug-curto>.md`.
- Referências: `<slug-curto>.md`, sem data no nome (a data está no frontmatter).

## Não-objetivos

- Não publicar automaticamente em redes sociais.
- Geração de imagem é **opcional e sob demanda**, via Gemini (`scripts/gemini_image.py`). O gerador sempre entrega o briefing visual em texto; a arte só é gerada quando o usuário pedir. Requer billing ativo no projeto Gemini.
- Não criar dashboards próprios — Obsidian + Dataview cobre.
- Versionado no GitHub: `Andreikcs/marketing-smark` (branch `main`). **Salvamento automático** via launchd (`com.smark.autosave`, roda `scripts/autosave.sh` a cada 5 min: commit+push só quando há mudança). `.env` e artes-draft ficam fora pelo `.gitignore`.
