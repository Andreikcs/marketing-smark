#!/usr/bin/env python3
"""Gera a proposta comercial de social media, personalizada por cliente.

O HTML sai autocontido (artes embutidas em base64), então pode ser enviado por
e-mail, hospedado em qualquer lugar ou impresso em PDF pelo navegador.

Uso:
    python3 build.py                          # versão genérica
    python3 build.py "Contabilidade Silva"    # personalizada

Para trocar as peças de exemplo, substitua os arquivos em `_artes/`
(prova-1.jpg, prova-2.jpg, prova-3.jpg) e rode de novo.
"""
import base64
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ARTES = RAIZ / "_artes"
TEMPLATE = RAIZ / "proposta_template.html"

# Preços dos planos. Alterar aqui e rodar de novo — o preço por peça é recalculado.
PLANOS = {
    "P1": {"valor": 297, "pecas": 8},
    "P2": {"valor": 397, "pecas": 12},
}


def slug(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def brl(valor):
    return f"{valor:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")


def main():
    cliente = sys.argv[1] if len(sys.argv) > 1 else "seu escritório"
    html = TEMPLATE.read_text(encoding="utf-8")

    html = html.replace("{{CLIENTE}}", cliente)
    for chave, p in PLANOS.items():
        html = html.replace("{{%s}}" % chave, str(p["valor"]))
        html = html.replace("{{%s_UNIT}}" % chave, brl(p["valor"] / p["pecas"]))

    for n in (1, 2, 3):
        b64 = base64.b64encode((ARTES / f"prova-{n}.jpg").read_bytes()).decode("ascii")
        html = html.replace("{{IMG%d}}" % n, f"data:image/jpeg;base64,{b64}")

    faltando = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    if faltando:
        raise SystemExit(f"placeholder não substituído: {sorted(set(faltando))}")

    nome = f"proposta-{slug(cliente)}.html" if len(sys.argv) > 1 else "proposta.html"
    saida = RAIZ / nome
    saida.write_text(html, encoding="utf-8")
    print(f"{nome} — {saida.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
