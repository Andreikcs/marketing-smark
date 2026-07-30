#!/usr/bin/env python3
"""Uma conta de Instagram servindo várias marcas.

O modelo antigo guardava o token DENTRO da linha da marca (`canal_conexao`, PK
`(marca, canal)`). Ligar o mesmo Instagram em duas empresas do mesmo dono exigia
fazer OAuth duas vezes e deixava duas cópias do mesmo token — o refresh renovava
uma e a outra vencia calada, derrubando a publicação de uma marca sem aviso.

Agora a conta é entidade própria (`conta_canal`) e a marca guarda só o vínculo.
Este arquivo protege as quatro coisas que não podem regredir:

  - duas marcas, uma conta: o token é o MESMO objeto, não uma cópia
  - linha legada (payload inteiro na marca) migra sozinha na primeira leitura
  - desvincular uma marca não derruba o acesso das outras
  - `esquecer_conta` diz quem dependia dela antes de apagar

Nada aqui toca a conta real: usa `user_id` e marcas de teste, e limpa no fim.

Rodar: python3 scripts/tests/test_contas_compartilhadas.py
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

# Marcas e conta de teste. Prefixo improvável de colidir com marca de cliente.
M1 = "zz-teste-conta-a"
M2 = "zz-teste-conta-b"
UID = "99999999999999001"
CANAL = "instagram"


def _payload(token="tok-inicial", username="zz_conta_teste", expira="2030-01-01T00:00:00"):
    """Payload de conta conectada — o formato que o OAuth real grava."""
    return {
        "canal": CANAL, "connected": True, "modo": "fake",
        "user_id": UID, "username": username, "nome": "Conta de teste",
        "access_token": token, "expires_in": 5184000, "expira_em": expira,
        "permissoes": ["instagram_business_content_publish"],
    }


class BaseContas(unittest.TestCase):
    """Cada teste roda num `.secrets` próprio, descartável.

    Antes usava o `.secrets` real. O editor (localhost:8765) varre esse diretório
    pra montar a lista de contas e, ao ler um payload legado, MIGRA — reescrevendo
    disco e banco. Com o servidor no ar a suíte falhava sozinha: ele ressuscitava
    a conta que o teste tinha acabado de esquecer. Fora do diretório real ele nem
    enxerga as marcas de teste, e a suíte para de depender de quem mais está vivo
    na máquina.
    """

    def setUp(self):
        import tempfile
        import _canais
        self.c = _canais
        self._tmp = tempfile.mkdtemp(prefix="zz-secrets-")
        self._secrets_real = _canais.SECRETS_DIR
        _canais.SECRETS_DIR = self._tmp
        self._limpar()

    def tearDown(self):
        import shutil
        self._limpar()
        self.c.SECRETS_DIR = self._secrets_real
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _limpar(self):
        """Some com tudo que o teste criou — arquivo e banco."""
        for m in (M1, M2):
            for p in (self.c._path_token(m, CANAL),):
                try:
                    os.remove(p)
                except OSError:
                    pass
        try:
            os.remove(self.c._path_conta(CANAL, UID))
        except OSError:
            pass
        try:
            import _db
            if _db.disponivel():
                for m in (M1, M2):
                    _db.canal_apagar(m, CANAL)
                if hasattr(_db, "conta_apagar"):
                    _db.conta_apagar(CANAL, UID)
        except Exception:
            pass


class TestUmaContaVariasMarcas(BaseContas):
    def test_vincular_nao_copia_token(self):
        self.c._persist_canal(M1, CANAL, _payload())
        r = self.c.vincular_marca(M2, CANAL, UID)
        self.assertTrue(r["ok"], r.get("erro"))
        self.assertEqual(sorted(r["marcas_da_conta"]), sorted([M1, M2]))

        # o vínculo da segunda marca não guarda token nenhum
        vinc = self.c._load_json(self.c._path_token(M2, CANAL))
        self.assertEqual(vinc.get("conta_user_id"), UID)
        self.assertNotIn("access_token", vinc,
                         "o vínculo copiou o token — é o furo que isso fecha")

        # e as duas marcas leem o MESMO token
        self.assertEqual(self.c.token_bruto(M1, CANAL).get("access_token"),
                         self.c.token_bruto(M2, CANAL).get("access_token"))

    def test_um_refresh_serve_as_duas(self):
        self.c._persist_canal(M1, CANAL, _payload(token="tok-velho"))
        self.c.vincular_marca(M2, CANAL, UID)

        # simula o que o refresh faz: grava o token novo NA CONTA
        raw = self.c.conta_bruta(CANAL, UID)
        raw["access_token"] = "tok-novo"
        self.c._persist_conta(CANAL, raw)

        for m in (M1, M2):
            self.assertEqual(self.c.token_bruto(m, CANAL).get("access_token"), "tok-novo",
                             "%s ficou com o token velho — venceria calada" % m)

    def test_status_todas_avisa_quem_divide_a_conta(self):
        self.c._persist_canal(M1, CANAL, _payload())
        self.c.vincular_marca(M2, CANAL, UID)
        st = self.c.status_todas([M1, M2])
        for m in (M1, M2):
            ig = st[m]["canais"][CANAL]
            self.assertTrue(ig["conectado"])
            self.assertEqual(sorted(ig.get("marcas_da_conta") or []), sorted([M1, M2]),
                             "a tela não teria como avisar que a conta é dividida")

    def test_conta_aparece_pra_reuso(self):
        self.c._persist_canal(M1, CANAL, _payload())
        achou = [c for c in self.c.contas_conectadas(CANAL) if c["user_id"] == UID]
        self.assertEqual(len(achou), 1, "conta não aparece no /config pra reuso")
        self.assertEqual(achou[0]["marcas"], [M1])


class TestMigracaoLegado(BaseContas):
    def test_linha_legada_migra_na_leitura(self):
        # grava do jeito ANTIGO: payload inteiro no arquivo da marca, sem conta
        self.c._save_json(self.c._path_token(M1, CANAL), _payload(token="tok-legado"))
        self.assertFalse(os.path.isfile(self.c._path_conta(CANAL, UID)))

        raw = self.c._load_canal(M1, CANAL)
        self.assertEqual(raw.get("access_token"), "tok-legado",
                         "migrar não pode perder o token — obrigaria reconectar")
        self.assertTrue(os.path.isfile(self.c._path_conta(CANAL, UID)),
                        "não promoveu o payload a conta")
        vinc = self.c._load_json(self.c._path_token(M1, CANAL))
        self.assertEqual(vinc.get("conta_user_id"), UID)

        # e depois de migrada, outra marca entra sem login
        r = self.c.vincular_marca(M2, CANAL, UID)
        self.assertTrue(r["ok"], r.get("erro"))

    def test_leitura_de_vinculo_nao_remigra(self):
        self.c._persist_canal(M1, CANAL, _payload())
        antes = os.path.getmtime(self.c._path_conta(CANAL, UID))
        for _ in range(3):
            self.c._load_canal(M1, CANAL)
        self.assertEqual(antes, os.path.getmtime(self.c._path_conta(CANAL, UID)),
                         "reescreveu a conta a cada leitura — grava por nada")


class TestBancoFalhando(BaseContas):
    """O disco é a palavra local. Banco que perde a escrita não pode esconder conta.

    Aconteceu de verdade rodando esta suíte: o proxy do Railway engasgou, o
    `_persist_canal` engoliu o erro do INSERT (de propósito — o arquivo já estava
    gravado) e a conta ficou INVISÍVEL, porque a listagem só olhava o banco. O
    usuário seria mandado pra um OAuth que não precisava.
    """

    def test_conta_no_disco_aparece_mesmo_sem_a_linha_no_banco(self):
        self.c._persist_canal(M1, CANAL, _payload())
        try:
            import _db
            if _db.disponivel():
                _db.conta_apagar(CANAL, UID)      # simula a escrita perdida
                _db.canal_apagar(M1, CANAL)
        except Exception:
            pass
        achou = [c for c in self.c.contas_conectadas(CANAL) if c["user_id"] == UID]
        self.assertEqual(len(achou), 1, "conta sumiu da tela porque o banco não tinha")
        self.assertEqual(achou[0]["marcas"], [M1])
        r = self.c.vincular_marca(M2, CANAL, UID)
        self.assertTrue(r["ok"], r.get("erro"))

    def test_marcas_da_conta_soma_banco_e_disco(self):
        self.c._persist_canal(M1, CANAL, _payload())
        self.c.vincular_marca(M2, CANAL, UID)
        try:
            import _db
            if _db.disponivel():
                _db.canal_apagar(M2, CANAL)       # vínculo só no disco agora
        except Exception:
            pass
        self.assertEqual(self.c.marcas_da_conta(CANAL, UID), sorted([M1, M2]),
                         "avisaria que só uma marca depende da conta")


class TestDesvincular(BaseContas):
    def test_desvincular_nao_derruba_a_outra(self):
        self.c._persist_canal(M1, CANAL, _payload())
        self.c.vincular_marca(M2, CANAL, UID)

        r = self.c.desconectar(M1, CANAL)
        self.assertTrue(r["ok"], r.get("erro"))
        self.assertEqual(r.get("conta_ainda_usada_por"), [M2],
                         "não avisou que a conta continua em uso")

        self.assertFalse(self.c.status_canal(M1, CANAL)["conectado"])
        self.assertTrue(self.c.status_canal(M2, CANAL)["conectado"],
                        "desvincular uma marca derrubou o acesso da outra")
        self.assertEqual(self.c.token_bruto(M2, CANAL).get("access_token"), "tok-inicial")

    def test_esquecer_conta_diz_quem_dependia(self):
        self.c._persist_canal(M1, CANAL, _payload())
        self.c.vincular_marca(M2, CANAL, UID)

        r = self.c.esquecer_conta(CANAL, UID)
        self.assertTrue(r["ok"], r.get("erro"))
        self.assertEqual(sorted(r["desvinculou"]), sorted([M1, M2]),
                         "apagou a conta sem dizer quantas marcas param de publicar")
        for m in (M1, M2):
            self.assertFalse(self.c.status_canal(m, CANAL)["conectado"])
        self.assertEqual([c for c in self.c.contas_conectadas(CANAL) if c["user_id"] == UID], [])

    def test_vincular_em_conta_inexistente_recusa(self):
        r = self.c.vincular_marca(M1, CANAL, "00000000000000000")
        self.assertFalse(r["ok"])
        self.assertIn("conta", (r.get("erro") or "").lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
