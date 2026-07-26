import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _roi  # noqa: E402


def test_start_e_touch_e_export():
    p = {"titulo": "Demo", "slug": "demo", "marca": "smark", "frames": []}
    act = _roi.start(p)
    assert act["started_at"]
    assert act["copy_calls"] == 0
    _roi.touch_copy(p)
    _roi.touch_image(p)
    _roi.touch_image(p)
    assert p["roi"]["active"]["copy_calls"] == 1
    assert p["roi"]["active"]["image_gens"] == 2
    assert p["roi"]["copy_calls_total"] == 1
    assert p["roi"]["image_gens_total"] == 2
    cyc = _roi.close_export(p)
    assert cyc["exported_at"]
    assert cyc["copy_calls"] == 1
    assert cyc["image_gens"] == 2
    assert cyc["minutes"] >= 0
    assert p["roi"]["active"] is None
    assert p["roi"]["exports_total"] == 1
    assert len(p["roi"]["cycles"]) == 1


def test_resumo_posts():
    posts = []
    for i in range(3):
        p = {"titulo": f"P{i}", "slug": f"p-{i}", "marca": "smark", "frames": [{}]}
        _roi.start(p)
        _roi.touch_copy(p)
        c = _roi.close_export(p)
        c["minutes"] = 10 + i  # força minutos para stats
        p["roi"]["cycles"][-1]["minutes"] = 10 + i
        p["roi"]["last_cycle"]["minutes"] = 10 + i
        posts.append(p)
    r = _roi.resumo_posts(posts, limit=20)
    assert r["n"] == 3
    assert r["stats"]["avg_minutes_per_post"]["n"] == 3
    assert r["stats"]["avg_minutes_per_post"]["mean"] == 11.0
    assert r["estimated_hours_saved"] is not None
    # baseline 45: (45*3 - (10+11+12))/60 = (135-33)/60 = 1.7
    assert abs(r["estimated_hours_saved"] - 1.7) < 0.05


def test_start_nao_reinicia_sem_force():
    p = {"titulo": "X", "slug": "x", "frames": []}
    a1 = _roi.start(p)
    t1 = a1["started_at"]
    a2 = _roi.start(p, force=False)
    assert a2["started_at"] == t1
    a3 = _roi.start(p, force=True)
    assert a3["started_at"] >= t1
