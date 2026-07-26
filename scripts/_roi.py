#!/usr/bin/env python3
"""ROI humano v1 — tempo e contadores por post no editor.

Cada post em editor.json pode ter:

  "roi": {
    "active": { "started_at", "copy_calls", "image_gens" } | null,
    "cycles": [ { started_at, exported_at, minutes, copy_calls, image_gens } ],
    "copy_calls_total": int,
    "image_gens_total": int,
    "exports_total": int
  }

Ciclo = do primeiro trabalho (copy/imagem/início manual) até o export PNG.
"""
import datetime
from statistics import mean, median


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
    return r


def start(post, force=False):
    """Abre ciclo ativo se não houver. force=True reinicia ciclo."""
    r = ensure(post)
    if force or not r.get("active"):
        r["active"] = {
            "started_at": _agora(),
            "copy_calls": 0,
            "image_gens": 0,
        }
    return r["active"]


def touch_copy(post):
    """+1 copy no ciclo ativo (abre ciclo se preciso)."""
    r = ensure(post)
    act = r.get("active") or start(post)
    act["copy_calls"] = int(act.get("copy_calls") or 0) + 1
    r["copy_calls_total"] = int(r.get("copy_calls_total") or 0) + 1
    r["active"] = act
    return act


def touch_image(post):
    """+1 imagem no ciclo ativo (abre ciclo se preciso)."""
    r = ensure(post)
    act = r.get("active") or start(post)
    act["image_gens"] = int(act.get("image_gens") or 0) + 1
    r["image_gens_total"] = int(r.get("image_gens_total") or 0) + 1
    r["active"] = act
    return act


def close_export(post):
    """Fecha ciclo ativo no export. Devolve o ciclo fechado ou None."""
    r = ensure(post)
    act = r.get("active")
    if not act or not act.get("started_at"):
        # export sem start: ciclo mínimo de 0 min
        act = {"started_at": _agora(), "copy_calls": 0, "image_gens": 0}
    end = _agora()
    t0 = _parse(act.get("started_at"))
    t1 = _parse(end)
    minutes = 0.0
    if t0 and t1:
        minutes = max(0.0, round((t1 - t0).total_seconds() / 60.0, 2))
    cycle = {
        "started_at": act.get("started_at"),
        "exported_at": end,
        "minutes": minutes,
        "copy_calls": int(act.get("copy_calls") or 0),
        "image_gens": int(act.get("image_gens") or 0),
    }
    cycles = list(r.get("cycles") or [])
    cycles.append(cycle)
    # mantém últimos 50 ciclos por post
    r["cycles"] = cycles[-50:]
    r["exports_total"] = int(r.get("exports_total") or 0) + 1
    r["active"] = None  # pronto para novo ciclo
    r["last_cycle"] = cycle
    return cycle


def minutos_medios(post):
    """Média de minutes dos ciclos fechados; None se vazio."""
    cycles = (post.get("roi") or {}).get("cycles") or []
    vals = [float(c.get("minutes") or 0) for c in cycles if c.get("exported_at")]
    if not vals:
        return None
    return round(mean(vals), 2)


def resumo_posts(posts, limit=20, totais_fn=None):
    """Lista os últimos `limit` posts com ROI + COGS opcional.

    `totais_fn(slug, marca) -> dict` se fornecido (ex. _ledger.totais_por_post).
    """
    items = []
    # mais recentes: invert order (editor costuma ter novos no topo = índice alto ou baixo?)
    # Usa ordem atual da lista; pega os primeiros `limit` que tenham algum sinal de ROI ou todos
    ordered = list(posts or [])
    # preferir posts com cycles ou activity; senão os primeiros N
    for i, p in enumerate(ordered):
        if len(items) >= limit:
            break
        r = p.get("roi") if isinstance(p.get("roi"), dict) else {}
        cycles = r.get("cycles") or []
        last = r.get("last_cycle") or (cycles[-1] if cycles else None)
        avg_m = minutos_medios(p)
        row = {
            "idx": i,
            "titulo": p.get("titulo") or p.get("slug") or f"post-{i}",
            "slug": p.get("slug") or "",
            "marca": p.get("marca") or "smark",
            "status": p.get("status") or "",
            "n_frames": len(p.get("frames") or []),
            "copy_calls_total": int(r.get("copy_calls_total") or 0),
            "image_gens_total": int(r.get("image_gens_total") or 0),
            "exports_total": int(r.get("exports_total") or 0),
            "cycles_n": len(cycles),
            "avg_minutes": avg_m,
            "last_minutes": (last or {}).get("minutes"),
            "last_exported_at": (last or {}).get("exported_at"),
            "active": bool(r.get("active")),
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

    # agregados
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
        # proxy ROI vs baseline 45 min (documentado no dossiê; ajustável)
        "baseline_minutes": 45.0,
        "estimated_hours_saved": (
            round((45.0 * len(mins) - sum(mins)) / 60.0, 2) if mins else None
        ),
    }
