#!/usr/bin/env python3
"""Migra editor.json + marcas (tokens) + notas .md → Postgres.

Uso:
  DATABASE_PUBLIC_URL=postgresql://... python3 scripts/migrate_to_db.py
  # ou com .env carregado
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# carrega .env
env_path = os.path.join(VAULT, ".env")
if os.path.isfile(env_path):
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# prefer public URL local
if not os.environ.get("DATABASE_URL") and os.environ.get("DATABASE_PUBLIC_URL"):
    os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]

import _db  # noqa: E402
import _marcas  # noqa: E402


def migrate_marcas():
    n = 0
    for slug in _marcas.list_slugs():
        m = _marcas.get(slug)
        m = dict(m)
        m["nome"] = m.get("nome") or slug
        m["papel"] = m.get("papel") or ("canonica" if slug in getattr(_marcas, "CANONICAS", ()) else "cliente")
        _db.ensure_marca(slug, m)
        n += 1
    return n


def migrate_editor():
    path = os.path.join(VAULT, "editor.json")
    if not os.path.isfile(path):
        print("AVISO: editor.json não encontrado")
        return 0
    data = json.load(open(path, encoding="utf-8"))
    posts = data.get("posts") or []
    # backup
    bak = path + ".pre-migrate.bak"
    open(bak, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"backup: {bak}")
    ok = 0
    for p in posts:
        try:
            pid = _db.upsert_post(p)
            if pid:
                ok += 1
                print(f"  post ok: {p.get('marca')}/{p.get('slug')} id={pid}")
        except Exception as e:
            print(f"  ERRO post {p.get('slug')}: {e}")
    return ok


def migrate_notas():
    import glob
    n = 0
    for md in glob.glob(os.path.join(VAULT, "marcas", "*", "publicacoes", "social", "*", "*.md")):
        rel = os.path.relpath(md, VAULT)
        parts = rel.split(os.sep)
        # marcas/<marca>/publicacoes/social/<canal>/file.md
        if len(parts) < 6:
            continue
        marca, canal = parts[1], parts[4]
        try:
            raw = open(md, encoding="utf-8").read()
        except OSError:
            continue
        fm, body = {}, raw
        if raw.startswith("---"):
            bits = raw.split("---", 2)
            if len(bits) >= 3:
                body = bits[2].lstrip("\n")
                for line in bits[1].splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip().strip('"').strip("'")
        titulo = fm.get("titulo") or fm.get("title") or os.path.basename(md)
        try:
            _db.ensure_marca(marca)
            with _db.conn() as c:
                with c.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO nota_publicacao (marca, canal, path, titulo, frontmatter, body, updated_at)
                        VALUES (%s,%s,%s,%s,%s::jsonb,%s,NOW())
                        ON CONFLICT (path) DO UPDATE SET
                          titulo=EXCLUDED.titulo,
                          frontmatter=EXCLUDED.frontmatter,
                          body=EXCLUDED.body,
                          updated_at=NOW()
                        """,
                        (marca, canal, rel, titulo, json.dumps(fm, ensure_ascii=False), body),
                    )
            n += 1
        except Exception as e:
            print(f"  ERRO nota {rel}: {e}")
    return n


def main():
    if not _db.disponivel():
        # tenta puxar do railway CLI
        print("DATABASE_URL ausente — exporte DATABASE_PUBLIC_URL do Railway")
        sys.exit(1)
    print("DSN ok")
    st = _db.init_schema()
    print("schema:", st)
    nm = migrate_marcas()
    print(f"marcas: {nm}")
    np = migrate_editor()
    print(f"posts editor: {np}")
    nn = migrate_notas()
    print(f"notas md: {nn}")
    print("contagens:", _db.contagens())
    # reexport editor from DB for safety check
    rebuilt = _db.load_posts_as_editor()
    out = os.path.join(VAULT, "editor.json.from-db.json")
    open(out, "w", encoding="utf-8").write(json.dumps(rebuilt, ensure_ascii=False, indent=2))
    print(f"reconstruído: {out} ({len(rebuilt.get('posts') or [])} posts)")
    print("OK")


if __name__ == "__main__":
    main()
