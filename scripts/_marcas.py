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
    """Lista dicts ricos para UI de gestão de marcas."""
    out = []
    for s in list_slugs():
        m = get(s)
        brasao = m.get("brasao") or {}
        logo = brasao.get("principal") or m.get("logo_file") or ""
        out.append({
            "slug": s,
            "nome": m.get("nome") or s,
            "handle": m.get("handle") or ("@" + s.replace("-", "")),
            "acento": m.get("acento") or "#8B3CF7",
            "acento_claro": m.get("acento_claro") or m.get("acento") or "#8B3CF7",
            "acento_alternativo": m.get("acento_alternativo") or "",
            "base_escura": m.get("base_escura") or "",
            "wordmark": m.get("wordmark") or m.get("nome") or s,
            "glyph": m.get("logo_glyph") or (m.get("nome") or s)[:1].upper(),
            "mood": m.get("mood") or "",
            "gradiente": m.get("gradiente") or "",
            "papel": m.get("papel") or ("canonica" if s in CANONICAS else "cliente"),
            "logo": logo,
            "logo_url": ("/" + logo.lstrip("/")) if logo else "",
            "pronta": pronta(s),
            "canonica": s in CANONICAS,
        })
    return out


def _hex_ok(h):
    return bool(h and re.match(r"^#[0-9A-Fa-f]{6}$", h.strip()))


def _base_escura_de(acento_hex):
    """Tom escuro parceiro do acento — NUNCA roxo smark (#2A1CA8).

    Teal/ciano → navy; vermelho/laranja → marrom-escuro; verde → verde-quase-preto;
    demais → near-black levemente tingido.
    """
    h = (acento_hex or "").strip().upper()
    if not _hex_ok(h):
        return "#0B0B0B"
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    # teal / ciano (Revoe, contábil)
    if g > 100 and b > 100 and abs(g - b) < 50 and r < min(g, b) + 40:
        return "#001A34"
    # laranja / vermelho quente
    if r > g + 30 and r > b + 20:
        return "#1A0A08"
    # lime / verde
    if g > r + 30 and g > b + 20:
        return "#0A1408"
    # azul puro
    if b > r + 30 and b >= g:
        return "#050D1A"
    # roxo/violeta (smark canônica)
    if r > 80 and b > 100 and g < r:
        return "#2A1CA8"
    return "#0B0B0B"


def atualizar(slug, *, nome=None, acento=None, acento_claro=None, handle=None,
              glyph=None, wordmark=None, mood=None, gradiente=None, endossa=None):
    """Atualiza campos editáveis de uma marca no tokens.json.

    Canônicas podem editar handle/mood/cores (cuidado), mas o slug não muda.
    Raises ValueError se slug desconhecido ou hex inválido.
    """
    slug = require(slug)
    t = _load_tokens()
    m = dict(t["marcas"][slug])

    if nome is not None:
        nome = str(nome).strip()
        if not nome:
            raise ValueError("nome não pode ser vazio")
        m["nome"] = nome
    if acento is not None:
        acento = str(acento).strip()
        if not _hex_ok(acento):
            raise ValueError(f"acento deve ser hex #RRGGBB: {acento!r}")
        m["acento"] = acento.upper()
        base_e = m.get("base_escura") or _base_escura_de(m["acento"])
        m["base_escura"] = base_e
        if gradiente is None:
            # recompõe gradiente on-brand (sem roxo smark)
            m["gradiente"] = f"linear-gradient(155deg,{m['acento']} 0%,{base_e} 100%)"
    if acento_claro is not None:
        acento_claro = str(acento_claro).strip()
        if not _hex_ok(acento_claro):
            raise ValueError(f"acento_claro deve ser hex #RRGGBB: {acento_claro!r}")
        m["acento_claro"] = acento_claro.upper()
    if handle is not None:
        handle = re.sub(r"[^@A-Za-z0-9_.]", "", str(handle))[:40].strip()
        if handle and not handle.startswith("@"):
            handle = "@" + handle
        if handle:
            m["handle"] = handle
    if glyph is not None:
        g = str(glyph).strip()[:2] or m.get("logo_glyph") or "M"
        m["logo_glyph"] = g
    if wordmark is not None:
        wm = str(wordmark).strip()[:60]
        if wm:
            m["wordmark"] = wm
    if mood is not None:
        m["mood"] = str(mood).strip()[:400]
    if gradiente is not None:
        g = str(gradiente).strip()[:200]
        if g:
            m["gradiente"] = g
    if endossa is not None:
        m["endossa"] = bool(endossa)

    t["marcas"][slug] = m
    _save_tokens(t)
    return {"slug": slug, "meta": m, "pronta": pronta(slug)}


