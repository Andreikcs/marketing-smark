#!/usr/bin/env python3
"""Resolve o perfil de imagem de uma marca: família, modelo, seed e acervo.

Fonte única: design-system/tokens/perfis-imagem.json. Nenhuma decisão estética
mora em código — só no contrato. Ver docs/superpowers/specs/2026-07-24-motor-de-imagem-calibrado-design.md
"""
import hashlib
import json
import os
from math import gcd

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRATO = os.path.join(VAULT, "design-system", "tokens", "perfis-imagem.json")


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
    return base + int(reroll or 0)


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


def resolver(marca, slug="", tipo="", reroll=0, size="1024x1536", cfg=None):
    """Devolve tudo que o orquestrador precisa pra chamar o provedor.

    Não existe tier: 1K/2K/4K custam o mesmo no modelo default, então a
    resolução é única e vem de `_base.resolution`.
    """
    cfg = cfg or carregar()
    base = cfg.get("_base", {})
    familia = familia_de(marca, cfg)
    fam = (cfg.get("familias") or {}).get(familia, {})

    modelo = fam.get("modelo")
    nao_calibrado = not modelo
    suplente = fam.get("suplente") or base.get("suplente") or {}

    if nao_calibrado:
        modelo = suplente.get("modelo", "gpt-image-1.5")

    cap = capacidades(modelo, cfg)
    provider = cap.get("provider") or fam.get("provider") or base.get("provider", "openrouter")

    acervo_base = base.get("acervo", {})
    acervo_fam = fam.get("acervo", {})
    acervo_dir = acervo_fam.get("dir") or acervo_base.get("dir")
    # O teto do contrato nunca pode passar do que o modelo aceita.
    teto = int(cap.get("max_refs", 0) or 0)
    acervo_max = min(int(acervo_base.get("max_refs", 20)), teto) if teto else 0

    return {
        "familia": familia,
        "modelo": modelo,
        "provider": provider,
        "resolution": base.get("resolution", "4K"),
        "aspect_ratio": aspect_de_size(size),
        "seed": calcular_seed(familia, slug, tipo, reroll),
        "enviar_seed": bool(cap.get("suporta_seed", False)),
        "suplente_modelo": suplente.get("modelo", "gpt-image-1.5"),
        "suplente_provider": suplente.get("provider", "openai"),
        "nao_calibrado": nao_calibrado,
        "acervo_ativo": bool(acervo_fam.get("ativo", acervo_base.get("ativo", False))),
        "acervo_dir": os.path.join(VAULT, acervo_dir) if acervo_dir else "",
        "acervo_max": acervo_max,
    }
