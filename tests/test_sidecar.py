import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _sidecar  # noqa: E402


def test_mantem_campos_existentes():
    bloco = _sidecar.meta_block("/x/arte/01.png", {"modelo": "gpt-image-1.5",
                                                   "qualidade": "high",
                                                   "tamanho": "1024x1536",
                                                   "paleta": "roxo"})
    assert "arte: arte/01.png" in bloco
    assert "arte-modelo: gpt-image-1.5" in bloco
    assert "arte-proporcao: 2:3" in bloco
    assert "embed-no-corpo: ![[arte/01.png]]" in bloco


def test_inclui_campos_novos():
    bloco = _sidecar.meta_block("/x/arte/01.png", {
        "modelo": "google/gemini-3-pro-image", "tamanho": "1024x1536",
        "seed": 12345, "custo_usd": 0.135,
        "provider": "openrouter", "suplente_usado": False})
    assert "arte-seed: 12345" in bloco
    assert "arte-custo-usd: 0.135" in bloco
    assert "arte-provider: openrouter" in bloco
    assert "arte-suplente: false" in bloco


def test_suplente_true_sai_como_true():
    bloco = _sidecar.meta_block("/x/a.png", {"suplente_usado": True})
    assert "arte-suplente: true" in bloco
