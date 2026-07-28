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
import secrets
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


def mesh_da_marca(acento, tema="escuro", base_escura="#0B0B0B"):
    """Mesh de placeholder tingido pelo acento (sem roxo smark fixo)."""
    r, g, b = _hex_rgb(acento)
    if tema == "claro":
        c1 = (min(255, r + 180), min(255, g + 180), min(255, b + 180))
        c2 = (min(255, r + 200), min(255, g + 200), min(255, b + 200))
        return (f"radial-gradient(60% 50% at 72% 16%, #{c1[0]:02x}{c1[1]:02x}{c1[2]:02x} 0%, transparent 60%),"
                f"radial-gradient(55% 48% at 16% 84%, #{c2[0]:02x}{c2[1]:02x}{c2[2]:02x} 0%, transparent 62%),"
                "linear-gradient(160deg, #f7f8fa 0%, #F4F2FB 72%)")
    # escuro: blobs na cor da marca, base near-black/navy da marca
    c1 = (max(0, r // 3), max(0, g // 3), max(0, b // 3))
    c2 = (max(0, r // 2), max(0, g // 2), max(0, b // 2))
    base = base_escura if (base_escura or "").startswith("#") else "#0B0B0B"
    mid = f"#{max(0,c1[0]//2):02x}{max(0,c1[1]//2):02x}{max(0,c1[2]//2):02x}"
    return (f"radial-gradient(60% 50% at 28% 16%, #{c1[0]:02x}{c1[1]:02x}{c1[2]:02x} 0%, transparent 60%),"
            f"radial-gradient(55% 48% at 84% 66%, #{c2[0]:02x}{c2[1]:02x}{c2[2]:02x} 0%, transparent 62%),"
            f"linear-gradient(160deg, {mid} 0%, {base} 72%)")
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


def readable_against(hex_c, tema="claro", target=4.5):
    """Garante contraste de TEXTO sobre fundo claro/escuro (evita branco no claro).

    Tema claro → base branca; se a cor for clara demais, escurece.
    Tema escuro → base preta; se a cor for escura demais, clareia.
    """
    if not hex_c or not str(hex_c).startswith("#"):
        return "#100D1C" if tema == "claro" else "#FFFFFF"
    h = str(hex_c).strip()
    if len(h) == 4:  # #RGB
        h = "#" + "".join(c * 2 for c in h[1:])
    try:
        rgb = _hex2rgb(h)
    except Exception:
        return "#100D1C" if tema == "claro" else "#FFFFFF"
    base = "#FFFFFF" if tema == "claro" else "#0B0B0B"
    bl = _lum(_hex2rgb(base))

    def contrast(r):
        l = _lum(r)
        hi, lo = max(l, bl), min(l, bl)
        return (hi + 0.05) / (lo + 0.05)

    if contrast(rgb) >= target:
        return h.upper() if len(h) == 7 else h

    if tema == "claro":
        # escurece
        f = 1.0
        out = rgb
        while contrast(out) < target and f > 0.08:
            f -= 0.05
            out = tuple(int(c * f) for c in rgb)
        return "#%02X%02X%02X" % out
    # escuro: clareia misturando com branco
    t = 0.0
    out = rgb
    while contrast(out) < target and t < 0.92:
        t += 0.06
        out = tuple(int(c + (255 - c) * t) for c in rgb)
    return "#%02X%02X%02X" % out


def load_brands():
    with open(TOKENS, "r", encoding="utf-8") as f:
        t = json.load(f)
    fund = dict(t["fundacao"])
    fund["_claro"] = t.get("tema_claro", {})
    brands = {}
    for slug, m in t["marcas"].items():
        brasao = m.get("brasao") or {}
        brands[slug] = {
            "name": m["nome"], "accent": m["acento"], "bright": m.get("acento_claro", m["acento"]),
            "glyph": m.get("logo_glyph", "•"), "handle": m.get("handle", "@" + slug),
            "endossa": m.get("endossa", False),
            "logo_path": m.get("logo_path", ""), "logo_svg": m.get("logo_svg", ""),
            "logo_file": brasao.get("principal") or m.get("logo_file") or "",
            "wordmark": m.get("wordmark", ""), "gradiente": m.get("gradiente", ""),
            "base_escura": m.get("base_escura") or (m.get("paleta_extra") or {}).get("navy") or "",
            "tab": (m["wordmark"].split("*")[0].split()[0].upper() if m.get("wordmark")
                    else m["nome"].split()[0].replace(".", "").upper()),
        }
    return brands, fund


def esc(s):
    return htmlmod.escape(s)


def _resolve_logo_file(rel):
    """Caminho absoluto do logo PNG/SVG: vault-root ou design-system/assets."""
    if not rel:
        return ""
    if os.path.isabs(rel) and os.path.isfile(rel):
        return rel
    p1 = os.path.join(VAULT, rel)
    if os.path.isfile(p1):
        return p1
    p2 = os.path.join(VAULT, "design-system", "assets", rel)
    if os.path.isfile(p2):
        return p2
    return ""


def _logo_is_mark(im):
    """True se a imagem parece marca/símbolo (não foto de feed 4:5 ou banner).

    Heurística: proporção ~quadrada/horizontal moderada, área útil pequena com
    transparência ou fundo quase uniforme, e dimensões que não gritem 'post'.
    """
    w, h = im.size
    if w < 16 or h < 16:
        return False
    ratio = w / max(1, h)
    # feed IG 4:5 / story 9:16 / vertical tall → quase sempre foto, não mark
    if ratio < 0.72 or ratio > 2.4:
        return False
    # foto full-bleed grande sem alpha e com muita variação → rejeita
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if not has_alpha and max(w, h) >= 900 and 0.78 <= ratio <= 1.28:
        # 1:1 grande sem alpha: pode ser app icon OU foto; olha entropia de borda
        try:
            rgb = im.convert("RGB")
            corners = [rgb.getpixel((0, 0)), rgb.getpixel((w - 1, 0)),
                       rgb.getpixel((0, h - 1)), rgb.getpixel((w - 1, h - 1))]
            # se 4 cantos muito diferentes → foto; se parecidos → mark com fundo sólido
            def dist(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
            spreads = [dist(corners[0], c) for c in corners[1:]]
            if max(spreads) > 90:
                return False
        except Exception:
            pass
    return True


def _logo_badge_png(path, color, px, pad_ratio=0.14):
    """Gera PNG base64 do logo para tab/chip: trim + mono na cor + padding.

    Devolve None se o arquivo for inadequado (foto/feed) — aí o caller usa glyph.
    """
    try:
        from PIL import Image, ImageOps
        import io
    except ImportError:
        return None
    try:
        im = Image.open(path)
    except Exception:
        return None
    # SVG não passa por PIL normalmente
    if path.lower().endswith(".svg"):
        return None
    if not _logo_is_mark(im):
        return None
    # RGBA
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    # trim por alpha ou por fundo quase-branco/uniforme
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    # se quase sem alpha útil, tenta tratar fundo claro como transparente
    alpha = im.split()[-1]
    if alpha.getextrema()[0] > 250:
        # sem transparência real — remove fundo claro
        rgb = im.convert("RGB")
        datas = list(rgb.getdata())
        out_px = []
        for r, g, b in datas:
            if r > 245 and g > 245 and b > 245:
                out_px.append((r, g, b, 0))
            else:
                out_px.append((r, g, b, 255))
        im = Image.new("RGBA", rgb.size)
        im.putdata(out_px)
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
    # mono: usa luminância invertida como alpha, preenche com `color`
    if (color or "").startswith("#") and len(color) >= 7:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    else:
        r, g, b = 255, 255, 255
    gray = ImageOps.grayscale(im.convert("RGB"))
    # pixels escuros = símbolo; claros = fundo → alpha
    # se o logo já é claro em fundo escuro, inverte
    hist = gray.histogram()
    dark = sum(hist[:96])
    light = sum(hist[160:])
    if light > dark * 1.4:
        # símbolo claro em fundo escuro
        mask = gray.point(lambda p: min(255, max(0, int((p - 40) * 1.2))))
    else:
        mask = gray.point(lambda p: min(255, max(0, int((220 - p) * 1.15))))
    # combina com alpha original
    a_orig = im.split()[-1]
    mask = Image.composite(mask, Image.new("L", mask.size, 0), a_orig)
    badge = Image.new("RGBA", im.size, (r, g, b, 0))
    badge.putalpha(mask)
    # encaixa em canvas px×px com padding
    canvas = Image.new("RGBA", (px * 2, px * 2), (0, 0, 0, 0))  # 2x nítido
    pad = int(px * 2 * pad_ratio)
    inner = px * 2 - pad * 2
    badge.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    ox = (px * 2 - badge.size[0]) // 2
    oy = (px * 2 - badge.size[1]) // 2
    canvas.paste(badge, (ox, oy), badge)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def glyph_html(b, color, px):
    """Símbolo inteligente: SVG path > logo processado (mono+trim) > letra.

    Nunca cola foto de feed na tab/chip — se o arquivo não parecer marca, usa glyph.
    """
    if b.get("logo_svg"):
        return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}" style="color:{color}">'
                f'{b["logo_svg"]}</svg>')
    if b.get("logo_path"):
        return (f'<svg viewBox="0 0 100 100" width="{px}" height="{px}">'
                f'<path fill-rule="evenodd" fill="{color}" d="{b["logo_path"]}"/></svg>')
    lf = _resolve_logo_file(b.get("logo_file") or "")
    if lf:
        ext = os.path.splitext(lf)[1].lower()
        if ext == ".svg":
            try:
                # embute SVG inline limitado
                raw = open(lf, "r", encoding="utf-8", errors="ignore").read()
                # remove scripts
                if "<script" not in raw.lower():
                    return (f'<span style="display:flex;width:{px}px;height:{px}px;align-items:center;'
                            f'justify-content:center;overflow:hidden">{raw}</span>')
            except OSError:
                pass
        else:
            data = _logo_badge_png(lf, color if (color or "").startswith("#") else "#FFFFFF", px)
            if data:
                return (f'<img src="data:image/png;base64,{data}" width="{px}" height="{px}" '
                        f'alt="" style="object-fit:contain;display:block;width:{px}px;height:{px}px"/>')
            # fallback: se for mark mas mono falhou, contain com padding
            try:
                from PIL import Image
                im = Image.open(lf)
                if _logo_is_mark(im):
                    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".webp": "image/webp"}.get(ext, "image/png")
                    b64 = base64.b64encode(open(lf, "rb").read()).decode()
                    return (f'<img src="data:{mime};base64,{b64}" width="{px}" height="{px}" alt="" '
                            f'style="object-fit:contain;display:block;width:{int(px*0.78)}px;height:{int(px*0.78)}px;'
                            f'margin:auto;padding:{max(2,int(px*0.08))}px;box-sizing:content-box"/>')
            except Exception:
                pass
    return esc(b.get("glyph") or "•")


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


def render_rich(text, tema="claro"):
    """Formatação: '|' ou '\\n'/Enter = quebra · **negrito** · _itálico_ · *acento* · {#hex:texto} = cor.

    Cores manuais passam por `readable_against` — branco no tema claro vira escuro legível.
    """
    s = esc((text or "").replace("\r", "").replace("|", "\n").replace("\\n", "\n"))
    BR = "\x00BR\x00"
    s = s.replace("\n", BR)

    def _rep_cor(m):
        hx, body = m.group(1), m.group(2)
        safe = readable_against(hx, tema)
        return f'<span style="color:{safe}">{body}</span>'

    for _ in range(12):
        new = re.sub(r"\{(#[0-9a-fA-F]{3,6}):([^{}]*)\}", _rep_cor, s)
        if new == s:
            break
        s = new
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"_(.+?)_", r"<i>\1</i>", s)
    s = re.sub(r"\*(.+?)\*", r'<span class="v">\1</span>', s)
    return s.replace(BR, "<br>")


# Fallback legado (smark). Preferir degrade_claro_da_marca(acento).
DEGRADE_CLARO = "linear-gradient(155deg,#F4F2FB 0%,#EFE6FF 42%,#D9C2FF 78%,#C6A8FF 100%)"


def _hex_rgb(h):
    h = (h or "").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return (139, 60, 247)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def degrade_claro_da_marca(acento, acento_claro=None):
    """Degradê claro tingido pelo acento da marca (não lavanda smark)."""
    r, g, b = _hex_rgb(acento)
    r2, g2, b2 = _hex_rgb(acento_claro or acento)
    # misturas claras
    def mix(a, t):
        return tuple(int(255 * (1 - t) + c * t) for c in a)
    c1 = mix((r, g, b), 0.08)
    c2 = mix((r2, g2, b2), 0.18)
    c3 = mix((r, g, b), 0.35)
    return (f"linear-gradient(155deg,#F7F8FA 0%,#{c1[0]:02x}{c1[1]:02x}{c1[2]:02x} 40%,"
            f"#{c2[0]:02x}{c2[1]:02x}{c2[2]:02x} 72%,#{c3[0]:02x}{c3[1]:02x}{c3[2]:02x} 100%)")


def _rgba(h, a):
    r, g, b = _hex_rgb(h)
    return f"rgba({r},{g},{b},{a})"


def tab_font(label):
    """Fonte do nome vertical da etiqueta — auto-ajusta pra todos caberem na MESMA altura, centrados."""
    n = max(len(label), 1)
    return int(max(13, min(18, 130 / (n * 1.05))))


def auto_hsize(text):
    plain = [ln.replace("*", "") for ln in (text or "").split("\\n")]
    longest = max((len(ln) for ln in plain), default=1) or 1  # nunca 0 (evita div/0)
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


def _ovx_bg(overlay, ang, pos, accent="#8B3CF7"):
    """Overlays. 'roxo'/'todo-roxo' = legado; usam o acento da marca ativa."""
    acc = accent or "#8B3CF7"
    r, g, b = _hex_rgb(acc)
    # versão mais escura pro fim do degradê
    rd, gd, bd = max(0, r // 2), max(0, g // 2), max(0, b // 2)
    if overlay in ("branco",):
        return f"linear-gradient({ang}deg, rgba(255,255,255,0) {pos}%, rgba(255,255,255,1) 100%)"
    if overlay in ("roxo", "acento", "marca"):
        return (f"linear-gradient({ang}deg, rgba({r},{g},{b},0) {pos}%, "
                f"rgba({rd},{gd},{bd},.96) 100%)")
    if overlay in ("todo-branco",):
        return "#FFFFFF"
    if overlay in ("todo-roxo", "todo-acento", "todo-marca"):
        return acc if acc.startswith("#") else f"#{acc}"
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

    has_img = bool(bg_url or bg)

    # grade/duotone usa acento da MARCA (não roxo smark fixo)
    gtint = accent_c
    if tema == "claro":
        cl = fund.get("_claro", {})
        base_c = base or cl.get("base", "#F4F2FB")
        txt = cl.get("texto", "#100D1C")
        # com foto, assume fundo claro no terço inferior → acento precisa contrastar com BRANCO
        base_for_acc = "#FFFFFF" if has_img else (
            base_c if (base_c.startswith("#") and len(base_c) in (4, 7)) else "#F4F2FB")
        acc_txt = readable_on(accent_c, base_for_acc, target=5.0 if has_img else 4.0)
        # scrim mais forte com imagem (garante legibilidade do apoio)
        if has_img:
            ov = ("linear-gradient(180deg, rgba(255,255,255,.15) 0%%, rgba(255,255,255,0) 22%%, "
                  "rgba(255,255,255,.55) 48%%, rgba(255,255,255,.92) 72%%, rgba(255,255,255,.98) 100%%)")
            subc = "#1A1830"
            hshadow = "0 2px 18px rgba(255,255,255,.55)"
        else:
            ov = ("linear-gradient(180deg, rgba(244,242,251,.30) 0%%, rgba(244,242,251,0) 28%%, "
                  "rgba(244,242,251,.5) 52%%, rgba(244,242,251,.93) 78%%, rgba(244,242,251,1) 100%%)")
            subc = cl.get("sub", "#4A4560")
            hshadow = "none"
        T = {"BASE": base_c, "TXT": txt, "SUBC": subc, "LH": ".98",
             "OV": ov,
             "HSHADOW": hshadow, "VSTYLE": f"color:{acc_txt};", "DOT": acc_txt,
             "FOOTTXT": cl.get("apoio", "#6B6680"), "FOOTBORDER": "rgba(0,0,0,.14)", "FOOTCRED": "#8B8698",
             "PAGETXT": txt, "PAGEBG": "rgba(255,255,255,.6)", "PAGEBORDER": "rgba(0,0,0,.14)",
             "GTINT": gtint, "GTO": ".07",
             "GVIG": f"radial-gradient(150% 130% at 50% 30%, transparent 60%, {_rgba(accent_c, 0.10)} 100%)",
             "GGO": ".05"}
    else:
        base_c = base or fund.get("base", "#0B0B0B")
        # acento claro precisa contrastar com preto/navy
        acc_dark = readable_against(bright_c or accent_c, "escuro", target=4.5)
        T = {"BASE": base_c, "TXT": "#FFFFFF", "SUBC": "#E8E8EC", "LH": ".96",
             "OV": "linear-gradient(180deg, rgba(11,11,11,.5) 0%%, rgba(11,11,11,0) 30%%, rgba(11,11,11,.42) 50%%, rgba(11,11,11,.9) 76%%, rgba(11,11,11,.99) 100%%)",
             "HSHADOW": "0 6px 34px rgba(0,0,0,.7)", "VSTYLE": f"color:{acc_dark};", "DOT": acc_dark,
             "FOOTTXT": "#9A9A9A", "FOOTBORDER": "rgba(255,255,255,.14)", "FOOTCRED": "#7A7A7A",
             "PAGETXT": "rgba(255,255,255,.7)", "PAGEBG": "rgba(0,0,0,.28)", "PAGEBORDER": "rgba(255,255,255,.14)",
             "GTINT": gtint, "GTO": ".12",
             "GVIG": "radial-gradient(135% 120% at 50% 34%, transparent 42%, rgba(0,0,0,.78) 100%)",
             "GGO": ".08"}

    bg_css = "none"
    if bg_url:
        bg_css = f"url({bg_url})"
    elif bg:
        bgp = bg if os.path.isabs(bg) else os.path.join(VAULT, bg)
        bg_css = f"url(data:image/png;base64,{base64.b64encode(open(bgp,'rb').read()).decode()})"
    elif placeholder:
        base_e = (b.get("base_escura") or "")
        if not base_e:
            import re as _re
            gm = _re.search(r"(#[0-9A-Fa-f]{6})\s+100%", b.get("gradiente") or "")
            base_e = gm.group(1) if gm else "#0B0B0B"
        bg_css = mesh_da_marca(accent_c, tema, base_e)

    hsz = hsize if hsize > 0 else min(auto_hsize(headline), 92 if cta else 104)
    # foto + tema claro sem overlay: força degradê branco legível
    use_ov = overlay
    use_op = overlay_op
    if has_img and tema == "claro" and (overlay or "none") in ("none", ""):
        use_ov = "branco"
        use_op = max(float(overlay_op or 0.85), 0.88)
    ovx_bg = _ovx_bg(use_ov, ov_ang, ov_pos, accent=accent_c)
    ovx_op = 0 if use_ov == "none" else max(0.0, min(1.0, float(use_op)))
    cssvars = {"W": w, "H": h, "BG": bg_css, "ACCENT": accent_c, "SQUARE": square, "ONACC": on_acc,
               "HSIZE": hsz, "TABF": tab_font(b["tab"]), "GRAIN": GRAIN,
               "POSX": posx, "POSY": posy, "ZOOM": zoom, "OVX": ovx_bg, "OVXO": ovx_op,
               "BRI": brilho, "CON": contraste, "SAT": satur}
    cssvars.update(T)
    css = CSS % cssvars

    sub_h = f'<div class="sub">{render_rich(sub, tema)}</div>' if sub else ""
    cta_h = f'<div><span class="cta">{esc(cta)}</span></div>' if cta else ""
    page_h = f'<div class="page">{esc(page)}</div>' if page else ""
    chip_h = ("" if no_chip else
              f'<div class="chip"><div class="av">{glyph_html(b, on_acc, 50)}</div>'
              f'<div class="hd">{wordmark_html(b)}</div><div class="ck">&#10003;</div></div>')
    # headline também com cores seguras
    grade_on = (not no_grade) and (has_img or placeholder)
    grade_html = '<div class="grade"><i class="gt"></i><i class="gv"></i><i class="gg"></i></div>' if grade_on else ''
    if raw:  # só a imagem (arte já pronta importada) + overlay/filtros; sem texto/moldura
        body = '<div class="card"><div class="bg"></div><div class="ovx"></div></div>'
    else:
        body = (f'<div class="card"><div class="bg"></div>{grade_html}<div class="ovx"></div><div class="ov"></div>{page_h}'
                f'<div class="tab"><div class="ic">{glyph_html(b, on_acc, 46)}</div><div class="vt">{esc(b["tab"])}</div></div>'
                f'<div class="ct">{chip_h}<div class="h">{render_rich(headline, tema)}</div>{sub_h}{cta_h}</div>'
                f'<div class="footer"><div>{esc(handle)}</div><div class="cred">{esc(rodape)}</div></div></div>')
    return PAGE % {"CSS": css, "BODY": body}, w, h


def render_html_to_png(page_html, out, w, h, tries=3):
    """Renderiza o HTML do frame pra PNG via Chrome headless (2x). Retorna True se gerou.
    Robusto: nome de tmp único (sem colisão entre renders simultâneos), timeout que mata
    Chrome travado, e retry — evita frame faltando no 'exportar carrossel todo'."""
    out_abs = out if os.path.isabs(out) else os.path.join(VAULT, out)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    tag = f"{os.getpid()}.{secrets.token_hex(4)}"
    html_path = os.path.join(VAULT, f".compositor.tmp.{tag}.html")
    open(html_path, "w", encoding="utf-8").write(page_html)
    try:
        for _ in range(max(1, tries)):
            try:
                if os.path.exists(out_abs):
                    os.remove(out_abs)  # garante que exists() reflita ESTE render, não um antigo
            except OSError:
                pass
            try:
                subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                "--force-device-scale-factor=2", f"--window-size={w},{h}",
                                "--virtual-time-budget=4000", f"--screenshot={out_abs}",
                                f"file://{html_path}"],
                               check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=60)
            except subprocess.TimeoutExpired:
                continue  # Chrome travou → o subprocess é morto; tenta de novo
            if os.path.exists(out_abs) and os.path.getsize(out_abs) > 0:
                return True
        return False
    finally:
        try:
            os.remove(html_path)
        except OSError:
            pass


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
