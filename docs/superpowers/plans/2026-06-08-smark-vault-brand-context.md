# Smark Vault — Brand Context System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar workspace local `/Users/andreik/smark/` como vault Obsidian multi-marca (Smark + Provider Max + Elever AI) com slash commands do Claude Code para geração de publicações sociais e materiais de marketing.

**Architecture:** Vault Obsidian onde `smark/` é a raiz. Estrutura: `shared/` (DNA Smark + templates), `marcas/<slug>/` (branding, referências, publicações isoladas por marca), `.claude/commands/` (5 slash commands customizados). Todo conteúdo é markdown com frontmatter rigoroso. Claude Code lê camadas de contexto em ordem de precedência (referências → branding da marca → shared → CLAUDE.md). Sem código executável, sem testes unitários — verificação por inspeção de estrutura + smoke test end-to-end.

**Tech Stack:** Markdown + YAML frontmatter, Obsidian (vault), Claude Code (slash commands em `.claude/commands/*.md`), nenhuma dependência de runtime.

**Nota de versionamento:** git diferido conforme spec seção 11. Tasks usam "Verify" no lugar de "Commit".

---

## File Structure

**Pastas a criar:**
```
/Users/andreik/smark/
├── CLAUDE.md
├── .claude/commands/{post-instagram,post-linkedin,anuncio,campanha,nova-referencia}.md
├── shared/
│   ├── voz-grupo.md
│   ├── pilares-gerais.md
│   ├── glossario.md
│   └── _templates/{publicacao,referencia,brand-voice}.md
├── marcas/
│   ├── smark/
│   │   ├── README.md
│   │   ├── branding/{posicionamento,brand-voice,tom-de-voz,personas,pilares-de-conteudo,do-and-dont}.md
│   │   ├── branding/source/branding.pdf  (movido do legado)
│   │   ├── referencias/inbox/
│   │   └── publicacoes/{social/{instagram,linkedin},marketing/{anuncios,campanhas}}/
│   ├── provider-max/  (mesma estrutura, sem source/branding.pdf)
│   └── elever-ai/     (mesma estrutura, sem source/branding.pdf)
└── docs/superpowers/{specs,plans}/

# Pastas a remover (legadas, vazias após mover PDF):
/Users/andreik/smark/branding/
/Users/andreik/smark/publicacoes/
/Users/andreik/smark/referencias/
```

**Responsabilidades por arquivo:**
- `CLAUDE.md` — instruções raiz, sempre carregadas pelo Claude Code. Define vault multi-marca, idioma, regras de tom transversais, lista as marcas válidas, descreve precedência de contexto.
- `shared/voz-grupo.md` — DNA Smark transversal a todas as marcas.
- `shared/pilares-gerais.md` — pilares de mensagem que o grupo todo defende.
- `shared/glossario.md` — termos consistentes entre marcas (evita explosão de tags).
- `shared/_templates/*.md` — esqueletos com frontmatter usados por slash commands e criação manual.
- `marcas/<slug>/branding/*.md` — 6 notas estruturadas que definem a marca específica.
- `marcas/<slug>/referencias/` — uma nota por referência + `inbox/` para originais.
- `marcas/<slug>/publicacoes/` — uma nota por publicação, organizadas por canal.
- `.claude/commands/*.md` — instruções para o Claude executar cada comando.

---

### Task 1: Limpar legado e criar scaffold de pastas

**Files:**
- Move: `/Users/andreik/smark/branding/branding.pdf` → `/Users/andreik/smark/marcas/smark/branding/source/branding.pdf`
- Delete: `/Users/andreik/smark/branding/`, `/Users/andreik/smark/publicacoes/`, `/Users/andreik/smark/referencias/`, `/Users/andreik/smark/.DS_Store`
- Create dirs: estrutura completa acima

- [ ] **Step 1: Verificar estado atual**

Run: `ls -la /Users/andreik/smark/`
Expected: 3 pastas legadas (`branding/`, `publicacoes/`, `referencias/`) e `docs/` já criado pelo brainstorming.

- [ ] **Step 2: Criar pastas-mãe novas**

```bash
mkdir -p /Users/andreik/smark/.claude/commands
mkdir -p /Users/andreik/smark/shared/_templates
mkdir -p /Users/andreik/smark/marcas/smark/branding/source
mkdir -p /Users/andreik/smark/marcas/smark/referencias/inbox
mkdir -p /Users/andreik/smark/marcas/smark/publicacoes/social/instagram
mkdir -p /Users/andreik/smark/marcas/smark/publicacoes/social/linkedin
mkdir -p /Users/andreik/smark/marcas/smark/publicacoes/marketing/anuncios
mkdir -p /Users/andreik/smark/marcas/smark/publicacoes/marketing/campanhas
mkdir -p /Users/andreik/smark/marcas/provider-max/branding/source
mkdir -p /Users/andreik/smark/marcas/provider-max/referencias/inbox
mkdir -p /Users/andreik/smark/marcas/provider-max/publicacoes/social/instagram
mkdir -p /Users/andreik/smark/marcas/provider-max/publicacoes/social/linkedin
mkdir -p /Users/andreik/smark/marcas/provider-max/publicacoes/marketing/anuncios
mkdir -p /Users/andreik/smark/marcas/provider-max/publicacoes/marketing/campanhas
mkdir -p /Users/andreik/smark/marcas/elever-ai/branding/source
mkdir -p /Users/andreik/smark/marcas/elever-ai/referencias/inbox
mkdir -p /Users/andreik/smark/marcas/elever-ai/publicacoes/social/instagram
mkdir -p /Users/andreik/smark/marcas/elever-ai/publicacoes/social/linkedin
mkdir -p /Users/andreik/smark/marcas/elever-ai/publicacoes/marketing/anuncios
mkdir -p /Users/andreik/smark/marcas/elever-ai/publicacoes/marketing/campanhas
```

- [ ] **Step 3: Mover PDF para o branding da Smark**

```bash
mv /Users/andreik/smark/branding/branding.pdf /Users/andreik/smark/marcas/smark/branding/source/branding.pdf
```
Expected: arquivo agora em `marcas/smark/branding/source/branding.pdf`.

- [ ] **Step 4: Remover pastas legadas vazias e .DS_Store**

```bash
rmdir /Users/andreik/smark/branding /Users/andreik/smark/publicacoes /Users/andreik/smark/referencias
rm -f /Users/andreik/smark/.DS_Store
```

- [ ] **Step 5: Verificar estrutura final**

Run: `find /Users/andreik/smark -type d -not -path '*/.*' | sort`
Expected (subset, abreviado):
```
/Users/andreik/smark
/Users/andreik/smark/.claude
/Users/andreik/smark/.claude/commands
/Users/andreik/smark/docs
/Users/andreik/smark/marcas
/Users/andreik/smark/marcas/elever-ai
/Users/andreik/smark/marcas/elever-ai/branding
/Users/andreik/smark/marcas/elever-ai/branding/source
/Users/andreik/smark/marcas/elever-ai/publicacoes
... (etc, 3 marcas espelhadas)
/Users/andreik/smark/shared
/Users/andreik/smark/shared/_templates
```
E: `ls /Users/andreik/smark/marcas/smark/branding/source/` → `branding.pdf`.

---

### Task 2: Criar `shared/voz-grupo.md` (DNA Smark)

**Files:**
- Create: `/Users/andreik/smark/shared/voz-grupo.md`

- [ ] **Step 1: Criar voz-grupo.md**

