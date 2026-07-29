#!/usr/bin/env python3
"""E2E leve (sem browser) do fluxo de preview/composição de imagens.

Garante que:
  - marcas órfãs não derrubam o preview
  - compose_html devolve HTML com headline
  - logo smark resolve no disco
  - frame_kwargs + preview path não quebram
  - dados dos posts (editor.json) não somem

Rodar: python3 scripts/tests/test_e2e_preview_flow.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
VAULT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))


class TestMarcaStubAndLogo(unittest.TestCase):
    def test_ensure_stub_idempotent(self):
        import _marcas
        slug = "e2e-marca-teste-xyz"
        # limpa se sobrou de run anterior (só stub)
        t = _marcas._load_tokens()
        t.get("marcas", {}).pop(slug, None)
        _marcas._save_tokens(t)
        m = _marcas.ensure_stub(slug, "E2E Teste")
        self.assertIsNotNone(m)
        self.assertTrue(_marcas.exists(slug))
        m2 = _marcas.ensure_stub(slug)
        self.assertEqual(m2.get("nome") or slug, m.get("nome") or slug)
        # cleanup
        t = _marcas._load_tokens()
        t.get("marcas", {}).pop(slug, None)
        _marcas._save_tokens(t)

    def test_smark_logo_resolves(self):
        import compositor
        import _marcas
        brands, _ = compositor.load_brands()
        self.assertIn("smark", brands)
        b = brands["smark"]
        # logo_file de smark costuma ser logos-perfil/...
        path = compositor._resolve_logo_file(b.get("logo_file") or "")
        # se não tem logo_file, glyph ainda vale
        if b.get("logo_file"):
            self.assertTrue(path and os.path.isfile(path), f"logo não achado: {b.get('logo_file')}")
        # listar_detalhes logo_url deve ser servível
        det = {d["slug"]: d for d in _marcas.listar_detalhes()}
        sm = det.get("smark") or {}
        if sm.get("logo"):
            full = VAULT / sm["logo"]
            self.assertTrue(full.is_file(), f"logo_url inválida: {sm.get('logo')}")


class TestComposePreview(unittest.TestCase):
    def test_compose_orphan_marca_no_crash(self):
        import compositor
        html, w, h = compositor.compose_html(
            marca="marca-inexistente-e2e-999",
            headline="Teste *destaque*|segunda linha",
            sub="legenda de teste",
            tema="claro",
            size="1080x1350",
            placeholder=True,
        )
        self.assertIn("Teste", html)
        self.assertGreater(w, 100)
        self.assertGreater(len(html), 500)

    def test_compose_smark_with_real_bg_if_exists(self):
        import compositor
        bg = None
        arte = VAULT / "marcas/smark/publicacoes/social/instagram/arte"
        if arte.is_dir():
            for p in arte.rglob("*.png"):
                if "_regen" in p.parts:
                    bg = str(p)
                    break
        html, w, h = compositor.compose_html(
            marca="smark",
            headline="Headline E2E *OK*",
            sub="Subtítulo com legenda",
            cta="CTA teste",
            tema="claro",
            size="1080x1350",
            bg=bg or "",
            placeholder=not bool(bg),
        )
        self.assertIn("Headline E2E", html)
        self.assertIn("legenda", html.lower() or html)
        # wordmark / handle smark costuma aparecer
        self.assertTrue("smark" in html.lower() or "@" in html)

    def test_frame_kwargs_preview_path(self):
        # import editor_server puxa servidor; só funções
        import editor_server as es
        fr = {
            "headline": "Linha um|Linha *dois*",
            "sub": "legenda",
            "cta": "vai",
            "tema": "claro",
            "bgmode": "claro",
        }
        kw = es.frame_kwargs(fr, "1080x1350", for_export=False, marca="smark")
        self.assertEqual(kw["marca"], "smark")
        self.assertIn("headline", kw)
        import compositor
        html, _, _ = compositor.compose_html(**kw)
        self.assertIn("Linha", html)


class TestPostsNotLost(unittest.TestCase):
    def test_editor_json_has_posts(self):
        path = VAULT / "editor.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        posts = data.get("posts") or []
        self.assertGreaterEqual(len(posts), 10, "posts sumiram do editor.json")
        # cada post tem frames
        with_frames = sum(1 for p in posts if p.get("frames"))
        self.assertGreaterEqual(with_frames, 5)

    def test_load_save_roundtrip_memory(self):
        import editor_server as es
        old = es.DATA
        old_cache = es._MEM_CACHE
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            es.DATA = path
            es._MEM_CACHE = None
            sample = {
                "posts": [{
                    "marca": "smark",
                    "slug": "e2e-roundtrip",
                    "titulo": "E2E",
                    "frames": [{"n": 1, "headline": "H", "tema": "claro"}],
                }],
                "version": 2,
            }
            with mock.patch.object(es, "_schedule_db_flush"):
                es.save(sample)
            loaded = es.load()
            self.assertEqual(len(loaded["posts"]), 1)
            self.assertEqual(loaded["posts"][0]["slug"], "e2e-roundtrip")
        finally:
            es.DATA = old
            es._MEM_CACHE = old_cache
            try:
                os.unlink(path)
            except OSError:
                pass


class TestDbIfAvailable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        envp = VAULT / ".env"
        if envp.is_file():
            for line in envp.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        if os.environ.get("DATABASE_PUBLIC_URL"):
            os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]

    def test_db_roundtrip_preserves_frames(self):
        import _db
        if not _db.disponivel():
            self.skipTest("sem DATABASE_URL")
        post = {
            "marca": "smark",
            "slug": "e2e-db-preserve",
            "titulo": "Preserve",
            "caption": "legenda e2e",
            "frames": [
                {"n": 1, "headline": "H1 *x*", "sub": "sub", "cta": "cta", "tema": "claro", "bg": ""},
            ],
        }
        _db.upsert_posts_batch([post])
        data = _db.load_posts_as_editor()
        found = next((p for p in data["posts"] if p.get("slug") == "e2e-db-preserve"), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.get("caption"), "legenda e2e")
        self.assertTrue(found.get("frames"))
        self.assertIn("H1", (found["frames"][0].get("headline") or ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
