# Grupo Smark — Design System · v2

Pacote de implementação do sistema visual do painel de conteúdo (smark · Provider Max · Elever AI).
Claro por padrão, escuro sob demanda. Roxo é a marca, lime é o segundo acento.

## Arquivos

| Arquivo | O que é | Você usa? |
|---|---|---|
| `smark-ds.css` | **Folha única: tokens + TODAS as classes de componente (fundamentos + editor + avançados v2).** Drop-in. | ✅ **É este que entra no seu sistema** |
| `smark-design-system-v2.html` | **Galeria v2 — todos os componentes, incl. os 13 novos (menu, acordeão, stepper, sliders, progresso, chips, avatares, listas, tooltip, skeleton, vazio, calendário, busca).** | 👁️ Consulta (mais recente) |
| `painel-corrigido.html` | Protótipo navegável de referência (Painel → Studio, Vitrine, Config). Abra no navegador. | 👁️ Alvo visual / de comportamento |
| `smark-design-system.html` | Galeria v1 (fundamentos + componentes base). | 👁️ Consulta |
| `README.md` | Este guia. | 📖 |

## ⬇️ O que baixar e implementar

Baixe a **pasta inteira**. Para colocar no seu sistema, o único arquivo que entra no código é **`smark-ds.css`**. Os `.html` são referência — abra no navegador pra ver como deve ficar/navegar.

Passos:
1. Copie `smark-ds.css` para os assets do seu projeto (ex.: `static/css/smark-ds.css`).
2. No `<head>` do seu `painel.html` / editor, adicione o link e defina o tema na raiz:
   ```html
   <html data-theme="escuro">   <!-- seu painel é escuro; use "claro" na vitrine -->
   <head><link rel="stylesheet" href="/static/css/smark-ds.css"></head>
   <body class="sk"> … </body>
   ```
3. Troque a marcação das telas pelas classes `.sk-*` (mapa abaixo). Comece pela topbar e pela toolbar de filtros — é o que mais estava fora do padrão.
4. Abra `painel-corrigido.html` lado a lado e vá casando tela por tela.



## Instalação

```html
<!doctype html>
<html data-theme="claro">      <!-- ou data-theme="escuro" -->
<head>
  <link rel="stylesheet" href="smark-ds.css">
</head>
<body class="sk">
  ...
</body>
</html>
```

As fontes (Anton, Archivo, JetBrains Mono) já são importadas pelo próprio CSS via Google Fonts.
Para uso offline, baixe as fontes e troque o `@import` do topo do `smark-ds.css` por `@font-face` locais.

## Trocar de tema

Basta alternar o atributo na raiz:

```js
document.documentElement.setAttribute('data-theme', escuro ? 'escuro' : 'claro');
```

Todos os tokens (`--bg`, `--surface`, `--accent`, ...) recalculam sozinhos. Nenhum componente precisa mudar.

## Tokens principais

```
--bg  --surface  --surface-2  --inset          superfícies
--text  --sub  --muted                          texto
--line  --field-line                            bordas
--accent  --accent-2  --accent-soft  --accent-ink   roxo (marca)
--lime  --lime-ink  --lime-soft                  lime (2º acento)
--good  --warn  --bad  --info (+ *-soft)         estados
--radius-sm/md/lg/pill                           raios (8/12/16/999)
--space-1..16                                    escala base 4
--font-display (Anton)  --font-text (Archivo)  --font-mono
```

## Componentes (classes)

- **Tipografia:** `.sk-h1` `.sk-h2` `.sk-display` `.sk-kicker` `.sk-lead` `.sk-accent`
- **Botões:** `.sk-btn` + `--secondary --ghost --lime --danger` · tamanhos `--sm --lg --icon` · `[disabled]`
- **Formulário:** `.sk-label` `.sk-input` `.sk-textarea` `.sk-select` `.sk-toggle` `.sk-check` `.sk-radio`
- **Cards:** `.sk-card` + `--flat --brand` · `.sk-metric-label` `.sk-metric-value`
- **Navegação:** `.sk-tabs/.sk-tab` `.sk-breadcrumb` `.sk-page` `.sk-pill` (+ `.is-active`)
- **Feedback:** `.sk-badge--info/warn/good/bad/accent` · `.sk-alert--info/warn/bad` · `.sk-toast` · `.sk-overlay/.sk-modal`
- **Dados:** `.sk-table` `.sk-table-head` `.sk-table-row` `.sk-mono`