```markdown
---
tipo: brand-voice-grupo
escopo: todas-as-marcas
versao: 1.0
atualizado: 2026-06-08
---

# Voz do Grupo Smark

DNA transversal a todas as marcas do grupo (Smark, Provider Max, Elever AI). Cada marca pode refinar ou sobrescrever em seu `branding/tom-de-voz.md`, mas o ponto de partida é este.

## Posicionamento de grupo

Tecnologia que deixa marcos. Resolver problema real de operação com tecnologia, automação e capacitação — não vender promessa.

## Pilares de tom

1. **Próximo, não corporativo.** "É um papo, não um formulário." Falamos como gente, não como release.
2. **Direto, sem jargão financeiro.** Métricas de vaidade não entram. "ROI" só quando faz sentido prático.
3. **Honesto sobre limitações.** "Nenhum sistema vai resolver tudo. Nunca." Confiabilidade vem de não prometer demais.
4. **Operacional, não estratégico-abstrato.** Falamos de dor concreta de quem opera, não de transformação digital.
5. **Quatro sócios que atendem o telefone.** Acessibilidade real é parte da marca.

## Palavras-marca (preferir)

- "deixar marcos", "marco", "marcar"
- "papo", "conversa"
- "operação", "operar", "rodar"
- "dor", "problema real"
- "resolver", "destravar"
- "parceiro técnico"

## Palavras-proibidas

- "transformação digital" (clichê vazio)
- "disruptivo", "disrupção"
- "alavancar", "alavancagem"
- "sinergia"
- "best-in-class", "world-class"
- "métricas vaidosas" (mencionar só pra rejeitar)
- "exponencial" (a menos que seja literal)
- "revolucionar"

## Sinais de que a voz está certa

- Um operador leria e pensaria "isso é pra mim", não "isso é pra meu diretor".
- Se trocássemos o logo, soaria estranho atribuir a uma big tech genérica.
- Não tem nenhuma frase que poderia estar num pitch deck de qualquer startup.

## Sinais de que escorregou

- Uso de buzzword sem aterramento concreto.
- Promessa absoluta ("resolve tudo", "elimina X 100%").
- Tom de palestrante de evento.
- Frases longas demais para um post — se passou de 3 linhas no Instagram, repensar.
```

- [ ] **Step 2: Verify**

Run: `head -5 /Users/andreik/smark/shared/voz-grupo.md`
Expected: começa com `---` e contém `tipo: brand-voice-grupo`.

---

### Task 3: Criar `shared/pilares-gerais.md`

**Files:**
- Create: `/Users/andreik/smark/shared/pilares-gerais.md`

- [ ] **Step 1: Criar pilares-gerais.md**

```markdown
---
tipo: pilares-de-mensagem-grupo
escopo: todas-as-marcas
versao: 1.0
atualizado: 2026-06-08
---

# Pilares Gerais de Mensagem — Grupo Smark

Temas que toda marca do grupo pode (e deve) tocar. Cada marca adapta com seu próprio recorte.

## Pilar 1 — Tecnologia que deixa marco

A tecnologia entrega valor quando muda algo mensurável na operação. Não é sobre estar "atualizado" — é sobre resolver dor.

**Ângulos típicos:**
- Antes/depois operacional concreto
- Métrica que mudou (sem inflar)
- O que a empresa parou de fazer (manual, retrabalho, planilha)

## Pilar 2 — Diagnóstico antes de venda

A gente investiga antes de propor. Vender antes de entender é falta de respeito com o orçamento do cliente.

**Ângulos típicos:**
- O que um diagnóstico real revela
- Por que "implantar sistema" sem mapa dá errado
- Casos onde a recomendação foi "não compre nada agora"

## Pilar 3 — Capacitação > dependência

Treinamos o time do cliente. Não queremos dependência permanente, queremos parceria que dispensa muleta.

**Ângulos típicos:**
- Time interno aprendendo a operar IA / automação
- Por que terceirizar tudo enfraquece a empresa
- Como medir autonomia conquistada

## Pilar 4 — Honestidade sobre limitação

Nenhuma ferramenta resolve tudo. Falamos o que ela faz, o que não faz, e o que precisa do humano.

**Ângulos típicos:**
- O que IA não vai resolver
- Quando uma planilha bem feita ainda vence sistema
- Por que projetos falham (e quem mais erra)

## Pilar 5 — Operação como protagonista

Não falamos com "C-suite estratégico" — falamos com quem opera. Gerente de relacionamento, head de comercial, supervisor de SAC.

**Ângulos típicos:**
- Dia-a-dia que melhora
- Decisão de operação que dependia de quem
- Histórias de operador que virou referência
```

- [ ] **Step 2: Verify**

Run: `grep -c "## Pilar" /Users/andreik/smark/shared/pilares-gerais.md`
Expected: `5`.

---

### Task 4: Criar `shared/glossario.md`

**Files:**
- Create: `/Users/andreik/smark/shared/glossario.md`

- [ ] **Step 1: Criar glossario.md**

```markdown
---
tipo: glossario-grupo
escopo: todas-as-marcas
versao: 1.0
atualizado: 2026-06-08
---

# Glossário Smark

Padroniza termos usados em referências, publicações e tags. Evita duplicação (`tom-direto` vs `direto` vs `tom_direto`).

## Tags de tom (frontmatter `tags:` em referências)

- `tom-proximo` — fala como gente, não como release
- `tom-ironico` — usa humor ácido, geralmente em redes sociais
- `tom-tecnico` — assume conhecimento técnico do leitor
- `tom-direto` — sem rodeios, hook seco
- `tom-narrativo` — começa contando história
- `tom-confessional` — admite erro/dificuldade da própria empresa

## Tags de estrutura

- `copy-curto` — funciona com menos de 80 palavras
- `copy-longo` — 200+ palavras, exige investimento de leitura
- `carrossel` — peça em frames
- `hook-pergunta` — abre com pergunta
- `hook-afirmacao-polemica` — abre tomando posição
- `hook-numero` — abre com estatística/dado

## Tags de visual

- `visual-minimalista` — pouca informação na arte
- `visual-denso` — bastante texto na peça
- `visual-foto-real` — foto crua, não ilustração
- `visual-ilustracao` — desenho/grafismo
- `visual-cor-dominante` — cor única forte
- `visual-tipografico` — tipografia é o destaque

## Tags de objetivo

- `obj-awareness` — apresentar quem somos / o que fazemos
- `obj-educacao` — ensinar conceito que prepara venda
- `obj-conversao` — fala direta de produto/serviço
- `obj-recrutamento` — atrai talento
- `obj-comunidade` — conversa com base existente

## Tags de produto (sub-marcas)

- `produto-providermax`, `produto-eleverai`, `servico-consultoria`, `servico-sistemas-sob-medida`, `servico-treinamento`

## Status de publicação (frontmatter `status:`)

- `draft` — gerado, ainda não revisado
- `revisado` — passou pelo usuário, pronto pra arte/agendamento
- `aprovado` — arte pronta, agendado
- `publicado` — no ar, frontmatter recebe `url-publicado`
- `arquivado` — não usado, mantido pra histórico
```

- [ ] **Step 2: Verify**

Run: `grep -c "^## " /Users/andreik/smark/shared/glossario.md`
Expected: `6` (6 seções `##`).

---

### Task 5: Criar templates em `shared/_templates/`

**Files:**
- Create: `/Users/andreik/smark/shared/_templates/publicacao.md`
- Create: `/Users/andreik/smark/shared/_templates/referencia.md`
- Create: `/Users/andreik/smark/shared/_templates/brand-voice.md`

- [ ] **Step 1: Criar `_templates/publicacao.md`**

