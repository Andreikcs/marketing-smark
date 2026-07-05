#!/usr/bin/env python3
"""SUPER EDITOR — servidor local do editor de arte por FRAME (localhost:8765).

Preview ao vivo (mesmo HTML/CSS do compositor) + export do PNG final + upload de fundo
+ regerar fundo de IA. Fonte de dados: editor.json (posts → frames).

Rodar:  python3 scripts/editor_server.py   →   http://localhost:8765
"""
import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import socketserver
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compositor  # noqa: E402

PORT = 8765
PAINEL = os.path.join(VAULT, "painel.html")
VITRINE = os.path.join(VAULT, "lancamento.html")

HUB = """<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>smark · Sistema</title>
<style>
:root{--rox:#8b3cf7}*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0b13;color:#ece9f4;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px}
h1{font-size:26px;margin-bottom:6px}h1 span{color:var(--rox)}
.sub{color:#9a92ad;font-size:14px;margin-bottom:34px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;max-width:760px;width:100%}
a.card{display:block;background:#141019;border:1px solid #2a2338;border-radius:16px;padding:22px;text-decoration:none;color:inherit;transition:.15s}
a.card:hover{border-color:var(--rox);transform:translateY(-2px)}
.card .ic{font-size:30px;margin-bottom:12px}
.card b{font-size:16px;display:block;margin-bottom:5px}
.card p{color:#9a92ad;font-size:12.5px;line-height:1.45}
.foot{color:#6a6480;font-size:11px;margin-top:30px}
</style></head><body>
<h1>Grupo <span>smark</span> · Sistema</h1>
<div class=sub>Tudo local · localhost:8765</div>
<div class=grid>
  <a class=card href="/editor"><div class=ic>✎</div><b>Super Editor</b><p>Edita arte frame a frame, preview ao vivo, troca de fundo, cor, upload e regenerar por IA.</p></a>
  <a class=card href="/painel"><div class=ic>▦</div><b>Painel de Conteúdo</b><p>Todas as publicações com preview de Instagram/LinkedIn e download.</p></a>
  <a class=card href="/vitrine"><div class=ic>▤</div><b>Vitrine</b><p>Galeria read-only por marca — feed pra aprovar copy e conceito.</p></a>
  <a class=card href="/config"><div class=ic>⚙</div><b>Configurações</b><p>Como o sistema está se comportando: temas, cores, degradês, conceitos e estado.</p></a>
</div>
<div class=foot>Editor, Painel e Vitrine servidos pelo mesmo servidor.</div>
</body></html>"""

def config_html():
    """Tela read-only das configurações do sistema (como ele está se comportando)."""
    try:
        tok = json.load(open(os.path.join(VAULT, "design-system", "tokens", "tokens.json"), encoding="utf-8"))
    except Exception:
        tok = {}
    try:
        import _direcao
        conceitos = list(getattr(_direcao, "CONCEITOS", {}).keys())
    except Exception:
        conceitos = []
    ed = load() if os.path.isfile(DATA) else {"posts": []}
    fund = tok.get("fundacao", {})
    marcas = tok.get("marcas", {})
    tp = tok.get("tema_padrao") or "claro"
    sw = lambda c: f"<span style='display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;margin-right:6px;background:{c};border:1px solid #333'></span>"
    rows_m = "".join(
        f"<tr><td><b>{m.get('nome', s)}</b></td><td>{sw(m.get('acento','#000'))}{m.get('acento','')}</td>"
        f"<td>{sw(m.get('acento_claro', m.get('acento','#000')))}{m.get('acento_claro','—')}</td>"
        f"<td style='font-size:11px;max-width:260px;word-break:break-all'>{m.get('gradiente','—')}</td>"
        f"<td>{m.get('handle','')}</td></tr>" for s, m in marcas.items())
    rows_p = "".join(
        f"<tr><td>{i+1}</td><td>{p.get('titulo','')}</td><td>{p.get('slug','')}</td>"
        f"<td>{len(p.get('frames',[]))}</td></tr>" for i, p in enumerate(ed.get("posts", [])))
    chips = " ".join(f"<span class=chip>{c}</span>" for c in conceitos)
    return f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Configurações · smark</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0d0b13;color:#ece9f4;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:20px 30px 60px}}
