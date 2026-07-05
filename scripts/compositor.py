#!/usr/bin/env python3
"""
COMPOSITOR — motor de arte do Grupo Smark.
Fundo (imagem IA) + tipografia real + MOLDURA + auto-fit + scrim, render Chrome 2x.
Suporta --tema escuro|claro. Lê cores/handles do tokens.json (fonte única).

Uso:
  python3 scripts/compositor.py --marca elever-ai --out arte/x.png --bg fundo.png \
    --headline "LINHA 1\n*ACENTO*" --sub "..." [--tema claro] [--cta "..."] [--page "01/05"] [--no-chip]
"""
import argparse
import base64
import html as htmlmod
import json
import os
import re
import subprocess
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sidecar import meta_block  # noqa: E402
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TOKENS = os.path.join(VAULT, "design-system", "tokens", "tokens.json")
SMARK_TAGLINE = "TECNOLOGIA QUE DEIXA MARCOS"
LIME = ("#C6F24E", "#D6FF5C")
MESH_ESCURO = ("radial-gradient(60% 50% at 28% 16%, #2e2658 0%, transparent 60%),"
               "radial-gradient(55% 48% at 84% 66%, #3a2870 0%, transparent 62%),"
               "linear-gradient(160deg, #17131f 0%, #0B0B0B 72%)")
MESH_CLARO = ("radial-gradient(60% 50% at 72% 16%, #e7dcff 0%, transparent 60%),"
              "radial-gradient(55% 48% at 16% 84%, #efeaf8 0%, transparent 62%),"
              "linear-gradient(160deg, #f6f3fc 0%, #F4F2FB 72%)")
# Grão de filme (ruído fractal SVG, dessaturado) — camada da "grade" de acabamento
GRAIN = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E"
         "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2' "
         "stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E"
         "%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")")


def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def readable_on(accent, base, target=4.0):
    """Escurece o acento (preservando o tom) até ter contraste suficiente sobre 'base'."""
    arg = _hex2rgb(accent)
    bl = _lum(_hex2rgb(base))

    def contrast(rgb):
        l = _lum(rgb)
        hi, lo = max(l, bl), min(l, bl)
        return (hi + 0.05) / (lo + 0.05)

    rgb, f = arg, 1.0
    while contrast(rgb) < target and f > 0.06:
        f -= 0.04
        rgb = tuple(int(c * f) for c in arg)
    return "#%02X%02X%02X" % rgb


def load_brands():
    with open(TOKENS, "r", encoding="utf-8") as f:
        t = json.load(f)
    fund = dict(t["fundacao"])
    fund["_claro"] = t.get("tema_claro", {})
    brands = {}
    for slug, m in t["marcas"].items():
        brands[slug] = {
            "name": m["nome"], "accent": m["acento"], "bright": m.get("acento_claro", m["acento"]),
            "glyph": m.get("logo_glyph", "•"), "handle": m.get("handle", "@" + slug),
            "endossa": m.get("endossa", False),
            "logo_path": m.get("logo_path", ""), "logo_svg": m.get("logo_svg", ""),
            "wordmark": m.get("wordmark", ""), "gradiente": m.get("gradiente", ""),
            "tab": (m["wordmark"].split("*")[0].split()[0].upper() if m.get("wordmark")
                    else m["nome"].split()[0].replace(".", "").upper()),
        }
    return brands, fund


def esc(s):
    return htmlmod.escape(s)


def glyph_html(b, color, px):
    """Símbolo da marca: logo_svg (markup multi-elemento, usa currentColor) > logo_path (path único) > letra."""
    if b.get("logo_svg"):
        return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" style="color:{color}">'
                f'{b["logo_svg"]}</svg>')
    if b.get("logo_path"):
        return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}">'
                f'<path fill-rule="evenodd" fill="{color}" d="{b["logo_path"]}"/></svg>')
    return esc(b["glyph"])


