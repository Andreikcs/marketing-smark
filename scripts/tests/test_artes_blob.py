#!/usr/bin/env python3
"""Regressão da galeria em produção — artes servidas pelo Postgres.

O bug que isso trava: o Railway não recebe os PNGs de marcas/**/_regen/, e o
preview montava `background-image:url(/marcas/.../x.png)` mesmo assim. O arquivo
404, mas o /preview respondia 200, então o fallback da galeria nunca disparava e
o card aparecia com texto e sem arte.

Garante que:
  - _resolver_fundo NUNCA devolve URL de arquivo que não existe
  - com bg_sha, o fundo vem de /bg/<sha>.jpg (igual local e produção)
  - sem fundo nenhum, cai no mesh da marca em vez de URL quebrada
  - o round-trip de blob no Postgres preserva os bytes
  - a arte final referenciada pelos posts existe mesmo no banco

Rodar: python3 scripts/tests/test_artes_blob.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
VAULT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

envp = VAULT / ".env"
if envp.is_file():
    for _l in envp.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
if os.environ.get("DATABASE_PUBLIC_URL") and not os.environ.get("RAILWAY_ENVIRONMENT"):
    os.environ["DATABASE_URL"] = os.environ["DATABASE_PUBLIC_URL"]


class TestResolverFundo(unittest.TestCase):
    """A regra central: preview nunca aponta pra arquivo inexistente."""

    def _resolver(self, fr, for_export=False):
        import editor_server
        return editor_server._resolver_fundo(fr, for_export)

    def test_bg_sha_vira_url_do_postgres(self):
        sha = "a" * 64
        k = self._resolver({"bg": "marcas/x/nao-existe.png", "bg_sha": sha})
        self.assertEqual(k.get("bg_url"), "/bg/%s.jpg" % sha)
        self.assertNotIn("bg", k)

    def test_sha_tem_prioridade_sobre_arquivo_local(self):
        """Local e produção precisam renderizar a MESMA imagem."""
        real = None
        d = json.loads((VAULT / "editor.json").read_text(encoding="utf-8"))
        for p in d.get("posts") or []:
            for f in p.get("frames") or []:
                if f.get("bg") and f.get("bg_sha") and (VAULT / f["bg"]).is_file():
                    real = f
                    break
            if real:
                break
        if not real:
            self.skipTest("nenhum frame com bg local + bg_sha")
        k = self._resolver(real)
        self.assertEqual(k.get("bg_url"), "/bg/%s.jpg" % real["bg_sha"])

    def test_arquivo_ausente_sem_sha_cai_no_mesh(self):
        k = self._resolver({"bg": "marcas/nada/aqui/inexistente.png"})
        self.assertTrue(k.get("placeholder"), "deveria cair no mesh da marca")
        self.assertNotIn("bg_url", k)
        self.assertNotIn("bg", k)

    def test_export_sem_arquivo_e_sem_sha_nao_estoura(self):
        k = self._resolver({"bg": "marcas/nada/aqui/inexistente.png"}, for_export=True)
        self.assertTrue(k.get("placeholder"))

    def test_nenhum_frame_aponta_pra_arquivo_fantasma(self):
        """Varre o editor.json inteiro — é o cenário real da produção."""
        d = json.loads((VAULT / "editor.json").read_text(encoding="utf-8"))
        ruins = []
        for p in d.get("posts") or []:
            for f in p.get("frames") or []:
                if (f.get("bgmode") or "imagem") != "imagem":
                    continue
                if not (f.get("bg") or f.get("bg_sha")):
                    continue
                k = self._resolver(f)
                url = k.get("bg_url") or ""
                if url.startswith("/marcas/"):
                    rel = url.lstrip("/")
                    if not (VAULT / rel).is_file():
                        ruins.append("%s/%s → %s" % (p.get("marca"), p.get("slug"), url))
        self.assertEqual(ruins, [], "frames apontando pra arquivo que não existe:\n" + "\n".join(ruins))


class TestBlobPostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import _db
        cls._db = _db
        if not _db.disponivel():
            raise unittest.SkipTest("sem DATABASE_URL")
        _db.init_schema()

    def test_round_trip_preserva_bytes(self):
        data = b"\xff\xd8\xff\xe0 smark teste blob \x00\x01\x02" * 40
        sha = hashlib.sha256(data).hexdigest()
        self._db.blob_put(sha, data, kind="bg", w=10, h=20, origem="teste")
        got = self._db.blob_get(sha)
        self.assertIsNotNone(got)
        self.assertEqual(got["bytes"], data)
        self.assertEqual(got["w"], 10)
        # idempotente: gravar de novo não corrompe
        self._db.blob_put(sha, data, kind="bg")
        self.assertEqual(self._db.blob_get(sha)["bytes"], data)

    def test_blob_existe_em_lote(self):
        data = b"smark lote teste" * 10
        sha = hashlib.sha256(data).hexdigest()
        self._db.blob_put(sha, data, kind="bg")
        r = self._db.blob_existe([sha, "f" * 64])
        self.assertIn(sha, r)
        self.assertNotIn("f" * 64, r)

    def test_artes_referenciadas_existem_no_banco(self):
        """Se um post cita arte_sha/bg_sha, a imagem tem que estar lá."""
        d = json.loads((VAULT / "editor.json").read_text(encoding="utf-8"))
        refs = {s for p in d.get("posts") or [] for f in p.get("frames") or []
                for s in (f.get("bg_sha"), f.get("arte_sha")) if s}
        if not refs:
            self.skipTest("nenhuma arte enviada ainda (rode scripts/push_artes.py)")
        faltando = sorted(refs - self._db.blob_existe(list(refs)))
        self.assertEqual(faltando, [], "sha citado no post mas ausente do arte_blob: %s" % faltando)


if __name__ == "__main__":
    unittest.main(verbosity=2)
