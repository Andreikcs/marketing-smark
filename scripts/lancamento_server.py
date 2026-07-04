#!/usr/bin/env python3
"""EDITOR DE LANÇAMENTO — servidor local (sem nuvem) pra montar o storyboard e salvar EM DISCO.

Fluxo:  storyboard sequencial (img1 → img2 → …)  ·  reordena arrastando  ·  navega quadro a quadro
        ·  edita frase/legenda  ·  re-renderiza na hora (placeholder, GRÁTIS)  ·  status (aprovar/ajustar)
        ·  SALVA em lancamento.json  ·  "Gerar oficiais" roda o fundo de IA real SÓ nas aprovadas.

Rodar:  python3 scripts/lancamento_server.py   →   abre http://localhost:8765
Parar:  Ctrl+C
"""
import http.server
import json
import os
import socketserver
import subprocess
import sys
import urllib.parse
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lancamento as L  # noqa: E402

VAULT = L.VAULT
HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8765
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".json": "application/json", ".html": "text/html; charset=utf-8"}


def norm_headline(h):
    """Textarea (quebras reais ou '|') -> convenção '|' de uma linha por frase."""
    h = (h or "").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "|")
    return "|".join(p.strip() for p in h.split("|") if p.strip())


def prompt_oficial(marca, rec):
    """Prompt de fundo nível agência via direção de arte (conceito por tipo + composição guiada)."""
    import _direcao
    return _direcao.construir(marca, rec.get("tipo", ""), rec.get("tema", "escuro"), rec.get("headline", ""))


