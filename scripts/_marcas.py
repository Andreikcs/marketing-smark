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
            # string vazia = nenhum glyph (preservar); None/ausente → 1ª letra p/ UI
            "glyph": m["logo_glyph"] if "logo_glyph" in m else ((m.get("nome") or s)[:1].upper()),
            "mood": m.get("mood") or "",
            "gradiente": m.get("gradiente") or "",
            "segmento": m.get("segmento") or "",
            "site": m.get("site") or "",
            "papel": m.get("papel") or ("canonica" if s in CANONICAS else "cliente"),
            "logo": logo,
            "logo_url": ("/" + logo.lstrip("/")) if logo else "",
            "refs_n": len(listar_refs(s)) if exists(s) else 0,
            "pronta": pronta(s),
            "canonica": s in CANONICAS,
            "branding_book": os.path.isfile(branding_book_path(s)) if exists(s) else False,
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


SEGMENTOS = (
    ("contabilidade", "Contabilidade / fiscal"),
    ("telecom", "Telecom / ISP"),
    ("varejo", "Varejo / e-commerce"),
    ("imobiliaria", "Imobiliário"),
    ("saude", "Saúde / clínicas"),
    ("servicos", "Serviços B2B"),
    ("educacao", "Educação"),
    ("industria", "Indústria"),
    ("outro", "Outro"),
)

# mood base por segmento (pt-BR — idioma padrão da plataforma)
# Usado na UI e como direção de arte; o motor de imagem aceita pt-BR.
MOOD_POR_SEGMENTO = {
    "contabilidade": "marca B2B de contabilidade e fiscal — navy e teal, fotografia corporativa limpa, curvas geométricas, confiança e resultado",
    "telecom": "provedor regional de fibra — infraestrutura em escala, conexão de bairro confiável, visual industrial limpo e premium",
    "varejo": "marca de varejo e comércio — foto de produto clara, prateleiras limpas, energia de loja moderna e acessível",
    "imobiliaria": "marca imobiliária premium — interiores claros, fotografia arquitetônica, confiança e aspiração, composição arejada",
    "saude": "marca de saúde e clínicas — brancos clínicos e azuis suaves, cuidado humano, fotografia médica limpa",
    "servicos": "serviços B2B profissionais — corporativo contido, mesas limpas, fotografia premium e confiável",
    "educacao": "marca de educação — espaços de aprendizado claros e esperançosos, energia de campus moderno",
    "industria": "marca industrial — aço, máquinas de precisão, segurança e escala, engenharia premium em fundo escuro",
    "outro": "visual premium da marca — limpo, profissional e contido",
}


def listar_refs(slug):
    """Lista arquivos de feed + acervo da marca."""
    require(slug)
    out = []
    for kind, sub in (("feed", "referencias/feed"), ("acervo", "referencias/acervo")):
        d = os.path.join(MARCAS_DIR, slug, *sub.split("/"))
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n.startswith("."):
                continue
            low = n.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            rel = os.path.join("marcas", slug, sub, n).replace("\\", "/")
            out.append({
                "nome": n,
                "kind": kind,
                "path": rel,
                "url": "/" + rel,
                "base": os.path.splitext(n)[0],
            })
    return out


def remover_ref(slug, nome):
    """Remove ref do feed e/ou acervo pelo nome do arquivo (ou base)."""
    require(slug)
    nome = os.path.basename(nome or "")
    if not nome or ".." in nome:
        raise ValueError("nome inválido")
    base = os.path.splitext(nome)[0]
    removed = []
    for sub in ("referencias/feed", "referencias/acervo"):
        d = os.path.join(MARCAS_DIR, slug, *sub.split("/"))
        if not os.path.isdir(d):
            continue
        for n in list(os.listdir(d)):
            if n == nome or os.path.splitext(n)[0] == base:
                p = os.path.join(d, n)
                try:
                    os.remove(p)
                    removed.append(os.path.join("marcas", slug, sub, n).replace("\\", "/"))
                except OSError:
                    pass
    if not removed:
        raise FileNotFoundError(nome)
    return removed


