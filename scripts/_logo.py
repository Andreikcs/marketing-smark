#!/usr/bin/env python3
"""Interpreta a logo do cliente e devolve um brasão PNG limpo — uma vez só.

Por que este módulo existe
--------------------------
Antes, a logo era *reinterpretada a cada composição*: abrir o arquivo, tirar o
fundo branco pixel a pixel em Python puro, achar o recorte quadrado, montar a
máscara e codificar em base64. Isso custava ~465ms por chamada, e `compose_html`
chama duas ou três vezes (tab, chip, rodapé). Multiplicado pelos 69 frames que a
passada de arte percorre, virava minuto de CPU — no Mac passava despercebido, no
container do Railway travava o servidor inteiro.

A ideia aqui é simples: **interpretar uma vez, guardar o PNG, reusar sempre**.

- `normalizar()` roda no *upload* da logo. Aceita PNG, JPG, WEBP e SVG, entende
  onde está a marca, tira o fundo branco/off-white e grava um PNG RGBA com
  transparência de verdade. É esse PNG que o resto do sistema aplica.
- `icone_rgba()` e as variantes ficam atrás de cache em memória com chave
  (arquivo, mtime, tamanho) — mexeu no arquivo, o cache cai sozinho.

SVG não precisa de dependência nova: o Chromium já está na imagem por causa do
compositor, então rasterizamos com ele. Uma dependência a menos pra quebrar no
deploy.
"""
from __future__ import annotations

import base64
import io
import os
import secrets
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)

# Lado do brasão normalizado. 512 é suficiente pro maior uso real (tab a 2x em
# 128px) e mantém o PNG na casa das dezenas de KB.
LADO_BRASAO = 512

# Acima disso a logo é reduzida ANTES de qualquer análise. Cliente manda PNG de
# 4000px direto do designer; analisar 16 milhões de pixels pra decidir um ícone
# de 64px é desperdício puro.
LADO_ANALISE = 1024

_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_MAX = 96


def _chrome():
    """Binário do Chromium — o mesmo que o compositor usa."""
    import compositor
    return compositor.CHROME


def _flags():
    import compositor
    return list(getattr(compositor, "_FLAGS_CONTAINER", []))


def _chave(path, *extra):
    """Identidade do arquivo pro cache: caminho + mtime + tamanho."""
    try:
        st = os.stat(path)
        return (os.path.abspath(path), int(st.st_mtime), st.st_size) + tuple(extra)
    except OSError:
        return (os.path.abspath(path), 0, 0) + tuple(extra)


def _memo(chave, produzir):
    """Cache simples com teto. Guarda inclusive o None (logo que não dá brasão).

    Guardar o negativo importa: sem isso, uma logo que o interpretador recusa
    seria reprocessada em toda composição — exatamente o custo que queremos matar.
    """
    with _CACHE_LOCK:
        if chave in _CACHE:
            return _CACHE[chave]
    valor = produzir()
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.clear()
        _CACHE[chave] = valor
    return valor


def limpar_cache():
    """Esquece tudo — chamado quando a marca troca de logo."""
    with _CACHE_LOCK:
        _CACHE.clear()


# ---------------------------------------------------------------- SVG → PNG

