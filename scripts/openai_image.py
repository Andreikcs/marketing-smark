#!/usr/bin/env python3
"""
Gera UMA imagem de fundo (sem texto) e salva como PNG. Orquestrador: resolve o
perfil da marca via `_perfil.py` (modelo, provider, seed), chama `_provedor.py`
(OpenRouter ou OpenAI atrás da mesma interface) e cai no suplente uma vez se o
modelo principal falhar. Registra custo/uso em `_ledger.py`.

Exemplos:
  python3 scripts/openai_image.py --out arte/01.png --prompt-file /tmp/frame01.txt
  python3 scripts/openai_image.py --out arte/01.png --direcao --marca smark --tipo manifesto --tema claro

Chaves: OPENROUTER_API_KEY / OPENAI_API_KEY no .env da raiz do vault (ou variável
de ambiente). Nunca passadas por linha de comando.
Sizes válidos: 1024x1024, 1024x1536 (retrato), 1536x1024 (paisagem), auto.
Quality: low | medium | high | auto.
"""
import argparse
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sidecar import meta_block  # noqa: E402
from _paleta import aplicar_guard  # noqa: E402
import _perfil  # noqa: E402
import _provedor  # noqa: E402
import _ledger  # noqa: E402


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, "r", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def carregar_chaves(env):
    """Chaves dos dois provedores; ambiente tem precedência sobre o .env."""
    return {
        "openrouter": os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY"),
        "openai": os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY"),
    }


def fora_do_roster(modelo, roster, suplente):
    """True se o modelo não está no roster do contrato nem é o suplente declarado.

    `roster` é o dict de capacidades (`_base.roster`); basta testar as chaves."""
    return modelo not in (roster or {}) and modelo != suplente


def gerar_com_suplente(prompt, perfil, chaves, size, quality, refs=None):
    """Tenta o modelo do perfil; em falha, uma tentativa no suplente."""
    try:
        r = _provedor.gerar(prompt, perfil["modelo"], perfil["provider"], chaves,
                            resolution=perfil.get("resolution"),
                            aspect_ratio=perfil.get("aspect_ratio"),
                            seed=perfil.get("seed") if perfil.get("enviar_seed") else None,
                            size=size, quality=quality, refs=refs)
        r["suplente_usado"] = False
        return r
    except _provedor.ErroProvedor as e:
        print(f"AVISO: {perfil['modelo']} falhou ({e}). Tentando suplente "
              f"{perfil['suplente_modelo']}.", file=sys.stderr)
        r = _provedor.gerar(prompt, perfil["suplente_modelo"], perfil["suplente_provider"],
                            chaves, size=size, quality=quality)
        r["suplente_usado"] = True
        return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--size", default="1024x1536", help="1024x1024 | 1024x1536 | 1536x1024 | auto")
    ap.add_argument("--quality", default="high", help="low | medium | high | auto")
    ap.add_argument("--model", default=None, help="sobrescreve o modelo do perfil")
    ap.add_argument("--provider", default="auto", help="auto | openrouter | openai")
    ap.add_argument("--reroll", type=int, default=0, help="varia a seed de propósito")
    ap.add_argument("--slug", default="", help="slug do post — entra na seed determinística")
    ap.add_argument("--marca", default="")
    ap.add_argument("--canal", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--paleta", default="")
    ap.add_argument("--headline", default="")
    ap.add_argument("--post", default="")
    ap.add_argument("--legenda-file", default="")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    ap.add_argument("--direcao", action="store_true", help="monta o prompt do fundo via _direcao (nível agência)")
    ap.add_argument("--tipo", default="", help="tipo do post (manifesto/dor/prova/cta...)")
    ap.add_argument("--tema", default="escuro", help="escuro | claro")
    ap.add_argument("--conceito", default="", help="sobrescreve a metáfora visual")
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
    chaves = carregar_chaves(env)

    slug = args.slug or os.path.splitext(os.path.basename(args.out))[0]
    perfil = _perfil.resolver(args.marca or "smark", slug=slug,
                              tipo=args.tipo, reroll=args.reroll, size=args.size)
    if args.model:
        roster = _perfil.carregar().get("_base", {}).get("roster", {})
        if fora_do_roster(args.model, roster, perfil["suplente_modelo"]):
            sys.exit(f"ERRO: '{args.model}' não está no roster do contrato "
                     f"(design-system/tokens/perfis-imagem.json).\n"
                     f"Roster: {', '.join(roster)} | suplente: {perfil['suplente_modelo']}")
        perfil["modelo"] = args.model
    if args.provider != "auto":
        perfil["provider"] = args.provider
    if perfil["nao_calibrado"]:
        print(f"AVISO: família '{perfil['familia']}' sem calibração — usando suplente "
              f"{perfil['modelo']}. Rode scripts/calibrar.py.", file=sys.stderr)

    try:
        r = gerar_com_suplente(prompt, perfil, chaves, args.size, args.quality)
    except _provedor.ErroProvedor as e:
        sys.exit(f"ERRO: {e}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(r["png"])

    _ledger.registrar({
        "familia": perfil["familia"], "marca": args.marca, "slug": slug,
        "tipo": args.tipo, "modelo": r["modelo"],
        "provider": r["provider"], "seed": perfil["seed"],
        "resolucao": perfil["resolution"], "custo_usd": r["custo_usd"],
        "ok": True, "suplente_usado": r["suplente_usado"],
        "nao_calibrado": perfil["nao_calibrado"], "arquivo": os.path.basename(out),
    })

    print(f"OK: {out}  ({r['modelo']} via {r['provider']}, "
          f"seed={perfil['seed']}, custo=${r['custo_usd'] if r['custo_usd'] is not None else '?'})")
    print(meta_block(out, {"modelo": r["modelo"], "provider": r["provider"],
                           "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta,
                           "seed": perfil["seed"], "custo_usd": r["custo_usd"],
                           "suplente_usado": r["suplente_usado"]}))


if __name__ == "__main__":
    main()
