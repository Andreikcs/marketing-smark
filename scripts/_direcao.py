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

# Mundo visual por marca (canônicas). Clientes externos: tokens.mood ou genérico.
MARCA_MOOD = {
    "smark": "senior B2B technology consultancy — restrained, trustworthy, architectural",
    "provider-max": "infrastructure operating at scale (telecom / ISP) — systems executing tirelessly, industrial-premium",
    "elever-ai": "warm yet premium — human leads and conversations cared for around the clock, approachable",
}


def _meta_marca(marca):
    """Acento/mood da marca via tokens (multi-marca). Fallback smark."""
    try:
        import _marcas
        m = _marcas.get(marca) or {}
        if m:
            return m
    except Exception:
        pass
    return {}


def _cor(tema, acento=None, acento_claro=None):
    acc = (acento or HEX["roxo"]).upper()
    acc2 = (acento_claro or HEX["violeta"]).upper()
    if tema == "claro":
        return (f"strict palette only — airy off-white base {HEX['base_claro']} and soft tint of {acc2}, "
                f"with {acc} to {acc2} as the only accent; light and clean, lots of white space; "
                "no other hues unless in the brand accent family, no random warm casts")
    return (f"strict palette only — near-black base {HEX['base_escuro']}, deep tones with "
            f"{acc} to {acc2} for light and gradients; mostly dark; no other hues, no random warm casts")


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
    """Retorna o prompt completo (inglês) do fundo. `conceito` sobrescreve a metáfora do tipo (temas especiais).

    Usar no tier=final (Gemini). NÃO usar no Seedream — ele tipografa hex/85mm.
    """
    tema = "claro" if tema == "claro" else "escuro"
    conc = conceito.strip() or CONCEITOS.get((tipo or "").lower(), CONCEITO_PADRAO)
    meta = _meta_marca(marca)
    mood = meta.get("mood") or MARCA_MOOD.get(marca) or (
        f"premium on-brand visual for {meta.get('nome') or marca} — clean, professional")
    acc = meta.get("acento") or HEX["roxo"]
    acc2 = meta.get("acento_claro") or HEX["violeta"]
    vazio = "light" if tema == "claro" else "near-black"
    return (
        f"Editorial brand key visual for a {mood}; fully abstract, minimalist. "
        f"CONCEPT: {conc}. "
        f"COMPOSITION: the entire LOWER THIRD of the frame is calm, empty {vazio} negative space reserved for "
        "headline typography; all visual interest sits in the top two-thirds; asymmetric, generous breathing room. "
        f"LIGHT: {_luz(tema)}. "
        "CAMERA: 85mm, shallow depth of field, delicate bokeh, fine cinematic film grain. "
        f"COLOR: {_cor(tema, acc, acc2)}. "
        f"MATERIAL: {_material(tema)}. "
        "MOOD: restrained, sophisticated, expensive, confident, calm. "
        "FINISH: hyper-detailed where lit, sharp focus, color-graded like a magazine cover, 4k. "
        "CRITICAL HARD RULE: the image must contain ZERO written language — no text, no letters, "
        "no words, no typography, no numbers, no captions, no brand names written out, no logos with text, "
        "no watermark, no signage, no menu boards, no packaging labels with readable words. "
        "Pure visual photography/materials only; all typography is added later by a separate compositor. "
        "NEGATIVE: no text, no letters, no words, no numbers, no logos, no watermark, no people, no faces, "
        "no UI, no charts, no clutter, no busy patterns, no rainbow colors.")


def construir_rascunho(marca, tipo="", tema="escuro", headline="", conceito=""):
    """Prompt CURTO pro tier=rascunho (Seedream).

    Sem hex, sem 85mm, sem listas técnicas — o Seedream imprime isso na arte
    (bake-off 2026-07-24). Só conceito + composição + proibição de texto em
    linguagem natural. Cor: nome de família (violet/teal/etc) sem hex.
    """
    tema = "claro" if tema == "claro" else "escuro"
    conc = conceito.strip() or CONCEITOS.get((tipo or "").lower(), CONCEITO_PADRAO)
    if len(conc) > 220:
        conc = conc[:220].rsplit(" ", 1)[0]
    meta = _meta_marca(marca)
    # tom de cor SEM hex (Seedream tipografa #RRGGBB na arte — nunca colocar código)
    acc = (meta.get("acento") or "#8B3CF7").upper()
    if acc in ("#C6F24E", "#D6FF5C", "#B8E62E"):
        tint = "soft lime green light"
    elif acc in ("#1CA5B2", "#3DC4D0", "#17A2B8", "#0D9488", "#14B8A6"):
        tint = "soft teal cyan brand light on deep navy"
    elif acc.startswith("#E") or acc.startswith("#C0") or acc.startswith("#D4"):
        tint = "soft warm brand-colored light"
    elif len(acc) == 7:
        try:
            r, g, b = int(acc[1:3], 16), int(acc[3:5], 16), int(acc[5:7], 16)
            # marrom/mocha/nude escuro (ex. #30211D clínicas beauty)
            if r >= g >= b and r - b >= 8 and r < 160 and g < 120:
                tint = "soft warm mocha brown nude cocoa light"
            elif g > 100 and b > 100 and abs(g - b) < 40 and r < g:
                tint = "soft teal cyan brand light"
            elif r > g + 40 and r > b + 20:
                tint = "soft warm brand-colored light"
            elif b > r + 20 and b >= g:
                tint = "soft blue brand-colored light"
            elif r > 80 and b > 80 and g < min(r, b) + 30:
                tint = "soft violet brand-colored light"
            else:
                tint = "soft warm neutral brand-colored light"
        except ValueError:
            tint = "soft warm neutral brand-colored light"
    else:
        tint = "soft warm neutral brand-colored light"
    if tema == "claro":
        base = f"bright airy background soft white and pale tint, {tint}"
    else:
        base = f"dark premium background soft haze, {tint}"
    return (
        f"Premium brand background, {base}, clean empty lower third for overlay text later, "
        f"visual interest in upper two thirds, abstract editorial, sophisticated, "
        f"photorealistic materials. "
        f"HARD RULE: absolute zero text — no letters, words, numbers, hex codes, price tags, "
        f"labels, logos, watermark, packaging text, signage, UI, captions. "
        f"Product packaging must be blank unlabeled. Pure visual only; typography is added later "
        f"by software. Concept: {conc}."
    )


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    marca = a[0] if a else "smark"
    tipo = a[1] if len(a) > 1 else "nucleo"
    tema = a[2] if len(a) > 2 else "escuro"
    modo = a[3] if len(a) > 3 else "final"
    if modo == "rascunho":
        print(construir_rascunho(marca, tipo, tema))
    else:
        print(construir(marca, tipo, tema))
