#!/usr/bin/env python3
"""ESTÚDIO IA — cérebro do chat do Super Editor.

Recebe um pedido em linguagem natural ("post sobre a copa do mundo, tom leve")
e devolve JSON estruturado: copy por frame (headline/sub/cta no markup do
compositor), legenda, hashtags e um CONCEITO VISUAL em inglês que alimenta o
openai_image.py --direcao (não baixa a qualidade da arte).

Provider agnóstico (troca sozinho):
  - Se ANTHROPIC_API_KEY existir (.env ou ambiente) → Claude (claude-opus-4-8).
  - Senão → OpenAI chat (mesmo OPENAI_API_KEY que já gera as imagens).

Sem SDK — HTTP cru via urllib, igual openai_image.py. A chave nunca vai por
linha de comando.

Uso CLI (debug):  python3 scripts/estudio.py --marca smark --n 3 "post sobre a copa"
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)

JARGAO = ("alavancar", "sinergia", "exponencial", "transformação digital",
          "disrupção", "disruptivo", "solução", "inovador", "revolucionar")

try:
    import _marcas  # noqa: E402
except ImportError:
    _marcas = None

# ---- Regras de marca destiladas (voz-grupo + CLAUDE.md + estratégia) ----
SISTEMA = """Você é o redator e diretor de arte do Grupo Smark — assessoria de tecnologia
que coloca "funcionários de IA" em cada departamento das empresas. Você gera posts
de Instagram (feed 4:5, carrossel) prontos pra virar arte no editor.

REGRAS INVIOLÁVEIS:
1. Sempre pt-BR (Brasil). Zero anglicismo desnecessário.
2. NUNCA use jargão vazio: alavancar, sinergia, exponencial, transformação digital,
   disrupção, "solução", "inovador". Fale como pra uma criança de 7 anos: concreto,
   direto, humano.
3. NUNCA prometa venda, faturamento ou número mágico ("venda 3x", "fature mais").
   Fale de gestão: custo, tempo, produtividade, escala — nunca resultado comercial.
4. A marca pedida no contexto deve ser respeitada (slug registrado). Se for canônica ou cliente,
   use o posicionamento do grupo; se for marca de cliente externo, use o tom genérico
   claro e concreto daquela marca (sem inventar jargão).
5. smark (grupo) = assessoria com "funcionários de IA"; produtos Elever/Provider Max
   quando a marca for a deles. Clientes externos: fale da marca do cliente, não da smark.

MARKUP DA HEADLINE (obrigatório):
- Use | para quebrar linha. Ex: "Cada departamento|pode ter um *funcionário de IA*"
- Use *palavra* pra marcar a palavra-chave (vira roxo/acento). Só 1-2 acentos por frame.
- Headline curta e caixa-alta natural (o render já faz uppercase). 2 a 5 palavras por linha.

CONCEITO VISUAL:
- "conceito_visual" é uma linha CURTA em INGLÊS pro gerador de fundo (SEM texto na arte, sem logo).
- Se o usuário pede pra MUDAR/EDITAR uma imagem existente (ex.: "a partir desse fundo",
  "troque o carro por motos", "mesma cena mas…"): descreva a MUDANÇA e o que PRESERVAR,
  em tom fotográfico — NÃO invente cena abstrata nova. Ex: "same man and dusk parking lot,
  replace white car with luxury sport motorcycles, keep pose and lighting".
- Se é arte do zero (sem imagem-base): metáfora abstrata/editorial premium. Ex: "abstract
  stadium light trails, trophy silhouette in violet mist".

REGRA DE COR (CRÍTICA): o tema padrão é SEMPRE **claro** (fundo branco/lavanda, texto escuro,
acento roxo na palavra-chave). Só use "escuro" se o PEDIDO DO USUÁRIO disser explicitamente
escuro / dark / noturno / preto / fundo escuro. Palavras como "premium", "automotivo", "dramático",
"cinematográfico" NÃO são motivo pra escuro — mantenha CLARO. O conceito_visual também deve
descrever uma cena CLARA (ex.: "clean white studio, soft violet light") quando o tema for claro.