```markdown
---
marca: <smark|provider-max|elever-ai>
canal: <instagram|linkedin|anuncio|campanha>
formato: <post|carrossel|reels|headline-ad>
status: draft
data: YYYY-MM-DD
tags: []
referencias-usadas: []
pilares: []
url-publicado:
---

# <Título descritivo curto>

## Briefing original
<o que o usuário pediu, verbatim>

## Ângulo escolhido
<por que esse ângulo, qual insight guiou>

## Conteúdo

### Versão final
<copy/peça final pronta pra publicar>

### Variações (se aplicável)
<A/B/C quando o canal pede variação>

## Briefing visual
<descrição pra designer ou IA de imagem: composição, cor dominante, elementos, persona representada>

## Notas de decisão
<o que considerei e descartei, qual referência inspirou, ajustes feitos durante iteração>
```

- [ ] **Step 2: Criar `_templates/referencia.md`**

```markdown
---
marca: <smark|provider-max|elever-ai>
tipo: <post|anuncio|artigo|video|site|email>
fonte: <url ou "screenshot manual" ou "captura tela">
data-salvo: YYYY-MM-DD
tags: []
aplicabilidade: <alta|media|baixa>
arquivo-original:
---

# <Identificador curto: ex. "Magalu - post Black Friday ironico">

## Por que salvei
<1-2 frases — o gatilho da inclusão>

## O que extrair

- **Tom:** <descrição curta + 1 exemplo trecho>
- **Estrutura:** <como abre, desenvolve, fecha>
- **Visual:** <cor, tipografia, composição, peso de texto>
- **Copy-chave:** <trechos memoráveis transcritos>
- **CTA:** <verbo + benefício usados>

## Como aplicar na <marca>
<adaptação contextual ao tom da marca alvo>

## O que evitar
<armadilhas se imitar mal: o que NÃO copiar>
```

- [ ] **Step 3: Criar `_templates/brand-voice.md`**

```markdown
---
marca: <slug>
tipo: brand-voice-marca
versao: 1.0
atualizado: YYYY-MM-DD
fonte-extracao: <branding.pdf | site | conversa>
---

# Brand Voice — <Nome da marca>

## Posicionamento em uma frase
<descrição curta e clara>

## Missão
<por que essa marca existe>

## Personas (mínimo 2)

### Persona 1: <nome/cargo>
- Contexto: <empresa, setor, porte>
- Dor principal: <o que tira o sono>
- Linguagem: <como ela mesma fala — gírias, jargão, neutralidade>
- O que essa persona NÃO quer ouvir

### Persona 2: <nome/cargo>
... (mesmo formato)

## Pilares de conteúdo (3-5)

1. **<Pilar>** — <descrição + tipo de conteúdo que cabe>
2. **<Pilar>** — ...
3. **<Pilar>** — ...

## Tom de voz — 5 atributos

| Atributo | Definição | Exemplo correto | Exemplo errado |
|---|---|---|---|
| <ex: Direto> | <como se manifesta> | <"frase boa"> | <"frase ruim"> |
| ... | ... | ... | ... |

## Palavras-marca
<termos que reforçam a identidade — usar com frequência>

## Palavras-proibidas
<termos que NÃO usamos — clichês, jargões, promessas>

## Exemplos canônicos
<3 peças aprovadas que servem de referência — link interno [[...]]>
```

- [ ] **Step 4: Verify**

Run: `ls /Users/andreik/smark/shared/_templates/`
Expected: `brand-voice.md  publicacao.md  referencia.md`.

---

### Task 6: Criar `CLAUDE.md` raiz

**Files:**
- Create: `/Users/andreik/smark/CLAUDE.md`

- [ ] **Step 1: Criar CLAUDE.md**

```markdown
# Smark Vault — Instruções do Claude Code

Este diretório é o **vault Obsidian do grupo Smark**, usado para gerar publicações sociais e materiais de marketing com contexto de marca consistente.

## Regras invioláveis

1. **Sempre escreva em pt-BR** (Brasil). Sem anglicismos desnecessários.
2. **Nunca use jargão financeiro vazio** ("alavancar", "sinergia", "exponencial sem dado", "transformação digital", "disrupção"). Veja `shared/voz-grupo.md` → palavras-proibidas.
3. **Marcas válidas:** `smark`, `provider-max`, `elever-ai`. Recuse a operação se receber slug diferente — peça correção.
4. **Tudo é markdown.** Saídas vão para arquivos `.md` com frontmatter YAML. Nunca gere HTML, JSON ou outros formatos como artefato principal.
5. **Voz herda do grupo.** Toda publicação começa lendo `shared/voz-grupo.md`. A marca específica refina, não substitui inteiramente.

## Arquitetura do vault

```
smark/
├── shared/             # DNA Smark (voz, pilares, glossário, templates)
├── marcas/<slug>/      # uma pasta por marca, autocontida
│   ├── branding/       # 6 notas que definem a marca
│   ├── referencias/    # uma nota por referência + inbox/
│   └── publicacoes/    # social/{instagram,linkedin} + marketing/{anuncios,campanhas}
└── .claude/commands/   # slash commands customizados
```

## Precedência de contexto

Quando há conflito entre fontes, **o mais específico vence**:

```
referências do briefing  >  branding da marca  >  shared/voz-grupo  >  CLAUDE.md
```

## Quando o usuário invoca um slash command

Cada slash command em `.claude/commands/` já especifica a ordem de carregamento. O padrão é:

1. Validar a marca (`smark`, `provider-max` ou `elever-ai`).
2. Ler `shared/voz-grupo.md` + `shared/pilares-gerais.md`.
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
- Não gerar imagens — apenas briefing visual em texto.
- Não criar dashboards próprios — Obsidian + Dataview cobre.
- Não versionar com git nesta fase (diferido).
```

- [ ] **Step 2: Verify**

Run: `grep -c "^## " /Users/andreik/smark/CLAUDE.md`
Expected: `7` (Regras invioláveis, Arquitetura, Precedência, Quando o usuário invoca, Conversação livre, Convenções, Não-objetivos).

---

### Task 7: Extrair branding da Smark do PDF

**Files:**
- Read: `/Users/andreik/smark/marcas/smark/branding/source/branding.pdf`
- Create: `/Users/andreik/smark/marcas/smark/branding/posicionamento.md`
- Create: `/Users/andreik/smark/marcas/smark/branding/brand-voice.md`
- Create: `/Users/andreik/smark/marcas/smark/branding/tom-de-voz.md`
- Create: `/Users/andreik/smark/marcas/smark/branding/personas.md`
- Create: `/Users/andreik/smark/marcas/smark/branding/pilares-de-conteudo.md`
- Create: `/Users/andreik/smark/marcas/smark/branding/do-and-dont.md`
- Create: `/Users/andreik/smark/marcas/smark/README.md`

- [ ] **Step 1: Ler o PDF**

Use the Read tool with `file_path: /Users/andreik/smark/marcas/smark/branding/source/branding.pdf` and `pages: "1-20"` se o PDF tiver muitas páginas. Se exceder, ler em ranges adicionais.

Expected: conteúdo do PDF visível para extração.

- [ ] **Step 2: Criar `posicionamento.md`**

Estrutura base (preencher com extração do PDF, mantendo essa estrutura mínima — se o PDF for ambíguo ou faltar dado, **deixar marcador explícito `<<COMPLETAR COM USUÁRIO>>` no campo, nunca inventar**):