def wordmark_html(b):
    """Assinatura do chip. `*x*` no wordmark vira acento (ex: Elever *AI*); '.' final vira ponto-acento (smark.)."""
    wm = b.get("wordmark")
    if not wm:
        return esc(b["handle"])
    if "*" in wm:
        parts = wm.split("*")
        return "".join(f'<span class="dot">{esc(p)}</span>' if i % 2 else esc(p) for i, p in enumerate(parts))
    if wm.endswith("."):
        return f'{esc(wm[:-1])}<span class="dot">.</span>'
    return esc(wm)


def render_headline(text):
    out = []
    for line in text.split("\\n"):
        parts = line.split("*")
        buf = "".join(f'<span class="v">{esc(p)}</span>' if i % 2 else esc(p) for i, p in enumerate(parts))
        out.append(buf)
    return "<br>".join(out)


def render_rich(text):
    """Formatação: '|' ou '\\n' = quebra · **negrito** · _itálico_ · *acento* · {#hex|texto} = cor livre."""
    lines = []
    for line in (text or "").replace("|", "\\n").split("\\n"):
        s = esc(line)
        # cor {#hex:texto} — resolve de dentro pra fora (tolera aninhamento) e limpa artefatos
        for _ in range(12):
            new = re.sub(r"\{(#[0-9a-fA-F]{3,6}):([^{}]*)\}", r'<span style="color:\1">\2</span>', s)
            if new == s:
                break
            s = new
        s = s.replace("{", "").replace("}", "")
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"_(.+?)_", r"<i>\1</i>", s)
        s = re.sub(r"\*(.+?)\*", r'<span class="v">\1</span>', s)
        lines.append(s)
    return "<br>".join(lines)


# Degradê claro da marca (fundo instantâneo, sem IA) — off-white → lavanda → roxo suave
DEGRADE_CLARO = "linear-gradient(155deg,#F4F2FB 0%,#EFE6FF 42%,#D9C2FF 78%,#C6A8FF 100%)"


def tab_font(label):
    """Fonte do nome vertical da etiqueta — auto-ajusta pra todos caberem na MESMA altura, centrados."""
    n = max(len(label), 1)
    return int(max(13, min(18, 130 / (n * 1.05))))


