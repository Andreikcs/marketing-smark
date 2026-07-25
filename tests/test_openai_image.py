import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _provedor  # noqa: E402
import openai_image  # noqa: E402


def test_carregar_chaves_le_env_e_ambiente(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "do-ambiente")
    ch = openai_image.carregar_chaves({"OPENAI_API_KEY": "do-arquivo"})
    assert ch["openrouter"] == "do-ambiente"
    assert ch["openai"] == "do-arquivo"


def test_usa_o_modelo_do_perfil_quando_da_certo(monkeypatch):
    chamadas = []

    def fake(prompt, modelo, provider, chaves, **kw):
        chamadas.append(modelo)
        return {"png": b"x", "custo_usd": 0.04, "modelo": modelo, "provider": provider}

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "google/gemini-3-pro-image", "provider": "openrouter",
              "resolution": "4K", "aspect_ratio": "2:3", "seed": 7,
              "suplente_modelo": "gpt-image-1.5", "suplente_provider": "openai"}
    r = openai_image.gerar_com_suplente("p", perfil, {"openrouter": "k"}, "1024x1536", "high")
    assert chamadas == ["google/gemini-3-pro-image"]
    assert r["suplente_usado"] is False


def test_cai_no_suplente_quando_o_principal_falha(monkeypatch):
    chamadas = []

    def fake(prompt, modelo, provider, chaves, **kw):
        chamadas.append(modelo)
        if modelo == "google/gemini-3-pro-image":
            raise _provedor.ErroProvedor("sem credito", codigo=402)
        return {"png": b"y", "custo_usd": None, "modelo": modelo, "provider": provider}

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "google/gemini-3-pro-image", "provider": "openrouter",
              "resolution": "4K", "aspect_ratio": "2:3", "seed": 7,
              "suplente_modelo": "gpt-image-1.5", "suplente_provider": "openai"}
    r = openai_image.gerar_com_suplente("p", perfil, {"openai": "k"}, "1024x1536", "high")
    assert chamadas == ["google/gemini-3-pro-image", "gpt-image-1.5"]
    assert r["suplente_usado"] is True
    assert r["png"] == b"y"


def test_valida_modelo_contra_o_roster():
    cfg = __import__("_perfil").carregar()
    roster = cfg["_base"]["roster"]
    assert openai_image.fora_do_roster("modelo/inventado", roster, "gpt-image-1.5") is True
    assert openai_image.fora_do_roster("google/gemini-3-pro-image", roster, "gpt-image-1.5") is False
    assert openai_image.fora_do_roster("gpt-image-1.5", roster, "gpt-image-1.5") is False


def test_falha_dos_dois_propaga_erro(monkeypatch):
    def fake(prompt, modelo, provider, chaves, **kw):
        raise _provedor.ErroProvedor("caiu", codigo=500)

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "m1", "provider": "openrouter", "resolution": "4K",
              "aspect_ratio": "2:3", "seed": 1,
              "suplente_modelo": "m2", "suplente_provider": "openai"}
    try:
        openai_image.gerar_com_suplente("p", perfil, {}, "1024x1536", "high")
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor:
        pass