Responda SOMENTE com um objeto JSON válido, sem comentários, neste formato exato:
{
  "titulo": "título curto do post (pt-BR)",
  "tipo": "manifesto | dor | prova | cta",
  "tema": "claro | escuro",
  "frames": [
    {"headline": "linha1|linha2 com *acento*", "sub": "subtítulo curto ou vazio", "cta": "CTA só no último frame ou vazio", "tema": "claro | escuro"}
  ],
  "caption": "legenda pt-BR curta (2-4 frases), sem hashtags",
  "hashtags": "#a #b #c #d",
  "conceito_visual": "short english visual metaphor, no text",
  "resumo": "1 frase do que você gerou (pt-BR), pro chat"
}
Tema padrão = claro, a não ser que o pedido diga escuro/dark/roxo/noturno."""


def load_env(path):
    env = {}
    if os.path.isfile(path):
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ESCURO_CUES = ("escuro", "dark", "noturno", "à noite", "a noite", " noite",
               "preto", "black", "fundo escuro", "dramátic", "dramatic",
               "night", "sombrio", "tom escuro")


def _quer_escuro(txt):
    t = (txt or "").lower()
    return any(c in t for c in ESCURO_CUES)


def _instrucao(pedido, marca, n_frames, tipo, contexto="", historico=None):
    t = f"Marca: {marca}. " + (f"Tipo sugerido: {tipo}. " if tipo else "")
    t += f"Gere um carrossel de EXATAMENTE {n_frames} frame(s). "
    t += "O CTA (diagnóstico gratuito / link na bio) fica só no último frame. "
    if contexto:
        t += f"\n\nCONTEXTO (post que está aberto no editor agora — use pra manter coerência ou variar): {contexto}"
    if historico:
        h = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in historico[-6:] if m.get("content"))
        if h:
            t += f"\n\nCONVERSA ATÉ AGORA (continue a partir dela):\n{h}"
    t += f"\n\nPEDIDO AGORA: {pedido}"
    return t


def _post_json(url, headers, payload, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:400]}")


def _extrai_json(txt):
    """Pega o primeiro objeto JSON de uma resposta (robusto a cercas ```)."""
    s = txt.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("resposta sem JSON")
    return json.loads(s[i:j + 1])


def _via_claude(api_key, instrucao, imagem_b64=None, imagem_mime="image/jpeg"):
    """Devolve (resultado_json, meta_custo)."""
    content = []
    if imagem_b64:  # visão: Claude analisa a imagem de exemplo anexada
        content.append({"type": "image", "source": {"type": "base64",
                        "media_type": imagem_mime, "data": imagem_b64}})
    content.append({"type": "text", "text": instrucao})
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    data = _post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": api_key, "anthropic-version": "2023-06-01",
         "content-type": "application/json"},
        {"model": model,
         "max_tokens": 6000, "system": SISTEMA,
         "thinking": {"type": "adaptive"},          # + inteligência: raciocina antes
         "output_config": {"effort": "high"},        # esforço alto (trabalho sensível)
         "messages": [{"role": "user", "content": content}]})
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    usage = data.get("usage") or {}
    # Claude: input_tokens / output_tokens (+ cache opcional)
    inp = int(usage.get("input_tokens") or 0)
    # tokens de thinking às vezes vêm em output
    out = int(usage.get("output_tokens") or 0)
    cache_r = int(usage.get("cache_read_input_tokens") or 0)
    cache_c = int(usage.get("cache_creation_input_tokens") or 0)
    # soma cache no input para estimativa conservadora
    inp_total = inp + cache_r + cache_c
    import _custo_llm  # noqa: E402
    custo = _custo_llm.custo_tokens(model, inp_total, out)
    meta = {
        "modelo": model, "provider": "anthropic",
        "input_tokens": inp_total, "output_tokens": out,
        "custo_usd": custo, "ok": True,
    }
    return _extrai_json("".join(parts)), meta


def _via_openai(api_key, instrucao, imagem_b64=None, imagem_mime="image/jpeg"):
    """Devolve (resultado_json, meta_custo)."""
    model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")
    content = [{"type": "text", "text": instrucao}]
    if imagem_b64:
        content.insert(0, {"type": "image_url",
                           "image_url": {"url": f"data:{imagem_mime};base64,{imagem_b64}"}})
    data = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"model": model, "temperature": 0.8,
         "response_format": {"type": "json_object"},
         "messages": [{"role": "system", "content": SISTEMA},
                      {"role": "user", "content": content}]})
    usage = data.get("usage") or {}
    inp = int(usage.get("prompt_tokens") or 0)
    out = int(usage.get("completion_tokens") or 0)
    import _custo_llm  # noqa: E402
    custo = _custo_llm.custo_tokens(model, inp, out)
    meta = {
        "modelo": model, "provider": "openai",
        "input_tokens": inp, "output_tokens": out,
        "custo_usd": custo, "ok": True,
    }
    return _extrai_json(data["choices"][0]["message"]["content"]), meta


def gerar(pedido, marca="smark", n_frames=3, tipo="", contexto="", historico=None,
          imagem_b64=None, imagem_mime="image/jpeg", slug=""):
    """Devolve (resultado_dict, provider_usado, meta_custo). Levanta RuntimeError em falha."""
    # Marca desconhecida = erro explícito (sem fallback silencioso p/ smark)
    if _marcas:
        marca = _marcas.require(marca) if marca else "smark"
    else:
        marca = marca or "smark"
    n_frames = max(1, min(10, int(n_frames or 3)))
    env = load_env(os.path.join(VAULT, ".env"))
    ant = os.environ.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY")
    oai = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    instr = _instrucao(pedido, marca, n_frames, tipo, contexto, historico)
    # anexa voz da marca se existir (cliente externo ou canônica)
    voice_path = os.path.join(VAULT, "marcas", marca, "branding", "brand-voice.md")
    if os.path.isfile(voice_path):
        try:
            trecho = open(voice_path, encoding="utf-8").read()[:1200]
            instr += f"\n\nVOZ DA MARCA ({marca}) — respeite:\n{trecho}"
        except Exception:
            pass
    if imagem_b64:
        instr += ("\n\nO usuário ANEXOU UMA IMAGEM. O gerador vai EDITAR essa foto (não inventar outra). "
                  "No 'conceito_visual', diga em inglês o que PRESERVAR e o que MUDAR conforme o pedido "
                  "(ex.: same person and dusk scene, replace car with luxury motorcycles). "
                  "NÃO proponha cena abstrata, manequim ou estúdio novo se a foto é fotorealista. "
                  "Descreva no 'resumo' o que você entendeu e o que vai mudar.")
    meta = {"custo_usd": None, "ok": False}
    if ant:
        res, meta = _via_claude(ant, instr, imagem_b64, imagem_mime)
        prov = "claude"
    elif oai:
        res, meta = _via_openai(oai, instr, imagem_b64, imagem_mime)
        prov = "openai"
    else:
        raise RuntimeError("Sem chave: coloque OPENAI_API_KEY (ou ANTHROPIC_API_KEY) no .env")
    res = _sanea(res, marca, n_frames)
    # PADRÃO CLARO forte (regra #9): se o usuário não pediu escuro em lugar nenhum, força claro.
    hist_user = " ".join(m.get("content", "") for m in (historico or []) if m.get("role") == "user")
    quer_esc = _quer_escuro(pedido + " " + hist_user + " " + (contexto or ""))
    # com imagem de exemplo, o exemplo dita o tom (não força claro)
    forcar = (not quer_esc) and (not imagem_b64)
    if forcar:
        res["tema"] = "claro"
        for fr in res["frames"]:
            fr["tema"] = "claro"
    res["forcado_claro"] = forcar

    # Ledger de copy (separado da imagem) + BRL via cotação
    try:
        import _ledger  # noqa: E402
        from _cambio import enriquecer  # noqa: E402
        pack = enriquecer(meta.get("custo_usd"))
        evento = {
            "marca": marca,
            "slug": slug or (res.get("titulo") or "")[:60],
            "pedido": (pedido or "")[:200],
            "n_frames": n_frames,
            "modelo": meta.get("modelo"),
            "provider": meta.get("provider") or prov,
            "input_tokens": meta.get("input_tokens"),
            "output_tokens": meta.get("output_tokens"),
            "custo_usd": pack.get("custo_usd"),
            "custo_brl": pack.get("custo_brl"),
            "usd_brl": pack.get("usd_brl"),
            "cambio_fonte": pack.get("cambio_fonte"),
            "cambio_em": pack.get("cambio_em"),
            "ok": True,
        }
        _ledger.registrar_copy(evento)
        meta.update(pack)
        meta["ok"] = True
        res["_custo"] = {
            "tipo": "copy",
            "custo_usd": pack.get("custo_usd"),
            "custo_brl": pack.get("custo_brl"),
            "usd_brl": pack.get("usd_brl"),
            "modelo": meta.get("modelo"),
            "provider": meta.get("provider") or prov,
            "input_tokens": meta.get("input_tokens"),
            "output_tokens": meta.get("output_tokens"),
        }
    except Exception as e:
        print(f"AVISO: ledger de copy não gravou ({e})", file=sys.stderr)

    return res, prov, meta


def _sanea(res, marca, n_frames):
    """Garante formato + aplica as travas (jargão / promessa de venda)."""
    res.setdefault("titulo", "Post smark")
    res.setdefault("tipo", "manifesto")
    res.setdefault("tema", "claro")
    res.setdefault("caption", "")
    res.setdefault("hashtags", "")
    res.setdefault("conceito_visual", "")
    res.setdefault("resumo", "")
    res["marca"] = marca
    frames = res.get("frames") or []
    if not isinstance(frames, list):
        frames = []
    norm = []
    for fr in frames[:n_frames]:
        if not isinstance(fr, dict):
            continue
        norm.append({"headline": str(fr.get("headline", "")).strip(),
                     "sub": str(fr.get("sub", "")).strip(),
                     "cta": str(fr.get("cta", "")).strip(),
                     "tema": fr.get("tema") or res["tema"]})
    while len(norm) < n_frames:
        norm.append({"headline": "", "sub": "", "cta": "", "tema": res["tema"]})
    res["frames"] = norm
    # gate: sinaliza (não bloqueia) jargão/promessa pro usuário revisar
    blob = " ".join([res.get("caption", "")] + [f["headline"] + " " + f["sub"] for f in norm]).lower()
    res["alertas"] = [j for j in JARGAO if j in blob]
    if any(w in blob for w in ("fature", "venda mais", "3x mais venda", "vender mais", "faturamento")):
        res["alertas"].append("possível promessa de venda")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pedido")
    ap.add_argument("--marca", default="smark")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--tipo", default="")
    a = ap.parse_args()
    try:
        res, prov, meta = gerar(a.pedido, a.marca, a.n, a.tipo)
    except Exception as e:
        print(json.dumps({"erro": str(e)}, ensure_ascii=False))
        sys.exit(1)
    res.pop("_custo", None)
    print(json.dumps({"provider": prov, "custo": meta, **res}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