def auto_hsize(text):
    plain = [ln.replace("*", "") for ln in text.split("\\n")]
    longest = max((len(ln) for ln in plain), default=1)
    n = max(len(plain), 1)
    return int(max(54, min((1080 - 128) / (longest * 0.52), 360 / (n * 0.92), 104)))


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@500;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{width:%(W)spx;height:%(H)spx;overflow:hidden;}
.card{position:relative;width:%(W)spx;height:%(H)spx;background:%(BASE)s;}
.bg{position:absolute;inset:0;background-image:%(BG)s;background-size:cover;background-position:%(POSX)s%% %(POSY)s%%;transform:scale(%(ZOOM)s);transform-origin:%(POSX)s%% %(POSY)s%%;filter:brightness(%(BRI)s) contrast(%(CON)s) saturate(%(SAT)s);}
.ovx{position:absolute;inset:0;background:%(OVX)s;opacity:%(OVXO)s;}
.grade{position:absolute;inset:0;}
.grade i{position:absolute;inset:0;display:block;}
.grade .gt{background:%(GTINT)s;mix-blend-mode:soft-light;opacity:%(GTO)s;}
.grade .gv{background:%(GVIG)s;}
.grade .gg{background-image:%(GRAIN)s;background-size:180px 180px;mix-blend-mode:overlay;opacity:%(GGO)s;}
.ov{position:absolute;inset:0;background:%(OV)s;}
.tab{position:absolute;top:0;left:60px;width:72px;height:224px;background:%(SQUARE)s;border-radius:0 0 20px 20px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;z-index:2;}
.tab .ic{color:%(ONACC)s;display:flex;align-items:center;justify-content:center;}
.tab .vt{writing-mode:vertical-rl;transform:rotate(180deg);color:%(ONACC)s;font-family:'Archivo';font-weight:800;font-size:%(TABF)spx;letter-spacing:2px;}
.ct{position:absolute;left:64px;right:64px;top:50%%;bottom:132px;display:flex;flex-direction:column;justify-content:center;z-index:1;}
.chip{display:flex;align-items:center;gap:16px;margin-bottom:26px;}
.chip .av{width:64px;height:64px;border-radius:16px;background:%(SQUARE)s;color:%(ONACC)s;font-family:'Archivo';font-weight:800;font-size:40px;display:flex;align-items:center;justify-content:center;}
.chip .hd{color:%(TXT)s;font-family:'Archivo';font-weight:800;font-size:36px;letter-spacing:-1px;}
.chip .hd .dot{color:%(DOT)s;}
.chip .ck{width:32px;height:32px;border-radius:50%%;background:%(SQUARE)s;color:%(ONACC)s;font-size:19px;font-weight:800;display:flex;align-items:center;justify-content:center;}
.h{font-family:'Anton','Arial Narrow',Impact,sans-serif;text-transform:uppercase;color:%(TXT)s;font-size:%(HSIZE)spx;line-height:%(LH)s;letter-spacing:1px;text-shadow:%(HSHADOW)s;}
.v{%(VSTYLE)s}
.h b,.sub b{font-weight:800;}
.h i,.sub i{font-style:italic;}
.sub{font-family:'Archivo';font-weight:500;color:%(SUBC)s;font-size:33px;line-height:1.32;margin-top:28px;max-width:90%%;}
.footer{position:absolute;bottom:46px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center;font-family:'Archivo';font-size:23px;color:%(FOOTTXT)s;letter-spacing:1px;border-top:1px solid %(FOOTBORDER)s;padding-top:20px;z-index:1;}
.footer div{font-weight:400;}
.footer .cred{color:%(FOOTCRED)s;font-weight:400;letter-spacing:.5px;font-size:20px;}
.cta{display:inline-block;margin-top:30px;background:%(SQUARE)s;color:%(ONACC)s;font-family:'Archivo';font-weight:800;font-size:32px;letter-spacing:.5px;text-transform:uppercase;padding:18px 32px;border-radius:16px;}
.page{position:absolute;top:42px;right:48px;font-family:'Archivo';font-weight:500;font-size:21px;color:%(PAGETXT)s;background:%(PAGEBG)s;border:1px solid %(PAGEBORDER)s;border-radius:999px;padding:7px 16px;z-index:2;}
"""

PAGE = "<!doctype html><html><head><meta charset='utf-8'><style>%(CSS)s</style></head><body>%(BODY)s</body></html>"


def _ovx_bg(overlay, ang, pos):
    if overlay == "branco":
        return f"linear-gradient({ang}deg, rgba(255,255,255,0) {pos}%, rgba(255,255,255,1) 100%)"
    if overlay == "roxo":
        return f"linear-gradient({ang}deg, rgba(138,60,247,0) {pos}%, rgba(74,30,150,.96) 100%)"
    if overlay == "todo-branco":
        return "#FFFFFF"
    if overlay == "todo-roxo":
        return "#8A3CF7"
    return "none"


def compose_html(marca, headline, sub="", cta="", page="", no_chip=False, tema="claro",
                 size="1080x1350", hsize=0, accent="", bright="", base="", square="",
                 bg="", bg_url="", placeholder=False, no_grade=False,
                 zoom=1.0, posx=50, posy=50, overlay="none", overlay_op=0.85,
                 ov_ang=180, ov_pos=20, brilho=1.0, contraste=1.0, satur=1.0,
                 handle_over="", rodape_over="", raw=False):
    """Constrói o HTML completo do frame (mesmo motor do PNG final).
    `bg` = caminho de imagem (embutida em base64, p/ render headless).
    `bg_url` = URL direta (ex.: rota estática do servidor, p/ preview leve no navegador)."""
    brands, fund = load_brands()
    if marca not in brands:
        raise ValueError(f"marca '{marca}' não está no tokens.json")
    b = dict(brands[marca])
    if accent:
        b["accent"] = accent
        b["bright"] = bright or accent
    elif bright:
        b["bright"] = bright

    w, h = (int(x) for x in size.lower().split("x"))
    accent_c, bright_c = b["accent"], b["bright"]
    on_acc = "#0B0B0B" if accent_c.upper() in [c.upper() for c in LIME] else "#FFFFFF"
    square = square or b.get("gradiente") or accent_c
    rodape = rodape_over or fund.get("rodape", "@copywriting2026")
    handle = handle_over or b["handle"]

    if tema == "claro":
        cl = fund.get("_claro", {})
        base_c = base or cl.get("base", "#F4F2FB")
        txt = cl.get("texto", "#100D1C")
        base_hex = base_c if (base_c.startswith("#") and len(base_c) in (4, 7)) else cl.get("base", "#F4F2FB")
        acc_txt = readable_on(accent_c, base_hex)
        T = {"BASE": base_c, "TXT": txt, "SUBC": cl.get("sub", "#4A4560"), "LH": ".98",
             "OV": "linear-gradient(180deg, rgba(244,242,251,.30) 0%%, rgba(244,242,251,0) 28%%, rgba(244,242,251,.5) 52%%, rgba(244,242,251,.93) 78%%, rgba(244,242,251,1) 100%%)",
             "HSHADOW": "none", "VSTYLE": f"color:{acc_txt};", "DOT": acc_txt,
             "FOOTTXT": cl.get("apoio", "#6B6680"), "FOOTBORDER": "rgba(0,0,0,.14)", "FOOTCRED": "#8B8698",
             "PAGETXT": txt, "PAGEBG": "rgba(255,255,255,.6)", "PAGEBORDER": "rgba(0,0,0,.14)",
             "GTINT": "#8B3CF7", "GTO": ".07",
             "GVIG": "radial-gradient(150% 130% at 50% 30%, transparent 60%, rgba(40,28,168,.10) 100%)", "GGO": ".05"}
    else:
        base_c = base or fund.get("base", "#0B0B0B")
        T = {"BASE": base_c, "TXT": "#FFFFFF", "SUBC": "#DCDCDC", "LH": ".96",
             "OV": "linear-gradient(180deg, rgba(11,11,11,.5) 0%%, rgba(11,11,11,0) 30%%, rgba(11,11,11,.42) 50%%, rgba(11,11,11,.9) 76%%, rgba(11,11,11,.99) 100%%)",
             "HSHADOW": "0 6px 34px rgba(0,0,0,.7)", "VSTYLE": f"color:{bright_c};", "DOT": bright_c,
             "FOOTTXT": "#9A9A9A", "FOOTBORDER": "rgba(255,255,255,.14)", "FOOTCRED": "#7A7A7A",
             "PAGETXT": "rgba(255,255,255,.7)", "PAGEBG": "rgba(0,0,0,.28)", "PAGEBORDER": "rgba(255,255,255,.14)",
             "GTINT": "#2A1CA8", "GTO": ".15",
             "GVIG": "radial-gradient(135% 120% at 50% 34%, transparent 42%, rgba(0,0,0,.78) 100%)", "GGO": ".08"}

    has_img = False
    bg_css = "none"
    if bg_url:
        bg_css = f"url({bg_url})"
        has_img = True
    elif bg:
        bgp = bg if os.path.isabs(bg) else os.path.join(VAULT, bg)
        bg_css = f"url(data:image/png;base64,{base64.b64encode(open(bgp,'rb').read()).decode()})"
        has_img = True
    elif placeholder:
        bg_css = MESH_CLARO if tema == "claro" else MESH_ESCURO

    hsz = hsize if hsize > 0 else min(auto_hsize(headline), 92 if cta else 104)
    ovx_bg = _ovx_bg(overlay, ov_ang, ov_pos)
    ovx_op = 0 if overlay == "none" else max(0.0, min(1.0, float(overlay_op)))
    cssvars = {"W": w, "H": h, "BG": bg_css, "ACCENT": accent_c, "SQUARE": square, "ONACC": on_acc,
               "HSIZE": hsz, "TABF": tab_font(b["tab"]), "GRAIN": GRAIN,
               "POSX": posx, "POSY": posy, "ZOOM": zoom, "OVX": ovx_bg, "OVXO": ovx_op,
               "BRI": brilho, "CON": contraste, "SAT": satur}
    cssvars.update(T)
    css = CSS % cssvars

    sub_h = f'<div class="sub">{render_rich(sub)}</div>' if sub else ""
    cta_h = f'<div><span class="cta">{esc(cta)}</span></div>' if cta else ""
    page_h = f'<div class="page">{esc(page)}</div>' if page else ""
    chip_h = ("" if no_chip else
              f'<div class="chip"><div class="av">{glyph_html(b, on_acc, 50)}</div>'
              f'<div class="hd">{wordmark_html(b)}</div><div class="ck">&#10003;</div></div>')
    grade_on = (not no_grade) and (has_img or placeholder)
    grade_html = '<div class="grade"><i class="gt"></i><i class="gv"></i><i class="gg"></i></div>' if grade_on else ''
    if raw:  # só a imagem (arte já pronta importada) + overlay/filtros; sem texto/moldura
        body = '<div class="card"><div class="bg"></div><div class="ovx"></div></div>'
    else:
        body = (f'<div class="card"><div class="bg"></div>{grade_html}<div class="ovx"></div><div class="ov"></div>{page_h}'
                f'<div class="tab"><div class="ic">{glyph_html(b, on_acc, 46)}</div><div class="vt">{esc(b["tab"])}</div></div>'
                f'<div class="ct">{chip_h}<div class="h">{render_rich(headline)}</div>{sub_h}{cta_h}</div>'
                f'<div class="footer"><div>{esc(handle)}</div><div class="cred">{esc(rodape)}</div></div></div>')
    return PAGE % {"CSS": css, "BODY": body}, w, h


def render_html_to_png(page_html, out, w, h):
    """Renderiza o HTML do frame pra PNG via Chrome headless (2x). Retorna True se gerou."""
    html_path = os.path.join(VAULT, f".compositor.tmp.{os.getpid()}.html")
    open(html_path, "w", encoding="utf-8").write(page_html)
    out_abs = out if os.path.isabs(out) else os.path.join(VAULT, out)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size={w},{h}",
                    "--virtual-time-budget=4000", f"--screenshot={out_abs}", f"file://{html_path}"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        os.remove(html_path)
    except OSError:
        pass
    return os.path.exists(out_abs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marca", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bg", default="")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--size", default="1080x1350")
    ap.add_argument("--hsize", type=int, default=0)
    ap.add_argument("--accent", default="")
    ap.add_argument("--bright", default="")
    ap.add_argument("--cta", default="")
    ap.add_argument("--page", default="")
    ap.add_argument("--no-chip", action="store_true")
    ap.add_argument("--tema", default="claro", choices=["escuro", "claro"])
    ap.add_argument("--base", default="", help="sobrescreve a cor base")
    ap.add_argument("--square", default="", help="override do fundo dos quadrados/CTA (teste de gradiente)")
    ap.add_argument("--placeholder", action="store_true", help="fundo CSS (mesh roxo/branco) sem IA — pra simulação grátis")
    ap.add_argument("--no-grade", action="store_true", help="desliga a grade de acabamento (duotone+vinheta+grão)")
    args = ap.parse_args()

    try:
        page_html, w, h = compose_html(
            args.marca, args.headline, sub=args.sub, cta=args.cta, page=args.page,
            no_chip=args.no_chip, tema=args.tema, size=args.size, hsize=args.hsize,
            accent=args.accent, bright=args.bright, base=args.base, square=args.square,
            bg=args.bg, placeholder=args.placeholder, no_grade=args.no_grade)
    except ValueError as e:
        sys.exit(f"ERRO: {e}")

    out_abs = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    if render_html_to_png(page_html, args.out, w, h):
        print(f"OK: {out_abs}  (compositor 2x · {args.marca} · tema={args.tema})")
        print(meta_block(out_abs, {"modelo": f"compositor ({args.tema})", "qualidade": "2x",
                                   "tamanho": f"{w*2}x{h*2}", "paleta": args.accent or "—"}))
    else:
        sys.exit("ERRO: render falhou")


if __name__ == "__main__":
    main()
