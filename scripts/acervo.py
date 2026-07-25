#!/usr/bin/env python3
"""Curadoria do acervo de peças-referência.

  python3 scripts/acervo.py list --marca smark
  python3 scripts/acervo.py add marcas/smark/.../arte/01.png --marca smark
  python3 scripts/acervo.py rm 2026-07-24-01.png --marca smark

Só entra peça aprovada. O acervo alimenta input_references nas gerações
seguintes — peça mediana aqui puxa a qualidade das próximas pra baixo."""
import argparse
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _acervo  # noqa: E402
import _perfil  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["add", "list", "rm"])
    ap.add_argument("alvo", nargs="?", default="")
    ap.add_argument("--marca", default="smark")
    args = ap.parse_args()

    perfil = _perfil.resolver(args.marca)
    d = perfil["acervo_dir"]
    if not d:
        sys.exit(f"ERRO: família '{perfil['familia']}' sem diretório de acervo no contrato")

    if args.acao == "list":
        itens = _acervo.listar(d, perfil["acervo_max"])
        print(f"Acervo de '{perfil['familia']}' ({len(itens)}/{perfil['acervo_max']}) em {d}")
        for p in itens:
            print("  " + os.path.basename(p))
        if not perfil["acervo_ativo"]:
            print("\nAVISO: acervo INATIVO no contrato — não está sendo injetado nas gerações.")
            print("Ative com \"acervo\": {\"ativo\": true} na família em "
                  "design-system/tokens/perfis-imagem.json")
        return

    if not args.alvo:
        sys.exit(f"ERRO: '{args.acao}' precisa de um alvo")

    if args.acao == "add":
        origem = args.alvo if os.path.isabs(args.alvo) else os.path.join(VAULT, args.alvo)
        destino = _acervo.adicionar(origem, d)
        n = len(_acervo.listar(d, 10 ** 6))
        print(f"OK: {destino}")
        if n > perfil["acervo_max"]:
            print(f"AVISO: acervo com {n} peças, acima do teto de {perfil['acervo_max']}. "
                  "As mais antigas deixam de ser usadas.")
        return

    if args.acao == "rm":
        print("OK: removida" if _acervo.remover(args.alvo, d) else "nada a remover")


if __name__ == "__main__":
    main()