## Componentes avançados (v2 · seção 12 do CSS)

Inspirados no catálogo Material, reconstruídos com a cara Smark (nada de framework — só CSS + suas classes):

- **Menu / dropdown:** `.sk-menu-wrap > button + .sk-menu-backdrop + .sk-menu` · `.sk-menu-item` (`.is-danger`) · `.sk-menu-sep`
- **Acordeão:** `.sk-acc(.is-open) > .sk-acc-head (.sk-acc-chev) + .sk-acc-body`
- **Stepper:** `.sk-stepper > .sk-step(.is-done/.is-current) (.sk-step-num/.sk-step-label)` + `.sk-step-line(.is-done)` entre passos
- **Slider:** `.sk-slider-head (label + .sk-slider-val) + input.sk-slider`
- **Progresso:** `.sk-progress > .sk-progress-bar(--lime)` · indeterminado `.sk-progress--indeterminate > span` · `.sk-spinner` (SVG)
- **Chips:** `.sk-chip--input` (add/remove) · `.sk-chip--outline` · `.sk-chip--solid` (+ `.sk-segmented` para filtro)
- **Avatares:** `.sk-avatar--sm/md/lg` · `.sk-avatar-wrap > .sk-avatar-status` · `.sk-avatar-group` + `.sk-avatar-more`
- **Listas:** `.sk-list > .sk-list-item (.sk-list-icon / .sk-list-body > .sk-list-title + .sk-list-meta)`
- **Tooltip & popover:** `.sk-tip-wrap:hover .sk-tip` · `.sk-popover`
- **Skeleton:** `.sk-skel` (shimmer — aplique width/height/aspect-ratio inline)
- **Estado vazio:** `.sk-empty > .sk-empty-icon(--muted) + .sk-empty-title + .sk-empty-text + botão`
- **Calendário:** `.sk-cal > .sk-cal-grid > .sk-cal-dow / .sk-cal-day(.in-range/.is-selected)`
- **Busca / comando:** `.sk-command > .sk-command-head (input) + .sk-command-group + .sk-command-item(.is-active)` · `.sk-kbd`

## Padrões compostos (o que faltava)

Cor sozinha não conserta layout. Estes padrões resolvem "menus, filtros e grupos de elementos fora do padrão":

- **App shell:** `.sk-topbar` (barra fixa no topo — substitui botão flutuante de menu) + `.sk-navlink.is-active`
- **Cabeçalho de página:** `.sk-pagehead` + `.sk-pagehead-actions` (título à esquerda, ações à direita)
- **Barra de ferramentas:** `.sk-toolbar` com `.sk-filter-group` (rótulo + controle) e `.sk-toolbar-sep` (divisória)
- **Filtro segmentado:** `.sk-segmented > button.is-active` — o padrão certo para status/marca (em vez de pills soltas espalhadas)
- **Grade de cards:** `.sk-cardgrid` (auto-fill, colunas uniformes)
- **Card de post:** `.sk-post` (`.is-selected`) → `.sk-post-thumb` (`.sk-post-check.is-on`, `.sk-post-channel`) · `.sk-post-body` · `.sk-post-title` (clamp 2 linhas) · `.sk-post-meta` · `.sk-post-actions` (grid de 4 ações uniformes; `.act-edit` / `.act-del` com hover próprio)
- **Editor 3 colunas:** `.sk-editor` (`.sk-editor-rail` / `.sk-editor-canvas` / `.sk-editor-props`) + `.sk-prop-section`

Veja `painel-corrigido.html` para o painel montado com esses padrões — use como alvo visual e de estrutura.

### Antes → depois (as 4 correções principais)

1. **Menu flutuante → topbar.** Troque o botão `≡ Menu` roxo solto por `.sk-topbar` com nav e busca.
2. **Pills de filtro espalhadas → grupos segmentados.** `status:` e `marca:` viram dois `.sk-filter-group` com `.sk-segmented`, dentro de uma `.sk-toolbar`.
3. **Ações do card desalinhadas → grid de 4.** `.sk-post-actions` força Ver/Editar/Dup/Excluir em 4 colunas iguais, sem quebra de linha.
4. **Cards de altura irregular → estrutura fixa.** `.sk-post` é flex-column; thumb com `aspect-ratio`, título com clamp, meta e ações sempre no mesmo lugar.