def svg_para_png(svg_bytes: bytes, lado: int = LADO_BRASAO) -> bytes:
    """Rasteriza SVG com o Chromium headless, em cima de fundo transparente.

    Sem isto, logo em SVG caía no monograma (a letra) porque o Pillow não abre
    SVG — o cliente subia a marca dele e via um "M" genérico na arte.
    """
    texto = svg_bytes.decode("utf-8", errors="replace")
    if "<script" in texto.lower():
        raise ValueError("SVG com <script> recusado")
    pagina = (
        "<!doctype html><html><head><meta charset=utf-8><style>"
        "html,body{margin:0;padding:0;background:transparent}"
        f"body{{width:{lado}px;height:{lado}px;display:flex;align-items:center;"
        "justify-content:center;overflow:hidden}"
        "svg,img{max-width:100%;max-height:100%;display:block}"
        "</style></head><body>" + texto + "</body></html>"
    )
    tag = "%s.%s" % (os.getpid(), secrets.token_hex(4))
    html_path = os.path.join(tempfile.gettempdir(), "smark-logo-%s.html" % tag)
    png_path = os.path.join(tempfile.gettempdir(), "smark-logo-%s.png" % tag)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(pagina)
    try:
        subprocess.run(
            [_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
             *_flags(),
             # sem isto o screenshot vem com fundo branco chapado e a
             # transparência do SVG se perde
             "--default-background-color=00000000",
             "--force-device-scale-factor=2",
             "--window-size=%d,%d" % (lado, lado),
             "--virtual-time-budget=3000",
             "--screenshot=%s" % png_path,
             "file://%s" % html_path],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=45)
    except subprocess.TimeoutExpired as e:
        raise ValueError("Chromium travou ao rasterizar o SVG") from e
    finally:
        try:
            os.remove(html_path)
        except OSError:
            pass
    try:
        if not os.path.isfile(png_path) or os.path.getsize(png_path) == 0:
            raise ValueError("Chromium não gerou PNG a partir do SVG")
        with open(png_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(png_path)
        except OSError:
            pass


# ------------------------------------------------------- limpeza de fundo

def _tirar_fundo_claro(im):
    """Zera o alpha de branco e off-white — em C, não em laço Python.

    O laço equivalente (`for r,g,b,a in im.getdata()`) era o que fazia uma logo
    de 1080² custar centenas de milissegundos. Aqui a mesma regra vira três
    operações de canal do Pillow, que rodam em C:

      claro = (min(r,g,b) > 220) e (max-min < 18)   → cinza quase branco
      branco = r,g,b todos > 235                    → branco puro

    Pixel que casar vira transparente; o resto mantém o alpha original.
    """
    from PIL import Image, ImageChops
    r, g, b, a = im.split()
    # max e min por pixel entre os três canais
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    sat = ImageChops.difference(mx, mn)            # max - min (nunca negativo)

    branco = mn.point(lambda p: 255 if p > 235 else 0)
    quase = ImageChops.multiply(
        mn.point(lambda p: 255 if p > 220 else 0),
        sat.point(lambda p: 255 if p < 18 else 0),
    )
    fundo = ImageChops.lighter(branco, quase)      # união das duas regras
    manter = fundo.point(lambda p: 0 if p else 255)
    novo_a = ImageChops.multiply(a, manter)
    return Image.merge("RGBA", (r, g, b, novo_a))


def _recorte_quadrado(im):
    """Wordmark largo → janela quadrada com mais tinta (o brasão costuma abrir).

    A varredura é feita numa miniatura: a posição do recorte não muda por causa
    de resolução, e escanear 128px em vez de 4000px é ordens de grandeza mais
    barato.
    """
    from PIL import Image
    w, h = im.size
    if h <= 0:
        return im
    ratio = w / float(h)
    if ratio > 1.35:
        lado = h
        escala = min(1.0, 128.0 / max(1, h))
        pq = im.convert("L").resize(
            (max(1, int(w * escala)), max(1, int(h * escala))),
            Image.Resampling.NEAREST)
        pw, ph = pq.size
        janela = max(1, int(round(lado * escala)))
        melhor_x, melhor = 0, -1
        passo = max(1, janela // 8)
        for x in range(0, max(1, pw - janela + 1), passo):
            hist = pq.crop((x, 0, min(x + janela, pw), ph)).histogram()
            tinta = sum(hist[:128])
            if tinta > melhor:
                melhor, melhor_x = tinta, x
        x0 = min(max(0, int(melhor_x / escala)), max(0, w - lado))
        return im.crop((x0, 0, x0 + lado, h))
    if ratio < 0.75:
        lado = w
        y = max(0, (h - lado) // 4)
        return im.crop((0, y, lado, y + lado))
    return im


def interpretar(dados: bytes, ext: str = "") -> "object":
    """bytes de qualquer formato → PIL RGBA já limpo e recortado, ou None.

    É aqui que mora a "interpretação": descobrir se o arquivo é mesmo uma marca
    (e não uma foto que o cliente arrastou por engano), tirar o canvas branco,
    aparar as sobras e isolar o brasão.
    """
    from PIL import Image

    ext = (ext or "").lower()
    if ext == ".svg" or dados[:400].lstrip()[:5].lower() in (b"<svg ", b"<?xml"):
        dados = svg_para_png(dados)

    im = Image.open(io.BytesIO(dados))
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    # reduz ANTES de analisar: nada aqui precisa de 4000px
    if max(im.size) > LADO_ANALISE:
        im.thumbnail((LADO_ANALISE, LADO_ANALISE), Image.Resampling.LANCZOS)

    if im.split()[-1].getextrema()[0] > 200:   # sem transparência real
        im = _tirar_fundo_claro(im)

    caixa = im.getbbox()
    if caixa:
        im = im.crop(caixa)
    w, h = im.size
    if w < 8 or h < 8:
        return None

    # Foto de feed disfarçada de logo: grande, opaca e quase quadrada. Melhor o
    # monograma do que espremer uma foto no lugar do brasão.
    if max(w, h) >= 900 and im.split()[-1].getextrema()[0] > 200 \
            and 0.72 <= (w / float(h)) <= 1.35:
        return None

    return _recorte_quadrado(im)


def normalizar(dados: bytes, ext: str = "", lado: int = LADO_BRASAO) -> bytes:
    """Entrada de qualquer formato → PNG RGBA quadrado, pronto pra aplicar.

    Devolve os bytes do PNG. Levanta ValueError quando o arquivo não dá brasão —
    o chamador decide se cai no monograma ou avisa o usuário.
    """
    from PIL import Image
    im = interpretar(dados, ext)
    if im is None:
        raise ValueError("não deu pra interpretar um brasão nesse arquivo "
                         "(parece foto ou imagem sem marca isolável)")
    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    copia = im.copy()
    copia.thumbnail((lado, lado), Image.Resampling.LANCZOS)
    canvas.paste(copia, ((lado - copia.size[0]) // 2,
                         (lado - copia.size[1]) // 2), copia)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ------------------------------------------------------- uso na composição

def icone_rgba(path: str):
    """PIL RGBA do brasão, com cache por (arquivo, mtime, tamanho)."""
    if not path or not os.path.isfile(path):
        return None

    def produzir():
        try:
            with open(path, "rb") as f:
                dados = f.read()
            return interpretar(dados, os.path.splitext(path)[1])
        except Exception as e:
            print("  logo: %s não virou brasão (%s)" % (path, e), file=sys.stderr)
            return None

    return _memo(_chave(path, "icone"), produzir)


def badge_png_b64(path: str, color: str = "#FFFFFF", px: int = 64,
                  pad_ratio: float = 0.12):
    """Brasão monocromático na cor alvo, base64 de PNG. Cacheado."""

    def produzir():
        from PIL import Image, ImageChops, ImageFilter, ImageOps
        im = icone_rgba(path)
        if im is None:
            return None
        if (color or "").startswith("#") and len(color) >= 7:
            r, g, b = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        else:
            r, g, b = 255, 255, 255

        alpha = im.split()[-1]
        cinza = ImageOps.grayscale(im.convert("RGB"))

        # A tinta é escura ou clara? Antes isso vinha de um zip() sobre todos os
        # pixels; o histograma do Pillow dá a mesma resposta em C. Só contam
        # pixels com alpha real — o resto é fundo já removido.
        visivel = alpha.point(lambda p: 255 if p > 24 else 0)
        hist = cinza.histogram(mask=visivel)
        tinta_escura = sum(hist[:110]) >= sum(hist[160:])

        if tinta_escura:
            mask = cinza.point(
                lambda p: 255 if p < 175 else max(0, int((200 - p) * 3.5)))
        else:
            mask = cinza.point(
                lambda p: 255 if p > 80 else max(0, int((p - 20) * 3.0)))
        mask = ImageChops.multiply(mask, alpha.point(lambda p: 255 if p else 0))
        try:
            mask = mask.filter(ImageFilter.MaxFilter(3))
        except Exception:
            pass
        mask = mask.point(lambda p: 255 if p >= 90 else (int(p * 1.4) if p > 40 else 0))

        badge = Image.new("RGBA", im.size, (r, g, b, 0))
        badge.putalpha(mask)
        return _encaixar_b64(badge, px, pad_ratio)

    return _memo(_chave(path, "badge", color, px, pad_ratio), produzir)


def color_png_b64(path: str, px: int = 64, pad_ratio: float = 0.14):
    """Brasão com as cores originais, base64 de PNG. Cacheado."""

    def produzir():
        im = icone_rgba(path)
        if im is None:
            return None
        return _encaixar_b64(im.copy(), px, pad_ratio)

    return _memo(_chave(path, "color", px, pad_ratio), produzir)


def _encaixar_b64(im, px, pad_ratio):
    """Centraliza num canvas quadrado 2x e devolve base64 do PNG."""
    from PIL import Image
    lado = px * 2
    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    pad = int(lado * pad_ratio)
    interno = max(1, lado - pad * 2)
    im.thumbnail((interno, interno), Image.Resampling.LANCZOS)
    canvas.paste(im, ((lado - im.size[0]) // 2, (lado - im.size[1]) // 2), im)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: _logo.py <arquivo> [saida.png]", file=sys.stderr)
        raise SystemExit(2)
    sys.path.insert(0, HERE)
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else "brasao.png"
    with open(entrada, "rb") as f:
        bruto = f.read()
    png = normalizar(bruto, os.path.splitext(entrada)[1])
    with open(saida, "wb") as f:
        f.write(png)
    print("brasão gravado em %s (%d KB)" % (saida, len(png) // 1024))
