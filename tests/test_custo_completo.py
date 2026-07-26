import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _cambio  # noqa: E402
import _custo_llm  # noqa: E402
import _ledger  # noqa: E402


def test_custo_tokens_claude_opus():
    # 1M input @15 + 1M output @75 = 90
    c = _custo_llm.custo_tokens("claude-opus-4-8", 1_000_000, 1_000_000)
    assert abs(c - 90.0) < 0.01


def test_custo_tokens_pequeno():
    # 10k in + 2k out opus ≈ 0.15 + 0.15 = 0.30
    c = _custo_llm.custo_tokens("claude-opus-4-8", 10_000, 2_000)
    assert 0.14 < c < 0.35


def test_usd_para_brl_com_taxa_fixa():
    brl = _cambio.usd_para_brl(1.0, cot={"usd_brl": 5.5})
    assert brl == 5.5


def test_enriquecer_preenche_campos(monkeypatch):
    monkeypatch.setattr(_cambio, "cotacao", lambda forcar=False: {
        "usd_brl": 5.25, "fonte": "teste", "buscado_em": "2026-01-01", "cache": True
    })
    p = _cambio.enriquecer(0.24)
    assert p["custo_usd"] == 0.24
    assert abs(p["custo_brl"] - 1.26) < 0.001
    assert p["usd_brl"] == 5.25


def test_ledger_copy_e_imagem_e_totais(tmp_path, monkeypatch):
    monkeypatch.setattr(_ledger, "LEDGER_IMAGEM", str(tmp_path / "geracoes.jsonl"))
    monkeypatch.setattr(_ledger, "LEDGER_COPY", str(tmp_path / "copys.jsonl"))
    monkeypatch.setattr(_ledger, "LEDGER_POSTS", str(tmp_path / "posts.jsonl"))
    monkeypatch.setattr(_cambio, "cotacao", lambda forcar=False: {
        "usd_brl": 5.0, "fonte": "teste", "buscado_em": "x", "cache": True, "ts": 0
    })

    _ledger.registrar_imagem({
        "slug": "post-demo", "marca": "smark", "custo_usd": 0.24, "ok": True, "modelo": "gemini"
    })
    _ledger.registrar_copy({
        "slug": "post-demo", "marca": "smark", "custo_usd": 0.08, "ok": True, "modelo": "claude"
    })
    t = _ledger.totais_por_post("post-demo", "smark")
    assert t["n_imagens"] == 1
    assert t["n_copys"] == 1
    assert abs(t["total_usd"] - 0.32) < 1e-6
    assert abs(t["total_brl"] - 1.6) < 1e-6
    assert abs(t["imagem_usd"] - 0.24) < 1e-6
    assert abs(t["copy_usd"] - 0.08) < 1e-6


def test_resumo_periodo(tmp_path, monkeypatch):
    monkeypatch.setattr(_ledger, "LEDGER_IMAGEM", str(tmp_path / "g.jsonl"))
    monkeypatch.setattr(_ledger, "LEDGER_COPY", str(tmp_path / "c.jsonl"))
    monkeypatch.setattr(_cambio, "cotacao", lambda forcar=False: {
        "usd_brl": 5.0, "fonte": "t", "buscado_em": "x", "cache": True, "ts": 0
    })
    _ledger.registrar_imagem({"custo_usd": 0.24, "ok": True, "data": "2026-07-26T10:00:00"})
    _ledger.registrar_copy({"custo_usd": 0.10, "ok": True, "data": "2026-07-26T10:01:00"})
    r = _ledger.resumo_periodo("2026-07")
    assert r["n_imagens"] == 1
    assert r["n_copys"] == 1
    assert abs(r["total_usd"] - 0.34) < 1e-6
