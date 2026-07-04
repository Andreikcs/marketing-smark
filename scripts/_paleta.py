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


def aplicar_guard(prompt, paleta="", ativo=True):
    """Devolve o prompt com a cláusula de disciplina de cor anexada (se ativo)."""
    if not ativo:
        return prompt
    acc = ACENTOS.get((paleta or "").strip().lower())
    cor = (f"deep near-black base with {acc} accent tones" if acc
           else "a cohesive on-brand palette: a deep near-black base with the brand accent color")
    guard = (
        "COLOR DISCIPLINE (strictly on-brand): keep " + cor + "; cinematic, premium and controlled. "
        "Do NOT introduce unintended warm color casts — no random red, orange, pink or magenta tints — "
        "and no oversaturated rainbow lighting, unless the brief above explicitly asks for it. "
        "NO text, words, letters, logos or watermark."
    )
    return prompt.rstrip() + "\n\n" + guard
