#!/usr/bin/env python3
"""Bake-off de calibração: gera a MESMA direção nos modelos do roster e fixa a escolha.

Ritual de entrada de família. Mesma direção, mesma paleta, mesma resolução em todos
os candidatos — a comparação é estética, não técnica.

Atenção ao critério 3: foi ele que reprovou o seedream-4.5 no bake-off de 2026-07-24
(o modelo tipografava o próprio prompt na arte). Olhe a imagem, não só o custo.

  python3 scripts/calibrar.py --familia smark --marca smark
  python3 scripts/calibrar.py --familia smark --fixar google/gemini-3-pro-image

Critérios de avaliação (Seção 6 do spec):
  1. Aderência à paleta ativa
  2. Respeito ao espaço negativo do terço inferior
  3. Ausência de texto espúrio
  4. Parentesco com as peças já aprovadas

AVISO DE CUSTO: cada combinação modelo × tipo é uma chamada paga (~US$ 0,24). Rodar
o bake-off completo do roster custa alguns dólares. Não rode este script "só pra ver".
"""
import argparse
import datetime
import json
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _direcao  # noqa: E402
import _ledger  # noqa: E402
import _perfil  # noqa: E402
import _provedor  # noqa: E402
from _paleta import aplicar_guard  # noqa: E402

CRITERIOS = [
    "1. Aderência à paleta ativa (nenhuma cor fora da identidade)",
    "2. Respeito ao espaço negativo do terço inferior (o compositor precisa dele)",
    "3. Ausência de texto espúrio no fundo",
    "4. Parentesco com as peças já aprovadas da família",
]


def candidatos(cfg):
    """Modelos elegíveis para o bake-off — as chaves do roster, sem os banidos."""
    banidos = set((cfg.get("_base", {}).get("banidos") or {}).keys())
    return [m for m in (cfg.get("_base", {}).get("roster") or {}) if m not in banidos]


def fixar(familia, modelo, data, path=None):
    """Grava modelo e calibrado_em no contrato. Recusa modelo fora do roster.

    Preserva todo o resto do conteúdo do contrato: lê o cfg inteiro, muta só a
    família alvo e regrava o dict completo — roster, banidos e demais famílias
    saem intactos.
    """
    alvo = path or _perfil.CONTRATO
    cfg = _perfil.carregar(alvo)
    if modelo not in candidatos(cfg):
        raise ValueError(f"'{modelo}' não está no roster do contrato")
    fam = cfg.setdefault("familias", {}).setdefault(familia, {})
    fam["modelo"] = modelo
    fam["calibrado_em"] = data
    with open(alvo, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return cfg


def _sanitizar(modelo):
    return modelo.replace("/", "-").replace(".", "_")


def _gerar_variante(modelo, tipo, args, cfg, chaves, destino):
    """Gera uma variante (modelo × tipo) do bake-off: chama o provedor, grava o PNG
    e registra o evento no ledger. Devolve (ok: bool, mensagem: str).

    Uma chamada paga que tem sucesso e depois falha ao gravar em disco AINDA
    ASSIM registra o gasto no ledger — o dinheiro já foi cobrado nesse ponto e o
    ledger é o único registro dele. A falha de uma variante nunca aborta as
    outras; quem decide isso é o chamador (`main`), que apenas soma falhas.
    """
    seed = _perfil.calcular_seed(args.familia, "calibracao", tipo)
    cap = _perfil.capacidades(modelo, cfg)
    provider = cap.get("provider", "openrouter")
    prompt = aplicar_guard(
        _direcao.construir(args.marca, tipo, args.tema, "", ""), args.paleta, True)
    out = os.path.join(destino, f"{_sanitizar(modelo)}-{tipo}.png")

    try:
        r = _provedor.gerar(
            prompt, modelo, provider, chaves,
            resolution="2K", aspect_ratio="4:5",
            seed=seed if cap.get("suporta_seed") else None,
            size="1024x1536", quality="high")
    except _provedor.ErroProvedor as e:
        return False, f"FALHOU {modelo} / {tipo}: {e}"

    evento = {"familia": args.familia, "marca": args.marca, "slug": "calibracao",
              "tipo": tipo, "modelo": modelo, "provider": provider, "seed": seed,
              "resolucao": "2K", "custo_usd": r["custo_usd"],
              "suplente_usado": False, "nao_calibrado": True,
              "arquivo": os.path.basename(out)}

    # A chamada acima já foi cobrada (custo_usd conhecido). Se a gravação em
    # disco falhar a partir daqui, o ledger tem que registrar o gasto mesmo
    # assim — não pular o registro só porque o PNG não chegou no destino.
    try:
        with open(out, "wb") as f:
            f.write(r["png"])
    except OSError as e:
        evento["ok"] = False
        evento["erro"] = str(e)
        _ledger.registrar(evento)
        return False, (f"FALHOU (gravação em disco) {modelo} / {tipo}: {e} — "
                        f"gasto de ${r['custo_usd']} já registrado no ledger.")

    evento["ok"] = True
    _ledger.registrar(evento)
    return True, f"OK: {out}  (custo=${r['custo_usd']})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familia", default="smark")
    ap.add_argument("--marca", default="smark")
    ap.add_argument("--tipos", default="manifesto,dor,prova")
    ap.add_argument("--tema", default="claro")
    ap.add_argument("--paleta", default="roxo")
    ap.add_argument("--fixar", default="")
    args = ap.parse_args()

    if args.fixar:
        hoje = datetime.date.today().isoformat()
        fixar(args.familia, args.fixar, hoje)
        print(f"OK: família '{args.familia}' calibrada em {args.fixar} ({hoje})")
        return

    from openai_image import carregar_chaves, load_env
    cfg = _perfil.carregar()
    chaves = carregar_chaves(load_env(os.path.join(VAULT, ".env")))
    destino = os.path.join(VAULT, "design-system", "calibracao", args.familia)
    os.makedirs(destino, exist_ok=True)

    tipos = [t.strip() for t in args.tipos.split(",") if t.strip()]
    falhas = 0
    for modelo in candidatos(cfg):
        for tipo in tipos:
            ok, msg = _gerar_variante(modelo, tipo, args, cfg, chaves, destino)
            if ok:
                print(msg)
            else:
                print(msg, file=sys.stderr)
                falhas += 1

    print(f"\nVariantes em {destino}")
    print("Critérios de avaliação:")
    for c in CRITERIOS:
        print("  " + c)
    print(f"\nEscolhido o vencedor, rode:\n  python3 scripts/calibrar.py "
          f"--familia {args.familia} --fixar <modelo>")
    if falhas:
        sys.exit(f"\n{falhas} variante(s) falharam.")


if __name__ == "__main__":
    main()
