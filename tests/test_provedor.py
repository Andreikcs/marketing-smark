import base64
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _provedor  # noqa: E402

PNG = base64.b64encode(b"fake-png-bytes").decode()

_JPEG_1PX = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAA"
    "AAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==")


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _captura(monkeypatch, payload):
    """Substitui urlopen e devolve a lista onde os requests caem."""
    vistos = []

    def fake(req, timeout=None):
        vistos.append(req)
        return _Resp(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return vistos


def test_openrouter_envia_resolution_e_devolve_custo(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.135}})
    r = _provedor.gerar("um prompt", "google/gemini-3-pro-image", "openrouter",
                        {"openrouter": "k1"}, resolution="4K", aspect_ratio="4:5")
    assert r["png"] == b"fake-png-bytes"
    assert r["custo_usd"] == 0.135
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["resolution"] == "4K"
    assert corpo["aspect_ratio"] == "4:5"
    assert "seed" not in corpo          # não foi pedida — não vai no corpo
    assert "openrouter.ai" in vistos[0].full_url


def test_openrouter_envia_seed_quando_pedida(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.04}})
    _provedor.gerar("p", "m", "openrouter", {"openrouter": "k1"}, seed=99)
    assert json.loads(vistos[0].data.decode())["seed"] == 99


def test_openai_envia_size_e_quality_e_nao_manda_seed(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}]})
    r = _provedor.gerar("p", "gpt-image-1.5", "openai", {"openai": "k2"},
                        size="1024x1536", quality="high", seed=99)
    assert r["png"] == b"fake-png-bytes"
    assert r["custo_usd"] is None
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["size"] == "1024x1536"
    assert corpo["quality"] == "high"
    assert "seed" not in corpo
    assert "api.openai.com" in vistos[0].full_url


def test_refs_viram_input_references_no_openrouter(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.04}})
    _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"},
                    refs=["data:image/png;base64,AAA", "data:image/png;base64,BBB"])
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["input_references"] == ["data:image/png;base64,AAA", "data:image/png;base64,BBB"]


def test_sem_chave_levanta_erro_provedor():
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": None})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert "OPENROUTER_API_KEY" in str(e)


def test_http_402_vira_erro_provedor_com_codigo(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 402, "Payment Required", {},
                                     __import__("io").BytesIO(b'{"error":{"message":"sem credito"}}'))

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert e.codigo == 402


def test_resposta_sem_imagem_vira_erro_provedor(monkeypatch):
    _captura(monkeypatch, {"data": []})
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert "sem imagem" in str(e)


def test_png_passa_intacto():
    raw = b"\x89PNG\r\n\x1a\n" + b"resto"
    assert _provedor.para_png(raw) == raw


def test_jpeg_vira_png():
    """A MESMA chamada devolveu jpeg numa execução e png na outra. Normalizar sempre."""
    jpeg = _JPEG_1PX
    saida = _provedor.para_png(jpeg)
    assert saida.startswith(b"\x89PNG\r\n\x1a\n")


def test_bytes_irreconheciveis_passam_intactos():
    assert _provedor.para_png(b"fake-png-bytes") == b"fake-png-bytes"
