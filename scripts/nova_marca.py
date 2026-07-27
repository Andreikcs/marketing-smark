#!/usr/bin/env python3
"""Cria / lista marcas de cliente no vault (Sprint multi-marca).

  python3 scripts/nova_marca.py list
  python3 scripts/nova_marca.py add --slug netsul --nome "NetSul Fibra" --acento "#E0562D"
  python3 scripts/nova_marca.py add --slug foo --nome "Foo" --acento "#3366FF" --logo /path/logo.png
  python3 scripts/nova_marca.py check --slug netsul

Não altera smark/provider-max/elever-ai. Qualidade: exige nome + acento hex;
cria branding mínimo (identidade, voz, tom, do-and-dont).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _marcas  # noqa: E402


def cmd_list(_):
    for d in _marcas.listar_detalhes():
        flag = "pronta" if d["pronta"] else "INCOMPLETA"
        can = " · canônica" if d["canonica"] else ""
        print(f"  {d['slug']:20s}  {d['nome']:24s}  {d['acento']}  {flag}{can}")
    orfas = _marcas.pastas_sem_registro()
    if orfas:
        print("\nPastas sem registro no tokens.json:")
        for o in orfas:
            print(f"  ⚠ {o}  → rode: nova_marca.py add --slug {o} ...")


def cmd_add(a):
    try:
        r = _marcas.criar(
            a.slug, a.nome, a.acento,
            acento_claro=a.acento_claro or None,
            handle=a.handle or None,
            glyph=a.glyph or None,
            wordmark=a.wordmark or None,
            endossa=a.endossa,
            mood=a.mood or "",
        )
    except ValueError as e:
        sys.exit(f"ERRO: {e}")
    if a.logo:
        try:
            dest = _marcas.copiar_logo(r["slug"], a.logo if os.path.isabs(a.logo)
                                       else os.path.join(_marcas.VAULT, a.logo))
            print(f"logo: {dest}")
        except Exception as e:
            print(f"AVISO: logo não copiado ({e})", file=sys.stderr)
    print(f"OK: marca '{r['slug']}' criada")
    print(f"  dir: {r['dir']}")
    print(f"  pronta: {r['pronta']}")
    print(f"  tokens: acento {r['meta']['acento']} · handle {r['meta']['handle']}")
    print("\nPróximos passos:")
    print(f"  1. Revise marcas/{r['slug']}/branding/")
    print(f"  2. No Editor, selecione a marca '{r['slug']}' e gere 3 peças-piloto")
    print(f"  3. Só entregue lote com tier=final (Gemini) após aprovação visual")


def cmd_check(a):
    slug = a.slug
    if not _marcas.exists(slug):
        sys.exit(f"ERRO: '{slug}' não registrada")
    meta = _marcas.get(slug)
    ok = _marcas.pronta(slug)
    print(json.dumps({
        "slug": slug,
        "meta": {k: meta.get(k) for k in ("nome", "acento", "handle", "wordmark", "mood")},
        "pronta": ok,
        "canonica": slug in _marcas.CANONICAS,
    }, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 2)


def main():
    ap = argparse.ArgumentParser(description="Gestão de marcas do vault")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="lista marcas registradas")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("add", help="cria marca de cliente")
    p.add_argument("--slug", required=True, help="kebab-case, ex: netsul-fibra")
    p.add_argument("--nome", required=True)
    p.add_argument("--acento", required=True, help="hex #RRGGBB")
    p.add_argument("--acento-claro", dest="acento_claro", default="")
    p.add_argument("--handle", default="")
    p.add_argument("--glyph", default="")
    p.add_argument("--wordmark", default="")
    p.add_argument("--mood", default="", help="mood em inglês p/ direção de arte")
    p.add_argument("--logo", default="", help="caminho de PNG/SVG do logo")
    p.add_argument("--endossa", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("check", help="verifica se marca está pronta")
    p.add_argument("--slug", required=True)
    p.set_defaults(func=cmd_check)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
