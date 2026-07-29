#!/usr/bin/env python3
"""Gera thumbs de ALTA QUALIDADE (composição completa: fundo+texto+logo).

Uso local (precisa Chrome headless):
  python3 scripts/regen_thumbs_hq.py
  python3 scripts/regen_thumbs_hq.py --limit 5

Saída: .thumbs/<marca>__<slug>.jpg  (540px largura, q=88)
Atualiza editor.json e Postgres se DATABASE_URL estiver setado.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# .env
envp = os.path.join(VAULT, ".env")
if os.path.isfile(envp):
    for line in open(envp, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
if os.environ.get("DATABASE_PUBLIC_URL") and (
    not os.environ.get("DATABASE_URL") or "railway.internal" in os.environ.get("DATABASE_URL", "")
):
    if not os.environ.get("RAILWAY_ENVIRONMENT"):
        os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]

import compositor  # noqa: E402
import _marcas  # noqa: E402

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow necessário", file=sys.stderr)
    sys.exit(1)


def load_posts():
    try:
        import _db
        if _db.disponivel():
            d = _db.load_posts_as_editor()
            if d.get("posts"):
                return d["posts"]
    except Exception as e:
        print("DB aviso:", e, file=sys.stderr)
    path = os.path.join(VAULT, "editor.json")
    return json.load(open(path, encoding="utf-8")).get("posts") or []


def frame_to_html(post, fr):
    marca = post.get("marca") or "smark"
    try:
        _marcas.ensure_stub(marca)
    except Exception:
        pass
    # kwargs alinhados ao editor
    from editor_server import frame_kwargs  # reuse

    kw = frame_kwargs(fr, post.get("size") or "1080x1350", for_export=True, marca=marca)
    html, w, h = compositor.compose_html(**kw)
    return html, w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="slug parcial")
    args = ap.parse_args()

    out_dir = os.path.join(VAULT, ".thumbs")
    os.makedirs(out_dir, exist_ok=True)
    posts = load_posts()
    ok = err = 0
    for i, p in enumerate(posts):
        if args.limit and ok + err >= args.limit:
            break
        slug = p.get("slug") or f"p{i}"
        marca = p.get("marca") or "smark"
        if args.only and args.only not in slug and args.only not in marca:
            continue
        frs = p.get("frames") or []
        if not frs:
            continue
        fr = frs[0]
        dest = os.path.join(out_dir, f"{marca}__{slug}.jpg")
        try:
            html, w, h = frame_to_html(p, fr)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                png_path = tmp.name
            if not compositor.render_html_to_png(html, png_path, w, h):
                raise RuntimeError("chrome screenshot falhou")
            im = Image.open(png_path).convert("RGB")
            im.thumbnail((540, 680), Image.Resampling.LANCZOS)
            im.save(dest, "JPEG", quality=88, optimize=True)
            try:
                os.unlink(png_path)
            except OSError:
                pass
            rel = os.path.relpath(dest, VAULT).replace("\\", "/")
            p["thumb"] = rel
            fr["thumb"] = rel
            ok += 1
            print(f"OK {marca}/{slug} → {rel} ({os.path.getsize(dest)} bytes)")
        except Exception as e:
            err += 1
            print(f"ERR {marca}/{slug}: {e}", file=sys.stderr)

    # persist
    data = {"posts": posts, "version": 2}
    open(os.path.join(VAULT, "editor.json"), "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=2)
    )
    try:
        import _db
        if _db.disponivel():
            r = _db.upsert_posts_batch(posts)
            print("DB", r)
    except Exception as e:
        print("DB skip", e)
    print(f"done ok={ok} err={err}")


if __name__ == "__main__":
    main()
