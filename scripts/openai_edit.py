#!/usr/bin/env python3
"""
Edita/recompoe uma imagem a partir de UMA foto de referência + prompt.

Ordem de provedores:
  1. OpenRouter (google/gemini-3-pro-image + input_references) — crédito do motor calibrado
  2. OpenAI Images edits (gpt-image-1.5) — se OpenRouter falhar e houver OPENAI_API_KEY

Uso:
  python3 scripts/openai_edit.py --image /caminho/foto.png --out arte/x.png \
      --prompt-file /tmp/prompt.txt --size 1024x1536 --quality high
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sidecar import meta_block  # noqa: E402
from _paleta import aplicar_guard  # noqa: E402
import _ledger  # noqa: E402
import _provedor  # noqa: E402

DEFAULT_OPENAI_MODEL = "gpt-image-1.5"
DEFAULT_OR_MODEL = "google/gemini-3-pro-image"
ENDPOINT_OPENAI = "https://api.openai.com/v1/images/edits"
BOUNDARY = "----SmarkFormBoundary7MA4YWxkTrZu0gW29"


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, "r", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def multipart(fields, image_path):
    body = b""
    for k, v in fields.items():
        body += f"--{BOUNDARY}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    data = open(image_path, "rb").read()
    fn = os.path.basename(image_path)
    body += f"--{BOUNDARY}\r\n".encode()
    body += f'Content-Disposition: form-data; name="image"; filename="{fn}"\r\n'.encode()
    body += b"Content-Type: image/png\r\n\r\n"
    body += data + b"\r\n"
    body += f"--{BOUNDARY}--\r\n".encode()
    return body


def _data_url(image_path):
    raw = open(image_path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def _aspect_de_size(size):
    try:
        w, h = size.lower().split("x")
        w, h = int(w), int(h)
        if w == h:
            return "1:1"
        if abs(w / h - 2 / 3) < 0.05:
            return "2:3"
        if abs(w / h - 3 / 2) < 0.05:
            return "3:2"
        if abs(w / h - 4 / 5) < 0.05:
            return "4:5"
        return f"{w}:{h}"
    except Exception:
        return "2:3"


def _eh_billing(msg):
    m = (msg or "").lower()
    return any(x in m for x in (
        "billing", "hard limit", "insufficient_quota", "exceeded your current quota",
        "payment", "credit", "balance",
    ))


def editar_openrouter(img, prompt, size, env):
    """Edição via OpenRouter: a foto vira input_reference do modelo de imagem."""
    chave = os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY")
    if not chave:
        raise RuntimeError("OPENROUTER_API_KEY ausente")
    modelo = env.get("OPENROUTER_IMAGE_MODEL") or DEFAULT_OR_MODEL
    ref = _data_url(img)
    # Prompt de edição fotográfica (o _direcao NÃO entra aqui — pessoas são permitidas).
    full = (
        prompt.strip()
        + "\n\nCRITICAL: Use the provided reference image as the base. "
        "This is an edit of that photo, not a new invention. "
        "Preserve identity, pose, camera angle, lighting and environment unless asked to change them. "
        "Photorealistic, high detail, 4k. No text, no logos, no watermark."
    )
    r = _provedor.gerar(
        full, modelo, "openrouter",
        {"openrouter": chave, "openai": None},
        resolution="4K",
        aspect_ratio=_aspect_de_size(size),
        refs=[ref],
        timeout=240,
    )
    return r


def editar_openai(img, prompt, size, quality, model, input_fidelity, env):
    api_key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    model = model or env.get("OPENAI_IMAGE_MODEL") or DEFAULT_OPENAI_MODEL
    body = multipart({"model": model, "prompt": prompt, "size": size,
                      "quality": quality, "n": "1",
                      "input_fidelity": input_fidelity}, img)
    req = urllib.request.Request(
        ENDPOINT_OPENAI, data=body,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    try:
        payload = json.loads(urllib.request.urlopen(req, timeout=240).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "ignore")[:600]
        raise RuntimeError(f"HTTP {e.code}: {detalhe}")
    try:
        b64 = payload["data"][0]["b64_json"]
    except (KeyError, IndexError):
        raise RuntimeError(f"resposta sem imagem: {json.dumps(payload)[:600]}")
    raw = base64.b64decode(b64)
    return {
        "png": _provedor.para_png(raw),
        "custo_usd": None,
        "modelo": model,
        "provider": "openai",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="foto de referência (entrada)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--size", default="1024x1536")
    ap.add_argument("--quality", default="high")
    ap.add_argument("--model", default=None)
    ap.add_argument("--paleta", default="")
    ap.add_argument("--input-fidelity", default="high", help="high preserva rosto/logo (só OpenAI)")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    ap.add_argument("--provider", default="auto",
                    help="auto | openrouter | openai — auto tenta OpenRouter e cai na OpenAI")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file:
        sys.exit("ERRO: informe --prompt ou --prompt-file")
    prompt = args.prompt or open(args.prompt_file, "r", encoding="utf-8").read().strip()
    prompt = aplicar_guard(prompt, args.paleta, not args.no_guard)
    img = args.image if os.path.isabs(args.image) else os.path.join(VAULT, args.image)
    if not os.path.exists(img):
        sys.exit(f"ERRO: imagem não encontrada: {img}")

    env = load_env(os.path.join(VAULT, ".env"))
    ordem = []
    if args.provider == "openrouter":
        ordem = ["openrouter"]
    elif args.provider == "openai":
        ordem = ["openai"]
    else:
        # Preferência: OpenRouter (onde está o crédito do motor) → OpenAI
        if os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY"):
            ordem.append("openrouter")
        if os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY"):
            ordem.append("openai")
    if not ordem:
        sys.exit("ERRO: coloque OPENROUTER_API_KEY ou OPENAI_API_KEY no .env")

    erros = []
    result = None
    for prov in ordem:
        try:
            if prov == "openrouter":
                print("AVISO: edit via OpenRouter (imagem como referência)…", file=sys.stderr)
                result = editar_openrouter(img, prompt, args.size, env)
            else:
                print("AVISO: edit via OpenAI Images…", file=sys.stderr)
                result = editar_openai(img, prompt, args.size, args.quality,
                                       args.model, args.input_fidelity, env)
            break
        except Exception as e:
            msg = str(e)
            erros.append(f"{prov}: {msg[:300]}")
            print(f"AVISO: edit {prov} falhou ({msg[:180]}). "
                  f"{'Tentando próximo provedor…' if prov != ordem[-1] else ''}",
                  file=sys.stderr)
            # billing da OpenAI não deve abortar se ainda há OpenRouter na fila (e vice-versa)
            continue

    if result is None:
        resumo = " | ".join(erros)[:700]
        if any(_eh_billing(e) for e in erros):
            sys.exit(
                "ERRO: limite de billing no provedor de edição. "
                "OpenRouter tem crédito? confira OPENROUTER_API_KEY. "
                f"Detalhe: {resumo}"
            )
        sys.exit(f"ERRO: edição falhou em todos os provedores. {resumo}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    evento = {
        "familia": "", "marca": getattr(args, "marca", ""), "slug": "",
        "tipo": "edit", "modelo": result["modelo"], "provider": result["provider"],
        "seed": None, "resolucao": args.size, "custo_usd": result.get("custo_usd"),
        "refs": 1, "suplente_usado": False, "nao_calibrado": False,
        "arquivo": os.path.basename(out),
    }

    try:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "wb") as f:
            f.write(result["png"])
    except OSError as e:
        evento["ok"] = False
        evento["erro"] = str(e)
        _ledger.registrar(evento)
        sys.exit(f"ERRO: a edição foi paga mas a imagem não pôde ser salva em "
                 f"'{out}' ({e}). O gasto foi registrado no ledger; a arte não foi entregue.")

    evento["ok"] = True
    _ledger.registrar(evento)

    custo = result.get("custo_usd")
    custo_s = f"{custo}" if custo is not None else "?"
    print(f"OK: {out}  ({result['modelo']} via {result['provider']}, "
          f"edit de {os.path.basename(img)}, custo=${custo_s})")
    print(meta_block(out, {"modelo": result["modelo"], "provider": result["provider"],
                           "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta,
                           "custo_usd": custo, "suplente_usado": False}))


if __name__ == "__main__":
    main()
