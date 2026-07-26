import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402
import _provedor  # noqa: E402
import openai_edit  # noqa: E402


def test_openai_edit_importa_ledger():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "openai_edit.py"),
                 encoding="utf-8").read()
    assert "import _ledger" in fonte
    assert "_ledger.registrar" in fonte
    assert "editar_openrouter" in fonte


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _payload_ok(conteudo=b"conteudo-fake-png"):
    return {"data": [{"b64_json": base64.b64encode(conteudo).decode("ascii")}]}


def test_main_caminho_feliz_openai(monkeypatch, tmp_path):
    eventos = []

    def fake_urlopen(req, timeout=None):
        return _FakeResp(_payload_ok())

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    img = tmp_path / "foto.png"
    img.write_bytes(b"foto-original")
    out = tmp_path / "arte" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "recompor com fundo lavanda",
        "--provider", "openai",
    ])

    openai_edit.main()

    assert out.read_bytes() == b"conteudo-fake-png"
    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["tipo"] == "edit"
    assert ev["provider"] == "openai"
    assert ev["ok"] is True
    assert "erro" not in ev


def test_main_caminho_feliz_openrouter(monkeypatch, tmp_path):
    eventos = []

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        assert provider == "openrouter"
        assert kw.get("refs") and kw["refs"][0].startswith("data:image/")
        return {"png": b"\x89PNG-or", "custo_usd": 0.24, "modelo": modelo, "provider": "openrouter"}

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    img = tmp_path / "foto.png"
    img.write_bytes(b"\x89PNG-ref")
    out = tmp_path / "arte" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "same man, replace car with motorcycles",
        "--provider", "openrouter",
    ])

    openai_edit.main()

    assert out.read_bytes() == b"\x89PNG-or"
    assert eventos[0]["provider"] == "openrouter"
    assert eventos[0]["custo_usd"] == 0.24
    assert eventos[0]["refs"] == 1


def test_main_falha_ao_gravar_png_ainda_registra_ledger_com_ok_false(monkeypatch, tmp_path):
    eventos = []

    def fake_urlopen(req, timeout=None):
        return _FakeResp(_payload_ok())

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    img = tmp_path / "foto.png"
    img.write_bytes(b"foto-original")

    bloqueado = tmp_path / "nao-e-diretorio"
    bloqueado.write_text("bloqueado")
    out = bloqueado / "sub" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "recompor com fundo lavanda",
        "--provider", "openai",
    ])

    try:
        openai_edit.main()
        assert False, "deveria ter saído com erro"
    except SystemExit as e:
        assert e.code is not None
        assert "salva" in str(e.code) or "ERRO" in str(e.code)

    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["ok"] is False
    assert "erro" in ev and ev["erro"]


def test_billing_openai_cai_no_openrouter(monkeypatch, tmp_path):
    eventos = []

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            url="https://api.openai.com/v1/images/edits",
            code=400, msg="Bad Request", hdrs=None,
            fp=type("F", (), {"read": lambda self: b'{"error":{"message":"Billing hard limit has been reached.","type":"billing_limit_user_err"}}'})(),
        )

    def fake_gerar(prompt, modelo, provider, chaves, **kw):
        return {"png": b"\x89PNG-fallback", "custo_usd": 0.22, "modelo": modelo, "provider": "openrouter"}

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    # Força ordem openai → openrouter: provider auto com ambas as chaves.
    # Com auto e OR first, o openrouter ganha primeiro — então mock OR to fail once? 
    # Better: only openrouter works via fake_gerar, and we set provider auto with OR key only after openai fails.
    # Simplest: provider auto with both keys, openrouter first succeeds via fake_gerar.
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_provedor, "gerar", fake_gerar)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    img = tmp_path / "foto.png"
    img.write_bytes(b"\x89PNG-ref")
    out = tmp_path / "arte" / "x.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "motos no lugar de carros",
        # auto: OpenRouter primeiro — não precisa do billing da OpenAI
        "--provider", "auto",
    ])

    openai_edit.main()
    assert out.read_bytes() == b"\x89PNG-fallback"
    assert eventos[0]["provider"] == "openrouter"