def excluir(slug, *, apagar_pasta=True):
    """Remove marca de cliente do tokens e (opcional) da pasta marcas/.

    Canônicas (smark, provider-max, elever-ai) NÃO podem ser excluídas.
    Devolve dict com o que foi removido.
    """
    slug = (slug or "").strip().lower()
    if not is_slug_ok(slug):
        raise ValueError(f"slug inválido: {slug!r}")
    if slug in CANONICAS:
        raise ValueError(f"marca canônica '{slug}' não pode ser excluída")
    if not exists(slug):
        raise ValueError(f"marca '{slug}' não existe")
    t = _load_tokens()
    meta = t["marcas"].pop(slug, None)
    _save_tokens(t)
    # tira do perfil de imagem
    try:
        if os.path.isfile(PERFIS):
            with open(PERFIS, "r", encoding="utf-8") as f:
                p = json.load(f)
            fam = (p.get("familias") or {}).get("smark") or {}
            marcas = list(fam.get("marcas") or [])
            if slug in marcas:
                fam["marcas"] = [m for m in marcas if m != slug]
                p.setdefault("familias", {})["smark"] = fam
                with open(PERFIS, "w", encoding="utf-8") as f:
                    json.dump(p, f, ensure_ascii=False, indent=2)
                    f.write("\n")
    except Exception:
        pass
    pasta = os.path.join(MARCAS_DIR, slug)
    pasta_removida = False
    if apagar_pasta and os.path.isdir(pasta):
        shutil.rmtree(pasta)
        pasta_removida = True
    return {
        "slug": slug,
        "meta": meta,
        "pasta_removida": pasta_removida,
        "dir": pasta if pasta_removida else "",
    }


def remover_logo(slug):
    """Remove logo e limpa brasao.principal no tokens."""
    require(slug)
    t = _load_tokens()
    m = t["marcas"][slug]
    brasao = m.get("brasao") or {}
    rel = brasao.get("principal") or ""
    removed = []
    if rel:
        p = os.path.join(VAULT, rel) if not os.path.isabs(rel) else rel
        if os.path.isfile(p):
            os.remove(p)
            removed.append(rel)
    assets = os.path.join(MARCAS_DIR, slug, "branding", "assets")
    if os.path.isdir(assets):
        for n in os.listdir(assets):
            if n.lower().startswith("logo"):
                try:
                    os.remove(os.path.join(assets, n))
                    removed.append(os.path.join("marcas", slug, "branding/assets", n).replace("\\", "/"))
                except OSError:
                    pass
    if "brasao" in m and isinstance(m["brasao"], dict):
        m["brasao"].pop("principal", None)
    t["marcas"][slug] = m
    _save_tokens(t)
    return removed


def gerar_texto_ia_marca(slug=None, nome="", segmento="", acento="", site=""):
    """Gera mood + sugestões de copy sem chamar API externa (template por segmento).

    Retorna dict pronto para preencher o formulário.
    """
    seg = (segmento or "outro").strip().lower()
    if seg not in MOOD_POR_SEGMENTO:
        seg = "outro"
    nome = (nome or slug or "marca").strip()
    import unicodedata
    base = (slug or nome).lower()
    base = unicodedata.normalize("NFD", base)
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    handle = "@" + re.sub(r"[^a-z0-9]", "", base)[:24]
    mood = MOOD_POR_SEGMENTO[seg]
    # personaliza levemente com o nome (sempre pt-BR)
    mood = f"{mood} — nome da marca: {nome}"
    glyph = (nome[:1] or "M").upper()
    wordmark = nome
    dicas = {
        "contabilidade": "Use navy/teal, tema escuro, prazos e riscos fiscais sem prometer economia.",
        "telecom": "Use acento da marca, dor de queda de sinal e fibra local.",
        "varejo": "Tema claro, produto e oferta, CTA de loja/WhatsApp.",
        "imobiliaria": "Fotos de imóvel e confiança, sem promessa de venda.",
        "saude": "Tom calmo, humano, sem diagnóstico médico na arte.",
        "servicos": "B2B direto, autoridade e clareza.",
        "educacao": "Tom esperançoso e claro.",
        "industria": "Precisão e escala, fundo escuro.",
        "outro": "Siga paleta e referências enviadas.",
    }
    return {
        "segmento": seg,
        "mood": mood,
        "handle": handle,
        "glyph": glyph,
        "wordmark": wordmark,
        "dica": dicas.get(seg, dicas["outro"]),
        "site": (site or "").strip(),
    }


