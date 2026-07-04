#!/usr/bin/env python3
"""
Edita/recompoe uma imagem a partir de UMA foto de referência + prompt (OpenAI Images edits).
Usa a foto do usuário como base (preserva a pessoa) e gera uma nova composição.

Uso:
  python3 scripts/openai_edit.py --image /caminho/foto.png --out arte/x.png \
      --prompt-file /tmp/prompt.txt --size 1024x1536 --quality high

Chave: OPENAI_API_KEY no .env. Modelo default gpt-image-1.5.
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
DEFAULT_MODEL = "gpt-image-1.5"
ENDPOINT = "https://api.openai.com/v1/images/edits"
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
    ap.add_argument("--input-fidelity", default="high", help="high preserva rosto/logo da foto-base")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file:
        sys.exit("ERRO: informe --prompt ou --prompt-file")
    prompt = args.prompt or open(args.prompt_file, "r", encoding="utf-8").read().strip()
    prompt = aplicar_guard(prompt, args.paleta, not args.no_guard)
    img = args.image if os.path.isabs(args.image) else os.path.join(VAULT, args.image)
    if not os.path.exists(img):
        sys.exit(f"ERRO: imagem não encontrada: {img}")

    env = load_env(os.path.join(VAULT, ".env"))
    api_key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("ERRO: OPENAI_API_KEY não encontrada")
    model = args.model or env.get("OPENAI_IMAGE_MODEL") or DEFAULT_MODEL

    body = multipart({"model": model, "prompt": prompt, "size": args.size,
                      "quality": args.quality, "n": "1",
                      "input_fidelity": args.input_fidelity}, img)
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    try:
        payload = json.loads(urllib.request.urlopen(req, timeout=240).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:600]}")

    try:
        b64 = payload["data"][0]["b64_json"]
    except (KeyError, IndexError):
        sys.exit(f"ERRO: resposta sem imagem. {json.dumps(payload)[:600]}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"OK: {out}  ({model}, edit de {os.path.basename(img)})")
    print(meta_block(out, {"modelo": model, "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta}))


if __name__ == "__main__":
    main()