### Exemplos

```html
<!-- Botão primário -->
<button class="sk-btn">Gerar conteúdo</button>
<button class="sk-btn sk-btn--secondary">Cancelar</button>
<button class="sk-btn sk-btn--lime">Aprovar</button>

<!-- Toggle (defina o estado com a classe .is-on ou aria-checked) -->
<button class="sk-toggle is-on" aria-checked="true"></button>

<!-- Badge de status -->
<span class="sk-badge sk-badge--good">Publicado</span>
<span class="sk-badge sk-badge--warn">Agendado</span>

<!-- Card de métrica -->
<div class="sk-card">
  <div class="sk-metric-label">Posts no mês</div>
  <div class="sk-metric-value">37</div>
</div>

<!-- Tabela -->
<div class="sk-table">
  <div class="sk-table-head" style="grid-template-columns:2.4fr 1fr 1fr 1fr">
    <div>Publicação</div><div>Marca</div><div>Canal</div><div>Status</div>
  </div>
  <div class="sk-table-row" style="grid-template-columns:2.4fr 1fr 1fr 1fr">
    <div>Churn invisível nos ISPs</div><div>Provider Max</div><div>Instagram</div>
    <div><span class="sk-badge sk-badge--good">Publicado</span></div>
  </div>
</div>
```

Os grids de `.sk-table-*` usam `grid-template-columns` inline para você controlar as colunas por tabela.

## Navegação & telas (o novo layout)

- **Topbar fixa** (`.sk-topbar`): marca à esquerda, `.sk-navlink` (Painel / Vitrine / Config — o ativo leva `.is-active`), busca e ações à direita. Substitui o botão flutuante `≡ Menu`.
- **Troca de tela**: cada link mostra/esconde a `<section>` da view. No seu app pode ser rota (`/painel`, `/vitrine`, `/config`, `/editor`) ou toggle de `display`. O card e o "Novo post" levam ao editor.
- Veja o fluxo montado em `painel-corrigido.html`.

## Editor / Studio (a tela principal)

Classes da seção 11 do CSS que compõem o super editor:

- **Botão Estúdio IA:** `.sk-btn.sk-btn--studio`
- **Shell 3 colunas:** `.sk-editor` → `.sk-editor-rail` (lista) · `.sk-editor-canvas` · `.sk-editor-props`
- **Seção de propriedade:** `.sk-prop-section` + `.sk-prop-title`
- **Rich toolbar:** `.sk-richbar` (`| quebra`, `★ acento`, **B**, *I*, cor) — acima de cada textarea
- **Emojis:** `.sk-emojigrid`
- **Sliders:** `.sk-slider-row > label + input.sk-slider` (zoom, posição, brilho, contraste, saturação)
- **Grade de escolha:** `.sk-choicegrid > .sk-choice.is-active` (Camada por cima da imagem)
- **Ação de IA paga:** `.sk-btn.sk-btn--ai` (contorno verde)
- **Acordeão:** `.sk-accordion(.is-open) > .sk-accordion-head (.sk-accordion-chev) + .sk-accordion-body` (Estilo / Assinatura / Exportar)
- **Selo na capa:** `.sk-selo > .sk-selo-mark`

Comportamento (como no protótipo): os sliders aplicam `filter: brightness()/contrast()/saturate()` na camada de fundo do canvas; a Camada é um `<div>` sobreposto; o Tema do texto troca a cor do texto do canvas.

## Regras da marca

1. **Acento é palavra, nunca bloco.** Roxo colore a palavra-chave do título — não pinte caixas inteiras de roxo.
2. **Um primário por tela.** Só um `.sk-btn` roxo cheio por vista; o resto é secundário/fantasma.
3. **Lime com parcimônia.** Reservado a destaques positivos (aprovar, ganho).
4. **Claro é o padrão.** Escuro entra na UI do produto e como contraponto (~30% do feed).
5. **Display em caixa-alta.** Anton é sempre `text-transform:uppercase`, entrelinha apertada.

---
Fonte da verdade dos valores: `design-system/tokens/tokens.json`. Mudou lá, atualize os tokens aqui.
