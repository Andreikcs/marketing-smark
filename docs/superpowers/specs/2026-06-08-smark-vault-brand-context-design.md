# Smark Vault — Sistema de Contexto de Marca para Criação de Conteúdo

**Data:** 2026-06-08
**Status:** Aprovado pelo usuário, pronto para plano de implementação
**Escopo:** workspace local em `/Users/andreik/smark/` que serve como vault Obsidian + harness Claude Code para gerar publicações alinhadas ao branding de Smark e suas sub-marcas.

---

## 1. Contexto e motivação

A Smark é uma consultoria/assessoria tecnológica (marca-mãe) com dois SaaS próprios — **Provider Max** (inteligência comercial para ISPs) e **Elever AI** (IA para vendas inbound). Cada uma tem posicionamento próprio, mas todas herdam o DNA Smark: tom próximo, sem jargão financeiro, honesto sobre limitações.

Nos próximos 90 dias o foco de conteúdo é:
- **Posts de redes sociais** (Instagram e LinkedIn)
- **Materiais de marketing** (anúncios e campanhas)

O usuário precisa de um ambiente local onde:
1. O Claude Code mantém contexto consistente da marca entre sessões.
2. Referências (screenshots, URLs, PDFs, texto livre) são normalizadas e reutilizáveis.
3. Publicações geradas viram histórico consultável e linkado.
4. O Obsidian serve como camada de navegação, busca e visualização do grafo de conhecimento.
5. Tudo é editável em markdown — nada de banco de dados, nada de ferramenta fechada.

---

## 2. Decisões já tomadas (durante o brainstorming)

| Decisão | Escolha |
|---|---|
| Foco de conteúdo (90 dias) | Posts sociais + materiais de marketing |
| Modelo Obsidian | `smark/` **é** o vault, com pastas separadas e linkadas internamente |
| Interface de invocação | CLAUDE.md raiz + slash commands customizados |
| Processamento do `branding.pdf` | Extração one-shot em notas estruturadas em markdown |
| Formato de referências aceito | Mix — screenshots, URLs, PDFs, texto livre |
| Arquitetura de marca | Marca-mãe + sub-marcas simétricas em `marcas/`, com `shared/` para DNA comum |

---

## 3. Arquitetura de marca

```
Smark (consultoria, marca-mãe)
├── Provider Max  (SaaS — inteligência comercial para ISPs)
└── Elever AI     (SaaS — IA para vendas inbound)
```

Todas as marcas herdam DNA comum (tom Smark) via `shared/`, mas cada uma sobrescreve quando o posicionamento específico exige.

**Precedência de contexto (mais específico vence):**
```
referências do briefing  →  branding da marca  →  shared/voz-grupo  →  CLAUDE.md
```

---

## 4. Estrutura de pastas

```
smark/
├── CLAUDE.md                          # contexto raiz: como usar o vault, regras gerais
├── .claude/
│   └── commands/
│       ├── post-instagram.md
│       ├── post-linkedin.md
│       ├── anuncio.md
│       ├── campanha.md
│       └── nova-referencia.md
│
├── shared/                            # DNA Smark, herdado por todas
│   ├── voz-grupo.md
│   ├── pilares-gerais.md
│   ├── glossario.md
│   └── _templates/
│       ├── publicacao.md
│       ├── referencia.md
│       └── brand-voice.md
│
├── marcas/
│   ├── smark/
│   │   ├── README.md
│   │   ├── branding/
│   │   │   ├── posicionamento.md
│   │   │   ├── brand-voice.md
│   │   │   ├── tom-de-voz.md
│   │   │   ├── personas.md
│   │   │   ├── pilares-de-conteudo.md
│   │   │   ├── do-and-dont.md
│   │   │   └── source/branding.pdf
│   │   ├── referencias/
│   │   │   ├── inbox/                 # entradas brutas
│   │   │   └── (notas normalizadas)
│   │   └── publicacoes/
│   │       ├── social/
│   │       │   ├── instagram/
│   │       │   └── linkedin/
│   │       └── marketing/
│   │           ├── anuncios/
│   │           └── campanhas/
│   │
│   ├── provider-max/                  # mesma estrutura interna
│   └── elever-ai/                     # mesma estrutura interna
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-08-smark-vault-brand-context-design.md
```

**Convenções:**
- Slugs em `kebab-case` (`provider-max`, `elever-ai`).
- Cada marca é autocontida; nada do branding de uma vaza pra outra a menos que esteja em `shared/`.
- `inbox/` tem duplo papel: (a) drop zone para coisa bruta antes de normalizar, e (b) arquivo dos originais depois que `/nova-referencia` gera a nota normalizada em `referencias/<slug>.md`. A nota normalizada referencia o original via wikilink.
- Publicações são organizadas por canal, não por data — a data fica no nome do arquivo (`YYYY-MM-DD-<slug>.md`) e no frontmatter.

---

