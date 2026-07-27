#!/usr/bin/env python3
"""Registry de marcas do vault — fonte única para slugs válidos.

Ordem de verdade:
  1. design-system/tokens/tokens.json → chave "marcas"
  2. pastas em marcas/<slug>/ (descoberta) — devem ser registradas via nova_marca

Canônicas (smark, provider-max, elever-ai) sempre existem no tokens.
Clientes externos entram no tokens + pasta branding mínima.

Qualidade: marca sem tokens/paleta não é "pronta" (pronta()).
"""
import json
import os
import re
import shutil

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(VAULT, "design-system", "tokens", "tokens.json")
MARCAS_DIR = os.path.join(VAULT, "marcas")
PERFIS = os.path.join(VAULT, "design-system", "tokens", "perfis-imagem.json")

CANONICAS = ("smark", "provider-max", "elever-ai")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_tokens():
    with open(TOKENS, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_tokens(t):
    with open(TOKENS, "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=2)
        f.write("\n")


def list_slugs():
    """Slugs registrados no tokens.json (ordem: canônicas primeiro, depois alpha)."""
    t = _load_tokens()
    slugs = list((t.get("marcas") or {}).keys())
    can = [s for s in CANONICAS if s in slugs]
    extra = sorted(s for s in slugs if s not in CANONICAS)
    return can + extra


def pastas_sem_registro():
    """Pastas em marcas/ que ainda não estão no tokens (órfãs)."""
    if not os.path.isdir(MARCAS_DIR):
        return []
    reg = set(list_slugs())
    return sorted(
        n for n in os.listdir(MARCAS_DIR)
        if os.path.isdir(os.path.join(MARCAS_DIR, n))
        and not n.startswith(".")
        and n not in reg
        and SLUG_RE.match(n)
    )


def get(slug):
    """Dict do tokens para a marca, ou {}."""
    t = _load_tokens()
    return dict((t.get("marcas") or {}).get(slug) or {})


def exists(slug):
    return slug in ( _load_tokens().get("marcas") or {} )


def is_slug_ok(slug):
    return bool(slug and SLUG_RE.match(slug) and ".." not in slug and "/" not in slug)


def require(slug, allow_unknown=False):
    """Devolve slug se válido. ValueError se desconhecido (não cai em smark)."""
    slug = (slug or "").strip()
    if not is_slug_ok(slug):
        raise ValueError(f"slug de marca inválido: {slug!r}")
    if not allow_unknown and not exists(slug):
        conhecidas = ", ".join(list_slugs())
        raise ValueError(
            f"marca '{slug}' não registrada. "
            f"Registre com: python3 scripts/nova_marca.py --slug {slug} --nome \"...\" --acento \"#HEX\"\n"
            f"Marcas: {conhecidas}"
        )
    return slug


def safe_marca(m, fallback="smark"):
    """Para paths: se conhecida e slug-ok, devolve; senão fallback (path-safe).

    Preferir `require()` em APIs de geração. Este helper evita path traversal.
    """
    m = (m or "").strip()
    if is_slug_ok(m) and exists(m):
        return m
    fb = fallback if exists(fallback) else (list_slugs()[0] if list_slugs() else "smark")
    return fb


def pronta(slug):
    """True se a marca tem o mínimo de branding para produção.

    - entrada no tokens (acento + nome)
    - pasta branding com identidade-visual.md e brand-voice.md
    """
    if not exists(slug):
        return False
    meta = get(slug)
    if not meta.get("nome") or not meta.get("acento"):
        return False
    base = os.path.join(MARCAS_DIR, slug, "branding")
    return (
        os.path.isfile(os.path.join(base, "identidade-visual.md"))
        and os.path.isfile(os.path.join(base, "brand-voice.md"))
    )


def listar_detalhes():
    """Lista dicts para UI: slug, nome, handle, pronta, canonica."""
    out = []
    for s in list_slugs():
        m = get(s)
        out.append({
            "slug": s,
            "nome": m.get("nome") or s,
            "handle": m.get("handle") or ("@" + s.replace("-", "")),
            "acento": m.get("acento") or "#8B3CF7",
            "pronta": pronta(s),
            "canonica": s in CANONICAS,
        })
    return out


def _sync_perfis(slug):
    """Inclui slug na família smark do contrato de imagem (mesmo motor)."""
    if not os.path.isfile(PERFIS):
        return
    try:
        with open(PERFIS, "r", encoding="utf-8") as f:
            p = json.load(f)
        fam = (p.get("familias") or {}).get("smark") or {}
        marcas = list(fam.get("marcas") or [])
        if slug not in marcas:
            marcas.append(slug)
            fam["marcas"] = marcas
            p.setdefault("familias", {})["smark"] = fam
            with open(PERFIS, "w", encoding="utf-8") as f:
                json.dump(p, f, ensure_ascii=False, indent=2)
                f.write("\n")
    except Exception:
        pass


def _tpl_identidade(nome, acento, acento_claro, handle):
    return f"""---
marca: {{slug}}
tipo: identidade-visual
versao: 1.0
atualizado: auto
paleta-ativa: primaria
tema-padrao: claro
---

# Identidade Visual — {nome}

## Paleta ativa

```yaml
primaria:
  base_escuro: "#0B0B0B"
  base_claro:  "#F4F2FB"
  acento:      "{acento}"
  acento_claro: "{acento_claro}"
  texto_escuro: "#FFFFFF"
  texto_claro:  "#100D1C"
```

## Regras

- **Acento** só na palavra-chave da headline e CTAs.
- Fundo de IA sem texto; tipografia no compositor.
- Tema-padrão: **claro**. Escuro só sob pedido.
- Handle: `{handle}`

## Proibido

- Cores fora da paleta
- Texto/logo inventados pela IA no fundo
- Poluição visual / stock cafona
"""


def _tpl_voice(nome):
    return f"""---
marca: {{slug}}
tipo: brand-voice
---

# Brand voice — {nome}

## Essência

Fale de forma clara, concreta e humana. Sem jargão vazio.

## Palavras-proibidas

"alavancar", "sinergia", "disrupção", "transformação digital", "revolucionar", "solução inovadora"

## Tom

Direto, profissional, acessível. Nunca prometa venda/faturamento na vitrine social.
"""


def _tpl_tom(nome):
    return f"""---
marca: {{slug}}
tipo: tom-de-voz
---

# Tom de voz — {nome}

- Frases curtas.
- Explicar como para alguém inteligente, sem jargão.
- CTA simples (diagnóstico, link na bio, fale conosco).
"""


def _tpl_dont(nome):
    return f"""---
marca: {{slug}}
tipo: do-and-dont
---

# Do and don't — {nome}

## Faça
- Manter paleta e logo oficiais
- Headline curta com 1 acento
- Fundo limpo (terço inferior livre)

## Não faça
- Texto na imagem de IA
- Cores fora da marca
- Promessa de venda/faturamento
"""


def criar(slug, nome, acento, *, acento_claro=None, handle=None, glyph=None,
          wordmark=None, endossa=False, mood=""):
    """Registra marca no tokens + cria pasta branding mínima. Devolve meta.

    Raises ValueError se slug inválido ou já existir (use force=False).
    """
    slug = (slug or "").strip().lower()
    if not is_slug_ok(slug):
        raise ValueError(f"slug inválido (use kebab-case [a-z0-9-]): {slug!r}")
    if exists(slug):
        raise ValueError(f"marca '{slug}' já existe no tokens.json")

    nome = (nome or slug).strip()
    acento = (acento or "").strip()
    if not re.match(r"^#[0-9A-Fa-f]{6}$", acento):
        raise ValueError(f"acento deve ser hex #RRGGBB: {acento!r}")
    if not acento_claro:
        # clareia levemente o acento (simples)
        acento_claro = acento
    else:
        acento_claro = acento_claro.strip()
        if not re.match(r"^#[0-9A-Fa-f]{6}$", acento_claro):
            raise ValueError(f"acento_claro inválido: {acento_claro!r}")

    handle = (handle or ("@" + slug.replace("-", ""))).strip()
    if not handle.startswith("@"):
        handle = "@" + handle
    glyph = (glyph or nome[:1].upper() or "M")[:2]
    wordmark = wordmark or nome

    # gradiente a partir do acento
    grad = f"linear-gradient(155deg,{acento} 0%,#2A1CA8 100%)"

    entry = {
        "nome": nome,
        "papel": "cliente",
        "acento": acento.upper() if acento.startswith("#") else acento,
        "acento_claro": acento_claro.upper() if acento_claro.startswith("#") else acento_claro,
        "gradiente": grad,
        "logo_glyph": glyph,
        "wordmark": wordmark,
        "handle": handle,
        "endossa": bool(endossa),
        "mood": mood or f"premium brand for {nome} — clean, professional, on-brand",
        "_nota": "Marca de cliente — criada via scripts/nova_marca.py. Completar branding se necessário.",
    }

    t = _load_tokens()
    t.setdefault("marcas", {})[slug] = entry
    _save_tokens(t)
    _sync_perfis(slug)

    # pastas
    brand_dir = os.path.join(MARCAS_DIR, slug, "branding")
    arte = os.path.join(MARCAS_DIR, slug, "publicacoes", "social", "instagram", "arte")
    ref = os.path.join(MARCAS_DIR, slug, "referencias", "inbox")
    for d in (brand_dir, arte, ref):
        os.makedirs(d, exist_ok=True)

    files = {
        "identidade-visual.md": _tpl_identidade(nome, entry["acento"], entry["acento_claro"], handle).replace("{slug}", slug),
        "brand-voice.md": _tpl_voice(nome).replace("{slug}", slug),
        "tom-de-voz.md": _tpl_tom(nome).replace("{slug}", slug),
        "do-and-dont.md": _tpl_dont(nome).replace("{slug}", slug),
    }
    for fn, content in files.items():
        path = os.path.join(brand_dir, fn)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    readme = os.path.join(MARCAS_DIR, slug, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write(f"# {nome}\n\nMarca de cliente no vault Smark.\n\nSlug: `{slug}`\nHandle: {handle}\n")

    return {"slug": slug, "meta": entry, "pronta": pronta(slug), "dir": os.path.join(MARCAS_DIR, slug)}


def copiar_logo(slug, src_path):
    """Copia logo para marcas/<slug>/branding/assets/logo.png e anota no tokens (brasao)."""
    require(slug)
    if not os.path.isfile(src_path):
        raise FileNotFoundError(src_path)
    dest_dir = os.path.join(MARCAS_DIR, slug, "branding", "assets")
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower() or ".png"
    dest = os.path.join(dest_dir, "logo" + ext)
    shutil.copy2(src_path, dest)
    rel = os.path.relpath(dest, VAULT)
    t = _load_tokens()
    m = t["marcas"][slug]
    m.setdefault("brasao", {})["principal"] = rel.replace("\\", "/")
    t["marcas"][slug] = m
    _save_tokens(t)
    return dest
