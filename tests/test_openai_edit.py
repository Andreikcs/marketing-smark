import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402
import openai_edit  # noqa: E402


def test_openai_edit_importa_ledger():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "openai_edit.py"),
                 encoding="utf-8").read()
    assert "import _ledger" in fonte
    assert "_ledger.registrar" in fonte


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _payload_ok(conteudo=b"conteudo-fake-png"):
    return {"data": [{"b64_json": base64.b64encode(conteudo).decode("ascii")}]}


def test_main_caminho_feliz_grava_png_e_registra_ledger(monkeypatch, tmp_path):
    eventos = []

    def fake_urlopen(req, timeout=None):
        return _FakeResp(_payload_ok())

    def fake_registrar(evento, path=None):
        eventos.append(evento)
        return "ledger-fake"

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_ledger, "registrar", fake_registrar)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    img = tmp_path / "foto.png"
    img.write_bytes(b"foto-original")
    out = tmp_path / "arte" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "recompor com fundo lavanda",
    ])

    openai_edit.main()

    assert out.read_bytes() == b"conteudo-fake-png"
    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["tipo"] == "edit"
    assert ev["provider"] == "openai"
    assert ev["ok"] is True
    assert "erro" not in ev


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

    img = tmp_path / "foto.png"
    img.write_bytes(b"foto-original")

    # simula gravação impossível: o "diretório" pai é na verdade um arquivo,
    # então os.makedirs(dirname) falha com um OSError depois da edição paga.
    bloqueado = tmp_path / "nao-e-diretorio"
    bloqueado.write_text("bloqueado")
    out = bloqueado / "sub" / "post-01.png"

    monkeypatch.setattr(sys, "argv", [
        "openai_edit.py", "--image", str(img), "--out", str(out),
        "--prompt", "recompor com fundo lavanda",
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