## 5. Modelo de contexto

### 5.1 Camadas carregadas a cada slash command

1. **`CLAUDE.md` raiz** — sempre carregado. Regras do vault: pt-BR, multi-marca, validar `<marca>` antes de gerar, nunca usar jargão financeiro.
2. **`shared/voz-grupo.md`** — sempre carregado. DNA Smark transversal.
3. **`marcas/<slug>/branding/*`** — carregado quando `<marca>` é passada. Refina ou sobrescreve o DNA.
4. **`marcas/<slug>/referencias/*`** — busca por tags relevantes ao briefing; carrega 3-5 mais alinhadas (não tudo).
5. **Últimas 3 publicações do mesmo canal** — pra consistência de voz e variação de ângulos.

### 5.2 Precedência em conflitos

```
referências do briefing  >  branding da marca  >  shared/voz-grupo  >  CLAUDE.md
```

Exemplo: se `shared/voz-grupo.md` diz "tom próximo" e `marcas/provider-max/branding/tom-de-voz.md` diz "tom técnico-objetivo", Provider Max usa técnico-objetivo.

---

## 6. Slash commands

Todos seguem o padrão `<comando> <marca> <briefing/input>`.

### 6.1 `/post-instagram <marca> <briefing>`
**Saída:** `marcas/<marca>/publicacoes/social/instagram/YYYY-MM-DD-<slug>.md`
**Conteúdo gerado:**
- Copy da legenda + hashtags sugeridas
- Sugestão de carrossel (texto frame-por-frame), se aplicável
- Briefing visual (descrição pra designer ou IA gerar a arte)
- Notas de decisão (ângulo escolhido, referências usadas)
- Frontmatter completo

### 6.2 `/post-linkedin <marca> <briefing>`
Estrutura igual ao Instagram, otimizada pra LinkedIn: texto mais longo, hook nos 2 primeiros parágrafos, hashtags moderadas.

### 6.3 `/anuncio <marca> <produto-ou-objetivo>`
**Saída:** `marcas/<marca>/publicacoes/marketing/anuncios/YYYY-MM-DD-<slug>.md`
**Conteúdo gerado:**
- Headline (3 variações A/B/C)
- Copy primário (3 variações)
- Copy secundário/descrição
- CTA (verbo + benefício)
- Briefing visual + persona-alvo

### 6.4 `/campanha <marca> <tema>`
**Saída:** pasta `marcas/<marca>/publicacoes/marketing/campanhas/YYYY-MM-DD-<slug>/` com:
- `00-conceito.md` — big idea, pilares, narrativa
- `01-posts-social.md` — série de posts sugerida
- `02-anuncios.md` — variações de anúncio
- `03-cronograma.md` — ordem sugerida de publicação

### 6.5 `/nova-referencia <marca> <input>`
**Saída:** `marcas/<marca>/referencias/<slug>.md`
**Comportamento:**
- Aceita screenshot, URL, PDF ou texto livre
- Normaliza em nota com frontmatter (`tipo`, `fonte`, `tags`, `aplicabilidade`)
- Extrai padrões: tom, estrutura, visual, copy-chave
- Move arquivos originais (se houver) pra `referencias/inbox/` arquivado

---

## 7. Templates

Três templates em `shared/_templates/`:

### 7.1 `publicacao.md`
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
---

## Briefing original
## Ângulo escolhido
## Conteúdo
## Briefing visual
## Notas de decisão
```

### 7.2 `referencia.md`
```markdown
---
marca: <slug>
tipo: <post|anuncio|artigo|video|site>
fonte: <url ou "screenshot manual">
data-salvo: YYYY-MM-DD
tags: []
aplicabilidade: <alta|media|baixa>
---

