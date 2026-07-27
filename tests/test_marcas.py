import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _marcas  # noqa: E402


def test_list_slugs_inclui_canonicas():
    s = _marcas.list_slugs()
    assert "smark" in s
    assert "provider-max" in s
    assert "elever-ai" in s


def test_require_desconhecida_erra():
    try:
        _marcas.require("marca-que-nao-existe-xyz")
        assert False
    except ValueError as e:
        assert "não registrada" in str(e) or "inválid" in str(e).lower()


def test_safe_marca_path():
    assert _marcas.safe_marca("smark") == "smark"
    assert _marcas.safe_marca("../etc") == "smark"
    assert _marcas.safe_marca("fantasma-xyz") == "smark"


def test_criar_e_pronta(tmp_path, monkeypatch):
    # isola tokens e pastas em tmp
    tok = {
        "_doc": "test",
        "fundacao": {},
        "marcas": {
            "smark": {"nome": "smark.", "acento": "#8B3CF7", "handle": "@smark"},
        },
    }
    tok_path = tmp_path / "tokens.json"
    tok_path.write_text(json.dumps(tok), encoding="utf-8")
    marcas_dir = tmp_path / "marcas"
    marcas_dir.mkdir()
    perfis = tmp_path / "perfis.json"
    perfis.write_text(json.dumps({
        "familias": {"smark": {"marcas": ["smark"]}},
        "_base": {},
    }), encoding="utf-8")

    monkeypatch.setattr(_marcas, "TOKENS", str(tok_path))
    monkeypatch.setattr(_marcas, "MARCAS_DIR", str(marcas_dir))
    monkeypatch.setattr(_marcas, "PERFIS", str(perfis))
    monkeypatch.setattr(_marcas, "VAULT", str(tmp_path))

    r = _marcas.criar("netsul", "NetSul Fibra", "#E0562D", handle="@netsul", glyph="N")
    assert r["slug"] == "netsul"
    assert _marcas.exists("netsul")
    assert _marcas.pronta("netsul") is True
    assert "netsul" in _marcas.list_slugs()
    meta = json.loads(tok_path.read_text())["marcas"]["netsul"]
    assert meta["acento"] == "#E0562D"
    assert os.path.isdir(marcas_dir / "netsul" / "branding")
    assert os.path.isfile(marcas_dir / "netsul" / "branding" / "identidade-visual.md")
    # perfis sync
    p = json.loads(perfis.read_text())
    assert "netsul" in p["familias"]["smark"]["marcas"]


def test_criar_hex_invalido(tmp_path, monkeypatch):
    tok_path = tmp_path / "tokens.json"
    tok_path.write_text(json.dumps({"marcas": {"smark": {"nome": "s", "acento": "#8B3CF7"}}}), encoding="utf-8")
    monkeypatch.setattr(_marcas, "TOKENS", str(tok_path))
    monkeypatch.setattr(_marcas, "MARCAS_DIR", str(tmp_path / "marcas"))
    monkeypatch.setattr(_marcas, "PERFIS", str(tmp_path / "p.json"))
    try:
        _marcas.criar("x", "X", "vermelho")
        assert False
    except ValueError as e:
        assert "hex" in str(e).lower() or "acento" in str(e).lower()


def test_listar_detalhes_campos():
    d = _marcas.listar_detalhes()
    assert any(x["slug"] == "smark" and x["canonica"] for x in d)
    for x in d:
        assert "acento" in x and "pronta" in x
        assert "wordmark" in x and "glyph" in x


def test_atualizar_marca(tmp_path, monkeypatch):
    tok = {
        "marcas": {
            "smark": {"nome": "smark.", "acento": "#8B3CF7", "handle": "@smark"},
            "cliente": {
                "nome": "Cliente", "acento": "#112233", "acento_claro": "#445566",
                "handle": "@cliente", "wordmark": "Cliente", "logo_glyph": "C",
                "mood": "old",
            },
        },
    }
    tok_path = tmp_path / "tokens.json"
    tok_path.write_text(json.dumps(tok), encoding="utf-8")
    monkeypatch.setattr(_marcas, "TOKENS", str(tok_path))
    monkeypatch.setattr(_marcas, "MARCAS_DIR", str(tmp_path / "marcas"))
    (tmp_path / "marcas" / "cliente" / "branding").mkdir(parents=True)
    (tmp_path / "marcas" / "cliente" / "branding" / "identidade-visual.md").write_text("x")
    (tmp_path / "marcas" / "cliente" / "branding" / "brand-voice.md").write_text("x")

    r = _marcas.atualizar(
        "cliente",
        nome="Cliente Novo",
        acento="#E0562D",
        handle="@clientenovo",
        mood="warm fiber brand",
    )
    assert r["meta"]["nome"] == "Cliente Novo"
    assert r["meta"]["acento"] == "#E0562D"
    assert r["meta"]["handle"] == "@clientenovo"
    assert r["pronta"] is True


def test_salvar_logo_bytes(tmp_path, monkeypatch):
    tok_path = tmp_path / "tokens.json"
    tok_path.write_text(json.dumps({
        "marcas": {"foo": {"nome": "Foo", "acento": "#AABBCC", "handle": "@foo"}},
    }), encoding="utf-8")
    monkeypatch.setattr(_marcas, "TOKENS", str(tok_path))
    monkeypatch.setattr(_marcas, "MARCAS_DIR", str(tmp_path / "marcas"))
    monkeypatch.setattr(_marcas, "VAULT", str(tmp_path))
    # 1x1 png
    import base64
    raw = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    dest = _marcas.salvar_logo_bytes("foo", raw, ext=".png")
    assert os.path.isfile(dest)
    meta = json.loads(tok_path.read_text())["marcas"]["foo"]
    assert meta["brasao"]["principal"].endswith("logo.png")


def test_compositor_aceita_marca_do_tokens():
    """Canônicas e qualquer slug em tokens carregam no compositor."""
    import compositor  # noqa: E402
    brands, _ = compositor.load_brands()
    for s in _marcas.list_slugs():
        assert s in brands
        assert brands[s]["accent"]


def test_direcao_usa_acento_da_marca():
    import _direcao  # noqa: E402
    p = _direcao.construir("smark", "manifesto", "claro")
    assert "#8B3CF7" in p or "8B3CF7" in p.upper()
