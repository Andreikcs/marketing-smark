import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402
import _perfil  # noqa: E402
import _provedor  # noqa: E402
import openai_image  # noqa: E402


PERFIL_FAKE = {
    "familia": "smark-familia",
    "modelo": "google/gemini-3-pro-image",
    "provider": "openrouter",
    "resolution": "4K",
    "aspect_ratio": "2:3",
    "seed": 42,
    "enviar_seed": True,
    "suplente_modelo": "gpt-image-1.5",
    "suplente_provider": "openai",
    "nao_calibrado": False,
    "acervo_ativo": False,
    "acervo_dir": None,
    "acervo_max": 14,
    "tier": "final",
    "publicavel": True,
    "gate_texto": False,
    "prompt_modo": "direcao",
}


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


def test_main_caminho_feliz_grava_png_e_registra_ledger(monkeypatch, tmp_path):
    eventos = []

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        return {"png": b"fake-png-bytes", "custo_usd": 0.24, "modelo": modelo, "provider": provider}

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(_perfil, "resolver", lambda *a, **kw: dict(PERFIL_FAKE))
    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)

    out = tmp_path / "arte" / "post-01.png"
    monkeypatch.setattr(sys, "argv", [
        "openai_image.py", "--out", str(out), "--prompt", "um fundo qualquer",
        "--marca", "smark", "--tipo", "manifesto",
    ])

    openai_image.main()

    assert out.read_bytes() == b"fake-png-bytes"
    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["modelo"] == "google/gemini-3-pro-image"
    assert ev["provider"] == "openrouter"
    assert ev["custo_usd"] == 0.24
    assert ev["seed"] == 42
    assert ev["ok"] is True
    assert "erro" not in ev


def test_main_falha_ao_gravar_png_ainda_registra_ledger_com_ok_false(monkeypatch, tmp_path):
    eventos = []

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        return {"png": b"fake-png-bytes", "custo_usd": 0.24, "modelo": modelo, "provider": provider}

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(_perfil, "resolver", lambda *a, **kw: dict(PERFIL_FAKE))
    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)

    # simula gravação impossível: o "diretório" pai é na verdade um arquivo,
    # então os.makedirs(dirname) falha com um OSError depois da geração paga.
    bloqueado = tmp_path / "nao-e-diretorio"
    bloqueado.write_text("bloqueado")
    out = bloqueado / "sub" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_image.py", "--out", str(out), "--prompt", "um fundo qualquer",
        "--marca", "smark", "--tipo", "manifesto",
    ])

    try:
        openai_image.main()
        assert False, "deveria ter saído com erro"
    except SystemExit as e:
        assert e.code is not None
        assert "salva" in str(e.code) or "ERRO" in str(e.code)

    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["ok"] is False
    assert ev["custo_usd"] == 0.24
    assert "erro" in ev and ev["erro"]


def test_main_model_sobrepoe_o_modelo_do_perfil(monkeypatch, tmp_path):
    modelos_chamados = []

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        modelos_chamados.append(modelo)
        return {"png": b"x", "custo_usd": 0.1, "modelo": modelo, "provider": provider}

    def fake_registrar(evento, path=None):
        return "ledger-fake"

    monkeypatch.setattr(_perfil, "resolver", lambda *a, **kw: dict(PERFIL_FAKE))
    monkeypatch.setattr(_perfil, "carregar", lambda *a, **kw: {
        "_base": {"roster": {"outro-modelo-do-roster": {}, "gpt-image-1.5": {}}}
    })
    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)

    out = tmp_path / "arte" / "post-01.png"
    monkeypatch.setattr(sys, "argv", [
        "openai_image.py", "--out", str(out), "--prompt", "um fundo qualquer",
        "--marca", "smark", "--model", "outro-modelo-do-roster",
    ])

    openai_image.main()

    assert modelos_chamados == ["outro-modelo-do-roster"]