## Por que salvei
## O que extrair
- Tom:
- Estrutura:
- Visual:
- Copy-chave:
## Como aplicar na <marca>
## O que evitar
```

### 7.3 `brand-voice.md`
Template usado pela extração do PDF de branding. Cobre:
- Missão / posicionamento
- Personas (mínimo 2)
- Pilares de conteúdo (3-5)
- Tom de voz (5 atributos com exemplos do/don't)
- Palavras-marca e palavras-proibidas
- Exemplos canônicos (3 peças de referência aprovadas)

---

## 8. Fluxo end-to-end (exemplo canônico)

**Cenário:** post Instagram da Provider Max sobre "churn invisível em ISPs".

1. **Invocação:**
   `/post-instagram provider-max como ISPs estão perdendo dinheiro com churn invisível`

2. **Carregamento de contexto:**
   - `CLAUDE.md` (raiz)
   - `shared/voz-grupo.md`
   - `marcas/provider-max/branding/*`
   - Busca em `referencias/` por tags relevantes (ex: `[churn, dor-operacional, isp]`) — pega 3-5
   - Lê últimas 3 notas em `publicacoes/social/instagram/`

3. **Geração:**
   Claude mostra preview na conversa: copy, ângulo, referências usadas, briefing visual.

4. **Iteração:**
   Usuário ajusta ali mesmo ("muda o hook", "tira essa hashtag", "põe mais ironia").

5. **Persistência:**
   `marcas/provider-max/publicacoes/social/instagram/2026-06-08-churn-invisivel-isps.md` com `status: draft` e frontmatter completo.

6. **Linkagem Obsidian:**
   Wikilinks automáticos para `[[tom-de-voz]]`, `[[voz-grupo]]`, referências usadas. Aparece no graph view.

7. **Publicação:**
   Usuário edita `status: draft` → `status: publicado` + adiciona `url-publicado`. Vira histórico.

---

## 9. Extração inicial do `branding.pdf`

**Premissa:** o `branding.pdf` atual em `/Users/andreik/smark/branding/branding.pdf` é da Smark (marca-mãe).

**Procedimento:**
1. Mover `branding/branding.pdf` → `marcas/smark/branding/source/branding.pdf`.
2. Ler o PDF e gerar 6 notas em `marcas/smark/branding/`:
   - `posicionamento.md`
   - `brand-voice.md`
   - `tom-de-voz.md`
   - `personas.md`
   - `pilares-de-conteudo.md`
   - `do-and-dont.md`
3. Usuário revisa e ajusta inconsistências (commit fica diferido — ver seção 11).

**Provider Max e Elever AI** (sem PDF próprio): drafts iniciais baseados nos sites `max.smarktech.com.br` e `eleverai.smarktech.com.br`; usuário completa em conversa na primeira invocação real de cada marca.

---

## 10. Integração Obsidian

### 10.1 Configuração
- Vault: `/Users/andreik/smark`
- Wikilinks: ativados (padrão)
- Default attachment location: `<pasta da nota>/_assets/`
- Excluded files: `.claude/`, `docs/`, `shared/_templates/` (não poluem busca)

### 10.2 Plugins recomendados (opcionais)
- **Dataview** — dashboards por marca/canal/status
- **Templater** — criar notas manualmente seguindo templates (uso fora do slash command)
- **Tag Wrangler** — evitar explosão de tags duplicadas

### 10.3 Graph view
Wikilinks consistentes nos frontmatters (`referencias-usadas`, `pilares`) fazem o graph mostrar clusters por pilar de conteúdo, por canal e por marca — visualização de saturação e lacunas.

---

## 11. Controle de versão

**Diferido.** Prioridade nesta primeira fase é colocar o vault em uso o mais rápido possível. `git init` e configuração de `.gitignore` ficam como passo opcional, a ser feito depois das primeiras publicações reais (ou quando o usuário decidir).

---

## 12. Não-objetivos (YAGNI)

- **Sem CMS, sem banco de dados, sem servidor.** Tudo é markdown + Obsidian + Claude Code local.
- **Sem publicação automática** em redes sociais nesta fase. Usuário copia/cola.
- **Sem geração de imagem** dentro do vault — briefing visual é pra outra ferramenta/pessoa.
- **Sem dashboard web próprio.** Dataview no Obsidian cobre essa necessidade.
- **Sem multi-usuário, sem permissões.** Vault local single-user.
- **Sem versionamento automático de publicações** além do git. Não cria histórico de "drafts antigos".

---

## 13. Critérios de sucesso

A solução é considerada bem-sucedida quando:

1. Usuário invoca um slash command e recebe, em **uma única conversa**, uma publicação pronta pra revisão (não múltiplas idas e vindas pedindo contexto).
2. Voz da marca é **consistente** entre publicações geradas em sessões diferentes.
3. Sub-marcas (Provider Max, Elever AI) **soam diferentes** da Smark mãe — herdam o DNA mas têm identidade própria.
4. Adicionar uma referência via `/nova-referencia` leva **menos de 2 minutos**.
5. Adicionar uma nova sub-marca futura é uma operação de cópia de pasta + edição de branding, sem mudar lógica de comandos.
6. Após 30 dias de uso, o graph view do Obsidian mostra clusters claros de pilares de conteúdo e referências reutilizadas.

---

## 14. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Extração do PDF gera notas imprecisas | Usuário revisa antes do primeiro uso; tudo é markdown editável |
| Voz Smark "vaza" indevidamente nas sub-marcas | Precedência clara: branding da marca > shared; testar com primeiras publicações |
| Explosão de tags em `referencias/` | Tag Wrangler + glossário em `shared/glossario.md` reforça taxonomia |
| Histórico de publicações cresce e polui busca | Frontmatter `status` filtra; Dataview separa draft vs publicado |
| Slash commands ficam rígidos demais | Tudo é markdown em `.claude/commands/` — editar é trivial após uso real |

---

## 15. Próximo passo

Após aprovação deste documento pelo usuário, invocar a skill `superpowers:writing-plans` para gerar plano de implementação detalhado, fase por fase.
