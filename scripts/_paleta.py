#!/usr/bin/env python3
"""Trava de paleta — anexa disciplina de cor on-brand aos prompts de imagem.
Impede fundo fora da identidade (ex.: vazamento de vermelho/rosa, como já aconteceu).
Usado por openai_image.py e openai_edit.py. Desliga com --no-guard."""

ACENTOS = {
    "roxo": "purple, violet and indigo",
    "lime": "lime green and chartreuse",
    "verde-limao": "lime green and chartreuse",
    "verde-lima": "lime green and chartreuse",
}


def _cor_da_marca(marca):
    """Nome de família de cor a partir do acento da marca (sem exigir paleta nomeada)."""
    if not marca:
        return None
    try:
        import _marcas
        hex_c = ((_marcas.get(marca) or {}).get("acento") or "").upper()
    except Exception:
        return None
    if not hex_c.startswith("#") or len(hex_c) != 7:
        return None
    # mapeia hue grosso
    r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
    if g > r + 30 and g > b + 20:
        return "lime green and chartreuse brand accent"
    if r > g + 40 and r > b + 20:
        return "warm red-orange brand accent (only the brand red, controlled)"
    if b > r + 20 and b >= g:
        return "blue brand accent tones"
    if r > 100 and b > 100 and g < r:
        return "purple, violet and indigo brand accent"
    return f"the brand accent color close to {hex_c} only"


def aplicar_guard(prompt, paleta="", ativo=True, marca=""):
    """Devolve o prompt com a cláusula de disciplina de cor anexada (se ativo)."""
    if not ativo:
        return prompt
    acc = ACENTOS.get((paleta or "").strip().lower())
    if not acc:
        acc = _cor_da_marca(marca)
    cor = (f"deep near-black or soft off-white base with {acc}" if acc
           else "a cohesive on-brand palette: base + the brand accent color only")
    guard = (
        "COLOR DISCIPLINE (strictly on-brand): keep " + cor + "; cinematic, premium and controlled. "
        "Do NOT introduce unintended warm color casts — no random red, orange, pink or magenta tints — "
        "and no oversaturated rainbow lighting, unless the brief above explicitly asks for it. "
        "NO text, words, letters, logos or watermark."
    )
    return prompt.rstrip() + "\n\n" + guard
