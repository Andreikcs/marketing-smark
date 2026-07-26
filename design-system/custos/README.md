# Custos de geração

`geracoes.jsonl` — ledger append-only, uma linha por geração de imagem.

Campos: `data`, `familia`, `marca`, `slug`, `tipo`, `tier` (`final`|`rascunho`),
`modelo`, `provider`, `seed`, `resolucao`, `custo_usd`, `refs`, `ok`,
`publicavel`, `gate_poluido`, `suplente_usado`, `nao_calibrado`, `arquivo`.

- **final** — Gemini 4K (~US$ 0,24), publicável
- **rascunho** — Seedream (~US$ 0,04), NÃO publicável; use para explorar e depois `--tier final`

`custo_usd` só vem preenchido no provider `openrouter` — a OpenAI não devolve
custo na resposta.

Total do mês:

```bash
grep '"data":"2026-07' design-system/custos/geracoes.jsonl \
  | python3 -c "import json,sys; print(round(sum((json.loads(l).get('custo_usd') or 0) for l in sys.stdin),2))"
```

Por marca:

```bash
python3 -c "
import json,collections
t=collections.Counter()
for l in open('design-system/custos/geracoes.jsonl'):
    e=json.loads(l); t[e.get('marca') or '?'] += e.get('custo_usd') or 0
for m,v in t.most_common(): print(f'{m:20s} US\$ {v:.2f}')
"
```
