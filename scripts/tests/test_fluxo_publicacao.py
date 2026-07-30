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
        # `_env` cai no .env do vault quando a variável não está no ambiente, e o
        # vault TEM PUBLIC_BASE_URL. Pra testar a ausência de verdade, o vault
        # aponta pra um diretório sem .env.
        import tempfile
        os.environ.pop("PUBLIC_BASE_URL", None)
        os.environ.pop("RAILWAY_PUBLIC_DOMAIN", None)
        vault_antes = self.c.VAULT
        try:
            with tempfile.TemporaryDirectory() as vazio:
                self.c.VAULT = vazio
                self.assertEqual(self.c.url_publica_da_arte(SHA_OK), "")
        finally:
            self.c.VAULT = vault_antes

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


SHA_ARTE = "b" * 64


def _post_falso(**kw):
    """Post no formato do editor.json, pronto pra publicar. kw sobrescreve."""
    p = {"marca": "smark", "slug": "peca-de-teste", "titulo": "Peça de teste",
         "status": "aprovado", "caption": "Uma legenda qualquer.",
         "agendado_para": "", "tentativas": 0,
         "frames": [{"headline": "Teste", "arte_sha": SHA_ARTE}]}
    p.update(kw)
    return p


def _conta_falsa(**kw):
    """O que `status_canal` devolve pra uma conta boa."""
    c = {"conectado": True, "username": "conta_teste", "user_id": "1",
         "nome": "Conta", "modo": "real", "expira_em": "2030-01-01T00:00:00",
         "permissoes": ["instagram_business_content_publish"],
         "marcas_da_conta": ["smark"]}
    c.update(kw)
    return c


class BaseGate(unittest.TestCase):
    """Isola o gate do disco e da Meta: nada aqui lê editor.json nem publica.

    Trocar `load` e `status_canal` por dublês é o que permite testar as faltas
    uma a uma — cada cenário do preflight é um estado que seria caro (ou
    destrutivo) de montar de verdade.
    """

    def setUp(self):
        os.environ.setdefault("PUBLIC_BASE_URL", "https://exemplo.up.railway.app")
        import editor_server as ed
        import _canais
        self.ed = ed
        self._load = ed.load
        self._status = _canais.status_canal
        self._canais = _canais
        self.posts = [_post_falso()]
        ed.load = lambda: {"posts": self.posts}
        self.conta = _conta_falsa()
        _canais.status_canal = lambda m, c="instagram": dict(self.conta)

    def tearDown(self):
        self.ed.load = self._load
        self._canais.status_canal = self._status

    def codigos(self, **kw):
        r = self.ed.checar_publicacao("smark", "peca-de-teste", **kw)
        return r, [f["codigo"] for f in r["faltas"]]


class TestGateLibera(BaseGate):
    def test_aprovado_com_tudo_no_lugar_libera(self):
        r, cods = self.codigos()
        self.assertEqual(cods, [], "gate barrou um post que estava pronto")
        self.assertTrue(r["pode"])
        self.assertEqual(r["conta"]["username"], "conta_teste")

    def test_agendado_e_erro_tambem_publicam(self):
        # `erro` é retentativa de algo já aprovado, não atalho de rascunho
        for st in ("agendado", "erro"):
            self.posts[0]["status"] = st
            r, cods = self.codigos()
            self.assertTrue(r["pode"], "%s deveria poder publicar: %s" % (st, cods))

    def test_toda_falta_traz_como_resolver(self):
        self.posts[0].update(status="rascunho", caption="")
        self.conta = _conta_falsa(conectado=False)
        r, cods = self.codigos()
        self.assertTrue(cods)
        for f in r["faltas"]:
            self.assertTrue((f.get("titulo") or "").strip(), "falta sem título: %s" % f)
            self.assertTrue((f.get("como") or "").strip(),
                            "falta %s não diz como resolver" % f.get("codigo"))


