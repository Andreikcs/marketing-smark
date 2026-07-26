# Custos do vault (imagem + copy)

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `geracoes.jsonl` | Cada **imagem** (OpenRouter Gemini/Seedream ou edit) |
| `copys.jsonl` | Cada **copy** do Estúdio (Claude / OpenAI chat) |
| `posts.jsonl` | Fechamentos opcionais por post |
| `precos-llm.json` | Tabela US$/MTok para estimar Claude/GPT |
| `cambio-cache.json` | Cache da cotação USD→BRL (15 min) |

## Como o total é calculado

```text
total_usd = Σ custo_usd (imagens do slug) + Σ custo_usd (copys do slug)
total_brl = total_usd × cotação_USD_BRL_ao_vivo
```

Cotação: [AwesomeAPI](https://economia.awesomeapi.com.br/json/last/USD-BRL) via `scripts/_cambio.py`.

## Relatório

```bash
python3 scripts/custos_relatorio.py
python3 scripts/custos_relatorio.py --periodo 2026-07
python3 scripts/custos_relatorio.py --slug case-destaque --marca smark
```

## Campos imagem (`geracoes.jsonl`)

`data`, `familia`, `marca`, `slug`, `tipo`, `tier`, `modelo`, `provider`,
`seed`, `resolucao`, `custo_usd`, `custo_brl`, `usd_brl`, `cambio_fonte`,
`refs`, `ok`, `publicavel`, `gate_poluido`, `arquivo`

## Campos copy (`copys.jsonl`)

`data`, `marca`, `slug`, `pedido`, `modelo`, `provider`, `input_tokens`,
`output_tokens`, `custo_usd`, `custo_brl`, `usd_brl`, `ok`

## Preços de referência (unitário)

| Item | USD | Notas |
|------|-----|--------|
| Imagem final Gemini 4K | ~0,24 | medido |
| Imagem rascunho Seedream | ~0,04 | medido |
| Copy Claude Opus (ordem) | variável | tokens × tabela em `precos-llm.json` |

## UI

- Estúdio mostra custo da **copy** após gerar
- Após gerar **fundo**, mostra **acumulado do post** (copy + imagens) em USD e R$
- Card da imagem: custo imagem USD + R$ + cotação
