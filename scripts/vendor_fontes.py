#!/usr/bin/env python3
"""Baixa Anton + Archivo do Google Fonts e gera um CSS com as fontes embutidas.

Por que isto existe: o compositor pedia as fontes ao Google Fonts por `@import`
no meio do render. Isso é uma dependência de rede dentro do caminho que produz a
arte final — se o Google demorasse mais que o orçamento de render (4s), o Chrome
desenhava com fonte de fallback e a peça saía diferente. Ou seja: o cliente podia
aprovar uma arte e o Instagram receber outra.

Com o CSS embutido, o render não toca a rede e sai idêntico no Mac e no Railway.

Rodar só quando quiser atualizar as fontes:
    python3 scripts/vendor_fontes.py
O resultado (design-system/assets/fontes/fontes.css) é versionado.
"""
from __future__ import annotations

import base64
import os
import re
import sys
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(VAULT, "design-system", "assets", "fontes")
CSS_URL = ("https://fonts.googleapis.com/css2"
           "?family=Anton&family=Archivo:wght@500;700;800&display=swap")
# UA de navegador: sem isso o Google devolve TTF legado em vez de woff2
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

# pt-BR precisa de latin (á ã ç é ê í ó ô õ ú) e latin-ext. Os outros subsets
# (cirílico, grego, vietnamita) só engordariam o HTML sem nunca serem usados.
SUBSETS_OK = ("latin", "latin-ext")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    os.makedirs(DEST, exist_ok=True)
    css = _get(CSS_URL).decode("utf-8")

    # O CSS vem como uma sequência de blocos @font-face, cada um precedido de um
    # comentário com o nome do subset: /* latin */
    blocos = re.split(r"/\*\s*([a-z\-]+)\s*\*/", css)
    # Archivo é fonte VARIÁVEL: o Google devolve o mesmo woff2 para 500, 700 e
    # 800. Embutir os três seria triplicar 34KB de base64 em todo render. Aqui a
    # gente agrupa por arquivo e declara a faixa (`font-weight: 500 800`), que é
    # exatamente o que a fonte variável sabe fazer.
    grupos: dict[str, dict] = {}
    ordem: list[str] = []
    pulados = 0
    # blocos = ['', 'latin', '@font-face{...}', 'latin-ext', '@font-face{...}', ...]
    for i in range(1, len(blocos) - 1, 2):
        subset, corpo = blocos[i], blocos[i + 1]
        if subset not in SUBSETS_OK:
            pulados += 1
            continue
        m = re.search(r"url\((https://[^)]+\.woff2)\)", corpo)
        if not m:
            continue
        url = m.group(1)
        g = grupos.get(url)
        if g is None:
            fam = re.search(r"font-family:\s*'([^']+)'", corpo)
            rng = re.search(r"unicode-range:\s*([^;}]+)", corpo)
            g = grupos[url] = {
                "familia": fam.group(1) if fam else "sans-serif",
                "subset": subset,
                "range": (rng.group(1).strip() if rng else ""),
                "pesos": set(),
            }
            ordem.append(url)
        peso = re.search(r"font-weight:\s*([0-9]+)", corpo)
        g["pesos"].add(int(peso.group(1)) if peso else 400)

    saida, baixados = [], 0
    for url in ordem:
        g = grupos[url]
        nome = url.rsplit("/", 1)[-1]
        caminho = os.path.join(DEST, nome)
        if os.path.isfile(caminho):
            dados = open(caminho, "rb").read()
        else:
            dados = _get(url)
            open(caminho, "wb").write(dados)
            baixados += 1
        pesos = sorted(g["pesos"])
        wt = str(pesos[0]) if len(pesos) == 1 else "%d %d" % (pesos[0], pesos[-1])
        b64 = base64.b64encode(dados).decode()
        face = ("@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
                "font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');"
                % (g["familia"], wt, b64))
        if g["range"]:
            face += "unicode-range:%s;" % g["range"]
        face += "}"
        print("  %-9s %-9s %-8s %6.1fKB" % (g["familia"], g["subset"], wt, len(dados) / 1024))
        saida.append(face)

    if not saida:
        print("nada baixado — formato do CSS do Google mudou?", file=sys.stderr)
        return 1

    cab = ("/* Gerado por scripts/vendor_fontes.py — NÃO editar à mão.\n"
           "   Fontes embutidas em base64 pra que o render da arte não dependa\n"
           "   da rede: mesma tipografia no Mac e no Railway, sempre. */\n")
    alvo = os.path.join(DEST, "fontes.css")
    open(alvo, "w", encoding="utf-8").write(cab + "\n".join(saida) + "\n")
    kb = os.path.getsize(alvo) / 1024
    print("\n%s  (%.0fKB, %d faces, %d subsets ignorados, %d arquivos novos)"
          % (os.path.relpath(alvo, VAULT), kb, len(saida), pulados, baixados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