def atualizar(slug, *, nome=None, acento=None, acento_claro=None, handle=None,
              glyph=None, wordmark=None, mood=None, gradiente=None, endossa=None,
              segmento=None, site=None):
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
        # string vazia = sem glyph (só logo ou nada no chip/tab)
        g = str(glyph).strip()[:2]
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
    if segmento is not None:
        seg = str(segmento).strip().lower()
        if seg and seg not in dict(SEGMENTOS):
            raise ValueError(f"segmento inválido: {seg}")
        m["segmento"] = seg or m.get("segmento") or "outro"
    if site is not None:
        site = str(site).strip()[:200]
        if site:
            m["site"] = site
        elif "site" in m:
            m.pop("site", None)

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
    # se colidir, acrescenta -2, -3… (slug gerado automaticamente a partir do nome)
    if exists(slug):
        base = slug
        n = 2
        while exists(f"{base}-{n}") and n < 50:
            n += 1
        if exists(f"{base}-{n}"):
            raise ValueError(f"marca '{slug}' já existe no tokens.json")
        slug = f"{base}-{n}"

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
    # glyph="" explícito = nenhum; None/omitido = 1ª letra do nome
    if glyph is None:
        glyph = (nome[:1].upper() or "M")[:2]
    else:
        glyph = str(glyph).strip()[:2]
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
        "mood": mood or f"visual premium da marca {nome} — limpo, profissional e alinhado à identidade",
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


def _rgb_to_hex(r, g, b):
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"


def _hex_lum(h):
    if not _hex_ok(h):
        return 0
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def extrair_paleta_de_imagens(paths_or_bytes, *, n=4):
    """Extrai cores dominantes de imagens (paths ou bytes).

    Devolve lista de hex #RRGGBB ordenada por saturação/presença (acentos primeiro).
    """
    try:
        from PIL import Image
        from collections import Counter
        import io
    except ImportError as e:
        raise RuntimeError("Pillow necessário para extrair paleta") from e

    samples = []
    for item in paths_or_bytes or []:
        try:
            if isinstance(item, (bytes, bytearray)):
                im = Image.open(io.BytesIO(item))
            else:
                if not item or not os.path.isfile(str(item)):
                    continue
                im = Image.open(str(item))
            im = im.convert("RGB")
            im.thumbnail((160, 160))
            # quantiza pra ~32 cores
            try:
                q = im.quantize(colors=24, method=getattr(Image, "MEDIANCUT", 0))
            except Exception:
                q = im.convert("P", palette=Image.ADAPTIVE, colors=24)
            pal = q.getpalette() or []
            counts = Counter(q.getdata())
            for idx, cnt in counts.most_common(12):
                if idx * 3 + 2 >= len(pal):
                    continue
                r, g, b = pal[idx * 3], pal[idx * 3 + 1], pal[idx * 3 + 2]
                # ignora near-white / near-black
                mx, mn = max(r, g, b), min(r, g, b)
                if mx < 28 or mn > 240:
                    continue
                sat = (mx - mn) / max(1, mx)
                if sat < 0.12 and 40 < (r + g + b) / 3 < 220:
                    continue  # cinza médio
                samples.append(((r, g, b), cnt * (1 + sat * 2)))
        except Exception:
            continue

    if not samples:
        return []

    # agrupa cores parecidas
    buckets = []  # [(r,g,b,weight)]
    for (r, g, b), w in samples:
        placed = False
        for i, (br, bg, bb, bw) in enumerate(buckets):
            if abs(br - r) + abs(bg - g) + abs(bb - b) < 55:
                tot = bw + w
                buckets[i] = (
                    (br * bw + r * w) / tot,
                    (bg * bw + g * w) / tot,
                    (bb * bw + b * w) / tot,
                    tot,
                )
                placed = True
                break
        if not placed:
            buckets.append((float(r), float(g), float(b), float(w)))

    buckets.sort(key=lambda x: -x[3])
    out = []
    for r, g, b, _ in buckets:
        hx = _rgb_to_hex(round(r), round(g), round(b))
        if hx not in out:
            out.append(hx)
        if len(out) >= n:
            break
    return out