```markdown
---
marca: smark
tipo: posicionamento
versao: 1.0
atualizado: 2026-06-08
fonte-extracao: branding.pdf + site smarktech.com.br
---

# Posicionamento — Smark

## Em uma frase
<extrair do PDF; fallback do site: "Consultoria tecnológica operacional — parceiro técnico que resolve problemas reais de operação via tecnologia, automação e capacitação.">

## Categoria
Consultoria tecnológica + SaaS próprios. Não é McKinsey, não é SaaS puro — é assessoria operacional com produtos próprios como prova de capacidade.

## Promessa central
"Tecnologia que deixa marcos." Impacto prático e mensurável, não teoria.

## Diferenciais
<extrair do PDF; fallback: "Quatro sócios que atendem o telefone. Diagnóstico antes de venda. Honestidade sobre limitações. Capacitação do time interno em vez de dependência permanente.">

## O que NÃO somos
- Não somos consultoria estratégica abstrata
- Não somos software house genérica
- Não vendemos transformação digital de palco

## Produtos / serviços
- **Sistemas Internos Sob Medida** (ERPs/dashboards customizados)
- **Assessoria Tecnológica** (diagnóstico, auditoria, seleção de fornecedores)
- **Treinamento Corporativo** (IA, automação, inteligência de dados)
- **Provider Max** (SaaS — inteligência comercial para ISPs)
- **Elever AI** (SaaS — IA para vendas inbound)
```

- [ ] **Step 3: Criar `brand-voice.md`**

Use o template `shared/_templates/brand-voice.md` como esqueleto. Preencher com dados do PDF. Onde o PDF não cobre, usar fallback do site Smark (já analisado). Marcadores `<<COMPLETAR COM USUÁRIO>>` permitidos.

Conteúdo mínimo obrigatório:
- Posicionamento (1 frase)
- 2 personas (operador da empresa cliente + decisor operacional)
- 3-5 pilares de conteúdo (alinhar com `shared/pilares-gerais.md`)
- 5 atributos de tom de voz com exemplos do/don't
- Palavras-marca e palavras-proibidas (herdar de `shared/voz-grupo.md` + adicionar específicas Smark)
- 3 exemplos canônicos (extrair do PDF se houver; senão `<<COMPLETAR>>`)

- [ ] **Step 4: Criar `tom-de-voz.md`**

```markdown
---
marca: smark
tipo: tom-de-voz
versao: 1.0
atualizado: 2026-06-08
herda-de: [[shared/voz-grupo]]
---

# Tom de Voz — Smark

A Smark herda inteiro o tom do grupo (ver `[[shared/voz-grupo]]`). Refinamentos específicos abaixo.

## Voltagem do tom (escala 1-5)

| Eixo | Valor | Nota |
|---|---|---|
| Próximo ↔ Formal | 2 | Próximo, mas adulto. Não é informalidade de stories. |
| Sério ↔ Bem-humorado | 3 | Humor seco quando cabe. Não é tom de meme. |
| Técnico ↔ Genérico | 4 | Técnico quando preciso, traduzido sempre que possível. |
| Cauteloso ↔ Provocativo | 3 | Posiciona-se com clareza, mas sem tom de polêmica gratuita. |

## Frases de assinatura

- "Tecnologia que deixa marcos."
- "É um papo, não um formulário."
- "Quatro sócios que atendem o telefone."
- "Nenhum sistema vai resolver tudo. Nunca."

## Como abrir um post

- Pergunta direta voltada ao operador
- Afirmação contraintuitiva sobre operação
- Cena/situação observada de campo

## Como fechar

- Convite ao papo (não a formulário)
- Pergunta aberta que devolve a palavra
- Posição sem call-to-action agressivo
```

- [ ] **Step 5: Criar `personas.md`**

```markdown
---
marca: smark
tipo: personas
versao: 1.0
atualizado: 2026-06-08
---

# Personas — Smark

## Persona 1: Operador-decisor

- **Cargo típico:** Head de operações, gerente de relacionamento, supervisor de SAC, líder de comercial.
- **Empresa:** média/grande, 50-500 funcionários, operação complexa.
- **Dor:** processo manual virou gargalo; planilha não escala; ferramenta atual não conversa com nada.
- **O que quer ouvir:** "isso resolve essa dor específica e a gente capacita seu time".
- **O que NÃO quer ouvir:** "transformação digital", "transformar a cultura", "revolucionar a empresa".
- **Linguagem própria:** prática, com vocabulário do setor dele (ISP, SAC, NPS, churn).

## Persona 2: Diretor operacional pragmático

- **Cargo típico:** Diretor de operações, COO de empresa média.
- **Empresa:** olha o todo, prioriza por ROI claro.
- **Dor:** orçamento limitado; equipe pequena pra muito projeto; cansado de fornecedor que sumiu pós-implantação.
- **O que quer ouvir:** "vamos diagnosticar antes de propor", "a gente treina seu time pra reduzir dependência".
- **O que NÃO quer ouvir:** "best-in-class", "alavancagem", "líderes do setor".
- **Linguagem própria:** ROI concreto, prazos, riscos.

<<COMPLETAR COM USUÁRIO se o PDF identificar personas específicas adicionais>>
```

- [ ] **Step 6: Criar `pilares-de-conteudo.md`**

```markdown
---
marca: smark
tipo: pilares-de-conteudo
versao: 1.0
atualizado: 2026-06-08
herda-de: [[shared/pilares-gerais]]
---

# Pilares de Conteúdo — Smark

Smark adota inteiros os 5 pilares do grupo (`[[shared/pilares-gerais]]`). Refinamentos por canal abaixo.

## Distribuição sugerida (Instagram + LinkedIn)

| Pilar | % do mix | Formato dominante |
|---|---|---|
| Tecnologia que deixa marco | 25% | Carrossel antes/depois |
| Diagnóstico antes de venda | 20% | Post-narrativa |
| Capacitação > dependência | 20% | Post-educativo + carrossel |
| Honestidade sobre limitação | 15% | Post curto-provocativo |
| Operação como protagonista | 20% | Post-narrativa + reels |

## Para marketing/anúncios

Anúncios da Smark priorizam pilares 1, 2 e 3. Pilar 4 raramente cabe em anúncio (muito reflexivo). Pilar 5 cabe em campanhas longas.

<<COMPLETAR COM USUÁRIO: ajustar % conforme realidade de produção>>
```

- [ ] **Step 7: Criar `do-and-dont.md`**

```markdown
---
marca: smark
tipo: do-and-dont
versao: 1.0
atualizado: 2026-06-08
---

# Do & Don't — Smark

## Sempre

- Falar com nome de cargo operacional ("gerente de relacionamento", "supervisor de SAC"), não C-suite genérico.
- Citar dor concreta antes de apresentar solução.
- Quando usar número, citar a fonte ou marcar como exemplo ("um cliente nosso reduziu X em Y").
- Reconhecer limitação do que vendemos.
- Linkar pra pilares quando o post se encaixa em mais de um.

## Nunca

- Promessa absoluta ("zero erro", "100% automatizado").
- Tom de evangelista de IA / palestra TED.
- Anglicismo sem necessidade ("delivery", "framework", "rollout") quando há equivalente claro em pt-BR.
- Citação genérica de "líderes da indústria" sem nome.
- Hashtag spam (Instagram: 5-8 hashtags relevantes; LinkedIn: 3-5).
- Emoji por emoji — só quando funcional (separador, indicador).

## Em caso de dúvida

Se perguntar "isso a Magalu/Nubank poderia ter postado igual"? Sim → repensar, está genérico. Não → provavelmente está com voz Smark.
```

- [ ] **Step 8: Criar `marcas/smark/README.md`**

