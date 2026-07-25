import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402


def test_registra_uma_linha_por_evento(tmp_path):
    alvo = str(tmp_path / "sub" / "geracoes.jsonl")
    _ledger.registrar({"marca": "smark", "custo_usd": 0.04}, path=alvo)
    _ledger.registrar({"marca": "elever-ai", "custo_usd": 0.04}, path=alvo)
    linhas = open(alvo, encoding="utf-8").read().strip().split("\n")
    assert len(linhas) == 2
    assert json.loads(linhas[0])["marca"] == "smark"


def test_acrescenta_data_automaticamente(tmp_path):
    alvo = str(tmp_path / "g.jsonl")
    _ledger.registrar({"marca": "smark"}, path=alvo)
    ev = json.loads(open(alvo, encoding="utf-8").read().strip())
    assert "data" in ev and ev["data"].startswith("20")


def test_preserva_data_informada(tmp_path):
    alvo = str(tmp_path / "g.jsonl")
    _ledger.registrar({"data": "2020-01-01T00:00:00", "marca": "smark"}, path=alvo)
    ev = json.loads(open(alvo, encoding="utf-8").read().strip())
    assert ev["data"] == "2020-01-01T00:00:00"


def test_falha_de_escrita_nao_propaga(tmp_path):
    # diretório inexistente E sem permissão de criação → não pode explodir
    _ledger.registrar({"marca": "smark"}, path="/proc/impossivel/g.jsonl")