a.menu{{position:fixed;top:8px;left:8px;background:#8b3cf7;color:#fff;padding:6px 12px;border-radius:8px;font:600 12px sans-serif;text-decoration:none;z-index:9}}
h1{{font-size:22px;margin:18px 0 4px}}h1 span{{color:#8b3cf7}} .sub{{color:#9a92ad;font-size:13px;margin-bottom:24px}}
.grp{{background:#141019;border:1px solid #2a2338;border-radius:14px;padding:16px 18px;margin-bottom:16px;max-width:860px}}
.grp h3{{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:#9a92ad;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:7px 8px;border-bottom:1px solid #221c30}}th{{color:#9a92ad;font-weight:600;font-size:11px;text-transform:uppercase}}
.kv{{display:flex;flex-wrap:wrap;gap:10px}}.kv div{{background:#1a1524;border:1px solid #2a2338;border-radius:9px;padding:8px 12px;font-size:13px}}.kv b{{color:#c9b6ff}}
.chip{{display:inline-block;background:#241a38;border:1px solid #3a2b58;color:#c9b6ff;border-radius:999px;padding:4px 11px;font-size:12px;margin:2px}}
.ok{{color:#37c26b}}
</style></head><body>
<a class=menu href="/">☰ Menu</a>
<h1>Configurações do <span>Sistema</span></h1>
<div class=sub>Read-only · como o sistema está se comportando agora.</div>

<div class=grp><h3>Tema & padrões de geração</h3><div class=kv>
<div>Tema-padrão: <b>{tp}</b></div>
<div>Regra #9: imagens geradas saem <b>claras</b> por padrão</div>
<div>Base clara: <b>{tok.get('tema_claro',{}).get('base','#F4F2FB')}</b></div>
<div>Base escura: <b>{fund.get('base','#0B0B0B')}</b></div>
<div>Rodapé: <b>{fund.get('rodape','—')}</b></div>
<div>Degradê da marca (claro): <b>ativo</b></div>
</div></div>

<div class=grp><h3>Marcas (cores / degradê / handle)</h3>
<table><tr><th>Marca</th><th>Acento</th><th>Acento claro</th><th>Degradê</th><th>Handle</th></tr>{rows_m}</table></div>

<div class=grp><h3>Conceitos de direção de arte ({len(conceitos)})</h3>{chips}</div>

<div class=grp><h3>Posts no editor ({len(ed.get('posts',[]))})</h3>
<table><tr><th>#</th><th>Título</th><th>Slug</th><th>Frames</th></tr>{rows_p}</table></div>

<div class=grp><h3>Servidor & segurança</h3><div class=kv>
<div>Porta: <b>{PORT}</b></div>
<div>Hosts permitidos: <b>localhost:8765 / 127.0.0.1:8765</b></div>
<div>Proteção CSRF/DNS: <b class=ok>ativa</b> (Host+Origin+token)</div>
<div>Dados do editor: <b>editor.json</b></div>
</div></div>
</body></html>"""


# Segurança (CSRF / DNS rebinding): o servidor é local, mas tem rotas que gastam
# dinheiro (regerar-fundo→OpenAI) e escrevem em disco. Um site malicioso aberto no
# navegador poderia dar POST em localhost. Defesa: Host + Origin + token de sessão.
ALLOWED_HOSTS = {"127.0.0.1:8765", "localhost:8765"}
TOKEN = secrets.token_hex(16)  # novo a cada boot; injetado no HTML servido
DATA = os.path.join(VAULT, "editor.json")
UI = os.path.join(HERE, "_editor2.html")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".svg": "image/svg+xml", ".css": "text/css",
        ".js": "application/javascript", ".html": "text/html; charset=utf-8"}


def load():
    return json.load(open(DATA, encoding="utf-8"))


def save(d):
    json.dump(d, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def hl(text):
    """headline do editor usa '|' como quebra; o compositor usa '\\n'."""
    return (text or "").replace("|", "\\n")


def frame_kwargs(fr, size, for_export):
    """Traduz um frame do editor.json nos kwargs do compose_html.
    for_export=True embute a imagem (base64, render headless); False usa URL estática (preview leve)."""
    k = dict(marca="smark", headline=hl(fr.get("headline", "")), sub=fr.get("sub", ""),
             cta=fr.get("cta", ""), page=fr.get("page", ""), no_chip=not fr.get("chip", False),
             tema=fr.get("tema", "escuro"), size=size, hsize=int(fr.get("hsize", 0) or 0),
             accent=fr.get("accent", ""), no_grade=not fr.get("grade", True),
             zoom=float(fr.get("zoom", 1.0) or 1.0), posx=int(fr.get("posx", 50)),
             posy=int(fr.get("posy", 50)), overlay=fr.get("overlay", "none"),
             overlay_op=float(fr.get("overlay_op", 0.85)))
    mode = fr.get("bgmode", "imagem")
    if mode == "imagem" and fr.get("bg"):
        if for_export:
            k["bg"] = fr["bg"]
        else:
            k["bg_url"] = "/" + urllib.parse.quote(fr["bg"])
    elif mode == "cor":
        k["base"] = fr.get("cor") or ""
    elif mode == "degrade":  # degradê claro da marca (instantâneo, sem IA)
        k["base"] = compositor.DEGRADE_CLARO
        k["tema"] = "claro"
    else:  # escuro | claro (preset com mesh)
        k["placeholder"] = True
        k["tema"] = "claro" if mode == "claro" else "escuro"
    return k


def normaliza(d):
    """Garante n sequencial e caminho 'out' pra todo frame (permite adicionar/remover cards)."""
    A = "marcas/smark/publicacoes/social/instagram/arte"
    for p in d.get("posts", []):
        for i, fr in enumerate(p.get("frames", []), 1):
            fr["n"] = i
            fr["out"] = f"{A}/{p['slug']}/{i:02d}.png"
    return d


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def _host_ok(self):
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def _post_allowed(self):
        """POST muda estado / gasta dinheiro → exige Host + Origin próprios + token."""
        if not self._host_ok():
            return False
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlparse(origin).netloc not in ALLOWED_HOSTS:
            return False
        return self.headers.get("X-Editor-Token", "") == TOKEN

    def _serve_module(self, fp, nome):
        if not os.path.isfile(fp):
            return self._send(200, f"<body style='font-family:sans-serif;background:#0d0b13;color:#ccc;padding:40px'>"
                              f"<a href='/' style='color:#8b3cf7'>← Menu</a><h2>{nome} ainda não foi gerado.</h2></body>",
                              MIME[".html"])
        bar = ('<a href="/" style="position:fixed;top:8px;left:8px;z-index:99999;background:#8b3cf7;color:#fff;'
               'padding:6px 12px;border-radius:8px;font:600 12px sans-serif;text-decoration:none">☰ Menu</a>')
        html = open(fp, encoding="utf-8").read().replace("</body>", bar + "</body>", 1)
        return self._send(200, html, MIME[".html"])

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._host_ok():  # bloqueia DNS rebinding
            return self._send(403, {"erro": "host não permitido"})
        if path in ("/", "/menu"):
            return self._send(200, HUB, MIME[".html"])
        if path == "/editor":
            html = open(UI, encoding="utf-8").read().replace("__EDITOR_TOKEN__", TOKEN)
            return self._send(200, html, MIME[".html"])
        if path == "/painel":
            return self._serve_module(PAINEL, "Painel")
        if path == "/vitrine":
            return self._serve_module(VITRINE, "Vitrine")
        if path == "/config":
            return self._send(200, config_html(), MIME[".html"])
        if path == "/dados":
            return self._send(200, load())
        # arquivo estático dentro do vault (imagens)
        rel = urllib.parse.unquote(path.lstrip("/"))
        full = os.path.realpath(os.path.join(VAULT, rel))
        if full.startswith(VAULT) and os.path.isfile(full):
            ext = os.path.splitext(full)[1].lower()
            with open(full, "rb") as f:
                return self._send(200, f.read(), MIME.get(ext, "application/octet-stream"))
        return self._send(404, {"erro": "não encontrado"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._post_allowed():
            return self._send(403, {"ok": False, "erro": "bloqueado (host/origin/token) — recarregue o editor"})
        try:
            req = self._body()
        except Exception as e:
            return self._send(400, {"ok": False, "erro": f"body inválido: {e}"})

        if path == "/preview":
            try:
                html, _, _ = compositor.compose_html(**frame_kwargs(req.get("frame", {}),
                                                     req.get("size", "1080x1350"), for_export=False))
                return self._send(200, html, MIME[".html"])
            except Exception as e:
                return self._send(200, f"<pre style='color:#f66;font-family:monospace;padding:20px'>preview erro: {e}</pre>", MIME[".html"])

        if path == "/salvar":
            save(normaliza(req.get("dados", load())))
            return self._send(200, {"ok": True})

        if path == "/novo-post":
            d = load()
            slug = re.sub(r"[^a-z0-9-]+", "-", (req.get("slug") or "").lower()).strip("-") \
                or ("novo-" + secrets.token_hex(3))
            if any(p["slug"] == slug for p in d["posts"]):
                slug = slug + "-" + secrets.token_hex(2)
            fr = {"headline": "SEU TÍTULO|*AQUI.*", "sub": "", "cta": "", "page": "01/01",
                  "chip": True, "tema": "claro", "bgmode": "claro", "bg": "", "cor": "#F4F2FB",
                  "accent": "", "hsize": 0, "grade": True}
            d["posts"].append({"slug": slug, "marca": "smark",
                               "titulo": req.get("titulo") or "Novo post", "size": "1080x1350",
                               "frames": [fr]})
            save(normaliza(d))
            return self._send(200, {"ok": True, "index": len(d["posts"]) - 1, "slug": slug})

        if path == "/exportar":
            d = load()
            try:
                post = d["posts"][req["post"]]
                idxs = [req["frame"]] if req.get("frame") is not None and req.get("frame") != "all" \
                    else list(range(len(post["frames"])))
                feitas = []
                for i in idxs:
                    fr = post["frames"][i]
                    kw = frame_kwargs(fr, post.get("size", "1080x1350"), for_export=True)
                    html, w, h = compositor.compose_html(**kw)
                    out = fr.get("out") or f"{os.path.dirname(post['frames'][0].get('out',''))}/{i+1:02d}.png"
                    if compositor.render_html_to_png(html, out, w, h):
                        feitas.append(out)
                return self._send(200, {"ok": True, "feitas": feitas})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/upload":
            try:
                data = req["dataurl"].split(",", 1)[1]
                raw = base64.b64decode(data)
                slug = req.get("slug", "avulso")
                dd = os.path.join(VAULT, "marcas", "smark", "publicacoes", "social", "instagram",
                                  "arte", slug, "_uploads")
                os.makedirs(dd, exist_ok=True)
                name = hashlib.sha1(raw).hexdigest()[:10] + ".png"
                full = os.path.join(dd, name)
                open(full, "wb").write(raw)
                return self._send(200, {"ok": True, "path": os.path.relpath(full, VAULT)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/regerar-fundo":
            d = load()
            try:
                post = d["posts"][req["post"]]
                fr = post["frames"][req["frame"]]
                slug = post["slug"]
                dd = os.path.join(VAULT, "marcas", "smark", "publicacoes", "social", "instagram",
                                  "arte", slug, "_regen")
                os.makedirs(dd, exist_ok=True)
                out = os.path.join(dd, f"{req['frame']+1:02d}-{hashlib.sha1(str(req).encode()).hexdigest()[:6]}.png")
                ref = req.get("ref", "")
                if ref:  # referência → openai_edit (usa o contexto do usuário como prompt)
                    ctx = (req.get("prompt", "") or "").strip()
                    full = ((ctx + ". ") if ctx else "") + (
                        "Brand key visual for smark — abstract, premium, violet/roxo palette, "
                        "editorial, lower third kept clean for headline text, 4k, no text, no logos.")
                    cmd = ["python3", os.path.join(HERE, "openai_edit.py"),
                           "--image", os.path.join(VAULT, ref), "--out", out,
                           "--prompt", full, "--size", "1024x1536", "--quality", "high"]
                else:  # direção de arte
                    tema = req.get("tema", "claro")  # PADRÃO CLARO (rule #9)
                    cmd = ["python3", os.path.join(HERE, "openai_image.py"), "--out", out, "--direcao",
                           "--marca", "smark", "--tipo", req.get("tipo", "manifesto"),
                           "--tema", tema, "--headline", (fr.get("headline", "") or "").replace("|", " "),
                           "--size", "1024x1536", "--quality", "high"]
                r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True)
                if os.path.exists(out):
                    rel = os.path.relpath(out, VAULT)
                    return self._send(200, {"ok": True, "path": rel, "tema": req.get("tema", "claro")})
                return self._send(500, {"ok": False, "erro": (r.stderr or r.stdout or "falhou")[-400:]})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        return self._send(404, {"erro": "rota desconhecida"})


def main():
    if not os.path.isfile(DATA):
        sys.exit(f"ERRO: {DATA} não existe. Gere o editor.json primeiro.")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
        print(f"\n  ✎ SUPER EDITOR rodando em  http://localhost:{PORT}   (Ctrl+C pra parar)\n")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