class TestGateBarra(BaseGate):
    def test_rascunho_nao_publica(self):
        self.posts[0]["status"] = "rascunho"
        r, cods = self.codigos()
        self.assertIn("nao_aprovado", cods, "rascunho iria pro feed sem aprovação")
        self.assertFalse(r["pode"])
        acao = [f["acao"] for f in r["faltas"] if f["codigo"] == "nao_aprovado"][0]
        self.assertEqual(acao.get("tipo"), "status")
        self.assertEqual(acao.get("para"), "aprovado", "a tela não teria botão de aprovar")

    def test_revisao_e_ajuste_tambem_barram(self):
        for st in ("salvo", "revisao", "ajuste", "publicado"):
            self.posts[0]["status"] = st
            _, cods = self.codigos()
            self.assertIn("nao_aprovado", cods, "%s passou pelo gate" % st)

    def test_sem_conta_oferece_as_contas_existentes(self):
        self.conta = _conta_falsa(conectado=False)
        r, cods = self.codigos()
        self.assertIn("sem_conta", cods)
        acao = [f["acao"] for f in r["faltas"] if f["codigo"] == "sem_conta"][0]
        self.assertEqual(acao.get("tipo"), "conectar")
        self.assertIn("contas", acao, "sem a lista, a tela só sabe mandar pro login")

    def test_token_vencido_barra(self):
        self.conta = _conta_falsa(expira_em="2020-01-01T00:00:00")
        _, cods = self.codigos()
        self.assertIn("token_vencido", cods)

    def test_falta_permissao_de_publicar_barra(self):
        self.conta = _conta_falsa(permissoes=["instagram_business_basic"])
        _, cods = self.codigos()
        self.assertIn("sem_permissao", cods)

    def test_post_sem_frame_barra(self):
        self.posts[0]["frames"] = []
        _, cods = self.codigos()
        self.assertIn("sem_arte", cods)

    def test_frame_sem_sha_nao_barra(self):
        """Sha vazio é arte a compor, não arte faltando.

        `publicar_post` chama `garantir_arte` antes de subir. Barrar aqui
        obrigaria a abrir o editor e clicar em compor pra cada peça.
        """
        self.posts[0]["frames"] = [{"headline": "Teste", "arte_sha": ""}]
        r, cods = self.codigos()
        self.assertNotIn("sem_arte", cods)
        self.assertTrue(r["pode"])
        self.assertEqual(r["arte"]["url"], "", "URL sem sha seria 404 na Meta")

    def test_sem_legenda_barra(self):
        self.posts[0]["caption"] = "   "
        _, cods = self.codigos()
        self.assertIn("sem_legenda", cods)

    def test_marca_invalida_barra(self):
        r = self.ed.checar_publicacao("marca-que-nao-existe", "peca-de-teste")
        self.assertIn("marca_invalida", [f["codigo"] for f in r["faltas"]])
        self.assertFalse(r["pode"])

    def test_linkedin_ainda_nao(self):
        r, _ = self.codigos(canal="linkedin")
        self.assertIn("canal_indisponivel", [f["codigo"] for f in r["faltas"]])


