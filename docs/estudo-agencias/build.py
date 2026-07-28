#!/usr/bin/env python3
"""Gera white-studio.html a partir do template, embutindo as artes de prova em base64.

As artes ficam em `_artes/` como JPEG. O HTML final é autocontido — abre em qualquer
lugar, inclusive fora do servidor, sem depender de caminho relativo.

Uso:  python3 build.py
"""
import base64
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ARTES = RAIZ / "_artes"
TEMPLATE = RAIZ / "white-studio_template.html"
SAIDA = RAIZ / "white-studio.html"

html = TEMPLATE.read_text(encoding="utf-8")
for n in (1, 2, 3):
    png = ARTES / f"prova-{n}.jpg"
    b64 = base64.b64encode(png.read_bytes()).decode("ascii")
    html = html.replace("{{IMG%d}}" % n, f"data:image/jpeg;base64,{b64}")

faltando = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
if faltando:
    raise SystemExit(f"placeholder não substituído: {faltando}")

SAIDA.write_text(html, encoding="utf-8")
print(f"white-studio.html gerado — {SAIDA.stat().st_size // 1024} KB")
