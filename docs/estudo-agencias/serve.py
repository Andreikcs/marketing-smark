#!/usr/bin/env python3
"""Servidor local do estudo de agências.

Existe por dois motivos que o `python3 -m http.server` não resolve:

1. Ele manda `Content-type: text/html` SEM charset, e `text/markdown` idem.
   O navegador então assume latin-1 e todo acento quebra. Aqui todo `text/*`
   sai com `; charset=utf-8`.
2. Markdown cru no navegador é ilegível. Aqui `.md` é renderizado em HTML
   com o mesmo visual do resto do material — mantendo o `.md` como fonte única.

Uso:  python3 serve.py [porta]     (padrão: 8791)
"""
import html
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

CSS = """
:root{--paper:#F4F1FA;--card:#fff;--ink:#17111F;--soft:#5A5268;--faint:#8B8399;
 --line:#E5DFF0;--violet-2:#8B3CF7;--code-bg:#F2EEFA;
 --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#120D1C;--card:#1B1428;--ink:#F3EFFA;
 --soft:#ABA1C0;--faint:#7A7091;--line:#2A2140;--violet-2:#B98CFF;--code-bg:#1E1630}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
 font-size:16.5px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto;padding:56px 24px 96px}
.back{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;
 color:var(--violet-2);text-decoration:none;font-weight:600;display:inline-block;margin-bottom:32px}
.back:hover{text-decoration:underline}
h1{font-size:clamp(28px,5vw,42px);font-weight:850;letter-spacing:-.03em;line-height:1.08;
 margin:0 0 26px;text-transform:uppercase}
h2{font-size:clamp(21px,3.2vw,28px);font-weight:820;letter-spacing:-.02em;
 margin:52px 0 16px;padding-top:22px;border-top:1px solid var(--line)}
h3{font-size:18.5px;font-weight:780;margin:32px 0 12px}
p{margin:0 0 16px}
a{color:var(--violet-2)}
strong{font-weight:750}
hr{border:none;border-top:1px solid var(--line);margin:40px 0}
ul,ol{margin:0 0 18px;padding-left:22px}
li{margin-bottom:7px}
blockquote{margin:22px 0;padding:14px 22px;border-left:3px solid var(--violet-2);
 background:var(--card);border-radius:0 10px 10px 0;color:var(--soft)}
blockquote p:last-child{margin-bottom:0}
code{font-family:var(--mono);font-size:.88em;background:var(--code-bg);
 padding:2px 6px;border-radius:5px}
pre{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:20px 22px;overflow-x:auto;margin:0 0 22px}
pre code{background:none;padding:0;font-size:13.5px;line-height:1.55}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
 border-radius:12px;overflow:hidden;margin:0 0 24px;font-size:15px;display:table}
th,td{padding:12px 15px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--line);font-family:var(--mono);font-size:11px;letter-spacing:.09em;
 text-transform:uppercase;color:var(--soft);font-weight:700}
tbody tr:last-child td{border-bottom:none}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
"""

_INLINE = (
    (re.compile(r"`([^`]+)`"), lambda m: f"<code>{m.group(1)}</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), lambda m: f"<strong>{m.group(1)}</strong>"),
    (re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)"), lambda m: f"<em>{m.group(1)}</em>"),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>'),
)


def inline(txt):
    """Escapa HTML e aplica marcação inline. Código vem primeiro para não ser reprocessado."""
    out = html.escape(txt, quote=False)
    for pat, rep in _INLINE:
        out = pat.sub(rep, out)
    return out


def _linha_tabela(linha):
    celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
    return celulas


def md_para_html(md):
    linhas = md.split("\n")
    out, i = [], 0
    n = len(linhas)

    while i < n:
        ln = linhas[i]

        # bloco de código
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < n and not linhas[i].startswith("```"):
                buf.append(html.escape(linhas[i], quote=False))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        # front matter / separador
        if ln.strip() == "---" and i != 0:
            out.append("<hr>")
            i += 1
            continue

        # tabela: linha com | seguida de separadora
        if ln.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", linhas[i + 1]):
            cab = _linha_tabela(ln)
            i += 2
            corpo = []
            while i < n and linhas[i].strip().startswith("|"):
                corpo.append(_linha_tabela(linhas[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in cab)
            trs = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in linha) + "</tr>"
                for linha in corpo
            )
            out.append(f'<div class="scroll"><table><thead><tr>{th}</tr></thead>'
                       f"<tbody>{trs}</tbody></table></div>")
            continue

        # títulos
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            nivel = len(m.group(1))
            out.append(f"<h{nivel}>{inline(m.group(2))}</h{nivel}>")
            i += 1
            continue

        # citação
        if ln.startswith(">"):
            buf = []
            while i < n and linhas[i].startswith(">"):
                buf.append(linhas[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(buf)) + "</p></blockquote>")
            continue

        # listas
        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            ordenada = bool(re.match(r"^\s*\d+\.\s+", ln))
            tag = "ol" if ordenada else "ul"
            itens = []
            while i < n and (re.match(r"^\s*[-*]\s+", linhas[i]) or re.match(r"^\s*\d+\.\s+", linhas[i])):
                txt = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", linhas[i])
                i += 1
                # continuação indentada da mesma entrada
                while i < n and linhas[i].startswith("  ") and linhas[i].strip() \
                        and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", linhas[i]):
                    txt += " " + linhas[i].strip()
                    i += 1
                itens.append(f"<li>{inline(txt)}</li>")
            out.append(f"<{tag}>" + "".join(itens) + f"</{tag}>")
            continue

        # parágrafo
        if ln.strip():
            buf = [ln.strip()]
            i += 1
            while i < n and linhas[i].strip() and not re.match(
                    r"^(#{1,4}\s|```|>|\s*[-*]\s|\s*\d+\.\s|\|)", linhas[i]) \
                    and linhas[i].strip() != "---":
                buf.append(linhas[i].strip())
                i += 1
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
            continue

        i += 1

    return "\n".join(out)


def pagina(titulo, corpo):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>{CSS}</style>
</head>
<body><div class="wrap"><a class="back" href="/">← voltar ao índice</a>
{corpo}
</div></body>
</html>
"""


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # nada de latin-1: todo texto sai declarado como utf-8
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        tipo = super().guess_type(path)
        base = tipo.split(";")[0].strip()
        if base.startswith("text/") or base in ("application/javascript", "application/json"):
            return f"{base}; charset=utf-8"
        return tipo

    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho.endswith(".md"):
            alvo = (RAIZ / caminho.lstrip("/")).resolve()
            if RAIZ in alvo.parents and alvo.is_file():
                md = alvo.read_text(encoding="utf-8")
                # remove front matter YAML antes de renderizar
                if md.startswith("---\n"):
                    fim = md.find("\n---", 4)
                    if fim != -1:
                        md = md[fim + 4:]
                titulo = next((l.lstrip("# ").strip() for l in md.split("\n")
                               if l.startswith("# ")), alvo.stem)
                corpo = pagina(titulo, md_para_html(md)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return
        super().do_GET()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8791
    handler = partial(Handler, directory=str(RAIZ))
    print(f"estudo de agências em http://localhost:{porta}  (ctrl+c para parar)")
    ThreadingHTTPServer(("127.0.0.1", porta), handler).serve_forever()
