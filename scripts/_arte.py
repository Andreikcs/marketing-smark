#!/usr/bin/env python3
"""Composição da arte final e guarda no Postgres — o mesmo caminho no Mac e no Railway.

Isto existe pra apagar um passo manual. Antes, a arte só era composta no Mac e
empurrada à mão (`scripts/push_artes.py`); produção só sabia exibir o que já
tinha sido empurrado. Consequências: peça editada na tela não aparecia até alguém
rodar um script, e agendamento era impossível — às 9h da manhã não há ninguém
com o notebook aberto pra gerar a imagem.

Duas ideias sustentam o módulo:

1. **Um renderizador só.** O que o cliente aprova tem que ser byte a byte o que
   vai pro Instagram. Por isso servidor e script chamam esta mesma função, e não
   duas implementações parecidas que divergem com o tempo.

2. **Cache pelo conteúdo.** `arte_src_sha` é o sha256 do HTML que gerou a peça —
   muda sozinho quando qualquer coisa do frame muda (texto, fundo, cor, tema).
   `arte_sha` é o sha256 do JPEG resultante, que é a chave do blob e a URL
   pública. Se o HTML não mudou, não re-renderiza: compor custa ~5s de CPU.
"""
from __future__ import annotations

import hashlib
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import compositor  # noqa: E402

from PIL import Image  # noqa: E402

Image.MAX_IMAGE_PIXELS = None  # os fundos de IA passam do limite padrão do Pillow

