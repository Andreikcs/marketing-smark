#!/usr/bin/env python3
"""
Gera UMA imagem via OpenAI Images API (gpt-image-*) e salva como PNG.
Análogo a gemini_image.py — escolha o gerador por qualidade/custo.

Exemplos:
  python3 scripts/openai_image.py --out arte/01.png --prompt-file /tmp/frame01.txt
  python3 scripts/openai_image.py --out arte/01.png --prompt "..." --quality medium --size 1024x1536

Chave: OPENAI_API_KEY no .env da raiz do vault. Nunca passada por linha de comando.
Modelos disponíveis (na conta): gpt-image-1.5 (default), gpt-image-2, gpt-image-1, gpt-image-1-mini.
Sizes válidos: 1024x1024, 1024x1536 (retrato), 1536x1024 (paisagem), auto.
Quality: low | medium | high | auto.
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
ENDPOINT = "https://api.openai.com/v1/images/generations"


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, "r", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--size", default="1024x1536", help="1024x1024 | 1024x1536 | 1536x1024 | auto")
    ap.add_argument("--quality", default="high", help="low | medium | high | auto")
    ap.add_argument("--model", default=None)
    # Metadados p/ a ficha (sidecar .md) — opcionais mas recomendados
    ap.add_argument("--marca", default="")
    ap.add_argument("--canal", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--paleta", default="")
    ap.add_argument("--headline", default="")
    ap.add_argument("--post", default="")
    ap.add_argument("--legenda-file", default="")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    ap.add_argument("--direcao", action="store_true", help="monta o prompt do fundo via _direcao (nível agência)")
    ap.add_argument("--tipo", default="", help="tipo do post (manifesto/dor/prova/cta...) p/ a biblioteca de conceitos")
    ap.add_argument("--tema", default="escuro", help="escuro | claro (afeta cor/luz da direção de arte)")
    ap.add_argument("--conceito", default="", help="sobrescreve a metáfora visual (temas especiais, ex: Copa)")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file and not args.direcao:
        sys.exit("ERRO: informe --prompt, --prompt-file ou --direcao")
    if args.direcao and not args.prompt and not args.prompt_file:
        import _direcao
        prompt = _direcao.construir(args.marca, args.tipo, args.tema, args.headline, args.conceito)
    else:
        prompt = args.prompt
        if args.prompt_file:
            prompt = open(args.prompt_file, "r", encoding="utf-8").read().strip()
    prompt = aplicar_guard(prompt, args.paleta, not args.no_guard)

    env = load_env(os.path.join(VAULT, ".env"))
    api_key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("ERRO: OPENAI_API_KEY não encontrada (.env na raiz do vault)")
    model = args.model or env.get("OPENAI_IMAGE_MODEL") or DEFAULT_MODEL

    body = {"model": model, "prompt": prompt, "size": args.size,
            "quality": args.quality, "n": 1}
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        payload = json.loads(urllib.request.urlopen(req, timeout=180).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:600]}")

    try:
        b64 = payload["data"][0]["b64_json"]
    except (KeyError, IndexError):
        sys.exit(f"ERRO: resposta sem imagem. Trecho: {json.dumps(payload)[:600]}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))

    print(f"OK: {out}  ({model}, {args.size}, {args.quality})")
    print(meta_block(out, {"modelo": model, "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta}))


if __name__ == "__main__":
    main()
