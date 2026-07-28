#!/usr/bin/env python3
"""ROI humano — tempo e contadores por post no editor.

Ciclo = do primeiro trabalho real (copy/imagem) até o export PNG.
Não conta “aba aberta” nem foco passivo.

  "roi": {
    "active": { started_at, last_activity_at, copy_calls, image_gens } | null,
    "cycles": [ { started_at, exported_at, minutes, copy_calls, image_gens } ],
    "copy_calls_total", "image_gens_total", "exports_total"
  }
"""
import datetime
from statistics import mean, median

# teto de um ciclo (evita 26h se algo ficar preso)
MAX_CICLO_MIN = 180.0
# se ativo sem atividade há mais que isso → descarta (minutos)
STALE_IDLE_MIN = 45.0


def _agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _parse(iso):
    if not iso:
        return None
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", ""))
    except Exception:
        return None


def ensure(post):
    """Garante estrutura roi no post (mutável)."""
    r = post.get("roi")
    if not isinstance(r, dict):
        r = {}
        post["roi"] = r
    r.setdefault("active", None)
    r.setdefault("cycles", [])
    r.setdefault("copy_calls_total", 0)
    r.setdefault("image_gens_total", 0)
    r.setdefault("exports_total", 0)
    # limpa ciclos absurdos e ativos stale
    _sanitizar(r)
    return r


def _sanitizar(r):
    """Remove ciclos com minutos absurdos e fecha ativos ociosos."""
    cycles = []
    for c in (r.get("cycles") or []):
        try:
            m = float(c.get("minutes") or 0)
        except (TypeError, ValueError):
            m = 0
        if m > MAX_CICLO_MIN:
            c = dict(c)
            c["minutes"] = MAX_CICLO_MIN
            c["capped"] = True
        if m >= 0:
            cycles.append(c)
    r["cycles"] = cycles[-50:]

    act = r.get("active")
    if not isinstance(act, dict) or not act.get("started_at"):
        r["active"] = None
        return
    last = _parse(act.get("last_activity_at") or act.get("started_at"))
    if not last:
        r["active"] = None
        return
    idle = (datetime.datetime.now() - last).total_seconds() / 60.0
    # ocioso sem trabalho real → descarta
    work = int(act.get("copy_calls") or 0) + int(act.get("image_gens") or 0)
    if idle > STALE_IDLE_MIN and work == 0:
        r["active"] = None
        return
    # ocioso há muito com trabalho → fecha como ciclo (usa last_activity)
    if idle > STALE_IDLE_MIN and work > 0:
        _fechar_ativo(r, act, exported=False)
        return


def _fechar_ativo(r, act, exported=True):
    t0 = _parse(act.get("started_at"))
    t1 = _parse(act.get("last_activity_at") or act.get("started_at")) or datetime.datetime.now()
    if t0 and t1 < t0:
        t1 = t0
    minutes = 0.0
    if t0:
        minutes = max(0.0, (t1 - t0).total_seconds() / 60.0)
    minutes = min(minutes, MAX_CICLO_MIN)
    cycle = {
        "started_at": act.get("started_at"),
        "exported_at": _agora() if exported else (act.get("last_activity_at") or _agora()),
        "minutes": round(minutes, 2),
        "copy_calls": int(act.get("copy_calls") or 0),
        "image_gens": int(act.get("image_gens") or 0),
        "auto_closed": not exported,
    }
    cycles = list(r.get("cycles") or [])
    cycles.append(cycle)
    r["cycles"] = cycles[-50:]
    if exported:
        r["exports_total"] = int(r.get("exports_total") or 0) + 1
        r["last_cycle"] = cycle
    r["active"] = None
    return cycle


def start(post, force=False):
    """Abre ciclo ativo só com trabalho real — preferir touch_copy/touch_image.

    force=True reinicia. Sem force, se já há ativo, só renova last_activity.
    """
    r = ensure(post)
    now = _agora()
    if force or not r.get("active"):
        r["active"] = {
            "started_at": now,
            "last_activity_at": now,
            "copy_calls": 0,
            "image_gens": 0,
        }
    else:
        act = r["active"]
        act["last_activity_at"] = now
        r["active"] = act
    return r["active"]


def touch_copy(post):
    """+1 copy no ciclo ativo (abre ciclo se preciso)."""
    r = ensure(post)
    act = r.get("active")
    if not act:
        act = start(post)
    else:
        act["last_activity_at"] = _agora()
    act["copy_calls"] = int(act.get("copy_calls") or 0) + 1
    r["copy_calls_total"] = int(r.get("copy_calls_total") or 0) + 1
    r["active"] = act
    return act


def touch_image(post):
    """+1 imagem no ciclo ativo (abre ciclo se preciso)."""
    r = ensure(post)
    act = r.get("active")
    if not act:
        act = start(post)
    else:
        act["last_activity_at"] = _agora()
    act["image_gens"] = int(act.get("image_gens") or 0) + 1
    r["image_gens_total"] = int(r.get("image_gens_total") or 0) + 1
    r["active"] = act
    return act


def close_export(post):
    """Fecha ciclo ativo no export. Devolve o ciclo fechado ou None."""
    r = ensure(post)
    act = r.get("active")
    if not act or not act.get("started_at"):
        # export sem trabalho prévio: ciclo mínimo
        return {
            "started_at": _agora(),
            "exported_at": _agora(),
            "minutes": 0.0,
            "copy_calls": 0,
            "image_gens": 0,
        }
    act["last_activity_at"] = _agora()
    return _fechar_ativo(r, act, exported=True)


