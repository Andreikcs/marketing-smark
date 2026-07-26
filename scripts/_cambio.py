#!/usr/bin/env python3
"""Cotação USD→BRL em tempo quase real (cache local).

Fonte: AwesomeAPI (economia.awesomeapi.com.br) — gratuita, sem chave.
Cache em design-system/custos/cambio-cache.json (TTL default 15 min).
Se a rede falhar, usa o último cache; se não houver cache, fallback 5.0.
"""
import datetime
import json
import os
import time
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(VAULT, "design-system", "custos", "cambio-cache.json")
URL = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
TTL_SEG = 15 * 60  # 15 minutos
FALLBACK = 5.0


def _ler_cache():
    if not os.path.isfile(CACHE):
        return None
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _gravar_cache(dados):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _buscar_rede():
    req = urllib.request.Request(URL, headers={"User-Agent": "smark-vault/1.0"})
    bruto = urllib.request.urlopen(req, timeout=8).read().decode("utf-8")
    data = json.loads(bruto)
    # formato: {"USDBRL": {"bid": "5.42", "ask": "5.43", ...}}
    bloco = data.get("USDBRL") or next(iter(data.values()))
    bid = float(bloco.get("bid") or bloco.get("ask"))
    return {
        "usd_brl": bid,
        "ask": float(bloco.get("ask") or bid),
        "bid": bid,
        "fonte": "awesomeapi",
        "create_date": bloco.get("create_date"),
        "buscado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        "ts": time.time(),
    }


def cotacao(forcar=False):
    """Devolve dict: usd_brl, fonte, buscado_em, cache (bool)."""
    c = _ler_cache()
    agora = time.time()
    if not forcar and c and (agora - float(c.get("ts") or 0)) < TTL_SEG and c.get("usd_brl"):
        out = dict(c)
        out["cache"] = True
        return out
    try:
        novo = _buscar_rede()
        _gravar_cache(novo)
        novo["cache"] = False
        return novo
    except Exception:
        if c and c.get("usd_brl"):
            out = dict(c)
            out["cache"] = True
            out["aviso"] = "rede falhou; usando cache"
            return out
        return {
            "usd_brl": FALLBACK,
            "fonte": "fallback",
            "buscado_em": datetime.datetime.now().isoformat(timespec="seconds"),
            "ts": agora,
            "cache": False,
            "aviso": f"sem rede e sem cache; usando {FALLBACK}",
        }


def usd_para_brl(usd, cot=None):
    """Converte valor em USD para BRL com a cotação (ou busca agora)."""
    if usd is None:
        return None
    c = cot or cotacao()
    taxa = float(c.get("usd_brl") or FALLBACK)
    return round(float(usd) * taxa, 4)


def enriquecer(usd):
    """Pacote pronto pra gravar no ledger/UI."""
    c = cotacao()
    taxa = float(c.get("usd_brl") or FALLBACK)
    brl = None if usd is None else round(float(usd) * taxa, 4)
    return {
        "custo_usd": None if usd is None else round(float(usd), 6),
        "custo_brl": brl,
        "usd_brl": taxa,
        "cambio_fonte": c.get("fonte"),
        "cambio_em": c.get("buscado_em"),
        "cambio_cache": bool(c.get("cache")),
    }
