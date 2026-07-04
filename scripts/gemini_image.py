#!/usr/bin/env python3
"""
Gera UMA imagem via Gemini Image API e salva como PNG.
Uso pelos comandos de conteúdo (ex: /post-instagram) — não é chamado direto pelo usuário normalmente.

Exemplos:
  python3 scripts/gemini_image.py --out arte/01.png --prompt "..."
  python3 scripts/gemini_image.py --out arte/01.png --prompt-file /tmp/frame01.txt --aspect 4:5

A chave vem do .env na raiz do vault (GEMINI_API_KEY). Nunca é passada por linha de comando.
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
DEFAULT_MODEL = "gemini-2.5-flash-image"


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def build_body(prompt, aspect, with_format):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    if with_format and aspect:
        body["generationConfig"]["responseFormat"] = {"image": {"aspectRatio": aspect}}
    return body


def call(model, version, body, api_key):
    url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_image(payload):
    for cand in payload.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inline_data") or part.get("inlineData")
            if inline and inline.get("data"):
                return inline["data"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="caminho do PNG de saída")
    ap.add_argument("--prompt", help="prompt de imagem")
    ap.add_argument("--prompt-file", help="arquivo com o prompt (preferível p/ textos longos)")
    ap.add_argument("--aspect", default="4:5", help="proporção (ex: 4:5, 1:1, 16:9)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--marca", default="")
    ap.add_argument("--canal", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--paleta", default="")
    ap.add_argument("--headline", default="")
    ap.add_argument("--post", default="")
    ap.add_argument("--legenda-file", default="")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file:
        sys.exit("ERRO: informe --prompt ou --prompt-file")
    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()

    env = load_env(os.path.join(VAULT, ".env"))
    api_key = os.environ.get("GEMINI_API_KEY") or env.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("ERRO: GEMINI_API_KEY não encontrada (.env na raiz do vault)")
    model = args.model or env.get("GEMINI_IMAGE_MODEL") or DEFAULT_MODEL

    # Tentativas resilientes: versão da API (v1beta/v1) x responseFormat (com/sem).
    attempts = [
        ("v1beta", True), ("v1beta", False),
        ("v1", True), ("v1", False),
    ]
    last_err = None
    payload = None
    for version, with_format in attempts:
        try:
            payload = call(model, version, build_body(prompt, args.aspect, with_format), api_key)
            break
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code} ({version}, format={with_format}): {e.read().decode('utf-8', 'ignore')[:500]}"
            if e.code in (400, 404):
                continue
            sys.exit(f"ERRO: {last_err}")
        except Exception as e:  # noqa
            last_err = str(e)
            continue
    if payload is None:
        sys.exit(f"ERRO: todas as tentativas falharam. Última: {last_err}")

    b64 = extract_image(payload)
    if not b64:
        txt = json.dumps(payload)[:600]
        sys.exit(f"ERRO: resposta sem imagem. Trecho: {txt}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))

    print(f"OK: {out}")
    print(meta_block(out, {"modelo": model, "qualidade": "",
                           "tamanho": args.aspect, "paleta": args.paleta}))


if __name__ == "__main__":
    main()
