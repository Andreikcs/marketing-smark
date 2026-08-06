# Grupo Smark — Design System · pacote portátil

Sistema visual da smark, Provider Max e Elever AI, empacotado para ser aplicado em
**outro projeto**, em qualquer stack (HTML puro, Django, Flask, Rails, Next.js, Astro…).

Não tem build, não tem dependência, não tem framework. É CSS com variáveis.

---

## O que tem aqui

| Arquivo | O que é | Você usa? |
|---|---|---|
| `smark-ds.css` | **Folha única: tokens + todos os componentes `.sk-*`.** Drop-in, 34 KB. | ✅ é este que entra no código |
| `tokens.css` | Só as variáveis CSS (sem componente nenhum). | ✅ se você já tem componentes próprios |
| `tokens.json` | Os mesmos valores em JSON, para gerar tema, preset ou documentação. | 🔧 build / automação |
| `galeria.html` | Galeria navegável com tudo renderizado, claro e escuro. | 👁️ referência e print |
| `README.md` | Este guia. | 📖 |

> **Escolha uma das duas folhas.** `smark-ds.css` já contém `tokens.css` dentro dele —
> carregar as duas duplica as variáveis sem quebrar nada, mas é desperdício.

---

## Instalação em 3 passos

**1.** Copie `smark-ds.css` para os assets do projeto-destino (ex.: `static/css/smark-ds.css`).

**2.** Declare o tema na raiz e a classe `sk` no body:

```html
<!doctype html>
<html lang="pt-BR" data-theme="claro">   <!-- "claro" (padrão) ou "escuro" -->
<head>
  <link rel="stylesheet" href="/static/css/smark-ds.css">
</head>
<body class="sk">
  …
</body>
</html>
```

`body class="sk"` é obrigatório — é o que aplica fundo, cor de texto e a família tipográfica.
Sem `data-theme` o sistema assume claro.

**3.** Use as classes. Nada é automático em elemento nativo: um `<button>` sem `.sk-btn`
continua sendo um botão do navegador.

```html
<button class="sk-btn">Ação primária</button>
<input class="sk-input" placeholder="Buscar…">
<div class="sk-card">…</div>
```

### Fontes

O CSS importa Anton, Archivo e JetBrains Mono do Google Fonts na primeira linha.
Se o projeto-destino não pode bater no Google (CSP, offline, LGPD), remova o `@import`
do topo do arquivo e sirva as fontes localmente — os `font-family` continuam funcionando
pelos fallbacks (`system-ui`, `ui-monospace`).

### Trocar de tema em runtime

```js
document.documentElement.setAttribute('data-theme', 'escuro');
```

Para aplicar um tema só em um trecho da página, use as classes `.theme-claro` / `.theme-escuro`
num container — elas redeclaram as variáveis localmente.

---

## Os tokens

Tudo é variável CSS. Se você só quer as cores certas sem adotar os componentes,
use `tokens.css` e escreva o seu próprio CSS em cima de `var(--accent)`, `var(--surface)` etc.

### Cor

| Grupo | Variáveis |
|---|---|
| Superfície | `--bg` `--surface` `--surface-2` `--inset` |
| Texto | `--text` `--sub` `--muted` |
| Traço | `--line` `--line-strong` `--field` `--field-line` |
| Acento | `--accent` `--accent-2` `--accent-soft` `--accent-ink` |
| Acento 2 | `--lime` `--lime-ink` `--lime-soft` |
| Semântico | `--good` `--warn` `--bad` `--info` (+ cada um com `-soft`) |
| Elevação | `--shadow` `--shadow-lg` |

Roxo `#8B3CF7` é o primário do grupo. Lime `#C6F24E` é o segundo acento — só destaque positivo.
No tema escuro o roxo clareia para `#B18BFF` para manter contraste legível.

### Tipografia

`--font-display` (Anton) · `--font-text` (Archivo) · `--font-mono` (JetBrains Mono)

Classes prontas: `.sk-h1` `.sk-h2` `.sk-display` `.sk-kicker` `.sk-lead` `.sk-accent` `.sk-mono`

### Forma e ritmo

`--radius-sm|md|lg|pill` = 8 / 12 / 16 / 999 px
`--space-1|2|3|4|6|8|12|16` = 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 px

---

## Mapa de componentes

Todas as classes começam com `.sk-`. Modificadores usam `--` (`.sk-btn--ghost`);
estados usam `.is-` (`.is-active`, `.is-open`, `.is-on`, `.is-selected`).

