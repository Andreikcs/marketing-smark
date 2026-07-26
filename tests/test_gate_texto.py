import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _gate_texto  # noqa: E402
import _direcao  # noqa: E402


def test_padroes_poluicao_hex_e_mm():
    hits = _gate_texto._achados_poluicao("palette #9A4DFF camera 85mm NEGATIVE no text")
    assert any("#9A4DFF" in h or "9A4DFF" in h for h in hits) or any("85" in h for h in hits)
    assert hits


def test_texto_limpo_sem_hits():
    hits = _gate_texto._achados_poluicao("")
    assert hits == []


def test_avaliar_arquivo_ausente():
    r = _gate_texto.avaliar("/tmp/nao-existe-gate-smark-xyz.png")
    assert r["ok"] is False
    assert r["poluido"] is True


def test_construir_rascunho_sem_hex_nem_85mm():
    p = _direcao.construir_rascunho("smark", "dor", "claro", conceito="violet thread")
    assert "#9A4DFF" not in p
    assert "85mm" not in p
    assert "no text" in p.lower()
    assert "violet thread" in p


def test_construir_final_ainda_tem_detalhe():
    p = _direcao.construir("smark", "dor", "claro")
    assert "85mm" in p
    assert "#9A4DFF" in p or "violet" in p.lower()