def extrair_paleta_marca(slug, *, n=4):
    """Lê refs da marca e extrai acento + acento_claro sugeridos."""
    require(slug)
    refs = listar_refs(slug)
    paths = []
    for r in refs:
        for k in ("acervo", "feed", "path", "full"):
            p = r.get(k) if isinstance(r, dict) else None
            if p:
                full = p if os.path.isabs(p) else os.path.join(VAULT, p)
                if os.path.isfile(full):
                    paths.append(full)
                    break
    # também tenta pastas feed/acervo direto
    for sub in ("referencias/acervo", "referencias/feed"):
        d = os.path.join(MARCAS_DIR, slug, sub)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    paths.append(os.path.join(d, fn))
    # dedupe
    seen, uniq = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    cores = extrair_paleta_de_imagens(uniq[:16], n=max(n, 3))
    if not cores:
        return {"acento": "", "acento_claro": "", "cores": [], "n_imgs": len(uniq)}
    # acento = mais saturada entre as top
    def sat(h):
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        mx, mn = max(r, g, b), min(r, g, b)
        return (mx - mn) / max(1, mx)

    ranked = sorted(cores, key=lambda h: (-sat(h), -_hex_lum(h)))
    acento = ranked[0]
    # acento_claro = versão mais clara da mesma família ou 2ª cor
    acento_claro = ranked[1] if len(ranked) > 1 and _hex_lum(ranked[1]) > _hex_lum(acento) else None
    if not acento_claro:
        r, g, b = int(acento[1:3], 16), int(acento[3:5], 16), int(acento[5:7], 16)
        acento_claro = _rgb_to_hex(min(255, r + 40), min(255, g + 40), min(255, b + 40))
    return {
        "acento": acento,
        "acento_claro": acento_claro,
        "cores": cores,
        "n_imgs": len(uniq),
    }


def aplicar_paleta(slug, acento, acento_claro=None):
    """Atualiza acento/acento_claro/gradiente/base_escura da marca."""
    return atualizar(
        slug,
        acento=acento,
        acento_claro=acento_claro or acento,
    )


def branding_book_path(slug):
    return os.path.join(MARCAS_DIR, slug, "branding", "branding-book.md")


def branding_book_status(slug):
    """Info se a marca tem branding book gerado/adicionado."""
    require(slug)
    p = branding_book_path(slug)
    assets = os.path.join(MARCAS_DIR, slug, "branding", "branding-book")
    n_assets = 0
    if os.path.isdir(assets):
        n_assets = len([f for f in os.listdir(assets)
                        if not f.startswith(".") and os.path.isfile(os.path.join(assets, f))])
    return {
        "existe": os.path.isfile(p),
        "path": os.path.relpath(p, VAULT).replace("\\", "/") if os.path.isfile(p) else "",
        "assets_n": n_assets,
        "assets_dir": os.path.relpath(assets, VAULT).replace("\\", "/") if os.path.isdir(assets) else "",
    }


