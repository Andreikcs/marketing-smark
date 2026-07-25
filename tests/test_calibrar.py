import argparse
import json
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402
import _perfil  # noqa: E402
import _provedor  # noqa: E402
import calibrar  # noqa: E402


def test_candidatos_vem_do_roster():
    cfg = _perfil.carregar()
    assert "google/gemini-3-pro-image" in calibrar.candidatos(cfg)


def test_fixar_grava_modelo_e_data(tmp_path):
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    cfg = calibrar.fixar("smark", "google/gemini-3-pro-image", "2026-07-24", path=alvo)
    assert cfg["familias"]["smark"]["modelo"] == "google/gemini-3-pro-image"
    assert cfg["familias"]["smark"]["calibrado_em"] == "2026-07-24"
    gravado = json.load(open(alvo, encoding="utf-8"))
    assert gravado["familias"]["smark"]["modelo"] == "google/gemini-3-pro-image"


def test_fixar_recusa_modelo_fora_do_roster(tmp_path):
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    try:
        calibrar.fixar("smark", "modelo/inventado", "2026-07-24", path=alvo)
        assert False, "deveria ter recusado"
    except ValueError as e:
        assert "roster" in str(e)


def test_fixar_preserva_o_resto_do_contrato(tmp_path):
    """fixar() não pode truncar o contrato: roster, banidos e outras famílias
    têm que sobreviver intactos — só a família alvo muda."""
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    original = json.load(open(alvo, encoding="utf-8"))

    cfg = calibrar.fixar("smark", "gpt-image-1.5", "2026-07-24", path=alvo)

    assert cfg["_base"]["roster"] == original["_base"]["roster"]
    assert cfg["_base"]["banidos"] == original["_base"]["banidos"]
    assert cfg["familias"]["smark"]["marcas"] == original["familias"]["smark"]["marcas"]
    gravado = json.load(open(alvo, encoding="utf-8"))
    assert gravado["_base"]["roster"] == original["_base"]["roster"]


def test_fixar_nao_corrompe_contrato_se_escrita_falhar_no_meio(tmp_path, monkeypatch):
    """Se json.dump() explodir no meio da escrita, o contrato no destino tem que
    continuar sendo o original íntegro — nunca truncado ou com JSON inválido.
    E nenhum arquivo temporário pode sobrar no diretório."""
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    original = json.load(open(alvo, encoding="utf-8"))

    def dump_quebrado(*a, **kw):
        raise RuntimeError("falha simulada no meio da escrita")

    monkeypatch.setattr(json, "dump", dump_quebrado)

    with pytest.raises(RuntimeError):
        calibrar.fixar("smark", "gpt-image-1.5", "2026-07-24", path=alvo)

    gravado = json.load(open(alvo, encoding="utf-8"))
    assert gravado == original
    assert gravado["_base"]["roster"] == original["_base"]["roster"]
    assert gravado["_base"]["banidos"] == original["_base"]["banidos"]
    assert gravado["familias"] == original["familias"]

    sobras = [p for p in os.listdir(tmp_path) if p != "perfis-imagem.json"]
    assert sobras == [], f"arquivo(s) temporário(s) deixados para trás: {sobras}"


def _args(**over):
    base = dict(familia="smark", marca="smark", tema="claro", paleta="roxo")
    base.update(over)
    return argparse.Namespace(**base)


def test_gerar_variante_sucesso_grava_png_e_ledger(tmp_path, monkeypatch):
    eventos = []
    monkeypatch.setattr(_ledger, "registrar", lambda ev, path=None: eventos.append(ev))
    monkeypatch.setattr(
        _provedor, "gerar",
        lambda prompt, modelo, provider, chaves, **kw: {
            "png": b"fake-png-bytes", "custo_usd": 0.24, "modelo": modelo, "provider": provider})

    cfg = _perfil.carregar()
    destino = tmp_path / "calibracao"
    destino.mkdir()
    ok, msg = calibrar._gerar_variante(
        "google/gemini-3-pro-image", "manifesto", _args(), cfg, {}, str(destino))

    assert ok is True
    assert (destino / "google-gemini-3-pro-image-manifesto.png").read_bytes() == b"fake-png-bytes"
    assert len(eventos) == 1
    assert eventos[0]["ok"] is True
    assert eventos[0]["custo_usd"] == 0.24
    assert "erro" not in eventos[0]


