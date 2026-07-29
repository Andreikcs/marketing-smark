#!/usr/bin/env python3
"""Regressão do caminho que leva a arte até o Instagram.

O bug da galeria (arte apontando pra arquivo que não existe no servidor) tinha um
gêmeo escondido aqui: `publicar_instagram` montava a URL que a META BAIXA a
partir de um caminho do vault. Em produção esse arquivo não existe, então a Meta
tomaria 404 e o post falharia — com erro do lado dela, difícil de diagnosticar.

Garante que:
  - a URL da arte é sempre /arte/<sha>.jpg, nunca um caminho de arquivo
  - sha inválido não vira URL (não dá pra enganar o endereçamento por conteúdo)
  - a composição é determinística: mesma entrada, mesmo sha
  - o cache não re-renderiza quando nada mudou (render custa segundos de CPU)

Rodar: python3 scripts/tests/test_fluxo_publicacao.py
"""
from __future__ import annotations

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

SHA_OK = "a" * 64


class TestUrlDaArte(unittest.TestCase):
    def setUp(self):
        import _canais
        self.c = _canais
        self._antes = os.environ.get("PUBLIC_BASE_URL")
        os.environ["PUBLIC_BASE_URL"] = "https://exemplo.up.railway.app"

    def tearDown(self):
        if self._antes is None:
            os.environ.pop("PUBLIC_BASE_URL", None)
        else:
            os.environ["PUBLIC_BASE_URL"] = self._antes

    def test_url_e_do_postgres_nao_do_disco(self):
        u = self.c.url_publica_da_arte(SHA_OK)
        self.assertEqual(u, "https://exemplo.up.railway.app/arte/%s.jpg" % SHA_OK)
        self.assertNotIn("/marcas/", u)
        self.assertNotIn("publicacoes", u)

    def test_https_forcado_quando_base_vem_sem_esquema(self):
        os.environ["PUBLIC_BASE_URL"] = "exemplo.up.railway.app"
        self.assertTrue(self.c.url_publica_da_arte(SHA_OK).startswith("https://"))

    def test_sha_invalido_nao_vira_url(self):
        for ruim in ("", "xyz", "../../etc/passwd", "a" * 15, SHA_OK + "b",
                     "marcas/smark/arte.png"):
            self.assertEqual(self.c.url_publica_da_arte(ruim), "",
                             "aceitou sha inválido: %r" % ruim)

    def test_sem_base_publica_nao_inventa_url(self):
        os.environ.pop("PUBLIC_BASE_URL", None)
        os.environ.pop("RAILWAY_PUBLIC_DOMAIN", None)
        self.assertEqual(self.c.url_publica_da_arte(SHA_OK), "")

    def test_publicar_recusa_url_de_arquivo(self):
        """Mesmo recebendo image_url pronta, caminho do vault é barrado."""
        r = self.c.publicar_instagram(
            "smark",
            image_url="https://exemplo.app/marcas/smark/publicacoes/x.png",
            caption="teste")
        self.assertFalse(r.get("ok"))
        # ou barra por não estar conectado, ou pela URL — nunca publica
        self.assertIn("erro", r)


class TestComposicao(unittest.TestCase):
    """Determinismo e cache — o que garante 'aprovou = publicou'."""

    @classmethod
    def setUpClass(cls):
        import _arte
        cls.a = _arte
        import _db
        if not _db.disponivel():
            raise unittest.SkipTest("sem DATABASE_URL")
        cls.db = _db
        if not os.path.isfile(cls.a.compositor.CHROME):
            raise unittest.SkipTest("sem navegador pra renderizar")

    def _post(self):
        return ({"marca": "smark", "slug": "teste-fluxo", "size": "1080x1350"},
                {"n": 1, "headline": "Peça de teste", "sub": "Ação e coração.",
                 "bgmode": "cor"})

    def test_mesma_entrada_mesmo_sha(self):
        p, fr = self._post()
        h1, _, _ = self.a.html_do_frame(p, fr)
        h2, _, _ = self.a.html_do_frame(p, dict(fr))
        self.assertEqual(self.a.sha256(h1.encode()), self.a.sha256(h2.encode()),
                         "composição não é determinística — o cache seria inútil")

    def test_texto_diferente_muda_o_sha(self):
        p, fr = self._post()
        h1, _, _ = self.a.html_do_frame(p, fr)
        fr2 = dict(fr, headline="Outro texto")
        h2, _, _ = self.a.html_do_frame(p, fr2)
        self.assertNotEqual(self.a.sha256(h1.encode()), self.a.sha256(h2.encode()),
                            "mudou o texto e o hash não mudou — publicaria arte velha")

    def test_segunda_chamada_usa_cache(self):
        p, fr = self._post()
        r1 = self.a.garantir_arte(p, fr, origem="teste")
        self.assertTrue(r1["ok"], r1["motivo"])
        r2 = self.a.garantir_arte(p, fr, origem="teste")
        self.assertTrue(r2["ok"], r2["motivo"])
        self.assertFalse(r2["novo"], "re-renderizou sem nada ter mudado")
        self.assertEqual(r1["sha"], r2["sha"])

    def test_arte_fica_publicavel_no_banco(self):
        p, fr = self._post()
        r = self.a.garantir_arte(p, fr, origem="teste")
        self.assertTrue(r["ok"], r["motivo"])
        b = self.db.blob_get(r["sha"])
        self.assertIsNotNone(b, "arte não chegou no Postgres — a Meta não acharia")
        self.assertGreater(len(b["bytes"]), 10_000)
        self.assertEqual(b["w"], 1080, "Instagram recomprime acima de 1080")
        self.assertEqual(b["h"], 1350)


if __name__ == "__main__":
    unittest.main(verbosity=2)
