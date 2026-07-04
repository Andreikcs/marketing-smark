#!/usr/bin/env python3
"""QUALITY GATE — revisa um post (nota .md) contra a linha vermelha do grupo, antes de aprovar.
Lê palavras-proibidas de shared/voz-grupo.md + adicionais do brand-voice da marca. Saída ✅/⚠️/❌.

Uso:
  python3 scripts/revisar.py marcas/<marca>/publicacoes/social/instagram/2026-XX-XX-slug.md
  python3 scripts/revisar.py --texto "legenda..." --marca provider-max   (ad-hoc)
"""
import argparse
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCAS = {"smark", "provider-max", "elever-ai"}


def frontmatter(txt):
    fm = {}
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def secao(txt, nome):
    m = re.search(rf"^##\s*{nome}\s*\n(.*?)(?=^##\s|\Z)", txt, re.S | re.M | re.I)
    return m.group(1).strip() if m else ""


def proibidas_de(path):
    """Extrai os termos entre aspas listados sob '## Palavras-proibidas'."""
    if not os.path.exists(path):
        return []
    bloco = secao(open(path, encoding="utf-8").read(), "Palavras-proibidas")
    return [t.lower() for t in re.findall(r'"([^"]+)"', bloco) if "métric" not in t.lower()]


def jargao_de(path):
    """Termos da seção '## Jargão técnico' (entre aspas, antes do Tradutor) — sinal ⚠️, não bloqueio."""
    if not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"^##\s*Jargão.*?\n(.*?)(?=^##\s|\Z)", txt, re.S | re.M)
    if not m:
        return []
    bloco = m.group(1).split("Tradutor")[0]  # só a lista de termos, não a tabela do tradutor
    return [t.lower() for t in re.findall(r'"([^"]+)"', bloco) if "métric" not in t.lower()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post", nargs="?", help="caminho da nota .md do post")
    ap.add_argument("--texto", default="")
    ap.add_argument("--marca", default="")
    a = ap.parse_args()

    if a.post:
        p = a.post if os.path.isabs(a.post) else os.path.join(VAULT, a.post)
        txt = open(p, encoding="utf-8").read()
        fm = frontmatter(txt)
        marca = fm.get("marca", "")
        legenda = "\n".join(s for s in (secao(txt, "Legenda"), secao(txt, "Legenda Instagram"),
                                        secao(txt, "Legenda LinkedIn")) if s)
        if not legenda:  # fallback: corpo sem frontmatter (evita contar hashtags 2x)
            legenda = re.sub(r"^---.*?---", "", txt, flags=re.S)
        hashtags = secao(txt, "Hashtags")
        alt = fm.get("alt", "")
        endossa = marca in {"provider-max", "elever-ai"}
    else:
        marca, legenda, hashtags, alt, fm = a.marca, a.texto, a.texto, "", {}
        endossa = marca in {"provider-max", "elever-ai"}

    base = legenda + "\n" + hashtags
    low = base.lower()

    proib = set(proibidas_de(os.path.join(VAULT, "shared", "voz-grupo.md")))
    if marca:
        proib |= set(proibidas_de(os.path.join(VAULT, "marcas", marca, "branding", "brand-voice.md")))

    erros, avisos, oks = [], [], []

    # marca válida
    (oks if marca in MARCAS else erros).append(
        f"marca '{marca or '—'}' " + ("válida" if marca in MARCAS else "INVÁLIDA (use smark/provider-max/elever-ai)"))

    # palavras-proibidas
    achou = sorted({w for w in proib if re.search(r"\b" + re.escape(w) + r"\b", low)})
    (erros.append(f"palavra-proibida: {', '.join(achou)}") if achou else oks.append("sem palavras-proibidas"))

    # promessa absoluta
    abs_pat = r"(100%|garantid|zero (churn|erro|falha)|nunca (erra|falha)|sempre funciona|resolve tudo|elimina(r)? (100|tod[oa]))"
    m = re.search(abs_pat, low)
    (erros.append(f"promessa absoluta: \"{m.group(0)}\"") if m else oks.append("sem promessa absoluta"))

    # promessa de venda/faturamento (brief 2026-06-23: vender função/custo, nunca resultado comercial)
    venda_pat = (r"(vende[r]? mais|mais vendas|aumenta\w* (as |suas |o |seu )?(vendas|faturamento)|"
                 r"dobr\w+ (as |o )?(vendas|faturamento)|gera\w* (mais )?vendas|"
                 r"garant\w+[^.]{0,20}vend|fatur\w+ mais|mais faturamento)")
    mv2 = re.search(venda_pat, low)
    (erros.append(f"promessa de venda/faturamento: \"{mv2.group(0).strip()}\"") if mv2
     else oks.append("não promete venda/faturamento"))

    # jargão técnico na vitrine (sinal, não bloqueio) — whitelist do selo e da exceção da mãe
    jarg = jargao_de(os.path.join(VAULT, "shared", "voz-grupo.md"))
    low_j = low.replace("uma plataforma smark", " ").replace("plataforma smark", " ")
    if marca == "smark":
        low_j = low_j.replace("assessoria tecnológica", " ")
    achou_j = sorted({w for w in jarg if re.search(r"\b" + re.escape(w) + r"\b", low_j)})
    (avisos.append(f"jargão técnico (traduzir p/ vitrine — ver tradutor DE→PARA): {', '.join(achou_j)}")
     if achou_j else oks.append("sem jargão técnico"))

    # métrica de vaidade (soft)
    mv = re.search(r"(\+?\s?\d+\s?(mil|mi|bi|milh|bilh)|\d{3,}%)", low)
    (avisos.append(f"possível métrica de vaidade: \"{mv.group(0).strip()}\" (tem fonte/contexto?)") if mv
     else oks.append("sem métrica de vaidade óbvia"))

    # CTA
    cta = re.search(r"(→|diagn[óo]stico|comenta|chama no direct|fala com|arrasta|quero|link na bio|agendar)", low)
    (oks.append("tem CTA") if cta else avisos.append("sem CTA claro (→ / comenta / diagnóstico…)"))

    # hashtags 3-8
    n = len(re.findall(r"#\w+", base))
    if n == 0:
        avisos.append("sem hashtags")
    elif 3 <= n <= 8:
        oks.append(f"hashtags ok ({n})")
    else:
        avisos.append(f"hashtags fora de 3–8 (tem {n})")

    # endosso de produto
    if endossa:
        (oks.append("traz selo 'uma plataforma smark'") if "uma plataforma smark" in low
         else avisos.append("produto sem 'uma plataforma smark' na legenda"))

    # alt-text
    (oks.append("tem alt-text") if alt else avisos.append("sem alt-text (acessibilidade/SEO)"))

    # tamanho (3 linhas de IG ~ não exagerar; aqui: legenda muito curta?)
    if len(legenda.split()) < 12:
        avisos.append("legenda muito curta (<12 palavras)")

    print(f"\n=== QUALITY GATE · {a.post or '(ad-hoc)'} · marca={marca or '—'} ===")
    for o in oks:
        print(f"  ✅ {o}")
    for w in avisos:
        print(f"  ⚠️  {w}")
    for e in erros:
        print(f"  ❌ {e}")
    veredito = "REPROVADO" if erros else ("REVISAR" if avisos else "APROVADO")
    print(f"\n  → {veredito}  ({len(erros)} erro(s), {len(avisos)} aviso(s))\n")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
