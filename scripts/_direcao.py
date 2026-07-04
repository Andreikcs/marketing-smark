#!/usr/bin/env python3
"""DIREÇÃO DE ARTE — constrói o prompt do FUNDO (sem texto) nível agência pro gpt-image.

Mescla das simulações aprovadas (B+C):
- riqueza de conceito (B): metáfora visual específica por TIPO de post (variedade com coerência);
- composição guiada pelo layout (C): o texto fica no terço inferior → o visual vai pro topo, base limpa;
- minimalismo e disciplina de cor (hex estritos, espelham tokens.json).

A grade de acabamento (duotone+vinheta+grão) é aplicada DEPOIS, no compositor.py (--grade, ligada por padrão).

Uso:  import _direcao;  _direcao.construir(marca, tipo, tema, headline="", conceito="")
"""

# Paleta estrita (espelha design-system/tokens/tokens.json) — usada na cláusula COR
HEX = {"base_escuro": "#0B0B0B", "indigo": "#2A1CA8", "violeta": "#9A4DFF", "roxo": "#8B3CF7",
       "base_claro": "#F4F2FB", "lavanda": "#E7DCFF"}

# Metáfora visual por TIPO de post — variedade com coerência (a "biblioteca de conceitos")
CONCEITOS = {
    "manifesto": "a vast calm space with a single dawning violet light on the horizon — a new beginning, restraint and scale",
    "nucleo": "a single luminous violet filament threading through and connecting a sparse lattice of dark modular blocks — new intelligence integrating into an existing structure",
    "dor": "a tangled knot of cables and blocks slowly being resolved by one clean thread of violet light — friction giving way to order",
    "provoca": "two contrasting zones, chaotic dim clutter versus one clean ordered violet beam — tension between method and noise",
    "educativo": "a clean minimal arrangement of three glowing violet nodes connected by thin light paths — clarity, a teaching diagram abstracted",
    "antihype": "a calm human-scaled surface bathed in soft violet light, tools set down, room to breathe — technology that frees rather than replaces",
    "prova": "a sleek fast streak of violet light tracing from a rough sketch form into a polished glowing object — idea to reality",
    "autoridade": "a solid grounded architectural form lit by confident violet rim light — stable, senior, dependable",
    "diferencial": "existing structures kept fully intact while a violet light wraps gently around them — building around what already works",
    "cta": "an open violet doorway, a path of light leading forward into negative space — an invitation",
}
CONCEITO_PADRAO = "an abstract premium technology key visual — a single restrained violet light gesture in open space"

# Mundo visual por marca (nuance de mood; paleta sempre unificada em roxo)
MARCA_MOOD = {
    "smark": "senior B2B technology consultancy — restrained, trustworthy, architectural",
    "provider-max": "infrastructure operating at scale (telecom / ISP) — systems executing tirelessly, industrial-premium",
    "elever-ai": "warm yet premium — human leads and conversations cared for around the clock, approachable",
}


def _cor(tema):
    if tema == "claro":
        return (f"strict palette only — airy off-white base {HEX['base_claro']} and soft lavender {HEX['lavanda']}, "
                f"with violet {HEX['violeta']} to {HEX['roxo']} as the only accent; light and clean, lots of white space; "
                "no other hues, no warm tones")
    return (f"strict palette only — near-black base {HEX['base_escuro']}, deep indigo {HEX['indigo']} to vivid "
            f"violet {HEX['violeta']} for light and gradients; mostly dark; no other hues, no warm tones")


def _luz(tema):
    if tema == "claro":
        return "soft, airy volumetric light from the upper right, bright and clean"
    return ("dramatic volumetric rim light from the upper right, deep falloff into near-black, "
            "faint atmospheric haze, a single delicate violet glow")


def _material(tema):
    if tema == "claro":
        return "soft frosted glass, matte light surfaces, subtle paper texture, gentle light"
    return "glossy obsidian, brushed dark metal, a thread of glowing glass light"


def construir(marca, tipo="", tema="escuro", headline="", conceito=""):
    """Retorna o prompt completo (inglês) do fundo. `conceito` sobrescreve a metáfora do tipo (temas especiais)."""
    tema = "claro" if tema == "claro" else "escuro"
    conc = conceito.strip() or CONCEITOS.get((tipo or "").lower(), CONCEITO_PADRAO)
    mood = MARCA_MOOD.get(marca, MARCA_MOOD["smark"])
    vazio = "light" if tema == "claro" else "near-black"
    return (
        f"Editorial brand key visual for a {mood}; fully abstract, minimalist. "
        f"CONCEPT: {conc}. "
        f"COMPOSITION: the entire LOWER THIRD of the frame is calm, empty {vazio} negative space reserved for "
        "headline typography; all visual interest sits in the top two-thirds; asymmetric, generous breathing room. "
        f"LIGHT: {_luz(tema)}. "
        "CAMERA: 85mm, shallow depth of field, delicate bokeh, fine cinematic film grain. "
        f"COLOR: {_cor(tema)}. "
        f"MATERIAL: {_material(tema)}. "
        "MOOD: restrained, sophisticated, expensive, confident, calm. "
        "FINISH: hyper-detailed where lit, sharp focus, color-graded like a magazine cover, 4k. "
        "NEGATIVE: no text, no letters, no words, no numbers, no logos, no watermark, no people, no faces, "
        "no UI, no charts, no clutter, no busy patterns, no rainbow colors.")


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    marca = a[0] if a else "smark"
    tipo = a[1] if len(a) > 1 else "nucleo"
    tema = a[2] if len(a) > 2 else "escuro"
    print(construir(marca, tipo, tema))