def salvar_logo_bytes(slug, raw, *, ext=".png"):
    """Grava logo binário em branding/assets e anota brasao.principal no tokens."""
    require(slug)
    if not raw:
        raise ValueError("logo vazio")
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("logo maior que 8 MB")
    ext = (ext or ".png").lower()
    if not ext.startswith("."):
        ext = "." + ext
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        raise ValueError(f"extensão de logo não suportada: {ext}")
    dest_dir = os.path.join(MARCAS_DIR, slug, "branding", "assets")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "logo" + ext)
    with open(dest, "wb") as f:
        f.write(raw)
    rel = os.path.relpath(dest, VAULT).replace("\\", "/")
    t = _load_tokens()
    m = t["marcas"][slug]
    m.setdefault("brasao", {})["principal"] = rel
    t["marcas"][slug] = m
    _save_tokens(t)
    return dest


def salvar_referencia_bytes(slug, raw, *, nome=None, ext=".jpg"):
    """Salva print/peça de referência em referencias/feed e PNG no acervo da marca.

    O acervo (referencias/acervo/*.png) alimenta gerações via _perfil (prioridade
    por marca). Devolve dict com paths.
    """
    require(slug)
    if not raw:
        raise ValueError("referência vazia")
    if len(raw) > 12 * 1024 * 1024:
        raise ValueError("referência maior que 12 MB")
    ext = (ext or ".jpg").lower()
    if not ext.startswith("."):
        ext = "." + ext
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        ext = ".jpg"
    feed_dir = os.path.join(MARCAS_DIR, slug, "referencias", "feed")
    acervo_dir = os.path.join(MARCAS_DIR, slug, "referencias", "acervo")
    os.makedirs(feed_dir, exist_ok=True)
    os.makedirs(acervo_dir, exist_ok=True)
    base = nome or f"ref-{len(os.listdir(feed_dir))+1:02d}"
    base = re.sub(r"[^a-z0-9._-]+", "-", base.lower()).strip("-") or "ref"
    feed_path = os.path.join(feed_dir, base + ext)
    with open(feed_path, "wb") as f:
        f.write(raw)
    # PNG no acervo (input_references)
    acervo_path = os.path.join(acervo_dir, base + ".png")
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        # limita lado maior p/ não estourar refs
        im.thumbnail((1536, 1536))
        im.save(acervo_path, "PNG", optimize=True)
    except Exception:
        # se não for imagem decodável, só copia se já for png
        if ext == ".png":
            with open(acervo_path, "wb") as f:
                f.write(raw)
        else:
            acervo_path = ""
    return {
        "feed": os.path.relpath(feed_path, VAULT).replace("\\", "/"),
        "acervo": (os.path.relpath(acervo_path, VAULT).replace("\\", "/") if acervo_path and os.path.isfile(acervo_path) else ""),
    }


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

    acc_u = acento.upper() if acento.startswith("#") else acento
    acc2_u = acento_claro.upper() if acento_claro.startswith("#") else acento_claro
    # base escura do degradê = tom da própria marca (NUNCA roxo smark #2A1CA8)
    base_escura = _base_escura_de(acc_u)
    grad = f"linear-gradient(155deg,{acc_u} 0%,{base_escura} 100%)"

    entry = {
        "nome": nome,
        "papel": "cliente",
        "acento": acc_u,
        "acento_claro": acc2_u,
        "gradiente": grad,
        "base_escura": base_escura,
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