def gerar_oficial(marca, rec):
    """PAGO: gera fundo de IA real e recompõe a arte final no mesmo slot da vitrine."""
    tmp = f"/tmp/lanc_bg_{marca}_{rec['n']:02d}.png"
    size = "1024x1536" if rec.get("formato", "feed") != "quadrado" else "1024x1024"
    r = subprocess.run(["python3", os.path.join(VAULT, "scripts", "openai_image.py"),
                        "--out", tmp, "--prompt", prompt_oficial(marca, rec), "--size", size,
                        "--marca", marca, "--paleta", "roxo", "--headline", rec["headline"].replace("|", " ")],
                       cwd=VAULT, capture_output=True, text=True)
    if not os.path.exists(tmp):
        return {"ok": False, "erro": (r.stderr or r.stdout or "falha na geração")[-400:]}
    dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram", "arte", "_lancamento")
    png = os.path.join(dd, f"{rec['n']:02d}.png")
    args = ["python3", L.COMPO, "--marca", marca, "--out", png, "--bg", tmp, "--tema", rec["tema"],
            "--headline", rec["headline"].replace("|", "\\n"), "--sub", rec.get("sub", "")]
    if rec.get("cta"):
        args += ["--cta", rec["cta"]]
    subprocess.run(args, cwd=VAULT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["status"] = "gerado"
    rec["thumb"] = os.path.relpath(png, VAULT)
    return {"ok": True, "thumb": rec["thumb"]}


def find_rec(d, marca, n):
    for rec in d["marcas"].get(marca, {}).get("recs", []):
        if rec["n"] == n:
            return rec
    return None


class Handler(http.server.BaseHTTPRequestHandler):
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

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/editor"):
            fp = os.path.join(HERE, "_editor.html")
            return self._send(200, open(fp, encoding="utf-8").read(), "text/html; charset=utf-8")
        if path == "/dados":
            return self._send(200, L.load())
        # módulos (servidos como porta única, menu compartilhado)
        if path in ("/painel", "/vitrine"):
            arq = "painel.html" if path == "/painel" else "lancamento.html"
            fp = os.path.join(VAULT, arq)
            if not os.path.isfile(fp):
                return self._send(200, f"<h2 style='font-family:sans-serif'>Gere primeiro: "
                                  f"<code>python3 scripts/{'painel' if path=='/painel' else 'lancamento'}.py</code></h2>",
                                  "text/html; charset=utf-8")
            return self._send(200, open(fp, encoding="utf-8").read(), "text/html; charset=utf-8")
        # arquivo estático dentro do vault (imagens das artes)
        rel = urllib.parse.unquote(path.lstrip("/"))
        full = os.path.realpath(os.path.join(VAULT, rel))
        if not full.startswith(VAULT) or not os.path.isfile(full):
            return self._send(404, {"erro": "não encontrado"})
        ext = os.path.splitext(full)[1].lower()
        with open(full, "rb") as f:
            data = f.read()
        return self._send(200, data, MIME.get(ext, "application/octet-stream"))

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            req = self._body()
        except Exception as e:
            return self._send(400, {"ok": False, "erro": str(e)})

        if path == "/salvar":
            d = L.load()
            rec = find_rec(d, req.get("marca"), req.get("n"))
            if not rec:
                return self._send(404, {"ok": False, "erro": "arte não encontrada"})
            antes = (rec.get("headline"), rec.get("sub"), rec.get("cta"))
            rec["headline"] = norm_headline(req.get("headline", rec.get("headline", "")))
            rec["sub"] = req.get("sub", rec.get("sub", "")).strip()
            rec["cta"] = req.get("cta", rec.get("cta", "")).strip()
            rec["caption"] = req.get("caption", rec.get("caption", ""))
            if req.get("status"):
                rec["status"] = req["status"]
            mudou_arte = (rec["headline"], rec["sub"], rec["cta"]) != antes
            if req.get("rerender") or mudou_arte:
                L.render_one(req["marca"], rec)
            L.save(d)
            L.build_html(d)  # mantém a vitrine read-only em sincronia
            return self._send(200, {"ok": True, "thumb": rec["thumb"], "status": rec["status"],
                                    "rerender": bool(req.get("rerender") or mudou_arte)})

        if path == "/status":
            d = L.load()
            rec = find_rec(d, req.get("marca"), req.get("n"))
            if not rec:
                return self._send(404, {"ok": False, "erro": "arte não encontrada"})
            rec["status"] = req.get("status", rec["status"])
            L.save(d)
            L.build_html(d)
            return self._send(200, {"ok": True, "status": rec["status"]})

        if path == "/ordem":
            d = L.load()
            marca = req.get("marca")
            recs = d["marcas"].get(marca, {}).get("recs", [])
            by_n = {r["n"]: r for r in recs}
            nova = [by_n[n] for n in req.get("ordem", []) if n in by_n]
            for r in recs:  # segurança: não perder nenhum
                if r not in nova:
                    nova.append(r)
            d["marcas"][marca]["recs"] = nova
            L.save(d)
            L.build_html(d)
            return self._send(200, {"ok": True, "ordem": [r["n"] for r in nova]})

        if path == "/gerar":
            d = L.load()
            marca = req.get("marca")
            alvo = [r for r in d["marcas"].get(marca, {}).get("recs", []) if r["status"] == "aprovado"]
            if not alvo:
                return self._send(200, {"ok": True, "feitas": [], "msg": "nenhuma arte aprovada nessa marca"})
            feitas, falhas = [], []
            for rec in alvo:
                res = gerar_oficial(marca, rec)
                (feitas if res["ok"] else falhas).append({"n": rec["n"], **res})
                L.save(d)
            L.build_html(d)
            return self._send(200, {"ok": True, "feitas": feitas, "falhas": falhas})

        return self._send(404, {"erro": "rota desconhecida"})


def main():
    d = L.load()
    faltando = [True for info in d["marcas"].values() for r in info["recs"] if not r.get("thumb")]
    if faltando:
        print("Renderizando artes que faltam (placeholder, sem API)...")
        L.render_all(d)
        L.save(d)
        L.build_html(d)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n  ✎ Editor de Lançamento (storyboard) rodando em  {url}")
        print("    arraste pra reordenar · navegue quadro a quadro · edite · salve · gere oficiais.  (Ctrl+C pra parar)\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  servidor encerrado.")


if __name__ == "__main__":
    main()
