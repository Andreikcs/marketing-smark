#!/usr/bin/env python3
"""Única peça que fala HTTP com fornecedor de imagem.

Dois backends atrás da mesma interface:
  - openrouter → POST /api/v1/images  (seed, resolution, aspect_ratio, input_references, custo)
  - openai     → POST /v1/images/generations (size, quality; sem seed, sem custo na resposta)

Também normaliza a saída pra PNG: a MESMA chamada ao gemini-3-pro-image devolveu
image/jpeg numa execução e image/png na outra, e a regra 6 do CLAUDE.md exige .png.

Nenhuma decisão de modelo ou estética mora aqui — isso é do _perfil.py."""
import base64
import binascii
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

URL_OPENROUTER = "https://openrouter.ai/api/v1/images"
URL_OPENAI = "https://api.openai.com/v1/images/generations"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"


def para_png(raw):
    """Garante PNG na saída. Passa direto se já for; converte se for JPEG.

    Preferência: Pillow (funciona no Railway/Linux). Fallback: sips no macOS.
    """
    if not raw or raw.startswith(MAGIC_PNG):
        return raw
    if not raw.startswith(MAGIC_JPEG):
        print("AVISO: formato de imagem não reconhecido; gravando como veio",
              file=sys.stderr)
        return raw
    # 1) Pillow (produção Linux + local)
    try:
        from io import BytesIO
        from PIL import Image
        im = Image.open(BytesIO(raw))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        buf = BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        pass
    # 2) sips (macOS)
    try:
        d = tempfile.mkdtemp(prefix="smark-img-")
        src, dst = os.path.join(d, "i.jpg"), os.path.join(d, "o.png")
        with open(src, "wb") as f:
            f.write(raw)
        r = subprocess.run(["/usr/bin/sips", "-s", "format", "png", src, "--out", dst],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(dst):
            with open(dst, "rb") as f:
                return f.read()
        raise RuntimeError(r.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        print(f"AVISO: falha ao converter JPEG->PNG ({e}); gravando o JPEG original",
              file=sys.stderr)
        return raw


class ErroProvedor(Exception):
    """Falha ao gerar imagem. `codigo` traz o status HTTP quando houver."""

    def __init__(self, mensagem, codigo=None):
        super().__init__(mensagem)
        self.codigo = codigo


def _postar(url, corpo, chave, timeout):
    req = urllib.request.Request(
        url, data=json.dumps(corpo).encode("utf-8"),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        bruto = urllib.request.urlopen(req, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "ignore")[:400]
        raise ErroProvedor(f"HTTP {e.code}: {detalhe}", codigo=e.code)
    except Exception as e:
        raise ErroProvedor(f"falha de rede: {e}")
    try:
        texto = bruto.decode("utf-8")
        return json.loads(texto)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        trecho = bruto[:200].decode("utf-8", "ignore")
        raise ErroProvedor(f"resposta ilegível do provedor: {e} — corpo: {trecho!r}")


def gerar(prompt, modelo, provider, chaves, *, resolution=None, aspect_ratio=None,
          seed=None, size=None, quality=None, refs=None, timeout=180):
    """Gera uma imagem e devolve {'png', 'custo_usd', 'modelo', 'provider'}."""
    if provider == "openrouter":
        chave = (chaves or {}).get("openrouter")
        if not chave:
            raise ErroProvedor("OPENROUTER_API_KEY ausente (.env na raiz do vault)")
        corpo = {"model": modelo, "prompt": prompt}
        if resolution:
            corpo["resolution"] = resolution
        if aspect_ratio:
            corpo["aspect_ratio"] = aspect_ratio
        if seed is not None:
            corpo["seed"] = int(seed)
        if refs:
            # API unificada OpenRouter exige objetos {type, image_url:{url}},
            # não strings soltas (ZodError: expected object, received string).
            norm = []
            for r in refs:
                if isinstance(r, str):
                    norm.append({"type": "image_url", "image_url": {"url": r}})
                elif isinstance(r, dict):
                    norm.append(r)
            corpo["input_references"] = norm
        url = URL_OPENROUTER
    elif provider == "openai":
        chave = (chaves or {}).get("openai")
        if not chave:
            raise ErroProvedor("OPENAI_API_KEY ausente (.env na raiz do vault)")
        corpo = {"model": modelo, "prompt": prompt, "n": 1}
        if size:
            corpo["size"] = size
        if quality:
            corpo["quality"] = quality
        url = URL_OPENAI
    else:
        raise ErroProvedor(f"provider desconhecido: {provider}")

    payload = _postar(url, corpo, chave, timeout)

    try:
        b64 = payload["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError):
        raise ErroProvedor(f"resposta sem imagem: {json.dumps(payload)[:300]}")

    custo = None
    try:
        custo = float(payload["usage"]["cost"])
    except (KeyError, TypeError, ValueError):
        pass

    try:
        # Sem validate=True de propósito: provedores reais às vezes devolvem base64
        # com quebra de linha ou na variante URL-safe, e o modo estrito transformaria
        # resposta boa em falha — acionando o suplente pago à toa. O try/except abaixo
        # já pega a corrupção que importa (padding quebrado).
        imagem = base64.b64decode(b64)
    except (binascii.Error, ValueError) as e:
        raise ErroProvedor(f"b64_json corrompido na resposta do provedor: {e}")

    return {"png": para_png(imagem), "custo_usd": custo,
            "modelo": modelo, "provider": provider}
