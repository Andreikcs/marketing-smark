---
tipo: calendario-conteudo
escopo: todas-as-marcas
versao: 1.0
atualizado: 2026-06-10
---

# Calendário de Conteúdo — Grupo Smark

Hub de planejamento e produção das 3 marcas. Use com `/pauta` (geração em lote) e `/post-instagram` / `/post-linkedin` (avulso). Fluxo **híbrido**: enche o calendário em lote e encaixa avulsos do momento.

## Pauta da semana (preencher)

| Data | Marca | Canal | Tema | Pilar | Formato | Status |
|---|---|---|---|---|---|---|
| 2026-06-12 | smark | instagram | _(tema)_ | _(pilar)_ | post | planejado |
| | | | | | | |

> Edite esta tabela à mão, ou peça `/pauta smark instagram` que eu sugiro 5 temas a partir dos pilares e referências.

## Painel de produção (Dataview)

> Requer o plugin **Dataview** no Obsidian.

Todos os posts, por status e data:

```dataview
TABLE marca, canal, formato, status, data
FROM "marcas"
WHERE canal AND data
SORT data DESC
```

Drafts aguardando revisão:

```dataview
TABLE marca, canal, file.link AS post
FROM "marcas"
WHERE status = "draft"
SORT data DESC
```

## Fluxo de produção (estados)

`planejado` → `draft` (gerado) → `revisado` (você aprovou) → `aprovado` (arte ok, agendado) → `publicado` (recebe `url-publicado`).

Ver também: [[shared/padroes-instagram]] · [[shared/formatos-canais]] · [[shared/voz-grupo]].
