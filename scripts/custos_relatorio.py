#!/usr/bin/env python3
"""Relatório de custos: imagem (OpenRouter) + copy (Claude) em USD e BRL.

  python3 scripts/custos_relatorio.py
  python3 scripts/custos_relatorio.py --periodo 2026-07
  python3 scripts/custos_relatorio.py --slug case-destaque --marca smark
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ledger  # noqa: E402
import _cambio  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--periodo", default="", help="YYYY-MM ou vazio = tudo")
    ap.add_argument("--slug", default="")
    ap.add_argument("--marca", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cot = _cambio.cotacao()
    if a.slug:
        t = _ledger.totais_por_post(a.slug, a.marca)
        if a.json:
            print(json.dumps(t, ensure_ascii=False, indent=2))
            return
        print(f"Post: {t['slug']} ({t['marca'] or '—'})")
        print(f"  Imagens ({t['n_imagens']}): US$ {t['imagem_usd']:.4f} · R$ {t['imagem_brl']:.2f}")
        print(f"  Copy    ({t['n_copys']}): US$ {t['copy_usd']:.4f} · R$ {t['copy_brl']:.2f}")
        print(f"  TOTAL:        US$ {t['total_usd']:.4f} · R$ {t['total_brl']:.2f}")
        print(f"  Cotação USD/BRL {t['usd_brl']:.4f} ({t.get('cambio_fonte')})")
        return

    r = _ledger.resumo_periodo(a.periodo)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    print("=== Custos Smark vault ===")
    print(f"Período: {r['periodo']}")
    print(f"Cotação: USD/BRL {r['usd_brl']:.4f} ({r.get('cambio_fonte')}, {r.get('cambio_em')})")
    print()
    print(f"🖼  Imagem OpenRouter/OpenAI  n={r['n_imagens']:4d}   "
          f"US$ {r['imagem_usd']:.4f}   R$ {r['imagem_brl']:.2f}")
    print(f"📝 Copy Claude/chat          n={r['n_copys']:4d}   "
          f"US$ {r['copy_usd']:.4f}   R$ {r['copy_brl']:.2f}")
    print(f"Σ  TOTAL                              "
          f"US$ {r['total_usd']:.4f}   R$ {r['total_brl']:.2f}")
    print()
    if r["n_copys"] == 0:
        print("Nota: ledger de copy vazio — custos Claude passam a ser gravados "
              "nas próximas gerações do Estúdio (após este deploy).")


if __name__ == "__main__":
    main()
