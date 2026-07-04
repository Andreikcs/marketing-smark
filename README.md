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

````
```dataview
TABLE marca, canal, data
FROM "marcas"
WHERE status = "draft" AND contains(file.path, "publicacoes")
SORT data DESC
```
````

### Referências mais reutilizadas

````
```dataview
TABLE length(file.inlinks) AS "usada x"
FROM "marcas"
WHERE contains(file.path, "referencias") AND tipo != null
SORT length(file.inlinks) DESC
LIMIT 20
```
````

## Estado do vault (2026-06-23)

Posicionamento e voz reposicionados (brief Pedro Muschitz): **2 camadas** — smark (mãe) = método/assessoria; produtos = o funcionário de IA. Linguagem simples (criança de 7 anos), sem jargão na vitrine, sem promessa de venda. Visual **claro por padrão** + símbolo **APEX v3**.

| Marca | Posicionamento (uma frase) | Status |
|---|---|---|
| **smark** | "Assessoria tecnológica para crescer com eficiência e escala — sem trocar o que já funciona." | ✅ aplicado (v2.1) · método em `metodo-maia.md` |
| **Provider Max** | "Um funcionário de IA que renova os contratos dos seus clientes — sozinho, dia e noite, sem você contratar mais gente." | ✅ aplicado (v2.3) |
| **Elever AI** | "Um vendedor de IA no WhatsApp que atende seus clientes dia e noite — e nunca deixa ninguém sem resposta. Você só fecha." | ✅ aplicado (v2.3) |

Réguas de voz em `shared/voz-grupo.md` (tradutor DE→PARA + jargão proibido). Gate: `scripts/revisar.py`. Design system espelhado em claude.ai/design ("Grupo Smark — Design System").