| Área | Classes |
|---|---|
| **Botões** | `.sk-btn` + `--secondary` `--ghost` `--lime` `--danger` `--sm` `--lg` `--icon` `--studio` `--ai` |
| **Formulário** | `.sk-label` `.sk-input` `.sk-textarea` `.sk-select` `.sk-toggle` `.sk-check` `.sk-radio` `.sk-slider` `.sk-richbar` `.sk-emojigrid` `.sk-choicegrid`/`.sk-choice` |
| **Superfície** | `.sk-card` + `--flat` `--brand` · `.sk-metric-label` `.sk-metric-value` |
| **Navegação** | `.sk-topbar` `.sk-navlink` `.sk-tabs`/`.sk-tab` `.sk-segmented` `.sk-breadcrumb` `.sk-page` `.sk-pill` `.sk-menu` `.sk-stepper` |
| **Feedback** | `.sk-badge` `.sk-alert` `.sk-toast` `.sk-overlay`/`.sk-modal` `.sk-progress` `.sk-spinner` `.sk-skel` `.sk-tip` `.sk-popover` `.sk-empty` |
| **Dados** | `.sk-table` (`-head` `-row`) `.sk-list` `.sk-avatar` `.sk-chip` `.sk-cal` `.sk-command` `.sk-kbd` |
| **Composto** | `.sk-pagehead` `.sk-toolbar` `.sk-filter-group` `.sk-cardgrid` `.sk-post` `.sk-editor` `.sk-prop-section` `.sk-accordion` `.sk-thumbrail` `.sk-selo` |
| **Util** | `.sk-stack` `.sk-row` `.sk-gap-2|3|4` `.sk-grid-2` `.sk-grid-3` `.sk-spacer` `.sk-mono` |

Abra `galeria.html` para ver a marcação exata de cada um — a galeria é o exemplo executável.

### Detalhes que costumam pegar

- **Tabela:** `.sk-table-head` e `.sk-table-row` são grids. Você define as colunas inline,
  por tabela: `style="grid-template-columns:2.4fr 1fr 1fr 1fr"`. Cabeçalho e linhas
  precisam do **mesmo** valor.
- **Topbar:** é `position:sticky` e usa `color-mix()` + `backdrop-filter`. Se o alvo
  precisa suportar navegador antigo, troque o `background` por um `var(--bg)` sólido.
- **Toast:** é `position:fixed`. Injete no `<body>`, não dentro de um container com `transform`.
- **Ícones:** o sistema não traz biblioteca de ícone. A galeria usa SVG inline estilo Feather
  com `stroke="currentColor"` e `stroke-width` 2 — mantenha esse padrão.

---

## Regras da marca

Isto não é estilo, é identidade. Quebrou aqui, o resultado deixa de parecer smark:

1. **O acento é a palavra, nunca o bloco.** Roxo colore a palavra-chave do título.
   Não pinte caixas inteiras de roxo.
2. **Um primário por tela.** Um único `.sk-btn` cheio por vista; o resto é
   `--secondary` ou `--ghost`.
3. **Lime com parcimônia.** Só confirmação positiva (aprovar, ganho, saldo).
4. **Claro é o padrão.** Escuro entra na UI de produto e como contraponto.
5. **Display em caixa-alta.** Anton é sempre `uppercase` com entrelinha 0.94–1.
   Anton nunca carrega texto corrido.
6. **Quadrados de moldura** (chip, selo, CTA de arte) usam o degradé roxo→azul
   `linear-gradient(155deg,#9A4DFF,#2A1CA8)` — é o padrão do ecossistema.

---

## Trocar de marca

O sistema é um só; a marca troca o acento, o gradiente e a assinatura. Para rodar o
projeto-destino nas cores de outra marca do grupo, redeclare duas variáveis:

```css
:root[data-marca="provider-max"]{ --accent:#8B3CF7; --accent-2:#A472FF; }
:root[data-marca="elever-ai"]   { --accent:#8B3CF7; --accent-2:#A472FF; }
```

Os hex de cada marca, incluindo gradiente, glyph e path do símbolo, estão em `tokens.json`
→ `marcas`.

---

## Ver e printar

```bash
cd design-system/export
python3 -m http.server 8790
# abre http://localhost:8790/galeria.html
```

Abrir o arquivo direto com `file://` também funciona (não há fetch nem módulo),
mas servir é mais fiel ao ambiente real.

---

## Manutenção

A fonte da verdade **dentro do vault** é `design-system/tokens/tokens.json`.
Este pacote é uma exportação: mudou o token lá, atualize aqui o bloco `1. TOKENS`
de `smark-ds.css`, o `tokens.css` e o `tokens.json`.

Nota conhecida: `.sk-slider` está definido duas vezes em `smark-ds.css` (seção 11 e
seção 12) — a segunda vence. Inofensivo, mas se for editar, edite as duas.
