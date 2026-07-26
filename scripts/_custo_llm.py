#!/usr/bin/env python3
"""Estima custo USD de chamadas LLM a partir de tokens e tabela local."""
import json
import os

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABELA = os.path.join(VAULT, "design-system", "custos", "precos-llm.json")


def _carregar():
    try:
        with open(TABELA, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"modelos": {}, "fallback": {"input_por_mtok": 5.0, "output_por_mtok": 25.0}}


def preco_modelo(modelo):
    cfg = _carregar()
    m = (modelo or "").strip()
    tab = cfg.get("modelos") or {}
    if m in tab:
        return tab[m]
    # match parcial (claude-opus-4-8-2025... → claude-opus-4-8)
    for k, v in tab.items():
        if m.startswith(k) or k in m:
            return v
    return cfg.get("fallback") or {"input_por_mtok": 5.0, "output_por_mtok": 25.0}


def custo_tokens(modelo, input_tokens=0, output_tokens=0):
    """US$ a partir de tokens. Arredonda a 6 casas."""
    p = preco_modelo(modelo)
    inp = float(p.get("input_por_mtok") or 0) * (int(input_tokens or 0) / 1_000_000)
    out = float(p.get("output_por_mtok") or 0) * (int(output_tokens or 0) / 1_000_000)
    return round(inp + out, 6)
