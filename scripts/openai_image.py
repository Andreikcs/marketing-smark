#!/usr/bin/env python3
"""
Gera UMA imagem de fundo (sem texto) e salva como PNG. Orquestrador: resolve o
perfil da marca via `_perfil.py` (modelo, provider, seed, tier), chama `_provedor.py`
e cai no suplente uma vez se o modelo principal falhar. Registra custo em `_ledger.py`.

Tiers:
  final     — Gemini 4K, publicável (default)
  rascunho  — Seedream barato, prompt curto, gate anti-texto, NÃO publicável

Exemplos:
  python3 scripts/openai_image.py --out arte/01.png --direcao --marca smark --tipo manifesto --tema claro
  python3 scripts/openai_image.py --out /tmp/r.png --direcao --marca smark --tipo dor --tema claro --tier rascunho

Chaves: OPENROUTER_API_KEY / OPENAI_API_KEY no .env (nunca em CLI).
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
import _acervo  # noqa: E402
import _gate_texto  # noqa: E402


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
    """True se o modelo não está no roster do contrato nem é o suplente declarado."""
    return modelo not in (roster or {}) and modelo != suplente


def gerar_com_suplente(prompt, perfil, chaves, size, quality, refs=None):
    """Tenta o modelo do perfil; em falha, uma tentativa no suplente.

    No tier=rascunho o suplente é Gemini final (OpenRouter), não gpt-image —
    a OpenAI com hard limit de billing não pode derrubar o rascunho barato.
    """
    try:
        r = _provedor.gerar(prompt, perfil["modelo"], perfil["provider"], chaves,
                            resolution=perfil.get("resolution"),
                            aspect_ratio=perfil.get("aspect_ratio"),
                            seed=perfil.get("seed") if perfil.get("enviar_seed") else None,
                            size=size, quality=quality, refs=refs)
        r["suplente_usado"] = False
        return r
    except _provedor.ErroProvedor as e:
        if perfil.get("tier") == "rascunho":
            # sobe pro Gemini 4K (pago, mas funciona) em vez da OpenAI sem crédito
            alt_modelo = "google/gemini-3-pro-image"
            alt_provider = "openrouter"
            print(f"AVISO: rascunho {perfil['modelo']} falhou ({e}). "
                  f"Caindo no Gemini final ({alt_modelo}).", file=sys.stderr)
            r = _provedor.gerar(prompt, alt_modelo, alt_provider, chaves,
                                resolution="4K",
                                aspect_ratio=perfil.get("aspect_ratio"),
                                size=size, quality=quality, refs=refs)
            r["suplente_usado"] = True
            return r
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
    ap.add_argument("--tier", default="final", choices=["final", "rascunho"],
                    help="final=Gemini 4K publicável | rascunho=Seedream barato + gate")
    ap.add_argument("--reroll", type=int, default=0, help="varia a seed de propósito")
    ap.add_argument("--sem-acervo", action="store_true",
                    help="não injeta as peças-referência da família")
    ap.add_argument("--sem-gate", action="store_true",
                    help="não roda gate de texto (só use em debug)")
    ap.add_argument("--slug", default="", help="slug do post — entra na seed determinística")
    ap.add_argument("--marca", default="")
    ap.add_argument("--canal", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--paleta", default="")
    ap.add_argument("--headline", default="")
    ap.add_argument("--post", default="")
    ap.add_argument("--legenda-file", default="")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    ap.add_argument("--direcao", action="store_true", help="monta o prompt do fundo via _direcao")
    ap.add_argument("--tipo", default="", help="tipo do post (manifesto/dor/prova/cta...)")
    ap.add_argument("--tema", default="escuro", help="escuro | claro")
    ap.add_argument("--conceito", default="", help="sobrescreve a metáfora visual")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file and not args.direcao:
        sys.exit("ERRO: informe --prompt, --prompt-file ou --direcao")

    slug = args.slug or os.path.splitext(os.path.basename(args.out))[0]
    perfil = _perfil.resolver(args.marca or "smark", slug=slug,
                              tipo=args.tipo, reroll=args.reroll, size=args.size,
                              tier=args.tier)

    if args.direcao and not args.prompt and not args.prompt_file:
        import _direcao
        if perfil.get("prompt_modo") == "curto" or perfil.get("tier") == "rascunho":
            prompt = _direcao.construir_rascunho(
                args.marca, args.tipo, args.tema, args.headline, args.conceito)
            print("AVISO: tier=rascunho — prompt curto (Seedream não recebe _direcao longo).",
                  file=sys.stderr)
        else:
            prompt = _direcao.construir(
                args.marca, args.tipo, args.tema, args.headline, args.conceito)
    else:
        prompt = args.prompt
        if args.prompt_file:
            prompt = open(args.prompt_file, "r", encoding="utf-8").read().strip()
    prompt = aplicar_guard(prompt, args.paleta, not args.no_guard)

    env = load_env(os.path.join(VAULT, ".env"))
    chaves = carregar_chaves(env)

    if args.model:
        roster = _perfil.carregar().get("_base", {}).get("roster", {})
        if fora_do_roster(args.model, roster, perfil["suplente_modelo"]):
            sys.exit(f"ERRO: '{args.model}' não está no roster do contrato "
                     f"(design-system/tokens/perfis-imagem.json).\n"
                     f"Roster: {', '.join(roster)} | suplente: {perfil['suplente_modelo']}")
        # bloquear Seedream forçado em final via --model
        if perfil["tier"] == "final":
            cap = roster.get(args.model) or {}
            papeis = cap.get("papel") or []
            if papeis and "final" not in papeis and "suplente" not in papeis:
                sys.exit(f"ERRO: '{args.model}' só pode ser usado com --tier rascunho "
                         f"(papel={papeis}). Final publicável exige Gemini.")
        perfil["modelo"] = args.model
    if args.provider != "auto":
        perfil["provider"] = args.provider
    if perfil["nao_calibrado"]:
        print(f"AVISO: família '{perfil['familia']}' sem calibração — usando suplente "
              f"{perfil['modelo']}. Rode scripts/calibrar.py.", file=sys.stderr)

    if perfil["tier"] == "rascunho":
        print(f"tier=rascunho · modelo={perfil['modelo']} · res={perfil['resolution']} "
              f"· NÃO publicável (promova a --tier final)", file=sys.stderr)

    refs = []
    # acervo só no final (rascunho deve ser exploração livre e barata)
    if perfil.get("acervo_ativo") and not args.sem_acervo and perfil["tier"] == "final":
        caminhos = _acervo.listar(perfil.get("acervo_dir"), perfil.get("acervo_max") or 20)
        refs = _acervo.como_data_urls(caminhos)
        if refs:
            print(f"acervo: {len(refs)} peça(s) de referência da família "
                  f"'{perfil['familia']}'", file=sys.stderr)

    try:
        r = gerar_com_suplente(prompt, perfil, chaves, args.size, args.quality, refs=refs)
    except _provedor.ErroProvedor as e:
        sys.exit(f"ERRO: {e}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    from _cambio import enriquecer  # noqa: E402
    pack_fx = enriquecer(r.get("custo_usd"))
    evento = {
        "familia": perfil["familia"], "marca": args.marca, "slug": slug,
        "tipo": args.tipo, "tier": perfil["tier"], "modelo": r["modelo"],
        "provider": r["provider"], "seed": perfil["seed"],
        "resolucao": perfil["resolution"],
        "custo_usd": pack_fx.get("custo_usd"),
        "custo_brl": pack_fx.get("custo_brl"),
        "usd_brl": pack_fx.get("usd_brl"),
        "cambio_fonte": pack_fx.get("cambio_fonte"),
        "cambio_em": pack_fx.get("cambio_em"),
        "refs": len(refs),
        "suplente_usado": r["suplente_usado"],
        "nao_calibrado": perfil["nao_calibrado"],
        "publicavel": perfil.get("publicavel", perfil["tier"] == "final"),
        "arquivo": os.path.basename(out),
    }

    try:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "wb") as f:
            f.write(r["png"])
    except OSError as e:
        evento["ok"] = False
        evento["erro"] = str(e)
        _ledger.registrar_imagem(evento)
        sys.exit(f"ERRO: a geração foi paga (custo=${r['custo_usd']}) mas a imagem "
                 f"não pôde ser salva em '{out}' ({e}). O gasto foi registrado no "
                 f"ledger; a arte não foi entregue.")

    # Gate de texto (rascunho Seedream)
    gate = {"ok": True, "poluido": False, "metodo": "n/a", "aviso": "", "trechos": []}
    if perfil.get("gate_texto") and not args.sem_gate:
        gate = _gate_texto.avaliar(out)
        evento["gate_metodo"] = gate.get("metodo")
        evento["gate_poluido"] = bool(gate.get("poluido"))
        if gate.get("aviso"):
            print(f"AVISO gate: {gate['aviso']}", file=sys.stderr)
        if gate.get("poluido"):
            evento["ok"] = True
            evento["publicavel"] = False
            evento["gate_falhou"] = True
            _ledger.registrar_imagem(evento)
            brl = evento.get("custo_brl")
            brl_s = f" R${brl:.2f}" if brl is not None else ""
            print(f"OK: {out}  (tier={perfil['tier']}, {r['modelo']} via {r['provider']}, "
                  f"seed={perfil['seed']}, custo=${evento.get('custo_usd') or '?'}{brl_s}, "
                  f"GATE_FALHOU poluído)")
            print(meta_block(out, {"modelo": r["modelo"], "provider": r["provider"],
                                   "qualidade": args.quality,
                                   "tamanho": args.size, "paleta": args.paleta,
                                   "seed": perfil["seed"], "custo_usd": evento.get("custo_usd"),
                                   "suplente_usado": r["suplente_usado"]}))
            sys.exit(3)

    evento["ok"] = True
    evento["gate_metodo"] = gate.get("metodo")
    evento["gate_poluido"] = False
    _ledger.registrar_imagem(evento)

    pub = "publicável" if evento.get("publicavel") else "rascunho NÃO publicável"
    brl = evento.get("custo_brl")
    brl_s = f" · R${brl:.2f}" if brl is not None else ""
    fx = evento.get("usd_brl")
    fx_s = f" · USD/BRL {fx:.4f}" if fx else ""
    print(f"OK: {out}  (tier={perfil['tier']}, {pub}, {r['modelo']} via {r['provider']}, "
          f"seed={perfil['seed']}, custo=${evento.get('custo_usd') or '?'}{brl_s}{fx_s})")
    print(meta_block(out, {"modelo": r["modelo"], "provider": r["provider"],
                           "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta,
                           "seed": perfil["seed"], "custo_usd": evento.get("custo_usd"),
                           "suplente_usado": r["suplente_usado"]}))


if __name__ == "__main__":
    main()
