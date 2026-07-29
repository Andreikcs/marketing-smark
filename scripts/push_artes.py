#!/usr/bin/env python3
"""Sobe as artes pro Postgres — é isso que faz a galeria funcionar em produção.

O Railway não recebe os PNGs de `marcas/**/_regen/` (o deploy estouraria o limite
de upload), então até agora a produção montava `background-image:url(/marcas/...)`
apontando pra arquivo que não existe lá: card com texto e sem arte.

Este script resolve na origem. Para cada frame:

  fundo  → JPEG web (máx 1440px, q85)   → arte_blob kind='bg'    → fr['bg_sha']
  final  → composição 1080x1350 (Chrome) → arte_blob kind='final' → fr['arte_sha']

E o servidor passa a servir os dois em /bg/<sha>.jpg e /arte/<sha>.jpg — URLs
públicas, imutáveis e cacheáveis, que funcionam igual no Mac e no Railway. A do
final é também a URL HTTPS que o Instagram exige pra publicar.

**Não é mais rotina.** Desde que o servidor ganhou Chromium, ele compõe a arte
sozinho ao salvar (`_agendar_arte` no editor_server) — quem edita na tela não
precisa rodar nada. Este script continua útil para *backfill*: subir os fundos
originais que só existem no disco do Mac, ou reprocessar tudo depois de mudar o
design. O render em si é o mesmo código dos dois lados (`scripts/_arte.py`), de
propósito: o que o cliente aprova tem que ser o que vai pro Instagram.

  python3 scripts/push_artes.py                 # tudo que mudou
  python3 scripts/push_artes.py --only covatti  # só uma marca/slug
  python3 scripts/push_artes.py --force         # reprocessa mesmo sem mudança
  python3 scripts/push_artes.py --dry-run       # só mostra o que faria
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# .env — o LaunchAgent/terminal nem sempre exporta DATABASE_PUBLIC_URL
envp = os.path.join(VAULT, ".env")
if os.path.isfile(envp):
    for line in open(envp, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
if os.environ.get("DATABASE_PUBLIC_URL") and not os.environ.get("RAILWAY_ENVIRONMENT"):
    if "railway.internal" in os.environ.get("DATABASE_URL", "") or not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]

import _db  # noqa: E402

# Um renderizador só, compartilhado com o servidor — ver docstring de _arte.py.
from _arte import (  # noqa: E402
    BG_MAX, BG_Q, html_do_frame, html_para_jpeg, para_jpeg_web, sha256, sha_arquivo,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="filtra por marca ou slug (substring)")
    ap.add_argument("--force", action="store_true", help="reprocessa mesmo sem mudança")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sem-final", action="store_true", help="só os fundos (mais rápido)")
    args = ap.parse_args()

    if not _db.disponivel():
        sys.exit("ERRO: DATABASE_URL/DATABASE_PUBLIC_URL ausente — não dá pra subir blob")
    _db.init_schema()

    ed_path = os.path.join(VAULT, "editor.json")
    data = json.load(open(ed_path, encoding="utf-8"))
    posts = data.get("posts") or []

    # o que já está lá — evita reenviar dezenas de MB a cada rodada
    ja = set()
    shas_conhecidos = [s for p in posts for f in (p.get("frames") or [])
                       for s in (f.get("bg_sha"), f.get("arte_sha")) if s]
    if shas_conhecidos:
        ja = _db.blob_existe(shas_conhecidos)

    n_bg = n_final = n_skip = n_err = 0
    bytes_env = 0

    for p in posts:
        marca = p.get("marca") or "smark"
        slug = p.get("slug") or "?"
        if args.only and args.only not in marca and args.only not in slug:
            continue
        for fr in (p.get("frames") or []):
            alvo = f"{marca}/{slug}#{fr.get('n', 1)}"

            # ── fundo ───────────────────────────────────────────────────────
            rel = (fr.get("bg") or "").strip()
            if rel:
                src = rel if os.path.isabs(rel) else os.path.join(VAULT, rel)
                if not os.path.isfile(src):
                    if not fr.get("bg_sha"):
                        print(f"·· {alvo}: fundo sumiu do disco ({rel}) — vai usar mesh da marca")
                    n_skip += 1
                else:
                    src_sha = sha_arquivo(src)
                    atual = fr.get("bg_sha") or ""
                    if (not args.force and fr.get("bg_src_sha") == src_sha
                            and atual and atual in ja):
                        n_skip += 1
                    else:
                        try:
                            jpg, w, h = para_jpeg_web(src, BG_MAX, BG_Q)
                            sha = sha256(jpg)
                            if args.dry_run:
                                print(f"[dry] bg    {alvo}  {len(jpg)//1024}KB {w}x{h}")
                            else:
                                if sha not in ja:
                                    _db.blob_put(sha, jpg, kind="bg", w=w, h=h, origem=rel)
                                    ja.add(sha)
                                    bytes_env += len(jpg)
                                print(f"bg    {alvo}  {len(jpg)//1024}KB {w}x{h}  {sha[:12]}")
                            fr["bg_sha"] = sha
                            fr["bg_src_sha"] = src_sha
                            n_bg += 1
                        except Exception as e:
                            n_err += 1
                            print(f"ERR bg {alvo}: {e}", file=sys.stderr)

            # ── arte final (a que o Instagram publica) ───────────────────────
            if args.sem_final:
                continue
            try:
                html, w, h = html_do_frame(p, fr)
            except Exception as e:
                n_err += 1
                print(f"ERR html {alvo}: {e}", file=sys.stderr)
                continue
            # a composição inteira (fundo embutido + texto + cores) vira a chave
            # de cache: mudou qualquer coisa no frame, o hash muda e recompõe.
            src_sha = sha256(html.encode("utf-8"))
            atual = fr.get("arte_sha") or ""
            if not args.force and fr.get("arte_src_sha") == src_sha and atual and atual in ja:
                n_skip += 1
                continue
            if args.dry_run:
                print(f"[dry] final {alvo}  {w}x{h}")
                n_final += 1
                continue
            try:
                jpg, fw, fh = html_para_jpeg(html, w, h)
                sha = sha256(jpg)
                if sha not in ja:
                    _db.blob_put(sha, jpg, kind="final", w=fw, h=fh, origem=f"{marca}/{slug}")
                    ja.add(sha)
                    bytes_env += len(jpg)
                fr["arte_sha"] = sha
                fr["arte_src_sha"] = src_sha
                if int(fr.get("n", 1)) == 1:
                    p["arte_sha"] = sha  # capa do post, pra galeria e vitrine
                n_final += 1
                print(f"final {alvo}  {len(jpg)//1024}KB {fw}x{fh}  {sha[:12]}")
            except Exception as e:
                n_err += 1
                print(f"ERR final {alvo}: {e}", file=sys.stderr)

    if args.dry_run:
        print(f"\n[dry-run] fundos={n_bg} finais={n_final} pulados={n_skip} erros={n_err}")
        return

    with open(ed_path, "w", encoding="utf-8") as f:
        json.dump({"posts": posts, "version": data.get("version", 2)}, f,
                  ensure_ascii=False, indent=2)
    r = _db.upsert_posts_batch(posts)
    st = _db.blob_stats()
    total = sum(v["bytes"] for v in st.values())
    print(f"\nfundos={n_bg} finais={n_final} pulados={n_skip} erros={n_err} "
          f"enviados={bytes_env//1024}KB")
    print(f"posts sincronizados: {r}")
    print(f"arte_blob: {st}  → {total/1e6:.1f} MB no Postgres")


if __name__ == "__main__":
    main()
