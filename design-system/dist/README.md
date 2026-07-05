# Grupo Smark — Design System

Pacote de implementação do sistema visual do painel de conteúdo (smark · Provider Max · Elever AI).
Claro por padrão, escuro sob demanda. Roxo é a marca, lime é o segundo acento.

## Arquivos

| Arquivo | O que é |
|---|---|
| `smark-ds.css` | Folha única: tokens (CSS variables) + classes de componentes. Drop-in. |
| `smark-design-system.html` | Página de referência interativa (offline), com todos os componentes e o toggle de tema. |
| `README.md` | Este guia. |

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

## Regras da marca

1. **Acento é palavra, nunca bloco.** Roxo colore a palavra-chave do título — não pinte caixas inteiras de roxo.
2. **Um primário por tela.** Só um `.sk-btn` roxo cheio por vista; o resto é secundário/fantasma.
3. **Lime com parcimônia.** Reservado a destaques positivos (aprovar, ganho).
4. **Claro é o padrão.** Escuro entra na UI do produto e como contraponto (~30% do feed).
5. **Display em caixa-alta.** Anton é sempre `text-transform:uppercase`, entrelinha apertada.

---
Fonte da verdade dos valores: `design-system/tokens/tokens.json`. Mudou lá, atualize os tokens aqui.