```markdown
# Smark — marca-mãe

Consultoria tecnológica do grupo. Marca-mãe; Provider Max e Elever AI são SaaS próprios sob este guarda-chuva.

## Mapa rápido

- [[branding/posicionamento]]
- [[branding/brand-voice]]
- [[branding/tom-de-voz]]
- [[branding/personas]]
- [[branding/pilares-de-conteudo]]
- [[branding/do-and-dont]]

## Fonte original

`branding/source/branding.pdf` — extração inicial feita em 2026-06-08. Notas acima foram derivadas do PDF + análise do site smarktech.com.br.
```

- [ ] **Step 9: Verify**

Run: `ls /Users/andreik/smark/marcas/smark/branding/*.md`
Expected: 6 arquivos `.md` listados.

Run: `head -5 /Users/andreik/smark/marcas/smark/branding/posicionamento.md`
Expected: começa com frontmatter `marca: smark`.

---

### Task 8: Criar drafts de branding da Provider Max

**Files:**
- Create: `/Users/andreik/smark/marcas/provider-max/branding/posicionamento.md`
- Create: `/Users/andreik/smark/marcas/provider-max/branding/brand-voice.md`
- Create: `/Users/andreik/smark/marcas/provider-max/branding/tom-de-voz.md`
- Create: `/Users/andreik/smark/marcas/provider-max/branding/personas.md`
- Create: `/Users/andreik/smark/marcas/provider-max/branding/pilares-de-conteudo.md`
- Create: `/Users/andreik/smark/marcas/provider-max/branding/do-and-dont.md`
- Create: `/Users/andreik/smark/marcas/provider-max/README.md`

Drafts baseados na análise do site `max.smarktech.com.br`. Onde faltar dado, marcar `<<COMPLETAR COM USUÁRIO>>`.

- [ ] **Step 1: Criar `posicionamento.md`**

```markdown
---
marca: provider-max
tipo: posicionamento
versao: 0.1-draft
atualizado: 2026-06-08
fonte-extracao: site max.smarktech.com.br
status-extracao: draft-inicial — completar com usuário
---

# Posicionamento — Provider Max

## Em uma frase
Plataforma de inteligência comercial que automatiza retenção e upgrade de clientes para provedores de internet (ISPs).

## Categoria
SaaS B2B vertical para ISPs. Integração nativa com ERPs do setor (IXC Provedor).

## Promessa central
"O dinheiro estava aí — a Provider Max te ajuda a não deixar escapar."

## Diferenciais
- Agentes autônomos que atuam em renovações e upgrades sem operador clicar.
- Integração nativa com IXC sem retrabalho.
- ROI mensurável em 60-90 dias.
- Operação comercial rastreada em tempo real (Dashboard Executivo).

## O que NÃO somos
- Não somos CRM genérico.
- Não somos discador / contact center.
- Não substituímos o time comercial — potencializamos.

## Produtos do SaaS
- **Gestor de Renovações** — antecipa contrato antes da concorrência agir.
- **Gestor de Upgrades** — identifica e oferta upgrade na base existente.
- **Dashboard Executivo** — visão em tempo real de receita recorrente e acionamentos.
```

- [ ] **Step 2: Criar `tom-de-voz.md`**

```markdown
---
marca: provider-max
tipo: tom-de-voz
versao: 0.1-draft
atualizado: 2026-06-08
herda-de: [[shared/voz-grupo]]
---

# Tom de Voz — Provider Max

Herda DNA Smark (`[[shared/voz-grupo]]`), mas com refinamentos:

## Refinamentos vs. Smark mãe

- **Mais técnico-vertical.** Audiência é ISP — pode usar termos do setor sem traduzir.
- **Mais comercial-direto.** Foco em ROI e receita não capturada. Usar números quando puder.
- **Tom motivador.** "O dinheiro estava aí" — provoca o operador a agir.
- **Metáforas comerciais OK.** "Vazamento de receita", "dinheiro na mesa", "deixar passar".

## Voltagem (1-5)

| Eixo | Valor | Nota |
|---|---|---|
| Próximo ↔ Formal | 2 | Próximo, papo de gerente comercial. |
| Sério ↔ Bem-humorado | 3 | Humor seco; ironia controlada sobre churn. |
| Técnico ↔ Genérico | 5 | Bem técnico — assume vocabulário ISP. |
| Cauteloso ↔ Provocativo | 4 | Provoca operação a agir. |

## Frases de assinatura
- "O dinheiro estava aí."
- "Renovação não é sorte. É processo."
- "Sua base é um ativo, não uma lista."

<<COMPLETAR COM USUÁRIO: validar com o time se essas frases pegam>>
```

- [ ] **Step 3: Criar `personas.md`**

```markdown
---
marca: provider-max
tipo: personas
versao: 0.1-draft
atualizado: 2026-06-08
---

# Personas — Provider Max

## Persona 1: Gerente comercial de ISP

- Empresa: ISP regional, 5-50 mil assinantes.
- Dor: churn alto sem entender causa; renovações perdidas pra concorrente; sem dado de base atualizado.
- Quer ouvir: "você vai antecipar a renovação antes que o cliente comece a olhar concorrente".
- Não quer ouvir: "transformação digital", soluções genéricas que ignoram realidade do setor.

## Persona 2: Dono / sócio operacional de ISP

- Empresa: ISP médio, sócio ainda envolvido na operação.
- Dor: equipe pequena, decisão centralizada, precisa de previsibilidade de receita.
- Quer ouvir: "ROI claro em 60-90 dias, integra com seu IXC, time atual não precisa virar especialista".
- Não quer ouvir: contratos longos sem prova, papo de "potencial".

<<COMPLETAR COM USUÁRIO: confirmar ou ajustar com casos reais>>
```

- [ ] **Step 4: Criar `pilares-de-conteudo.md`**

```markdown
---
marca: provider-max
tipo: pilares-de-conteudo
versao: 0.1-draft
atualizado: 2026-06-08
---

# Pilares de Conteúdo — Provider Max

## 1. Receita que está na sua base (e você não vê)
Posts sobre churn invisível, renovação tardia, upgrade não ofertado. Dor concreta de ISP.

## 2. Operação comercial sem caos
Como organizar o processo comercial do ISP com automação. Antes/depois de operação.

## 3. Integração que não dá trabalho
Falar de integração com IXC e ERPs do setor sem virar "release técnico".

## 4. Casos de ISP real
Histórias de provedores que mudaram um indicador. Sem inflar números.

## 5. Mercado de ISP — o que está mudando
Pílulas sobre concorrência, regulação, comportamento de assinante. Conteúdo educativo que prepara venda.

<<COMPLETAR COM USUÁRIO: priorizar/podar pilares conforme realidade>>
```

- [ ] **Step 5: Criar `do-and-dont.md`**

```markdown
---
marca: provider-max
tipo: do-and-dont
versao: 0.1-draft
atualizado: 2026-06-08
---

# Do & Don't — Provider Max

## Sempre
- Citar termos do setor sem traduzir excessivamente (ISP, churn, MRR, upgrade, renovação).
- Mencionar integração IXC quando relevante.
- Usar números concretos com fonte ou marcar como exemplo.
- Falar com nome de cargo do setor: gerente comercial de ISP, supervisor de retenção, dono de provedor.

## Nunca
- Vender como CRM genérico.
- Promessa absoluta ("zero churn", "elimina 100% da inadimplência").
- Mensagem genérica de telecom — somos pra ISP regional/médio, não pra big telco.
- Tratar agente autônomo como "robô que vai substituir o time" — sempre como ferramenta do time.

<<COMPLETAR COM USUÁRIO>>
```

- [ ] **Step 6: Criar `brand-voice.md`**

