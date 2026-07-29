#!/usr/bin/env python3
"""Testes de regessão: DB multi-marca, save/load rápidos, chaves, canais.

Rode: python3 scripts/tests/test_db_sync.py
Com DB: DATABASE_PUBLIC_URL=... python3 scripts/tests/test_db_sync.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
VAULT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))


class TestDbModule(unittest.TestCase):
    def test_disponivel_sem_url(self):
        import _db
        with mock.patch.dict(os.environ, {"DATABASE_URL": "", "DATABASE_PUBLIC_URL": ""}, clear=False):
            # força limpar
            old = os.environ.pop("DATABASE_URL", None)
            oldp = os.environ.pop("DATABASE_PUBLIC_URL", None)
            try:
                self.assertFalse(_db.disponivel())
                self.assertIsNone(_db.upsert_post({"marca": "smark", "slug": "x"}))
                self.assertEqual(_db.load_posts_as_editor()["posts"], [])
            finally:
                if old is not None:
                    os.environ["DATABASE_URL"] = old
                if oldp is not None:
                    os.environ["DATABASE_PUBLIC_URL"] = oldp

    def test_batch_vazio(self):
        import _db
        if not _db.disponivel():
            self.skipTest("sem DATABASE_URL")
        r = _db.upsert_posts_batch([])
        self.assertTrue(r.get("ok"))
        self.assertEqual(r.get("n"), 0)


class TestSaveLoadPerf(unittest.TestCase):
    """save() não pode bloquear em upsert síncrono de N posts."""

    def test_save_is_fast_file_only(self):
        # import editor_server com DATA temporário
        import editor_server as es

        posts = []
        for i in range(20):
            posts.append({
                "marca": "smark",
                "slug": f"t-perf-{i}",
                "titulo": f"T{i}",
                "size": "1080x1350",
                "status": "rascunho",
                "frames": [{"n": 1, "headline": "h", "sub": "", "cta": "", "tema": "claro"}],
            })
        data = {"posts": posts, "version": 2}

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        old_data = es.DATA
        old_cache = es._MEM_CACHE
        try:
            es.DATA = path
            es._MEM_CACHE = None
            # mock DB flush para não depender de rede
            with mock.patch.object(es, "_schedule_db_flush") as sch:
                t0 = time.time()
                es.save(data)
                elapsed = time.time() - t0
            self.assertLess(elapsed, 0.5, f"save bloqueou {elapsed:.2f}s — deveria ser <0.5s")
            sch.assert_called_once()
            loaded = es.load()
            self.assertEqual(len(loaded["posts"]), 20)
            # 2º load deve vir do cache (sem I/O pesado)
            t0 = time.time()
            loaded2 = es.load()
            self.assertLess(time.time() - t0, 0.2)
            self.assertEqual(len(loaded2["posts"]), 20)
        finally:
            es.DATA = old_data
            es._MEM_CACHE = old_cache
            try:
                os.unlink(path)
            except OSError:
                pass


class TestOpenRouterKeys(unittest.TestCase):
    def test_carregar_chaves_openrouter(self):
        import openai_image as oi
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-test", "OPENAI_API_KEY": "oa-test"}):
            ch = oi.carregar_chaves({})
            self.assertEqual(ch["openrouter"], "or-test")
            self.assertEqual(ch["openai"], "oa-test")

    def test_provedor_exige_openrouter(self):
        import _provedor
        with self.assertRaises(_provedor.ErroProvedor) as cm:
            _provedor.gerar("p", "google/gemini-3-pro-image", "openrouter", {}, timeout=1)
        self.assertIn("OPENROUTER", str(cm.exception))

    def test_para_png_identity(self):
        import _provedor
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        self.assertEqual(_provedor.para_png(png)[:8], b"\x89PNG\r\n\x1a\n")


class TestCanaisIntactos(unittest.TestCase):
    def test_canais_module_import(self):
        import _canais
        self.assertTrue(hasattr(_canais, "modo_instagram"))
        self.assertTrue(hasattr(_canais, "status_marca") or hasattr(_canais, "html_oauth_done"))
        # funções críticas de OAuth
        for name in ("html_oauth_done",):
            self.assertTrue(hasattr(_canais, name), f"falta {_canais}.{name}")

    def test_canal_db_helpers(self):
        import _db
        self.assertTrue(hasattr(_db, "canal_salvar"))
        self.assertTrue(hasattr(_db, "canal_carregar"))
        self.assertTrue(hasattr(_db, "canal_apagar"))


class TestLiveDb(unittest.TestCase):
    """Só roda se DATABASE_* estiver setado (integração)."""

    @classmethod
    def setUpClass(cls):
        # carrega .env se existir
        envp = VAULT / ".env"
        if envp.is_file():
            for line in envp.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        if os.environ.get("DATABASE_PUBLIC_URL") and not os.environ.get("DATABASE_URL"):
            os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]
        # se URL for internal, troca
        import _db
        if "railway.internal" in (_db.database_url() or "") and os.environ.get("DATABASE_PUBLIC_URL"):
            os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]

    def test_roundtrip_one_post(self):
        import _db
        if not _db.disponivel():
            self.skipTest("sem DATABASE_URL")
        _db.init_schema()
        post = {
            "marca": "smark",
            "slug": "test-sync-perf-unit",
            "titulo": "teste unit",
            "size": "1080x1350",
            "status": "rascunho",
            "caption": "cap",
            "canais": ["instagram"],
            "frames": [
                {"n": 1, "headline": "H1", "sub": "S", "cta": "C", "tema": "claro", "bg": ""},
            ],
        }
        t0 = time.time()
        r = _db.upsert_posts_batch([post])
        elapsed = time.time() - t0
        self.assertGreaterEqual(r.get("n"), 1)
        self.assertLess(elapsed, 8.0, f"batch 1 post demorou {elapsed:.1f}s")
        # load deve achar o post
        t0 = time.time()
        data = _db.load_posts_as_editor()
        load_t = time.time() - t0
        self.assertLess(load_t, 8.0, f"load demorou {load_t:.1f}s")
        slugs = {(p.get("marca"), p.get("slug")) for p in data.get("posts") or []}
        self.assertIn(("smark", "test-sync-perf-unit"), slugs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
