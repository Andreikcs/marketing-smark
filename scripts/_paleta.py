#!/usr/bin/env python3
"""Trava de paleta — anexa disciplina de cor on-brand aos prompts de imagem.
Impede fundo fora da identidade (ex.: vazamento de vermelho/rosa, como já aconteceu).
Usado por openai_image.py e openai_edit.py. Desliga com --no-guard.

REGRA CRÍTICA: NUNCA colocar hex (#RRGGBB) no prompt.
Seedream (e outros modelos baratos) IMPRIMEM o código na arte (ex.: #30211D).
Só nomes de cor em linguagem natural.
"""
import re

ACENTOS = {
    "roxo": "soft purple, violet and indigo",
    "lime": "soft lime green and chartreuse",
    "verde-limao": "soft lime green and chartreuse",
    "verde-lima": "soft lime green and chartreuse",
}

# Hex que vaza no prompt → arte poluída (gate + desperdício de crédito)
_RE_HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


def _nome_cor_hex(hex_c):
    """Traduz #RRGGBB em nome natural (sem dígitos) pro modelo de imagem."""
    if not hex_c or not str(hex_c).startswith("#"):
        return None
    h = str(hex_c).strip().upper()
    if len(h) == 4:  # #RGB
        h = "#" + "".join(c * 2 for c in h[1:])
    if len(h) != 7:
        return None
    try:
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    except ValueError:
        return None
    # quase preto / cinza escuro
    if max(r, g, b) < 40:
        return "deep near-black charcoal"
    if abs(r - g) < 18 and abs(g - b) < 18:
        if max(r, g, b) < 90:
            return "warm dark taupe charcoal"
        return "soft neutral gray"
    # marrom / mocha / nude (clínicas, beauty) — ex. #30211D
    if r >= g >= b and r - b >= 8 and r < 160 and g < 120:
        if r < 70:
            return "deep warm mocha brown cocoa"
        if r < 120:
            return "warm mocha brown nude cocoa"
        return "soft warm beige taupe nude"
    # verde limão / chartreuse
    if g > r + 30 and g > b + 20:
        return "soft lime green and chartreuse"
    # vermelho / laranja quente
    if r > g + 40 and r > b + 20:
        return "controlled warm brand red-orange"
    # azul / ciano
    if b > r + 20 and b >= g:
        if g > r + 15:
            return "soft teal cyan brand"
        return "soft blue brand"
    # roxo / violeta
    if r > 80 and b > 80 and g < min(r, b) + 30:
        return "soft purple violet indigo"
    # rosa
    if r > g + 20 and r > b and b > g:
        return "soft dusty rose blush"
    return "soft warm brand-colored light"


def _cor_da_marca(marca):
    """Nome de família de cor a partir do acento da marca (SEM hex no retorno)."""
    if not marca:
        return None
    try:
        import _marcas
        hex_c = ((_marcas.get(marca) or {}).get("acento") or "").upper()
    except Exception:
        return None
    return _nome_cor_hex(hex_c)


def strip_hex_do_prompt(prompt):
    """Remove qualquer #RRGGBB do prompt (Seedream tipografa isso na arte)."""
    if not prompt:
        return prompt
    # "close to #30211D" → some
    out = re.sub(r"\bclose to\s*#[0-9A-Fa-f]{3,8}\b", "brand accent", prompt, flags=re.I)
    out = _RE_HEX.sub("brand accent", out)
    return out


def aplicar_guard(prompt, paleta="", ativo=True, marca=""):
    """Devolve o prompt com a cláusula de disciplina de cor anexada (se ativo).

    Nunca injeta hex — só nomes naturais.
    """
    if not ativo:
        return strip_hex_do_prompt(prompt)
    acc = ACENTOS.get((paleta or "").strip().lower())
    if not acc:
        acc = _cor_da_marca(marca)
    cor = (f"deep near-black or soft off-white base with {acc}" if acc
           else "a cohesive on-brand palette: base + the brand accent color only")
    guard = (
        "COLOR DISCIPLINE (strictly on-brand): keep " + cor + "; cinematic, premium and controlled. "
        "Do NOT introduce unintended warm color casts — no random red, orange, pink or magenta tints — "
        "and no oversaturated rainbow lighting, unless the brief above explicitly asks for it. "
        "NO text, words, letters, numbers, hex color codes, logos or watermark anywhere in the image."
    )
    full = (prompt or "").rstrip() + "\n\n" + guard
    return strip_hex_do_prompt(full)