Esqueleto consolidado usando o template `shared/_templates/brand-voice.md`, populado com o que já foi escrito acima. Marcadores `<<COMPLETAR>>` onde faltar dado direto.

- [ ] **Step 7: Criar `marcas/provider-max/README.md`**

```markdown
# Provider Max — SaaS

Plataforma de inteligência comercial para ISPs. SaaS próprio do grupo Smark — sub-marca com domínio próprio (max.smarktech.com.br).

## Mapa rápido
- [[branding/posicionamento]]
- [[branding/brand-voice]]
- [[branding/tom-de-voz]]
- [[branding/personas]]
- [[branding/pilares-de-conteudo]]
- [[branding/do-and-dont]]

## Status
Drafts iniciais de 2026-06-08, derivados do site. Marcadores `<<COMPLETAR COM USUÁRIO>>` indicam pontos para preencher na primeira sessão real de uso.
```

- [ ] **Step 8: Verify**

Run: `ls /Users/andreik/smark/marcas/provider-max/branding/*.md`
Expected: 6 arquivos `.md`.

Run: `grep -l "<<COMPLETAR" /Users/andreik/smark/marcas/provider-max/branding/*.md | wc -l`
Expected: número > 0 (marcadores presentes em pelo menos alguns arquivos).

---

### Task 9: Criar drafts de branding da Elever AI

**Files:**
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/posicionamento.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/brand-voice.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/tom-de-voz.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/personas.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/pilares-de-conteudo.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/branding/do-and-dont.md`
- Create: `/Users/andreik/smark/marcas/elever-ai/README.md`

Como o site eleverai.smarktech.com.br deu timeout durante a análise, esses drafts ficam mais magros e usam `<<COMPLETAR COM USUÁRIO>>` com mais frequência. A info-base é apenas: "plataforma de IA para vendas inbound".

- [ ] **Step 1: Criar `posicionamento.md`**

```markdown
---
marca: elever-ai
tipo: posicionamento
versao: 0.1-draft
atualizado: 2026-06-08
fonte-extracao: análise mãe Smark (site eleverai.smarktech.com.br indisponível na extração)
status-extracao: draft-inicial-magro — completar com usuário
---

# Posicionamento — Elever AI

## Em uma frase
Plataforma de IA para vendas inbound — qualifica, prioriza e acelera leads que entram pelo topo do funil.

## Categoria
SaaS B2B horizontal de vendas. Sub-marca do grupo Smark.

## Promessa central
<<COMPLETAR COM USUÁRIO — frase de assinatura ainda não definida>>

## Diferenciais
<<COMPLETAR COM USUÁRIO>>

## O que NÃO somos
- Não somos chatbot genérico de site.
- Não somos discador de outbound.
- Não substituímos vendedor — entregamos lead pronto.

## Produtos / módulos
<<COMPLETAR COM USUÁRIO>>
```

- [ ] **Step 2-6: Criar `tom-de-voz.md`, `personas.md`, `pilares-de-conteudo.md`, `do-and-dont.md`, `brand-voice.md`**

Para cada arquivo, criar versão minimal seguindo o mesmo padrão do Provider Max (Task 8), mas com a maior parte do conteúdo marcada como `<<COMPLETAR COM USUÁRIO>>`. O esqueleto deve estar pronto pra o usuário preencher na primeira sessão real.

**Conteúdo herdado garantido** (não pode estar como `<<COMPLETAR>>`):
- Herança de `[[shared/voz-grupo]]` declarada explicitamente no tom-de-voz
- Pilares começam herdando `[[shared/pilares-gerais]]`
- Do & Don't herda as palavras-proibidas globais

Exemplo de `tom-de-voz.md`:

```markdown
---
marca: elever-ai
tipo: tom-de-voz
versao: 0.1-draft
atualizado: 2026-06-08
herda-de: [[shared/voz-grupo]]
status-extracao: esqueleto-inicial
---

# Tom de Voz — Elever AI

Herda DNA Smark (`[[shared/voz-grupo]]`). Refinamentos abaixo precisam ser validados pelo usuário.

## Refinamentos vs. Smark mãe
<<COMPLETAR COM USUÁRIO — definir 3-5 refinamentos: o tom é mais técnico? mais comercial? mais consumer?>>

## Voltagem (1-5)
<<COMPLETAR COM USUÁRIO — preencher escala>>

## Frases de assinatura
<<COMPLETAR COM USUÁRIO>>
```

Aplicar o mesmo padrão "esqueleto explícito + marcador onde falta dado" pros outros 4 arquivos.

- [ ] **Step 7: Criar `marcas/elever-ai/README.md`**

```markdown
# Elever AI — SaaS

Plataforma de IA para vendas inbound. SaaS próprio do grupo Smark — sub-marca com domínio próprio (eleverai.smarktech.com.br).

## Mapa rápido
- [[branding/posicionamento]]
- [[branding/brand-voice]]
- [[branding/tom-de-voz]]
- [[branding/personas]]
- [[branding/pilares-de-conteudo]]
- [[branding/do-and-dont]]