BG_MAX = 1440       # lado maior do fundo web; acima disso o browser reescala à toa
BG_Q = 85
FINAL_Q = 92        # o final vai pro Instagram — não economiza aqui


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_arquivo(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def para_jpeg_web(path: str, lado_max: int = BG_MAX, q: int = BG_Q) -> tuple:
    """PNG grande → JPEG web. Devolve (bytes, w, h)."""
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    if max(im.size) > lado_max:
        im.thumbnail((lado_max, lado_max), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return buf.getvalue(), im.size[0], im.size[1]


def html_para_jpeg(html: str, w: int, h: int) -> tuple:
    """Renderiza o HTML e devolve (bytes JPEG, w, h) no tamanho nominal."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        png = tmp.name
    try:
        if not compositor.render_html_to_png(html, png, w, h):
            raise RuntimeError("Chrome headless falhou (sem navegador no servidor?)")
        im = Image.open(png).convert("RGB")
        # o Chrome renderiza em 2x pra ficar nítido; o Instagram recomprime
        # qualquer coisa acima de 1080 de largura. Reamostrar o 2x pra 1080
        # dá uma imagem mais limpa do que deixar a Meta reduzir.
        if im.size[0] > w:
            im = im.resize((w, h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=FINAL_Q, optimize=True, progressive=True)
        return buf.getvalue(), im.size[0], im.size[1]
    finally:
        try:
            os.unlink(png)
        except OSError:
            pass


def html_do_frame(post: dict, fr: dict) -> tuple:
    """Composição completa (fundo + texto + logo) no tamanho real. (html, w, h)."""
    marca = post.get("marca") or "smark"
    try:
        import _marcas
        _marcas.ensure_stub(marca)
    except Exception:
        pass
    # tardio de propósito: editor_server importa este módulo, então importar lá
    # em cima fecharia um ciclo
    from editor_server import frame_kwargs
    kw = frame_kwargs(fr, post.get("size") or "1080x1350", for_export=True, marca=marca)
    return compositor.compose_html(**kw)


def impressao_frame(post: dict, fr: dict) -> str:
    """Impressão digital barata do frame — muda quando a arte mudaria.

    Existe por um motivo de desempenho concreto. O jeito antigo de saber se a
    arte precisava re-renderizar era montar o HTML de exportação e tirar o sha
    dele. Só que o HTML de exportação embute o fundo em base64: são ~28 MB de
    string por frame. Com 69 frames, cada passada gastava ~10s de CPU e gerava
    ~2 GB de texto só pra descobrir que nada tinha mudado — e a passada roda a
    cada salvamento. No Mac isso passava batido; no container do Railway
    saturava o processador e travava todo o resto (prévia, galeria, comandos).

    Aqui usamos o HTML de PRÉVIA (~160 KB, ~1ms, sem base64) mais a identidade
    do fundo. Cobre a mesma superfície: texto, cores, tema, moldura e filtros
    entram no HTML; a troca de imagem entra pela identidade do fundo.
    """
    from editor_server import frame_kwargs
    marca = post.get("marca") or "smark"
    kw = frame_kwargs(fr, post.get("size") or "1080x1350", for_export=False, marca=marca)
    html, _, _ = compositor.compose_html(**kw)

    # Identidade do fundo: o sha do blob quando existe; senão caminho + mtime +
    # tamanho do arquivo local. Sem isto, trocar o PNG mantendo o nome não
    # invalidaria o cache.
    fundo = (fr.get("bg_sha") or "").strip().lower()
    if not fundo:
        rel = (fr.get("bg") or "").strip()
        if rel:
            caminho = os.path.join(VAULT, rel) if not os.path.isabs(rel) else rel
            try:
                st = os.stat(caminho)
                fundo = "%s:%d:%d" % (rel, int(st.st_mtime), st.st_size)
            except OSError:
                fundo = rel
    return sha256(("%s|%s|%s" % (html, fundo, post.get("size") or "")).encode("utf-8"))


def garantir_arte(post: dict, fr: dict, *, force: bool = False, origem: str = "auto") -> dict:
    """Garante que o frame tenha arte final publicável no Postgres.

    Escreve `arte_sha` e `arte_fp` no próprio frame (o chamador salva).
    Devolve {"ok", "sha", "novo", "motivo"} — `novo=False` quer dizer que o cache
    valeu e nada foi re-renderizado.
    """
    import _db

    atual = (fr.get("arte_sha") or "").strip()

    # Caminho barato: impressão digital bate → nada mudou, nem monta o HTML caro.
    fp = ""
    if not force and atual:
        try:
            fp = impressao_frame(post, fr)
        except Exception:
            fp = ""   # não conseguiu a via barata: cai no caminho antigo
        if fp and fr.get("arte_fp") == fp:
            try:
                if atual in _db.blob_existe([atual]):
                    return {"ok": True, "sha": atual, "novo": False, "motivo": "cache"}
            except Exception:
                # banco fora do ar não é motivo pra re-renderizar
                return {"ok": True, "sha": atual, "novo": False,
                        "motivo": "cache (banco off)"}

    try:
        html, w, h = html_do_frame(post, fr)
    except Exception as e:
        return {"ok": False, "sha": "", "novo": False, "motivo": "compose_html: %s" % e}

    src = sha256(html.encode("utf-8"))
    if not force and atual and fr.get("arte_src_sha") == src:
        # Peça de antes desta versão: o HTML caro confirma que nada mudou, então
        # só gravamos a impressão nova e a próxima passada já usa o atalho.
        # Isso evita re-renderizar 69 frames de uma vez logo após o deploy.
        if fp:
            fr["arte_fp"] = fp
        try:
            if atual in _db.blob_existe([atual]):
                return {"ok": True, "sha": atual, "novo": False, "motivo": "cache"}
        except Exception:
            return {"ok": True, "sha": atual, "novo": False, "motivo": "cache (banco off)"}

    try:
        dados, jw, jh = html_para_jpeg(html, w, h)
    except Exception as e:
        return {"ok": False, "sha": "", "novo": False, "motivo": str(e)}

    sha = sha256(dados)
    try:
        _db.blob_put(sha, dados, kind="final", w=jw, h=jh, origem=origem)
    except Exception as e:
        return {"ok": False, "sha": "", "novo": False, "motivo": "blob_put: %s" % e}

    fr["arte_sha"] = sha
    fr["arte_src_sha"] = src
    # a impressão só é confiável depois do render; recalcula caso o atalho não
    # tenha rodado (force=True, ou frame que ainda não tinha arte)
    try:
        fr["arte_fp"] = fp or impressao_frame(post, fr)
    except Exception:
        fr.pop("arte_fp", None)
    return {"ok": True, "sha": sha, "novo": True, "motivo": "renderizado"}


def garantir_post(post: dict, *, force: bool = False, origem: str = "auto") -> dict:
    """Garante a arte de todos os frames do post e define a capa.

    A capa é o frame 1: é o que a galeria e o portal do cliente mostram.
    """
    frames = post.get("frames") or []
    feitos, novos, erros = 0, 0, []
    for i, fr in enumerate(frames):
        r = garantir_arte(post, fr, force=force, origem=origem)
        if r["ok"]:
            feitos += 1
            novos += 1 if r["novo"] else 0
        else:
            erros.append("#%d %s" % (i + 1, r["motivo"]))
    if frames and (frames[0].get("arte_sha") or "").strip():
        post["arte_sha"] = frames[0]["arte_sha"]
    return {"ok": not erros, "frames": len(frames), "feitos": feitos,
            "novos": novos, "erros": erros}
