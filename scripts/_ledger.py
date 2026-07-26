#!/usr/bin/env python3
"""Ledger de custos do vault — imagem (OpenRouter/OpenAI) e copy (Claude/chat).

Arquivos (append-only, JSONL):
  design-system/custos/geracoes.jsonl  — cada geração/edição de imagem
  design-system/custos/copys.jsonl     — cada chamada de copy (Estúdio)
  design-system/custos/posts.jsonl     — fechamento de custo por post (opcional)

Nunca derruba a geração: falha de escrita → aviso em stderr e segue.
"""
import datetime
import json
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(VAULT, "design-system", "custos")
LEDGER_IMAGEM = os.path.join(DIR, "geracoes.jsonl")
LEDGER_COPY = os.path.join(DIR, "copys.jsonl")
LEDGER_POSTS = os.path.join(DIR, "posts.jsonl")

try:
    from _cambio import enriquecer, cotacao  # noqa: E402
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _cambio import enriquecer, cotacao  # noqa: E402


def _agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _append(alvo, evento):
    ev = dict(evento)
    ev.setdefault("data", _agora())
    try:
        dirname = os.path.dirname(alvo)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(alvo, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"AVISO: não foi possível gravar no ledger ({e})", file=sys.stderr)
    return alvo


def _com_cambio(evento):
    """Garante custo_brl / usd_brl a partir de custo_usd se faltar."""
    ev = dict(evento)
    usd = ev.get("custo_usd")
    if usd is not None and ev.get("custo_brl") is None:
        pack = enriquecer(usd)
        for k, v in pack.items():
            ev.setdefault(k, v)
    elif usd is not None and ev.get("usd_brl") is None:
        c = cotacao()
        ev["usd_brl"] = float(c.get("usd_brl") or 5.0)
        ev["cambio_fonte"] = c.get("fonte")
        ev["cambio_em"] = c.get("buscado_em")
    return ev


def registrar(evento, path=None):
    """Compat: anexa evento de IMAGEM (como antes)."""
    alvo = path or LEDGER_IMAGEM
    ev = _com_cambio(evento)
    ev.setdefault("tipo_custo", "imagem")
    return _append(alvo, ev)


def registrar_imagem(evento, path=None):
    """Registra geração/edição de imagem (OpenRouter / OpenAI images)."""
    ev = dict(evento)
    ev["tipo_custo"] = "imagem"
    return registrar(ev, path=path or LEDGER_IMAGEM)


def registrar_copy(evento, path=None):
    """Registra chamada de copy (Claude / OpenAI chat no Estúdio)."""
    alvo = path or LEDGER_COPY
    ev = _com_cambio(evento)
    ev["tipo_custo"] = "copy"
    return _append(alvo, ev)


def registrar_post(evento, path=None):
    """Registra consolidado de um post (copy + imagens)."""
    alvo = path or LEDGER_POSTS
    ev = _com_cambio(evento)
    ev["tipo_custo"] = "post"
    # totais em BRL se só USD veio
    if ev.get("total_usd") is not None and ev.get("total_brl") is None:
        pack = enriquecer(ev["total_usd"])
        ev["total_brl"] = pack["custo_brl"]
        ev.setdefault("usd_brl", pack["usd_brl"])
        ev.setdefault("cambio_fonte", pack["cambio_fonte"])
        ev.setdefault("cambio_em", pack["cambio_em"])
    return _append(alvo, ev)


def _ler_jsonl(path):
    if not os.path.isfile(path):
        return []
    out = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def totais_por_post(slug, marca=""):
    """Soma custos de copy + imagem ligados ao slug (e marca se informada).

    Devolve dict com breakdown e totais USD/BRL (cotação ao vivo na hora da consulta).
    """
    slug = (slug or "").strip()
    imgs = [e for e in _ler_jsonl(LEDGER_IMAGEM)
            if e.get("ok", True) and (e.get("slug") == slug or e.get("arquivo", "").startswith(slug))]
    if marca:
        imgs = [e for e in imgs if (e.get("marca") or "") in ("", marca)]
    copys = [e for e in _ler_jsonl(LEDGER_COPY)
             if e.get("ok", True) and e.get("slug") == slug]
    if marca:
        copys = [e for e in copys if (e.get("marca") or "") in ("", marca)]

    img_usd = sum(float(e.get("custo_usd") or 0) for e in imgs)
    copy_usd = sum(float(e.get("custo_usd") or 0) for e in copys)
    total_usd = img_usd + copy_usd
    pack = enriquecer(total_usd)
    return {
        "slug": slug,
        "marca": marca,
        "n_imagens": len(imgs),
        "n_copys": len(copys),
        "imagem_usd": round(img_usd, 6),
        "copy_usd": round(copy_usd, 6),
        "total_usd": round(total_usd, 6),
        "imagem_brl": enriquecer(img_usd)["custo_brl"],
        "copy_brl": enriquecer(copy_usd)["custo_brl"],
        "total_brl": pack["custo_brl"],
        "usd_brl": pack["usd_brl"],
        "cambio_fonte": pack["cambio_fonte"],
        "cambio_em": pack["cambio_em"],
        "imagens": imgs,
        "copys": copys,
    }


def resumo_periodo(prefixo_data=""):
    """Totais globais (opcional filtro de data 'YYYY-MM')."""
    def ok_data(e):
        if not prefixo_data:
            return True
        return str(e.get("data") or "").startswith(prefixo_data)

    imgs = [e for e in _ler_jsonl(LEDGER_IMAGEM) if e.get("ok", True) and ok_data(e)]
    copys = [e for e in _ler_jsonl(LEDGER_COPY) if e.get("ok", True) and ok_data(e)]
    img_usd = sum(float(e.get("custo_usd") or 0) for e in imgs)
    copy_usd = sum(float(e.get("custo_usd") or 0) for e in copys)
    total = img_usd + copy_usd
    pack = enriquecer(total)
    return {
        "periodo": prefixo_data or "tudo",
        "n_imagens": len(imgs),
        "n_copys": len(copys),
        "imagem_usd": round(img_usd, 6),
        "copy_usd": round(copy_usd, 6),
        "total_usd": round(total, 6),
        "imagem_brl": enriquecer(img_usd)["custo_brl"],
        "copy_brl": enriquecer(copy_usd)["custo_brl"],
        "total_brl": pack["custo_brl"],
        "usd_brl": pack["usd_brl"],
        "cambio_fonte": pack["cambio_fonte"],
        "cambio_em": pack["cambio_em"],
    }
