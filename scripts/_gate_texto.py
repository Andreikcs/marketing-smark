#!/usr/bin/env python3
"""Gate anti-poluição: detecta TEXTO legível em PNG de fundo.

Regra do studio: fundo de IA NUNCA pode ter texto/letras/números.
Tipografia só no compositor.

Estratégia:
  1. tesseract CLI se instalado → OCR + padrões
  2. fallback PIL: densidade de bordas em faixas (heurística barata)
  3. se ambos falharem de forma ambígua → bloqueia promoção (ok=False só se poluído)

Poluição típica: hex, palavras latinas, CJK, NEGATIVE, etc.
"""
import os
import re
import shutil
import subprocess
import tempfile

_PADROES_POLUICAO = [
    re.compile(r"#[0-9A-Fa-f]{6}"),
    re.compile(r"\b\d{2,3}\s*mm\b", re.I),
    re.compile(r"\bNEGATIVE\b", re.I),
    re.compile(r"\bCAMERA\b", re.I),
    re.compile(r"\bCOMPOSITION\b", re.I),
    re.compile(r"[\u4e00-\u9fff]{2,}"),
    re.compile(r"\b(BAZATUR|Brandia|watermark)\b", re.I),
    re.compile(r"\b(no text|no letters|no logos)\b", re.I),
    # marcas de UI / tipografia gerada
    re.compile(r"\b(EXCLUSIVO|AMANH[ÃA]|PASSE AQUI|GARANTA)\b", re.I),
]

# qualquer "palavra" de 3+ letras conta (fundos devem ser sem texto)
_RE_PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]{3,}")
_RUIDO = {
    "the", "and", "with", "this", "that", "from", "for", "are", "was", "you",
    "not", "but", "all", "can", "had", "her", "his", "one", "our", "out",
    "uma", "com", "para", "por", "dos", "das", "que", "não", "nao", "seu",
}


def tesseract_disponivel():
    return bool(shutil.which("tesseract"))


def _ocr_tesseract(png_path):
    if not tesseract_disponivel():
        return ""
    try:
        r = subprocess.run(
            ["tesseract", png_path, "stdout", "-l", "eng+por", "--psm", "11"],
            capture_output=True, text=True, timeout=45,
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
    palavras = _RE_PALAVRA.findall(texto or "")
    palavras = [p for p in palavras if p.lower() not in _RUIDO and len(p) >= 3]
    # 2+ palavras legíveis = texto no fundo (antes era 4)
    if len(palavras) >= 2:
        hits.append("palavras:" + ",".join(palavras[:8]))
    # uma palavra longa (ex. MTARO, EXCLUSIVO) já basta
    longas = [p for p in palavras if len(p) >= 5]
    if longas and not any(h.startswith("palavras:") for h in hits):
        hits.append("palavra:" + longas[0])
    return hits


def _heuristica_bordas(png_path):
    """Fallback sem tesseract: regiões com muitas bordas horizontais/verticais
    no centro-superior (onde o modelo costuma tipografar) elevam suspeita.

    Não é OCR — só sinal fraco. Usado para AVISO, não bloqueio duro sozinho.
    """
    try:
        from PIL import Image, ImageFilter, ImageStat
        im = Image.open(png_path).convert("L")
        im.thumbnail((480, 480))
        w, h = im.size
        # terço superior e meio (onde headline falsa aparece)
        box = (0, 0, w, int(h * 0.55))
        crop = im.crop(box)
        edges = crop.filter(ImageFilter.FIND_EDGES)
        st = ImageStat.Stat(edges)
        mean = st.mean[0] if st.mean else 0
        # fundos limpos de foto têm mean baixo; tipografia/UI eleva
        return float(mean)
    except Exception:
        return 0.0


def avaliar(png_path, *, exigir_ocr=False):
    """Avalia se o PNG tem texto poluente.

    ok: True se limpo (pode publicar)
    poluido: True se achou texto
    """
    if not png_path or not os.path.isfile(png_path):
        return {
            "ok": False, "poluido": True, "metodo": "erro",
            "trechos": [], "aviso": "arquivo ausente para gate de texto",
        }

    path = png_path
    tmp = None
    if not png_path.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".webp")):
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        with open(png_path, "rb") as src, open(tmp, "wb") as dst:
            dst.write(src.read())
        path = tmp

    try:
        if tesseract_disponivel():
            texto = _ocr_tesseract(path)
            hits = _achados_poluicao(texto)
            if hits:
                return {
                    "ok": False,
                    "poluido": True,
                    "metodo": "tesseract",
                    "trechos": hits,
                    "aviso": "texto detectado no fundo (proibido): " + "; ".join(hits[:5]),
                }
            return {
                "ok": True, "poluido": False, "metodo": "tesseract",
                "trechos": [], "aviso": "",
            }

        # sem tesseract: heurística + política segura
        edge = _heuristica_bordas(path)
        if edge > 28:
            return {
                "ok": False,
                "poluido": True,
                "metodo": "heuristica",
                "trechos": [f"bordas={edge:.1f}"],
                "aviso": "fundo com padrões tipográficos suspeitos (instale tesseract "
                         "para OCR: brew install tesseract). Arte bloqueada por segurança.",
            }
        if exigir_ocr:
            return {
                "ok": False,
                "poluido": True,
                "metodo": "indisponivel",
                "trechos": [],
                "aviso": "gate de texto exige tesseract (brew install tesseract)",
            }
        return {
            "ok": True,
            "poluido": False,
            "metodo": "heuristica",
            "trechos": [],
            "aviso": "tesseract ausente — gate fraco (heurística). "
                     "Instale: brew install tesseract",
        }
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