def test_gerar_variante_falha_do_provedor_nao_gera_ledger(tmp_path, monkeypatch):
    """Sem cobrança (a chamada falhou antes de gerar imagem), não há o que registrar."""
    eventos = []
    monkeypatch.setattr(_ledger, "registrar", lambda ev, path=None: eventos.append(ev))

    def fake_falha(prompt, modelo, provider, chaves, **kw):
        raise _provedor.ErroProvedor("sem crédito", codigo=402)

    monkeypatch.setattr(_provedor, "gerar", fake_falha)

    cfg = _perfil.carregar()
    destino = tmp_path / "calibracao"
    destino.mkdir()
    ok, msg = calibrar._gerar_variante(
        "google/gemini-3-pro-image", "manifesto", _args(), cfg, {}, str(destino))

    assert ok is False
    assert "FALHOU" in msg
    assert eventos == []


def test_gerar_variante_falha_ao_gravar_ainda_assim_registra_ledger(tmp_path, monkeypatch):
    """Lacuna coberta além do brief: uma chamada paga com sucesso seguida de falha
    ao gravar em disco não pode pular o registro no ledger — o dinheiro já saiu."""
    eventos = []
    monkeypatch.setattr(_ledger, "registrar", lambda ev, path=None: eventos.append(ev))
    monkeypatch.setattr(
        _provedor, "gerar",
        lambda prompt, modelo, provider, chaves, **kw: {
            "png": b"fake-png-bytes", "custo_usd": 0.24, "modelo": modelo, "provider": provider})

    cfg = _perfil.carregar()
    destino = tmp_path / "calibracao"
    destino.mkdir()
    modelo, tipo = "google/gemini-3-pro-image", "manifesto"
    # Cria um diretório no exato caminho de saída: open(..., "wb") vai falhar com
    # IsADirectoryError (subclasse de OSError), sem precisar mockar builtins.open.
    (destino / f"{calibrar._sanitizar(modelo)}-{tipo}.png").mkdir()

    ok, msg = calibrar._gerar_variante(modelo, tipo, _args(), cfg, {}, str(destino))

    assert ok is False
    assert "gravação em disco" in msg
    assert len(eventos) == 1
    assert eventos[0]["ok"] is False
    assert eventos[0]["custo_usd"] == 0.24
    assert "erro" in eventos[0]


def test_main_bake_off_continua_apos_falha_parcial(tmp_path, monkeypatch):
    """Uma variante falhando não pode abortar as demais nem apagar o registro
    do que já foi gasto nas chamadas anteriores."""
    eventos = []
    monkeypatch.setattr(_ledger, "registrar", lambda ev, path=None: eventos.append(ev))

    chamadas = {"n": 0}

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise _provedor.ErroProvedor("falha simulada")
        return {"png": b"fake", "custo_usd": 0.24, "modelo": modelo, "provider": provider}

    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(calibrar, "VAULT", str(tmp_path))
    monkeypatch.setattr(
        sys, "argv",
        ["calibrar.py", "--familia", "smark", "--marca", "smark", "--tipos", "manifesto,dor"])

    with pytest.raises(SystemExit):
        calibrar.main()

    cfg = _perfil.carregar()
    total_combinacoes = len(calibrar.candidatos(cfg)) * 2  # 2 tipos
    assert chamadas["n"] == total_combinacoes
    # só as chamadas que geraram imagem (todas menos a primeira) viram evento
    assert len(eventos) == total_combinacoes - 1
    assert all(ev["ok"] is True for ev in eventos)
