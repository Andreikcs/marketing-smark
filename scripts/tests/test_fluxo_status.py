#!/usr/bin/env python3
"""Regressão do fluxo de aprovação (rascunho → … → publicado).

O que está sendo protegido aqui não é o caminho feliz — é o contrário dele:

  - não existe atalho de rascunho pro ar (o cliente não pode ser surpreendido)
  - editar um post aprovado tira a aprovação (ela vale pra peça que ele viu)
  - post que volta pra ajuste sai da fila de agendados na mesma hora
  - `salvo`, o status que 40+ posts do vault já têm, continua dentro da máquina
  - a data agendada vira UTC, venha ela de que fuso vier

Roda sem banco: o status mora no editor.json e a validação é pura.

Rodar: python3 scripts/tests/test_fluxo_status.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

import _db  # noqa: E402


class _FluxoSemBanco:
    """O vocabulário do fluxo, sem nenhuma conexão. Teste não fala com o Postgres."""
    STATUS_VALIDOS = _db.STATUS_VALIDOS
    STATUS_LABEL = _db.STATUS_LABEL
    TRANSICOES = _db.TRANSICOES
    transicao_ok = staticmethod(_db.transicao_ok)

    @staticmethod
    def disponivel():
        return False


class TestMaquinaDeEstados(unittest.TestCase):
    def test_todo_destino_e_um_status_valido(self):
        for de, destinos in _db.TRANSICOES.items():
            self.assertIn(de, _db.STATUS_VALIDOS, "estado órfão: %s" % de)
            for para in destinos:
                self.assertIn(para, _db.STATUS_VALIDOS,
                              "%s aponta pra status inexistente: %s" % (de, para))

    def test_todo_status_tem_rotulo_e_saida_definida(self):
        for s in _db.STATUS_VALIDOS:
            self.assertIn(s, _db.STATUS_LABEL, "status sem rótulo de tela: %s" % s)
            self.assertIn(s, _db.TRANSICOES, "status sem transições declaradas: %s" % s)

    def test_nao_existe_atalho_de_rascunho_pro_ar(self):
        """A regra que dá segurança ao cliente. Se cair, alguém publicou sem aval."""
        for de in ("rascunho", "salvo", "revisao", "ajuste"):
            self.assertFalse(_db.transicao_ok(de, "publicado"),
                             "%s → publicado não pode existir" % de)
            self.assertFalse(_db.transicao_ok(de, "agendado"),
                             "%s → agendado não pode existir" % de)

    def test_so_agenda_quem_esta_aprovado(self):
        entram = [de for de in _db.STATUS_VALIDOS if _db.transicao_ok(de, "agendado")]
        self.assertEqual(sorted(entram), ["aprovado", "erro"])

    def test_publicado_e_fim_de_linha(self):
        self.assertEqual(_db.proximos("publicado"), ())

    def test_salvo_esta_no_fluxo(self):
        """40+ posts do vault têm status 'salvo'. Fora da máquina, travariam."""
        self.assertIn("salvo", _db.STATUS_VALIDOS)
        self.assertTrue(_db.transicao_ok("salvo", "revisao"))
        self.assertTrue(_db.transicao_ok("rascunho", "salvo"))

    def test_status_desconhecido_nao_anda(self):
        self.assertFalse(_db.transicao_ok("inventado", "aprovado"))
        self.assertEqual(_db.proximos("inventado"), ())


class TestMudarStatusNoArquivo(unittest.TestCase):
    """O editor.json é quem manda no status — o banco recebe pelo upsert."""

    def setUp(self):
        import editor_server as es
        self.es = es
        self.tmp = tempfile.mkdtemp(prefix="fluxo-")
        self._data_antes = es.DATA
        self._cache_antes = es._MEM_CACHE
        es.DATA = os.path.join(self.tmp, "editor.json")
        es._MEM_CACHE = None
        self._escrever([{
            "marca": "smark", "slug": "post-teste", "titulo": "Teste",
            "status": "rascunho", "frames": [{"n": 1, "headline": "oi"}],
        }])
        # O editor_server lê o .env no import, então sem isto o teste escreveria
        # 'post-teste' no Postgres de PRODUÇÃO — e ainda mandaria renderizar arte.
        self._flush_antes, self._arte_antes = es._schedule_db_flush, es._agendar_arte
        es._schedule_db_flush = lambda posts: None
        es._agendar_arte = lambda *a, **k: None
        # a trilha é opcional (o fluxo funciona sem banco); aqui ela fica off
        self._db_mod_antes = es._db_mod
        es._db_mod = lambda: _FluxoSemBanco

    def tearDown(self):
        self.es.DATA = self._data_antes
        self.es._MEM_CACHE = self._cache_antes
        self.es._db_mod = self._db_mod_antes
        self.es._schedule_db_flush = self._flush_antes
        self.es._agendar_arte = self._arte_antes

    def _escrever(self, posts):
        with open(self.es.DATA, "w", encoding="utf-8") as f:
            json.dump({"version": 2, "posts": posts}, f)
        self.es._MEM_CACHE = None

    def _post(self):
        with open(self.es.DATA, encoding="utf-8") as f:
            return json.load(f)["posts"][0]

    def _ir(self, para, **kw):
        return self.es.mudar_status_post("smark", "post-teste", para, **kw)

    def test_caminho_completo_ate_publicado(self):
        self.assertTrue(self._ir("salvo")["ok"])
        self.assertTrue(self._ir("revisao")["ok"])
        r = self._ir("aprovado", por="cliente@amosim")
        self.assertTrue(r["ok"])
        p = self._post()
        self.assertEqual(p["status"], "aprovado")
        self.assertEqual(p["aprovado_por"], "cliente@amosim")
        self.assertTrue(p["aprovado_em"], "aprovação sem data não serve de prova")

    def test_transicao_proibida_e_recusada_com_motivo(self):
        r = self._ir("publicado")
        self.assertFalse(r["ok"])
        self.assertIn("rascunho", r["erro"])
        self.assertEqual(self._post()["status"], "rascunho", "recusou mas mexeu no post")

    def test_agendar_exige_data(self):
        self._ir("aprovado")
        r = self._ir("agendado")
        self.assertFalse(r["ok"])
        self.assertEqual(self._post()["status"], "aprovado")

    def test_agenda_vira_utc_venha_de_onde_vier(self):
        self._ir("aprovado")
        r = self._ir("agendado", quando="2026-08-03T12:00:00-03:00")
        self.assertTrue(r["ok"], r.get("erro"))
        self.assertEqual(self._post()["agendado_para"], "2026-08-03T15:00:00+00:00")

    def test_voltar_pra_ajuste_tira_da_fila(self):
        """Um post que o cliente mandou mudar não pode sair no ar às 9h."""
        self._ir("aprovado")
        self._ir("agendado", quando="2026-08-03T12:00:00+00:00")
        self.assertTrue(self._post()["agendado_para"])
        r = self._ir("ajuste", comentario="trocar a foto")
        self.assertTrue(r["ok"])
        p = self._post()
        self.assertEqual(p["status"], "ajuste")
        self.assertEqual(p["agendado_para"], "", "continuou agendado depois do ajuste")
        self.assertEqual(p["ultimo_comentario"], "trocar a foto")

    def test_post_sem_arte_nao_vai_pro_cliente(self):
        self._escrever([{"marca": "smark", "slug": "post-teste", "titulo": "Vazio",
                         "status": "rascunho", "frames": []}])
        r = self._ir("revisao")
        self.assertFalse(r["ok"])
        self.assertIn("arte", r["erro"])

    def test_post_inexistente_nao_explode(self):
        r = self.es.mudar_status_post("smark", "nao-existe", "salvo")
        self.assertFalse(r["ok"])
        self.assertIn("não encontrado", r["erro"])

    def test_mesmo_status_e_no_op(self):
        r = self._ir("rascunho")
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("sem_mudanca"))

    def test_forcar_ignora_a_maquina(self):
        """Escotilha de emergência — existe, mas só quem pede explicitamente usa."""
        r = self._ir("publicado", forcar=True)
        self.assertTrue(r["ok"])
        self.assertTrue(self._post()["publicado_em"])


class _DbEspiao:
    """Banco de mentira que só anota o que foi pedido."""
    STATUS_VALIDOS = _db.STATUS_VALIDOS
    TRANSICOES = _db.TRANSICOES
    transicao_ok = staticmethod(_db.transicao_ok)
    chamadas: list = []

    @staticmethod
    def disponivel():
        return True

    @staticmethod
    def aplicar_status(marca, slug, para, **kw):
        _DbEspiao.chamadas.append({"marca": marca, "slug": slug, "para": para, **kw})
        return {"ok": True, "linhas": 1}

    # guarda o espião de verdade: quem troca `aplicar_status` no meio do teste
    # devolve por aqui, senão o teste seguinte lê uma lista de chamadas vazia
    _espiao_real = None


_DbEspiao._espiao_real = _DbEspiao.__dict__["aplicar_status"]


class TestStatusNaoViajaDeCarona(unittest.TestCase):
    """O status tem que ir pro banco por conta própria.

    O upsert em lote passa por `_ensure_marca_cur` e reescreve os frames de 48
    posts numa transação; sob dois escritores ele estoura o statement_timeout em
    lock da tabela `marca` e o savepoint desfaz aquele post. Como o boot
    reconstrói o editor.json a partir do banco, a aprovação do cliente sumia no
    dia seguinte. Este teste é o que impede a volta desse caminho.
    """

    def setUp(self):
        import editor_server as es
        self.es = es
        self.tmp = tempfile.mkdtemp(prefix="fluxo-db-")
        self._data_antes, self._cache_antes = es.DATA, es._MEM_CACHE
        es.DATA = os.path.join(self.tmp, "editor.json")
        with open(es.DATA, "w", encoding="utf-8") as f:
            json.dump({"version": 2, "posts": [{
                "marca": "amosim", "slug": "p1", "titulo": "T", "status": "rascunho",
                "frames": [{"n": 1}]}]}, f)
        es._MEM_CACHE = None
        self._flush_antes, self._arte_antes = es._schedule_db_flush, es._agendar_arte
        es._schedule_db_flush = lambda posts: None
        es._agendar_arte = lambda *a, **k: None
        self._db_antes = es._db_mod
        _DbEspiao.chamadas = []
        _DbEspiao.aplicar_status = _DbEspiao._espiao_real
        es._db_mod = lambda: _DbEspiao

    def tearDown(self):
        self.es.DATA, self.es._MEM_CACHE = self._data_antes, self._cache_antes
        self.es._schedule_db_flush, self.es._agendar_arte = self._flush_antes, self._arte_antes
        self.es._db_mod = self._db_antes

    def test_aprovar_grava_no_banco_na_hora(self):
        r = self.es.mudar_status_post("amosim", "p1", "aprovado", por="cliente@amosim")
        self.assertTrue(r["ok"])
        self.assertEqual(len(_DbEspiao.chamadas), 1, "aprovação não foi ao banco na hora")
        c = _DbEspiao.chamadas[0]
        self.assertEqual((c["marca"], c["slug"], c["para"]), ("amosim", "p1", "aprovado"))
        self.assertEqual(c["por"], "cliente@amosim")
        self.assertTrue(c["aprovado_em"], "foi ao banco sem a data da aprovação")

    def test_agendar_leva_a_data_pro_banco(self):
        self.es.mudar_status_post("amosim", "p1", "aprovado")
        _DbEspiao.chamadas = []
        self.es.mudar_status_post("amosim", "p1", "agendado", quando="2026-08-03T12:00:00-03:00")
        self.assertEqual(_DbEspiao.chamadas[0]["agendado_para"], "2026-08-03T15:00:00+00:00")

    def test_ajuste_manda_limpar_a_data_no_banco(self):
        self.es.mudar_status_post("amosim", "p1", "aprovado")
        self.es.mudar_status_post("amosim", "p1", "agendado", quando="2026-08-03T12:00:00Z")
        _DbEspiao.chamadas = []
        self.es.mudar_status_post("amosim", "p1", "ajuste", comentario="muda a foto")
        c = _DbEspiao.chamadas[0]
        self.assertEqual(c["agendado_para"], "", "não pediu pro banco limpar a agenda")
        self.assertEqual(c["comentario"], "muda a foto")

    def test_voltar_atras_apaga_quem_aprovou(self):
        """Aprovação vale pra peça que o cliente viu.

        Se o post volta pra rascunho/ajuste/pronto e o `aprovado_por` fica lá, o
        modal mostra "Aprovado por X" numa peça que mudou depois — mentira com
        cara de registro.
        """
        self.es.mudar_status_post("amosim", "p1", "aprovado", por="cliente@amosim")
        _DbEspiao.chamadas = []
        r = self.es.mudar_status_post("amosim", "p1", "ajuste", comentario="troca o texto")
        self.assertEqual(r.get("aprovado_por"), "", "arquivo guardou aprovação vencida")
        c = _DbEspiao.chamadas[0]
        self.assertEqual(c["aprovado_por"], "", "não pediu pro banco limpar quem aprovou")
        self.assertEqual(c["aprovado_em"], "", "não pediu pro banco limpar a data da aprovação")

    def test_banco_recusando_nao_engole_o_erro(self):
        _DbEspiao.aplicar_status = staticmethod(lambda *a, **k: {"ok": False, "erro": "lock"})
        r = self.es.mudar_status_post("amosim", "p1", "salvo")
        self.assertTrue(r["ok"])          # o arquivo foi gravado
        self.assertIn("aviso", r)         # mas o usuário fica sabendo
        self.assertIn("lock", r["aviso"])
        # o setUp devolve o espião de verdade — não precisa desfazer aqui


class TestAbaVelhaNaoDesfazAprovacao(unittest.TestCase):
    """O /salvar manda o editor.json inteiro — e a aba pode estar desatualizada.

    Aconteceu de verdade: post foi pra `salvo`, uma aba aberta antes disso
    chamou /salvar, e o arquivo voltou pra `ajuste` com a aprovação por baixo.
    Numa vitrine que o cliente aprova, isso é apagar a aprovação em silêncio.
    """

    def setUp(self):
        import editor_server as es
        self.merge = es.merge_fluxo

    def _disco(self, **kw):
        p = {"marca": "smark", "slug": "p1", "status": "aprovado",
             "aprovado_por": "cliente@x", "aprovado_em": "2026-07-29T10:00:00+00:00",
             "agendado_para": "", "titulo": "T"}
        p.update(kw)
        return {"posts": [p]}

    def _aba(self, **kw):
        p = {"marca": "smark", "slug": "p1", "status": "ajuste",
             "aprovado_por": "", "aprovado_em": "", "titulo": "T editado"}
        p.update(kw)
        return {"posts": [p]}

    def test_status_velho_da_aba_e_ignorado(self):
        r = self.merge(self._aba(), self._disco())
        p = r["posts"][0]
        self.assertEqual(p["status"], "aprovado", "aba velha rebaixou o status")
        self.assertEqual(p["aprovado_por"], "cliente@x", "aba velha apagou quem aprovou")
        self.assertEqual(p["titulo"], "T editado", "o merge comeu a edição de verdade")

    def test_agenda_nao_vem_da_aba(self):
        r = self.merge(self._aba(agendado_para="2030-01-01T00:00:00+00:00"),
                       self._disco(status="agendado", agendado_para="2026-08-03T15:00:00+00:00"))
        self.assertEqual(r["posts"][0]["agendado_para"], "2026-08-03T15:00:00+00:00")

    def test_editar_ainda_derruba_a_aprovacao(self):
        r = self.merge(self._aba(status="rascunho"), self._disco())
        self.assertEqual(r["posts"][0]["status"], "rascunho",
                         "editar tem que tirar a peça de aprovado")

    def test_botao_salvar_ainda_promove_rascunho(self):
        r = self.merge(self._aba(status="salvo"), self._disco(status="rascunho"))
        self.assertEqual(r["posts"][0]["status"], "salvo")

    def test_salvo_nao_rebaixa_aprovado(self):
        r = self.merge(self._aba(status="salvo"), self._disco(status="aprovado"))
        self.assertEqual(r["posts"][0]["status"], "aprovado")

    def test_post_novo_passa_inteiro(self):
        r = self.merge({"posts": [{"marca": "smark", "slug": "novo", "status": "rascunho"}]},
                       self._disco())
        self.assertEqual(r["posts"][0]["slug"], "novo")
        self.assertEqual(r["posts"][0]["status"], "rascunho")


class _CursorFalso:
    def __init__(self, sacola): self.sacola = sacola; self.rowcount = 1
    def execute(self, sql, vals=None): self.sacola.append((sql, list(vals or [])))
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _ConnFalsa:
    def __init__(self, sacola): self.sacola = sacola
    def cursor(self, *a, **k): return _CursorFalso(self.sacola)
    def __enter__(self): return self
    def __exit__(self, *a): return False


class TestSqlDoFluxo(unittest.TestCase):
    """O SQL que a `aplicar_status` monta, sem banco.

    `aprovado_por` é NOT NULL DEFAULT '' — mandar NULL pra limpar derruba o
    UPDATE inteiro. Em produção isso apareceu como "aprovei, pedi ajuste e o
    banco ficou dizendo aprovado": o arquivo andava, o banco não.
    """

    def setUp(self):
        self.sacola: list = []
        self._conn, self._disp = _db.conn, _db.disponivel
        _db.conn = lambda *a, **k: _ConnFalsa(self.sacola)
        _db.disponivel = lambda: True

    def tearDown(self):
        _db.conn, _db.disponivel = self._conn, self._disp

    def _set(self) -> dict:
        """Devolve {coluna: valor} do UPDATE, casando %s com a ordem dos vals."""
        sql, vals = next(s for s in self.sacola if s[0].startswith("UPDATE post SET"))
        cols = sql.split("SET ", 1)[1].split(" WHERE")[0].split(",")
        out, i = {}, 0
        for c in cols:
            nome, _, val = c.partition("=")
            if val == "%s":
                out[nome] = vals[i]
                i += 1
        return out

    def test_limpar_quem_aprovou_manda_string_vazia(self):
        r = _db.aplicar_status("smark", "p1", "ajuste", de="aprovado",
                               por="time", aprovado_por="", aprovado_em="")
        self.assertTrue(r["ok"])
        s = self._set()
        self.assertEqual(s["aprovado_por"], "", "mandou NULL numa coluna NOT NULL")
        self.assertIsNone(s["aprovado_em"], "data vazia devia virar NULL")
        self.assertEqual(s["status"], "ajuste")

    def test_aprovar_leva_quem_aprovou(self):
        _db.aplicar_status("smark", "p1", "aprovado", de="revisao",
                           por="cliente@x", aprovado_em="2026-07-29T10:00:00+00:00")
        self.assertEqual(self._set()["aprovado_por"], "cliente@x")

    def test_evento_entra_junto(self):
        _db.aplicar_status("smark", "p1", "revisao", de="salvo", por="time",
                           comentario="olha isso")
        self.assertTrue(any(s[0].startswith("INSERT INTO post_evento") for s in self.sacola),
                        "mudou o status e não registrou na trilha")


class TestFusoDasDatasDoFluxo(unittest.TestCase):
    """Toda data do fluxo carrega fuso.

    Existia um `_agora_iso()` no editor_server devolvendo hora local SEM fuso.
    Com ele, `aprovado_em` ficava numa régua e `agendado_para` em outra — e o
    "já venceu?" da fila errava por 3 horas.
    """

    def test_agora_utc_tem_fuso(self):
        import editor_server as es
        s = es._agora_utc()
        self.assertTrue(s.endswith("+00:00"), "hora do fluxo sem fuso: %s" % s)
        d = __import__("datetime").datetime.fromisoformat(s)
        self.assertIsNotNone(d.tzinfo)

    def test_aprovado_em_e_comparavel_com_agendado_para(self):
        import datetime as _dt
        import editor_server as es
        a = _dt.datetime.fromisoformat(es._agora_utc())
        b = _dt.datetime.fromisoformat(es._norm_quando("2026-08-03T12:00:00-03:00"))
        self.assertLess(a, b)   # se um dos dois fosse ingênuo, isto explodiria


class TestNormalizacaoDeData(unittest.TestCase):
    def setUp(self):
        import editor_server as es
        self.n = es._norm_quando

    def test_lixo_vira_vazio(self):
        for ruim in ("", "amanhã", "2026-13-45", "quinta que vem", None):
            self.assertEqual(self.n(ruim), "", "aceitou data inválida: %r" % ruim)

    def test_z_e_offset_dao_no_mesmo(self):
        self.assertEqual(self.n("2026-08-03T15:00:00Z"),
                         self.n("2026-08-03T12:00:00-03:00"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