def gerar_branding_book(slug, *, forcar=False):
    """Gera/atualiza branding/branding-book.md consolidando tokens + identidade.

    Se já existe e forcar=False, só devolve status.
    """
    require(slug)
    m = get(slug)
    p = branding_book_path(slug)
    if os.path.isfile(p) and not forcar:
        st = branding_book_status(slug)
        st["gerado"] = False
        st["msg"] = "já existe — use forcar para reescrever"
        return st

    nome = m.get("nome") or slug
    acc = m.get("acento") or "#8B3CF7"
    acc2 = m.get("acento_claro") or acc
    base = m.get("base_escura") or _base_escura_de(acc)
    handle = m.get("handle") or ("@" + slug.replace("-", ""))
    mood = m.get("mood") or ""
    wordmark = m.get("wordmark") or nome
    glyph = m.get("logo_glyph") or nome[:1].upper()
    seg = m.get("segmento") or ""
    site = m.get("site") or ""
    logo = (m.get("brasao") or {}).get("principal") or m.get("logo_file") or ""

    # puxa trechos de identidade se existirem
    id_path = os.path.join(MARCAS_DIR, slug, "branding", "identidade-visual.md")
    extra_id = ""
    if os.path.isfile(id_path):
        try:
            raw = open(id_path, encoding="utf-8").read()
            # tira frontmatter
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    raw = parts[2].strip()
            extra_id = raw[:2500]
        except OSError:
            pass

    md = f"""---
marca: {slug}
tipo: branding-book
versao: 1.0
gerado: auto
---

# Branding Book — {nome}

> Documento vivo da marca no vault Smark. Fonte: `tokens.json` + branding.

## Essência

| Campo | Valor |
|-------|-------|
| Nome | {nome} |
| Slug | `{slug}` |
| Handle | {handle} |
| Wordmark | {wordmark} |
| Glyph | {glyph} |
| Segmento | {seg or "—"} |
| Site | {site or "—"} |
| Logo | {logo or "— (use glyph)"} |

## Paleta

| Papel | Hex |
|-------|-----|
| Acento | `{acc}` |
| Acento claro | `{acc2}` |
| Base escura | `{base}` |
| Gradiente | `{m.get("gradiente") or "—"}` |

```
■ {acc}  acento
■ {acc2}  acento claro
■ {base}  base escura
```

## Mood (direção de arte)

{mood or "_ainda sem mood — complete em Config → Editar marca_"}

## Regras de aplicação

1. **Tema-padrão = claro** (fundo branco/lavanda, texto escuro, acento na palavra-chave).
2. Escuro só sob pedido explícito.
3. Fundo de IA **sem texto** — tipografia e logo vêm do compositor.
4. Logo na tab/chip: preferir marca limpa (PNG com transparência ou SVG). Foto de feed **não** vira brasão.
5. Sem jargão vazio; sem promessa de venda/faturamento no social.

## Identidade visual (resumo)

{extra_id or "_complete `branding/identidade-visual.md`_"}

## Como usar neste sistema

1. Config → Marcas → Editar → confira cores, logo e referências.
2. Editor → selecione a marca no post → Estúdio IA gera copy + fundo na paleta.
3. Referências em `referencias/feed` e `referencias/acervo` guiam o fundo.

---
*Gerado pelo smark studio · edite este arquivo se o cliente tiver book oficial.*
"""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(md)
    st = branding_book_status(slug)
    st["gerado"] = True
    st["msg"] = "branding book gerado"
    return st


def salvar_branding_book_asset(slug, raw, *, nome="page", ext=".png"):
    """Anexa página/arquivo do branding book oficial do cliente."""
    require(slug)
    if not raw:
        raise ValueError("arquivo vazio")
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError("arquivo maior que 20 MB")
    ext = (ext or ".png").lower()
    if not ext.startswith("."):
        ext = "." + ext
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".pdf", ".svg"):
        raise ValueError(f"extensão não suportada: {ext}")
    dest_dir = os.path.join(MARCAS_DIR, slug, "branding", "branding-book")
    os.makedirs(dest_dir, exist_ok=True)
    base = re.sub(r"[^a-z0-9._-]+", "-", (nome or "page").lower()).strip("-") or "page"
    dest = os.path.join(dest_dir, base + ext)
    # evita sobrescrever
    if os.path.isfile(dest):
        i = 2
        while os.path.isfile(os.path.join(dest_dir, f"{base}-{i}{ext}")):
            i += 1
        dest = os.path.join(dest_dir, f"{base}-{i}{ext}")
    with open(dest, "wb") as f:
        f.write(raw)
    # garante book md
    if not os.path.isfile(branding_book_path(slug)):
        gerar_branding_book(slug, forcar=True)
    return {
        "path": os.path.relpath(dest, VAULT).replace("\\", "/"),
        **branding_book_status(slug),
    }
