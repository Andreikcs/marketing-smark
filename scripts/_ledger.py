#!/usr/bin/env python3
"""Ledger append-only de gerações de imagem: uma linha JSON por chamada.

Base do custo por peça, por marca e por campanha. Nunca derruba a geração:
se não conseguir escrever, avisa em stderr e segue."""
import datetime
import json
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_PADRAO = os.path.join(VAULT, "design-system", "custos", "geracoes.jsonl")


def registrar(evento, path=None):
    """Anexa `evento` ao ledger. Devolve o caminho usado."""
    alvo = path or LEDGER_PADRAO
    ev = dict(evento)
    ev.setdefault("data", datetime.datetime.now().isoformat(timespec="seconds"))
    try:
        dirname = os.path.dirname(alvo)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(alvo, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"AVISO: não foi possível gravar no ledger ({e})", file=sys.stderr)
    return alvo
