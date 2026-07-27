#!/usr/bin/env python3
"""Resolve o perfil de imagem de uma marca: família, modelo, seed, acervo e tier.

Fonte única: design-system/tokens/perfis-imagem.json.
Tiers: `rascunho` (Seedream barato, não publicável) e `final` (Gemini 4K, publicável).
"""
import hashlib
import json
import os
from math import gcd

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRATO = os.path.join(VAULT, "design-system", "tokens", "perfis-imagem.json")

TIERS_VALIDOS = ("rascunho", "final")


def carregar(path=None):
    """Lê o contrato de perfis. Erro explícito se estiver ausente ou inválido."""
    p = path or CONTRATO
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def familia_de(marca, cfg):
    """Nome da família que contém `marca`; a família padrão se não houver correspondência."""
    for nome, fam in (cfg.get("familias") or {}).items():
        if marca in (fam.get("marcas") or []):
            return nome
    return cfg.get("familia_padrao", "smark")


def calcular_seed(familia, slug, tipo, reroll=0):
    """Seed determinística: mesma entrada, mesma imagem. `reroll` varia de propósito."""
    chave = f"{familia}:{slug}:{tipo}".encode("utf-8")
    base = int(hashlib.sha256(chave).hexdigest()[:8], 16) % (2 ** 31)
    return (base + int(reroll or 0)) % (2 ** 31)


def aspect_de_size(size):
    """'1024x1536' -> '2:3'. Devolve '' se não der pra interpretar."""
    try:
        w, h = str(size).lower().split("x")
        w, h = int(w), int(h)
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    except Exception:
        return ""


def capacidades(modelo, cfg):
    """Entrada do roster pro modelo (suporta_seed, max_refs, provider). {} se fora do roster."""
    return ((cfg.get("_base", {}).get("roster") or {}).get(modelo)) or {}


def normalizar_tier(tier, cfg=None):
    """'rascunho' | 'final'. Default vem do contrato (`tier_padrao`)."""
    cfg = cfg or carregar()
    t = (tier or "").strip().lower() if tier is not None else ""
    if t in TIERS_VALIDOS:
        return t
    return (cfg.get("_base") or {}).get("tier_padrao", "rascunho")


def resolver(marca, slug="", tipo="", reroll=0, size="1024x1536", cfg=None, tier=None):
    """Devolve tudo que o orquestrador precisa pra chamar o provedor.

    `tier=rascunho` → modelo barato (Seedream), prompt curto, não publicável (padrão do contrato).
    `tier=final`    → modelo calibrado da família (Gemini), 4K, publicável.
    `tier=None`     → usa `_base.tier_padrao` do contrato.
    """
    cfg = cfg or carregar()
    base = cfg.get("_base", {})
    tier = normalizar_tier(tier, cfg)
    tier_cfg = (base.get("tiers") or {}).get(tier) or {}
    familia = familia_de(marca, cfg)
    fam = (cfg.get("familias") or {}).get(familia, {})

    suplente = fam.get("suplente") or base.get("suplente") or {}

    if tier == "rascunho":
        modelo = fam.get("modelo_rascunho") or tier_cfg.get("modelo")
        if not modelo:
            # sem rascunho configurado → cai pro final da família
            modelo = fam.get("modelo")
            tier = "final"
            tier_cfg = (base.get("tiers") or {}).get("final") or {}
        nao_calibrado = False
    else:
        modelo = fam.get("modelo")
        nao_calibrado = not modelo
        if nao_calibrado:
            modelo = suplente.get("modelo", "gpt-image-1.5")

    # Safety: Seedream nunca como final (mesmo se alguém cravar no JSON da família)
    cap = capacidades(modelo, cfg)
    papeis = cap.get("papel") or []
    if tier == "final" and papeis and "final" not in papeis and "suplente" not in papeis:
        # modelo só de rascunho forçado em final → sobe pro calibrado
        modelo = fam.get("modelo") or suplente.get("modelo", "gpt-image-1.5")
        cap = capacidades(modelo, cfg)
        nao_calibrado = not fam.get("modelo")

    provider = cap.get("provider") or fam.get("provider") or base.get("provider", "openrouter")
    resolution = tier_cfg.get("resolution") or base.get("resolution", "4K")
    # final sem resolution no tier → base
    if tier == "final" and not tier_cfg.get("resolution"):
        resolution = base.get("resolution", "4K")

    acervo_base = base.get("acervo", {})
    acervo_fam = fam.get("acervo", {})
    acervo_dir = acervo_fam.get("dir") or acervo_base.get("dir")
    teto = int(cap.get("max_refs", 0) or 0)
    acervo_max = min(int(acervo_base.get("max_refs", 20)), teto) if teto else 0

    # Acervo por marca (cliente) tem prioridade sobre o da família — isola refs
    brand_acervo = os.path.join(VAULT, "marcas", marca or "", "referencias", "acervo")
    if marca and os.path.isdir(brand_acervo) and any(
        n.lower().endswith(".png") for n in os.listdir(brand_acervo)
    ):
        acervo_dir_abs = brand_acervo
        acervo_ativo = True
    else:
        acervo_dir_abs = os.path.join(VAULT, acervo_dir) if acervo_dir else ""
        acervo_ativo = bool(acervo_fam.get("ativo", acervo_base.get("ativo", False)))

    return {
        "familia": familia,
        "tier": tier,
        "modelo": modelo,
        "provider": provider,
        "resolution": resolution,
        "aspect_ratio": aspect_de_size(size),
        "seed": calcular_seed(familia, slug, tipo, reroll),
        "enviar_seed": bool(cap.get("suporta_seed", False)),
        "suplente_modelo": suplente.get("modelo", "gpt-image-1.5"),
        "suplente_provider": suplente.get("provider", "openai"),
        "nao_calibrado": nao_calibrado,
        "publicavel": bool(tier_cfg.get("publicavel", tier == "final")),
        "gate_texto": bool(tier_cfg.get("gate_texto", tier == "rascunho")),
        "prompt_modo": tier_cfg.get("prompt") or ("curto" if tier == "rascunho" else "direcao"),
        "acervo_ativo": acervo_ativo,
        "acervo_dir": acervo_dir_abs,
        "acervo_max": acervo_max,
    }
