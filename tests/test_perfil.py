import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _perfil  # noqa: E402


def test_familia_agrupa_as_tres_marcas():
    cfg = _perfil.carregar()
    assert _perfil.familia_de("smark", cfg) == "smark"
    assert _perfil.familia_de("provider-max", cfg) == "smark"
    assert _perfil.familia_de("elever-ai", cfg) == "smark"


def test_marca_desconhecida_cai_na_familia_padrao():
    cfg = _perfil.carregar()
    assert _perfil.familia_de("cliente-novo", cfg) == "smark"


def test_seed_e_deterministica():
    a = _perfil.calcular_seed("smark", "churn-invisivel", "dor")
    b = _perfil.calcular_seed("smark", "churn-invisivel", "dor")
    assert a == b
    assert 0 <= a < 2 ** 31


def test_seed_muda_por_slug_e_por_reroll():
    base = _perfil.calcular_seed("smark", "post-a", "dor")
    assert _perfil.calcular_seed("smark", "post-b", "dor") != base
    assert _perfil.calcular_seed("smark", "post-a", "dor", reroll=1) == base + 1


def test_aspect_de_size():
    assert _perfil.aspect_de_size("1024x1536") == "2:3"
    assert _perfil.aspect_de_size("1024x1024") == "1:1"
    assert _perfil.aspect_de_size("1536x1024") == "3:2"


def test_resolver_familia_nao_calibrada_usa_suplente():
    cfg = _perfil.carregar()
    cfg["familias"]["smark"]["modelo"] = None
    r = _perfil.resolver("smark", slug="x", tipo="manifesto", cfg=cfg)
    assert r["nao_calibrado"] is True
    assert r["modelo"] == "gpt-image-1.5"
    assert r["provider"] == "openai"


def test_resolver_usa_modelo_calibrado_quando_existe():
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["modelo"] == "google/gemini-3-pro-image"
    assert r["provider"] == "openrouter"
    assert r["resolution"] == "4K"
    assert r["nao_calibrado"] is False


def test_seed_nao_e_enviada_para_modelo_sem_suporte():
    """gemini-3-pro-image aceita `seed` e ignora. Não mentir no corpo da requisição."""
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["seed"] > 0            # continua calculada, vai pros metadados
    assert r["enviar_seed"] is False


def test_seed_e_enviada_para_modelo_com_suporte():
    cfg = _perfil.carregar()
    cfg["_base"]["roster"]["modelo-ficticio"] = {
        "provider": "openrouter", "suporta_seed": True, "max_refs": 4}
    cfg["familias"]["smark"]["modelo"] = "modelo-ficticio"
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["enviar_seed"] is True


def test_acervo_max_respeita_o_teto_do_modelo():
    """O contrato pede 20 refs, mas o gemini aceita no máximo 14. Vence o menor."""
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["acervo_max"] == 14


def test_seedream_esta_banido_do_roster():
    """Reprovado no bake-off: tipografa o prompt na arte. Ver Global Constraints."""
    cfg = _perfil.carregar()
    assert "bytedance-seed/seedream-4.5" not in cfg["_base"]["roster"]


def test_contrato_tem_roster_e_acervo():
    cfg = _perfil.carregar()
    assert "google/gemini-3-pro-image" in cfg["_base"]["roster"]
    assert cfg["_base"]["acervo"]["max_refs"] == 20
