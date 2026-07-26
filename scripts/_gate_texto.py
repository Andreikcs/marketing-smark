#!/usr/bin/env python3
"""Gate anti-poluição: detecta texto legível em um PNG de fundo.

Seedream (e outros) às vezes tipografam o prompt na arte. Este módulo decide
se o rascunho pode ser mostrado / promovido.

Estratégia (stdlib + binários do sistema, sem pip novo):
  1. tesseract CLI se instalado (`brew install tesseract`)
  2. senão: gate "indisponível" — não bloqueia, mas marca para revisão humana

Padrões de poluição típicos do bake-off Seedream: hex (#9A4DFF), 85mm, CJK, etc.
"""
import os
import re
import shutil
import subprocess
import tempfile

# Sinais fortes de "prompt impresso na arte" (bake-off 2026-07-24)
_PADROES_POLUICAO = [
    re.compile(r"#[0-9A-Fa-f]{6}"),           # hex de paleta
    re.compile(r"\b\d{2,3}\s*mm\b", re.I),  # 85mm
    re.compile(r"\bNEGATIVE\b", re.I),
    re.compile(r"\bCAMERA\b", re.I),
    re.compile(r"\bCOMPOSITION\b", re.I),
    re.compile(r"[\u4e00-\u9fff]{2,}"),       # CJK (ex. 時裝)
    re.compile(r"\b(BAZATUR|Brandia|watermark)\b", re.I),
    re.compile(r"\b(no text|no letters|no logos)\b", re.I),
]

# OCR devolve lixo residual; exige tamanho mínimo de "palavra" alfanumérica
_RE_PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]{4,}")


def tesseract_disponivel():
    return bool(shutil.which("tesseract"))


def _ocr_tesseract(png_path):
    """Devolve texto OCR ou '' se falhar."""
    if not tesseract_disponivel():
        return ""
    try:
        # imagem pode ser enorme (4K); tesseract aguenta, mas limitamos timeout
        r = subprocess.run(
            ["tesseract", png_path, "stdout", "-l", "eng+por", "--psm", "11"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return ""
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _achados_poluicao(texto):
    hits = []
    for pat in _PADROES_POLUICAO:
        m = pat.search(texto or "")
        if m:
            hits.append(m.group(0)[:40])
    # muitas palavras latinas em fundo "abstrato" também suspeito
    palavras = _RE_PALAVRA.findall(texto or "")
    # filtra lixo OCR comum
    ruido = {"the", "and", "with", "this", "that", "from", "for", "are", "was"}
    palavras = [p for p in palavras if p.lower() not in ruido]
    if len(palavras) >= 4:
        hits.append("palavras:" + ",".join(palavras[:6]))
    return hits


def avaliar(png_path):
    """Avalia se o PNG tem texto poluente.

    Retorna dict:
      ok: bool — True se pode seguir (limpo OU gate indisponível)
      poluido: bool — True se OCR/padrões acharam texto de briefing
      metodo: 'tesseract' | 'indisponivel'
      trechos: list[str]
      aviso: str
    """
    if not png_path or not os.path.isfile(png_path):
        return {
            "ok": False, "poluido": True, "metodo": "erro",
            "trechos": [], "aviso": "arquivo ausente para gate de texto",
        }

    if not tesseract_disponivel():
        return {
            "ok": True,  # não bloqueia o pipeline se OCR não está instalado
            "poluido": False,
            "metodo": "indisponivel",
            "trechos": [],
            "aviso": "tesseract não instalado — gate de texto pulado "
                     "(brew install tesseract). Revise o rascunho visualmente "
                     "antes de promover a final.",
        }

    # tesseract prefere path com extensão legível; se for tmp sem .png, copia
    path = png_path
    tmp = None
    if not png_path.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".webp")):
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        with open(png_path, "rb") as src, open(tmp, "wb") as dst:
            dst.write(src.read())
        path = tmp

    try:
        texto = _ocr_tesseract(path)
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

    hits = _achados_poluicao(texto)
    if hits:
        return {
            "ok": False,
            "poluido": True,
            "metodo": "tesseract",
            "trechos": hits,
            "aviso": "texto detectado no fundo (possível prompt impresso): "
                     + "; ".join(hits[:5]),
        }
    return {
        "ok": True,
        "poluido": False,
        "metodo": "tesseract",
        "trechos": [],
        "aviso": "",
    }