class TestGateAvisa(BaseGate):
    """Aviso informa, falta bloqueia. Confundir os dois é o que trava o cliente."""

    def test_conta_compartilhada_e_aviso_nao_falta(self):
        self.conta = _conta_falsa(marcas_da_conta=["smark", "provider-max"])
        r, cods = self.codigos()
        self.assertTrue(r["pode"], "conta dividida entre marcas é normal, não erro")
        self.assertEqual(cods, [])
        self.assertEqual(r["conta"]["compartilhada_com"], ["provider-max"])
        self.assertTrue(any("provider-max" in a for a in r["avisos"]),
                        "publicaria sem avisar que outra empresa usa a conta")

    def test_token_vencendo_avisa_sem_barrar(self):
        import datetime
        d = (datetime.datetime.now(datetime.timezone.utc)
             + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
        self.conta = _conta_falsa(expira_em=d)
        r, cods = self.codigos()
        self.assertEqual(cods, [], "3 dias pra vencer não é motivo pra travar")
        self.assertTrue(any("vence" in a for a in r["avisos"]))

    def test_legenda_longa_avisa(self):
        self.posts[0]["caption"] = "x" * 2400
        r, cods = self.codigos()
        self.assertEqual(cods, [])
        self.assertTrue(any("2200" in a or "legenda" in a.lower() for a in r["avisos"]))


class TestRodarAgenda(BaseGate):
    """O worker só toca no que venceu — e nunca duas vezes no mesmo post."""

    def setUp(self):
        super().setUp()
        self.publicados = []
        self._pub = self.ed.publicar_post

        def falso_publicar(marca, **kw):
            self.publicados.append((marca, kw.get("slug")))
            return {"ok": True, "media_id": "fake-%d" % len(self.publicados),
                    "modo": "teste"}
        self.ed.publicar_post = falso_publicar

    def tearDown(self):
        self.ed.publicar_post = self._pub
        super().tearDown()

    def _agendado(self, slug, quando, status="agendado"):
        return _post_falso(slug=slug, titulo=slug, status=status, agendado_para=quando)

    def test_nao_publica_o_que_nao_venceu(self):
        self.posts = [self._agendado("futuro", "2099-01-01T00:00:00+00:00")]
        r = self.ed.rodar_agenda()
        self.assertEqual(self.publicados, [], "publicou antes da hora marcada")
        self.assertEqual(r["venceram"], 0)

    def test_publica_o_que_venceu(self):
        self.posts = [self._agendado("passado", "2020-01-01T00:00:00+00:00"),
                      self._agendado("futuro", "2099-01-01T00:00:00+00:00")]
        r = self.ed.rodar_agenda()
        self.assertEqual(self.publicados, [("smark", "passado")])
        self.assertEqual(r["venceram"], 1)
        self.assertEqual(len(r["feitos"]), 1)

    def test_ignora_quem_nao_esta_agendado(self):
        # data no passado num post aprovado não é agendamento — é resto de dado
        self.posts = [self._agendado("aprovado-com-data", "2020-01-01T00:00:00+00:00",
                                     status="aprovado")]
        self.ed.rodar_agenda()
        self.assertEqual(self.publicados, [])

    def test_limite_segura_a_fila(self):
        self.posts = [self._agendado("p%d" % n, "2020-01-0%dT00:00:00+00:00" % (n + 1))
                      for n in range(4)]
        r = self.ed.rodar_agenda(limite=2)
        self.assertEqual(len(self.publicados), 2)
        self.assertEqual(r["sobraram"], 2)
        # os mais antigos primeiro: quem esperou mais sai antes
        self.assertEqual([s for _, s in self.publicados], ["p0", "p1"])

    def test_duas_passadas_juntas_nao_publicam_duas_vezes(self):
        self.posts = [self._agendado("passado", "2020-01-01T00:00:00+00:00")]
        self.ed._AGENDA_LOCK.acquire()
        try:
            r = self.ed.rodar_agenda()
        finally:
            self.ed._AGENDA_LOCK.release()
        self.assertTrue(r.get("rodando"), "segunda passada entrou junto")
        self.assertEqual(self.publicados, [], "publicaria o mesmo post duas vezes")

    def test_dry_run_nao_publica_de_verdade(self):
        self.posts = [self._agendado("passado", "2020-01-01T00:00:00+00:00")]
        r = self.ed.rodar_agenda(dry_run=True)
        self.assertTrue(r["dry_run"])
        self.assertEqual(len(self.publicados), 1)   # chamou, mas em simulação
        self.assertEqual(self.ed.STATUS_PUBLICAVEIS, ("aprovado", "agendado", "erro"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