## Status
**Drafts esqueléticos** — extração do site não pôde ser feita na primeira tentativa. Antes da primeira invocação real de slash command pra Elever AI, o usuário precisa preencher os marcadores `<<COMPLETAR COM USUÁRIO>>` nos 6 arquivos de branding.
```

- [ ] **Step 8: Verify**

Run: `ls /Users/andreik/smark/marcas/elever-ai/branding/*.md`
Expected: 6 arquivos `.md`.

Run: `grep -c "<<COMPLETAR" /Users/andreik/smark/marcas/elever-ai/branding/posicionamento.md`
Expected: número >= 3 (marcadores presentes — esses drafts são intencionalmente magros).

---

### Task 10: Slash command `/post-instagram`

**Files:**
- Create: `/Users/andreik/smark/.claude/commands/post-instagram.md`

- [ ] **Step 1: Criar arquivo do comando**

```markdown
---
description: Gera post de Instagram para uma marca, salva em marcas/<marca>/publicacoes/social/instagram/
argument-hint: <marca> <briefing>
---

Você vai gerar um post de Instagram. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

O primeiro token de `$ARGUMENTS` é a marca. O restante é o briefing.

Marcas válidas: `smark`, `provider-max`, `elever-ai`. Se a primeira palavra não bater com nenhuma, **pare e pergunte ao usuário qual marca**. Não assuma.

## Passo 2 — Carregar contexto na ordem

Leia, nesta ordem:

1. `/Users/andreik/smark/shared/voz-grupo.md`
2. `/Users/andreik/smark/shared/pilares-gerais.md`
3. `/Users/andreik/smark/shared/glossario.md`
4. Todos os arquivos `.md` em `/Users/andreik/smark/marcas/<MARCA>/branding/`
5. Liste `/Users/andreik/smark/marcas/<MARCA>/referencias/` e identifique 3-5 referências cujas tags no frontmatter melhor casem com palavras-chave do briefing. Leia o conteúdo dessas.
6. Liste as 3 publicações mais recentes em `/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/instagram/` (por data no nome do arquivo) e leia-as para evitar repetir hook/ângulo.

Se a marca tiver marcadores `<<COMPLETAR COM USUÁRIO>>` em branding, **avise o usuário antes de gerar** — pergunte se quer completar primeiro ou seguir com o que tem.

## Passo 3 — Gerar preview na conversa

Apresente:

- **Ângulo escolhido** (1-2 linhas — qual insight guiou)
- **Pilar de conteúdo** que esse post ataca
- **Referências usadas** (slug + 1 linha do que extraiu)
- **Copy da legenda** (versão final pronta pra publicar)
- **Sugestão de carrossel** se aplicável (frame por frame)
- **Briefing visual** (descrição pra arte)
- **Hashtags** (5-8, relevantes — não spam)

**Não salve nada ainda.** Pergunte: "Quer ajustar algo ou já pode salvar como draft?"

## Passo 4 — Iterar conforme feedback

Ajuste o que o usuário pedir. Não regere tudo — só o que mudou.

## Passo 5 — Salvar quando o usuário confirmar

Salve em:
`/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/instagram/<YYYY-MM-DD>-<slug-do-tema>.md`

Onde `<YYYY-MM-DD>` é a data de hoje e `<slug-do-tema>` é um slug em kebab-case curto derivado do tema (ex: `churn-invisivel-isps`).

Use o template `/Users/andreik/smark/shared/_templates/publicacao.md` como base. Frontmatter mínimo:

```yaml
marca: <MARCA>
canal: instagram
formato: <post|carrossel>
status: draft
data: <YYYY-MM-DD>
tags: [<tags-relevantes>]
referencias-usadas: [<wikilinks-pras-refs>]
pilares: [<wikilinks-pros-pilares>]
url-publicado:
```

Confirme ao usuário o caminho do arquivo salvo.

## Regras invioláveis

- Sempre pt-BR.
- Nunca use palavras-proibidas listadas em `shared/voz-grupo.md`.
- Não gere arte/imagem — só briefing visual em texto.
- Se a marca não existir ou o briefing for vago demais (< 5 palavras), pergunte antes.
```

- [ ] **Step 2: Verify**

Run: `head -10 /Users/andreik/smark/.claude/commands/post-instagram.md`
Expected: começa com frontmatter `description:` e `argument-hint:`.

---

### Task 11: Slash command `/post-linkedin`

**Files:**
- Create: `/Users/andreik/smark/.claude/commands/post-linkedin.md`

- [ ] **Step 1: Criar arquivo do comando**

Mesma estrutura do `/post-instagram`, com 4 diferenças:

```markdown
---
description: Gera post de LinkedIn para uma marca, salva em marcas/<marca>/publicacoes/social/linkedin/
argument-hint: <marca> <briefing>
---

Você vai gerar um post de LinkedIn. Argumentos recebidos: `$ARGUMENTS`.

## Passo 1 — Parsear argumentos

O primeiro token de `$ARGUMENTS` é a marca. O restante é o briefing.

Marcas válidas: `smark`, `provider-max`, `elever-ai`. Se a primeira palavra não bater com nenhuma, **pare e pergunte ao usuário qual marca**.

## Passo 2 — Carregar contexto na ordem

Leia, nesta ordem:

1. `/Users/andreik/smark/shared/voz-grupo.md`
2. `/Users/andreik/smark/shared/pilares-gerais.md`
3. `/Users/andreik/smark/shared/glossario.md`
4. Todos os arquivos `.md` em `/Users/andreik/smark/marcas/<MARCA>/branding/`
5. Identifique 3-5 referências em `/Users/andreik/smark/marcas/<MARCA>/referencias/` por casamento de tags com palavras-chave do briefing.
6. As 3 publicações mais recentes em `/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/linkedin/`.

## Passo 3 — Gerar preview na conversa

Otimize para LinkedIn:

- **Hook nos 2 primeiros parágrafos** (LinkedIn corta com "ver mais").
- **Texto mais longo permitido** (150-400 palavras é a faixa boa).
- **Hashtags moderadas** (3-5, no fim).
- **Sem emoji excessivo** — máximo 1-2 funcionais.
- **Quebras de linha frequentes** — parágrafos de 1-3 frases.

Apresente:
- Ângulo escolhido
- Pilar de conteúdo
- Referências usadas
- Copy completo do post
- Briefing visual (se for usar imagem)
- Hashtags

**Não salve ainda.** Pergunte: "Quer ajustar ou já posso salvar como draft?"

## Passo 4 — Iterar conforme feedback

## Passo 5 — Salvar quando confirmado

Salve em:
`/Users/andreik/smark/marcas/<MARCA>/publicacoes/social/linkedin/<YYYY-MM-DD>-<slug>.md`

Use template `/Users/andreik/smark/shared/_templates/publicacao.md`. Frontmatter:

```yaml
marca: <MARCA>
canal: linkedin
formato: post
status: draft
data: <YYYY-MM-DD>
tags: [...]
referencias-usadas: [...]
pilares: [...]
url-publicado:
```

Confirme caminho ao usuário.

## Regras invioláveis

- Sempre pt-BR.
- Sem palavras-proibidas de `shared/voz-grupo.md`.
- Não gere imagem.
- Marca inválida ou briefing vago → pergunte.
```

- [ ] **Step 2: Verify**

Run: `grep "canal: linkedin" /Users/andreik/smark/.claude/commands/post-linkedin.md | wc -l`
Expected: `1` (o canal aparece exatamente uma vez no exemplo de frontmatter).

---

### Task 12: Slash command `/anuncio`

**Files:**
- Create: `/Users/andreik/smark/.claude/commands/anuncio.md`

- [ ] **Step 1: Criar arquivo do comando**

```markdown
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
```

- [ ] **Step 2: Verify**

Run: `grep -c "Variação " /Users/andreik/smark/.claude/commands/anuncio.md`
Expected: `>= 3` (instruções pra 3 variações).

---

### Task 13: Slash command `/campanha`

**Files:**
- Create: `/Users/andreik/smark/.claude/commands/campanha.md`

- [ ] **Step 1: Criar arquivo do comando**

```markdown
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
```

- [ ] **Step 2: Verify**

Run: `grep -c "^## Passo " /Users/andreik/smark/.claude/commands/campanha.md`
Expected: `5`.

---

### Task 14: Slash command `/nova-referencia`

**Files:**
- Create: `/Users/andreik/smark/.claude/commands/nova-referencia.md`

- [ ] **Step 1: Criar arquivo do comando**

```markdown
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
```

- [ ] **Step 2: Verify**

Run: `grep -c "^## Passo " /Users/andreik/smark/.claude/commands/nova-referencia.md`
Expected: `6`.

Run: `ls /Users/andreik/smark/.claude/commands/`
Expected: 5 arquivos `.md` (post-instagram, post-linkedin, anuncio, campanha, nova-referencia).

---

### Task 15: Notas de setup Obsidian + verificação final

**Files:**
- Create: `/Users/andreik/smark/README.md`

- [ ] **Step 1: Criar `README.md` raiz**

```markdown
# Smark Vault

Vault Obsidian + workspace Claude Code do grupo Smark. Gera publicações sociais e materiais de marketing com contexto de marca consistente em multi-marca (Smark, Provider Max, Elever AI).

## Setup Obsidian

1. Abrir Obsidian → "Open folder as vault" → selecionar `/Users/andreik/smark`.
2. Em **Settings → Files & Links**:
   - Default location for new attachments: `In subfolder under current folder`, nome: `_assets`
   - Wikilinks: ativados (padrão)
   - Excluded files: adicionar `.claude/`, `docs/`, `shared/_templates/`
3. Em **Settings → Community plugins**, instalar (opcional mas recomendado):
   - **Dataview** — para queries por marca/canal/status
   - **Templater** — para criar notas manualmente seguindo templates
   - **Tag Wrangler** — para gerenciar taxonomia de tags

## Como gerar conteúdo

Dentro do Claude Code, neste diretório:

- `/post-instagram <marca> <briefing>` — post de Instagram
- `/post-linkedin <marca> <briefing>` — post de LinkedIn
- `/anuncio <marca> <produto-ou-objetivo>` — anúncio com 3 variações
- `/campanha <marca> <tema>` — campanha (conceito + peças + cronograma)
- `/nova-referencia <marca> <url-ou-texto-ou-arquivo>` — normaliza referência

Marcas: `smark`, `provider-max`, `elever-ai`.

## Estrutura

- `shared/` — DNA do grupo (voz, pilares, glossário, templates)
- `marcas/<slug>/branding/` — 6 notas que definem cada marca
- `marcas/<slug>/referencias/` — referências normalizadas (+ `inbox/` para originais)
- `marcas/<slug>/publicacoes/` — publicações geradas, por canal

## Dashboards Dataview úteis

Cole numa nota qualquer pra ver as views:

### Publicações em draft de todas as marcas

```dataview
TABLE marca, canal, data
FROM "marcas"
WHERE status = "draft" AND contains(file.path, "publicacoes")
SORT data DESC
```

### Referências mais reutilizadas

```dataview
TABLE length(file.inlinks) AS "usada x"
FROM "marcas"
WHERE contains(file.path, "referencias") AND tipo != null
SORT length(file.inlinks) DESC
LIMIT 20
```

## Estado do vault

| Marca | Branding | Status |
|---|---|---|
| Smark | extraído do `branding.pdf` | revisar |
| Provider Max | draft do site max.smarktech.com.br | revisar e completar `<<COMPLETAR>>` |
| Elever AI | esqueleto magro (site indisponível na extração) | preencher antes do primeiro uso |
```

- [ ] **Step 2: Verificação completa da estrutura**

Run:
```bash
find /Users/andreik/smark -type f -not -path '*/.*' -not -path '*/source/*' | sort
```

Expected output (lista — deve conter todos os arquivos abaixo):
```
/Users/andreik/smark/.claude/commands/anuncio.md
/Users/andreik/smark/.claude/commands/campanha.md
/Users/andreik/smark/.claude/commands/nova-referencia.md
/Users/andreik/smark/.claude/commands/post-instagram.md
/Users/andreik/smark/.claude/commands/post-linkedin.md
/Users/andreik/smark/CLAUDE.md
/Users/andreik/smark/README.md
/Users/andreik/smark/docs/superpowers/plans/2026-06-08-smark-vault-brand-context.md
/Users/andreik/smark/docs/superpowers/specs/2026-06-08-smark-vault-brand-context-design.md
/Users/andreik/smark/marcas/elever-ai/README.md
/Users/andreik/smark/marcas/elever-ai/branding/brand-voice.md
/Users/andreik/smark/marcas/elever-ai/branding/do-and-dont.md
/Users/andreik/smark/marcas/elever-ai/branding/personas.md
/Users/andreik/smark/marcas/elever-ai/branding/pilares-de-conteudo.md
/Users/andreik/smark/marcas/elever-ai/branding/posicionamento.md
/Users/andreik/smark/marcas/elever-ai/branding/tom-de-voz.md
/Users/andreik/smark/marcas/provider-max/README.md
/Users/andreik/smark/marcas/provider-max/branding/brand-voice.md
/Users/andreik/smark/marcas/provider-max/branding/do-and-dont.md
/Users/andreik/smark/marcas/provider-max/branding/personas.md
/Users/andreik/smark/marcas/provider-max/branding/pilares-de-conteudo.md
/Users/andreik/smark/marcas/provider-max/branding/posicionamento.md
/Users/andreik/smark/marcas/provider-max/branding/tom-de-voz.md
/Users/andreik/smark/marcas/smark/README.md
/Users/andreik/smark/marcas/smark/branding/brand-voice.md
/Users/andreik/smark/marcas/smark/branding/do-and-dont.md
/Users/andreik/smark/marcas/smark/branding/personas.md
/Users/andreik/smark/marcas/smark/branding/pilares-de-conteudo.md
/Users/andreik/smark/marcas/smark/branding/posicionamento.md
/Users/andreik/smark/marcas/smark/branding/tom-de-voz.md
/Users/andreik/smark/shared/_templates/brand-voice.md
/Users/andreik/smark/shared/_templates/publicacao.md
/Users/andreik/smark/shared/_templates/referencia.md
/Users/andreik/smark/shared/glossario.md
/Users/andreik/smark/shared/pilares-gerais.md
/Users/andreik/smark/shared/voz-grupo.md
```

Mais o PDF: `/Users/andreik/smark/marcas/smark/branding/source/branding.pdf` (não aparece acima porque está dentro de `source/`).

- [ ] **Step 3: Verificar que pastas vazias de publicacoes existem**

Run:
```bash
find /Users/andreik/smark/marcas -type d -name "instagram" -o -name "linkedin" -o -name "anuncios" -o -name "campanhas" -o -name "inbox" | sort
```

Expected: 15 linhas (5 pastas × 3 marcas).

- [ ] **Step 4: Smoke test end-to-end (manual — usuário faz)**

Instrução pro usuário (não automatizável):

> Reinicie o Claude Code neste diretório (`/Users/andreik/smark/`) para carregar os slash commands. Em seguida, teste:
>
> ```
> /post-instagram smark teste de smoke: a importância do diagnóstico antes da venda
> ```
>
> **Esperado:**
> - Claude lê voz-grupo, pilares-gerais, branding da Smark, busca referências (não há ainda, vai relatar isso), gera preview na conversa, pergunta se pode salvar.
> - Ao confirmar, cria arquivo em `marcas/smark/publicacoes/social/instagram/2026-06-08-diagnostico-antes-da-venda.md` (ou similar) com frontmatter completo.
>
> Se falhar em qualquer ponto, anote o erro e me avise — vamos ajustar antes de avançar.

---

## Self-Review

**Cobertura do spec:**

- ✅ Seção 1-2 (contexto e decisões) — Task 1-6 implementam estrutura, shared, CLAUDE.md
- ✅ Seção 3 (arquitetura de marca) — Task 1 (scaffold das 3 marcas), Tasks 7-9 (branding por marca)
- ✅ Seção 4 (estrutura de pastas) — Task 1
- ✅ Seção 5 (modelo de contexto + precedência) — Task 6 (CLAUDE.md), Tasks 10-14 (cada slash command implementa a ordem)
- ✅ Seção 6 (slash commands) — Tasks 10-14, um por comando
- ✅ Seção 7 (templates) — Task 5
- ✅ Seção 8 (fluxo end-to-end) — Task 15 step 4 (smoke test)
- ✅ Seção 9 (extração do PDF) — Task 7
- ✅ Seção 10 (integração Obsidian) — Task 15 step 1 (README com setup)
- ✅ Seção 11 (git diferido) — refletido na nota do header e ausência de tasks de git
- ✅ Seção 12 (não-objetivos) — refletidos em CLAUDE.md
- ✅ Seção 13 (critérios de sucesso) — verificáveis após smoke test e primeiras publicações reais

**Placeholders:** Nenhum "TODO", "TBD" ou "implementar depois" no plano. Os marcadores `<<COMPLETAR COM USUÁRIO>>` que aparecem em alguns drafts de branding **são intencionais e parte do design** — sinalizam ao usuário onde ele precisa completar antes do primeiro uso real daquela marca.

**Consistência de tipos:** Os nomes dos slash commands são consistentes (`post-instagram`, `post-linkedin`, `anuncio`, `campanha`, `nova-referencia`). Frontmatter de publicacao.md tem os mesmos campos em todas as tasks que o usam. Slugs de marca (`smark`, `provider-max`, `elever-ai`) consistentes em todo o documento. Estrutura de pastas de cada marca é simétrica em Tasks 1, 7, 8, 9.