def minutos_medios(post):
    """Média de minutes dos ciclos fechados; None se vazio."""
    r = ensure(post) if isinstance(post, dict) else {}
    cycles = r.get("cycles") or []
    vals = [float(c.get("minutes") or 0) for c in cycles if c.get("exported_at") or c.get("minutes") is not None]
    vals = [v for v in vals if 0 <= v <= MAX_CICLO_MIN]
    if not vals:
        return None
    return round(mean(vals), 2)


def _ativo_span_min(act):
    """Minutos do ciclo ativo = started → last_activity (NÃO até agora)."""
    if not act or not act.get("started_at"):
        return 0.0
    t0 = _parse(act.get("started_at"))
    t1 = _parse(act.get("last_activity_at") or act.get("started_at"))
    if not t0 or not t1:
        return 0.0
    if t1 < t0:
        t1 = t0
    m = (t1 - t0).total_seconds() / 60.0
    return min(max(0.0, m), MAX_CICLO_MIN)


def minutos_totais(post):
    """Soma de minutos dos ciclos fechados + trecho ativo (até última atividade)."""
    r = ensure(post) if isinstance(post, dict) else {}
    total = 0.0
    for c in (r.get("cycles") or []):
        try:
            m = float(c.get("minutes") or 0)
        except (TypeError, ValueError):
            m = 0
        total += min(max(0.0, m), MAX_CICLO_MIN)
    act = r.get("active") or {}
    work = int(act.get("copy_calls") or 0) + int(act.get("image_gens") or 0)
    if work > 0:
        total += _ativo_span_min(act)
    return round(total, 2)


def ativo_minutos(post):
    """Minutos do ciclo ativo (até última atividade), ou None."""
    r = ensure(post) if isinstance(post, dict) else {}
    act = r.get("active") or {}
    if not act.get("started_at"):
        return None
    work = int(act.get("copy_calls") or 0) + int(act.get("image_gens") or 0)
    if work == 0:
        return None  # foco sem trabalho não conta
    return round(_ativo_span_min(act), 2)


def resumo_posts(posts, limit=50, totais_fn=None):
    """Lista posts com ROI + COGS — do mais recente ao mais antigo."""
    items = []
    indexed = list(enumerate(posts or []))
    indexed.reverse()
    for i, p in indexed[: max(1, int(limit or 50))]:
        r = ensure(p) if isinstance(p, dict) else {}
        cycles = r.get("cycles") or []
        last = r.get("last_cycle") or (cycles[-1] if cycles else None)
        avg_m = minutos_medios(p)
        tot_m = minutos_totais(p)
        row = {
            "idx": i,
            "titulo": p.get("titulo") or p.get("slug") or f"post-{i}",
            "slug": p.get("slug") or "",
            "marca": p.get("marca") or "smark",
            "status": p.get("status") or "rascunho",
            "n_frames": len(p.get("frames") or []),
            "created_at": p.get("created_at") or "",
            "updated_at": p.get("updated_at") or "",
            "copy_calls_total": int(r.get("copy_calls_total") or 0),
            "image_gens_total": int(r.get("image_gens_total") or 0),
            "exports_total": int(r.get("exports_total") or 0),
            "cycles_n": len(cycles),
            "avg_minutes": avg_m,
            "total_minutes": tot_m,
            "active_minutes": ativo_minutos(p),
            "last_minutes": (last or {}).get("minutes"),
            "last_exported_at": (last or {}).get("exported_at"),
            "active": bool(r.get("active") and (
                int((r.get("active") or {}).get("copy_calls") or 0)
                + int((r.get("active") or {}).get("image_gens") or 0)
            ) > 0),
            "imagem_usd": None,
            "copy_usd": None,
            "total_usd": None,
            "total_brl": None,
            "usd_brl": None,
        }
        if totais_fn and row["slug"]:
            try:
                t = totais_fn(row["slug"], row["marca"])
                row["imagem_usd"] = t.get("imagem_usd")
                row["copy_usd"] = t.get("copy_usd")
                row["total_usd"] = t.get("total_usd")
                row["total_brl"] = t.get("total_brl")
                row["usd_brl"] = t.get("usd_brl")
            except Exception:
                pass
        items.append(row)

    mins = [x["avg_minutes"] for x in items if x["avg_minutes"] is not None]
    lasts = [x["last_minutes"] for x in items if x["last_minutes"] is not None]
    costs = [x["total_usd"] for x in items if x["total_usd"] is not None]
    costs_brl = [x["total_brl"] for x in items if x["total_brl"] is not None]

    def _stat(vals):
        if not vals:
            return {"n": 0, "mean": None, "median": None, "sum": None}
        return {
            "n": len(vals),
            "mean": round(mean(vals), 3),
            "median": round(median(vals), 3),
            "sum": round(sum(vals), 4),
        }

    return {
        "posts": items,
        "n": len(items),
        "stats": {
            "avg_minutes_per_post": _stat(mins),
            "last_cycle_minutes": _stat(lasts),
            "cogs_usd": _stat(costs),
            "cogs_brl": _stat(costs_brl),
        },
        "baseline_minutes": 45.0,
        "estimated_hours_saved": (
            round((45.0 * len(mins) - sum(mins)) / 60.0, 2) if mins else None
        ),
    }
