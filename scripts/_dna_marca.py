#!/usr/bin/env python3
"""DNA de marca a partir de URL — inteligência do legacy (v2), enxuta pro smark.

Não muda o fluxo do studio: só propõe campos (nome, handle, mood, segmento…).
O humano revisa e salva no form de marca como sempre.

Origem:
  - /Users/andreik/dev/ia/backend/services/dna_service.py (crawl limpo + schema pt-BR)
  - LLM via mesmo padrão do estudio.py (Claude ou OpenAI no .env)

Sem dependências novas (sem BeautifulSoup): urllib + html.parser.
"""
from __future__ import annotations

import html as htmlmod
import json
import os
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Optional

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Subpáginas comuns (legado v2) — no máx. 3 além da home
SUBPAGES = ("/sobre", "/about", "/produto", "/solucao", "/pricing", "/features", "/como-funciona")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; smark-studio/1.0; +local)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
}

SEGMENTOS = (
    "contabilidade", "telecom", "varejo", "imobiliaria", "saude",
    "servicos", "educacao", "industria", "outro",
)


class _TextExtractor(HTMLParser):
    """Extrai texto visível + meta description/title, sem script/style."""

    SKIP = {"script", "style", "noscript", "svg", "path"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self.parts: list[str] = []
        self.title = ""
        self.meta_desc = ""
        self.og_image = ""
        self.theme_color = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.SKIP:
            self._skip += 1
            return
        if t == "title":
            self._in_title = True
        ad = {k.lower(): (v or "") for k, v in attrs}
        if t == "meta":
            name = (ad.get("name") or ad.get("property") or "").lower()
            content = ad.get("content") or ""
            if name in ("description", "og:description", "twitter:description") and content:
                if not self.meta_desc or name.startswith("og:"):
                    self.meta_desc = content.strip()
            if name in ("og:image", "twitter:image") and content and not self.og_image:
                self.og_image = content.strip()
            if name == "theme-color" and content:
                self.theme_color = content.strip()
        if t == "link" and ad.get("rel", "").lower() in ("icon", "shortcut icon", "apple-touch-icon"):
            href = ad.get("href") or ""
            if href and not self.og_image:
                self.og_image = href  # fallback visual fraco

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.SKIP and self._skip:
            self._skip -= 1
        if t == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip:
            return
        s = re.sub(r"\s+", " ", data or "").strip()
        if not s:
            return
        if self._in_title and not self.title:
            self.title = s
        self.parts.append(s)


def _load_env():
    env = {}
    p = os.path.join(VAULT, ".env")
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _fetch(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        charset = "utf-8"
        ct = r.headers.get_content_charset()
        if ct:
            charset = ct
        try:
            return raw.decode(charset, errors="replace")
        except Exception:
            return raw.decode("utf-8", errors="replace")


def _html_to_text(html: str) -> dict:
    p = _TextExtractor()
    try:
        p.feed(html)
        p.close()
    except Exception:
        pass
    text = " ".join(p.parts)
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "title": p.title,
        "meta_desc": p.meta_desc,
        "og_image": p.og_image,
        "theme_color": p.theme_color,
        "text": text[:3500],
    }


def crawl(url: str) -> dict:
    """Crawl home + até 3 subpáginas. Devolve texto limpo + metas."""
    url = (url or "").strip()
    if not url:
        raise ValueError("URL vazia")
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    url = url.rstrip("/")

    chunks = []
    meta = {"title": "", "meta_desc": "", "og_image": "", "theme_color": "", "pages": []}
    try:
        html = _fetch(url)
        d = _html_to_text(html)
        meta.update({k: d[k] for k in ("title", "meta_desc", "og_image", "theme_color") if d.get(k)})
        if d["text"]:
            chunks.append(d["text"])
        meta["pages"].append(url)
    except Exception as e:
        raise ValueError(f"Não consegui abrir o site: {e}") from e

    for sub in SUBPAGES:
        if len(chunks) >= 4:
            break
        try:
            html = _fetch(url + sub, timeout=8)
            d = _html_to_text(html)
            if d["text"] and len(d["text"]) > 120:
                chunks.append(d["text"][:2000])
                meta["pages"].append(url + sub)
        except Exception:
            continue

    content = "\n\n".join(chunks)[:8000]
    if len(content) < 80:
        raise ValueError("Site quase sem texto legível (pode ser só JavaScript). Cole o site ou envie referências.")
    meta["content"] = content
    meta["url"] = url
    return meta


DNA_PROMPT = """Você é especialista em branding B2B no Brasil.
Analise o conteúdo do site e extraia o essencial da marca para preencher um cadastro de studio de conteúdo.

URL: {url}
TÍTULO: {title}
META: {meta_desc}

CONTEÚDO:
{content}

Retorne APENAS um JSON válido (sem markdown) com esta estrutura:
{{
  "nome": "nome comercial da marca",
  "handle": "@semespacos",
  "segmento": "um de: contabilidade|telecom|varejo|imobiliaria|saude|servicos|educacao|industria|outro",
  "mood": "1-2 frases em português descrevendo o clima visual e de arte (sem jargão vazio)",
  "wordmark": "nome curto pro chip da arte",
  "proposta": "proposta de valor em 1 frase",
  "publico": "público-alvo em 1 frase",
  "tom": "tom de voz em poucas palavras",
  "restricoes": ["o que evitar na comunicação"],
  "confianca": {{
    "nome": "Alta|Média|Baixa",
    "mood": "Alta|Média|Baixa",
    "segmento": "Alta|Média|Baixa",
    "proposta": "Alta|Média|Baixa"
  }}
}}

Regras:
- Português do Brasil.
- handle só [a-z0-9] após @, minúsculo.
- mood serve para gerar fundo de IA: concreto e visual.
- Não invente números ou prêmios que não estejam no texto.
- Se incerto, confianca Baixa e valor conservador.
"""


def _post_json(url, headers, body, timeout=90):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:400]}") from e


def _parse_json_loose(txt: str) -> dict:
    s = (txt or "").strip()
    if s.startswith("```"):
        parts = s.split("```")
        s = parts[1] if len(parts) > 1 else s
        if s.startswith("json"):
            s = s[4:]
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("resposta sem JSON")
    return json.loads(s[i:j + 1])


def _llm_json(prompt: str) -> tuple[dict, dict]:
    """Claude → OpenAI. Devolve (json, meta)."""
    env = _load_env()
    ant = os.environ.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY")
    oai = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    meta = {"ok": False, "custo_usd": None, "provider": None, "modelo": None}

    if ant:
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        # DNA é tarefa barata: sonnet default (override via env)
        data = _post_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": ant, "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
            {"model": model, "max_tokens": 2000,
             "messages": [{"role": "user", "content": prompt}]},
        )
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        usage = data.get("usage") or {}
        try:
            import _custo_llm  # noqa: E402
            custo = _custo_llm.custo_tokens(
                model, int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0))
        except Exception:
            custo = None
        meta.update({"ok": True, "provider": "anthropic", "modelo": model, "custo_usd": custo})
        return _parse_json_loose("".join(parts)), meta

    if oai:
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        data = _post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {oai}", "Content-Type": "application/json"},
            {"model": model, "temperature": 0.3,
             "response_format": {"type": "json_object"},
             "messages": [
                 {"role": "system", "content": "Retorne só JSON válido."},
                 {"role": "user", "content": prompt},
             ]},
        )
        usage = data.get("usage") or {}
        try:
            import _custo_llm  # noqa: E402
            custo = _custo_llm.custo_tokens(
                model, int(usage.get("prompt_tokens") or 0),
                int(usage.get("completion_tokens") or 0))
        except Exception:
            custo = None
        meta.update({"ok": True, "provider": "openai", "modelo": model, "custo_usd": custo})
        return _parse_json_loose(data["choices"][0]["message"]["content"]), meta

    raise RuntimeError("Sem chave de IA: coloque ANTHROPIC_API_KEY ou OPENAI_API_KEY no .env")


def _sanea(raw: dict, crawled: dict) -> dict:
    nome = str(raw.get("nome") or crawled.get("title") or "").strip()[:80]
    # limpa title tipo "Home | Empresa"
    if "|" in nome:
        parts = [p.strip() for p in nome.split("|") if p.strip()]
        if parts:
            nome = parts[0] if len(parts[0]) > 3 else parts[-1]
    handle = str(raw.get("handle") or "").strip().lower()
    handle = re.sub(r"[^a-z0-9@]", "", handle)
    if handle and not handle.startswith("@"):
        handle = "@" + handle
    if not handle and nome:
        base = re.sub(r"[^a-z0-9]", "", nome.lower().replace(" ", ""))[:24]
        handle = "@" + base if base else ""

    seg = str(raw.get("segmento") or "outro").strip().lower()
    if seg not in SEGMENTOS:
        seg = "outro"

    mood = str(raw.get("mood") or "").strip()[:400]
    if not mood and nome:
        mood = f"visual limpo e profissional da marca {nome} — alinhado ao site e à identidade"

    wordmark = str(raw.get("wordmark") or nome).strip()[:40]
    conf = raw.get("confianca") if isinstance(raw.get("confianca"), dict) else {}

    # score simples
    weights = {"Alta": 100, "Média": 60, "Baixa": 30}
    scores = []
    for k in ("nome", "mood", "segmento", "proposta"):
        scores.append(weights.get(str(conf.get(k, "Média")), 60))
    score = int(round(sum(scores) / len(scores))) if scores else 50

    # theme-color do site → sugestão de acento se hex
    acento = ""
    tc = (crawled.get("theme_color") or "").strip()
    m = re.match(r"#?[0-9A-Fa-f]{6}$", tc)
    if m:
        acento = tc if tc.startswith("#") else ("#" + tc)
        acento = acento.upper()

    return {
        "nome": nome,
        "handle": handle,
        "segmento": seg,
        "mood": mood,
        "wordmark": wordmark,
        "proposta": str(raw.get("proposta") or "").strip()[:300],
        "publico": str(raw.get("publico") or "").strip()[:300],
        "tom": str(raw.get("tom") or "").strip()[:120],
        "restricoes": [str(x).strip() for x in (raw.get("restricoes") or []) if str(x).strip()][:8],
        "confianca": conf,
        "score": score,
        "site": crawled.get("url") or "",
        "acento_sugerido": acento,
        "og_image": crawled.get("og_image") or "",
        "paginas_lidas": crawled.get("pages") or [],
        "title_site": crawled.get("title") or "",
    }


def extrair_de_url(url: str) -> dict:
    """Pipeline completo: crawl + LLM + saneamento.

    Devolve dict pronto para a UI (campos do form de marca + extras informativos).
    """
    crawled = crawl(url)
    prompt = DNA_PROMPT.format(
        url=crawled.get("url", url),
        title=crawled.get("title") or "",
        meta_desc=crawled.get("meta_desc") or "",
        content=crawled.get("content") or "",
    )
    raw, meta = _llm_json(prompt)
    out = _sanea(raw if isinstance(raw, dict) else {}, crawled)
    out["meta_llm"] = meta
    return out


def para_formulario(dna: dict) -> dict:
    """Só os campos que o form de marca já entende (não grava sozinho)."""
    return {
        "nome": dna.get("nome") or "",
        "handle": dna.get("handle") or "",
        "segmento": dna.get("segmento") or "outro",
        "mood": dna.get("mood") or "",
        "wordmark": dna.get("wordmark") or "",
        "site": dna.get("site") or "",
        "acento": dna.get("acento_sugerido") or "",
    }


if __name__ == "__main__":
    import sys
    u = sys.argv[1] if len(sys.argv) > 1 else ""
    if not u:
        print("Uso: python3 scripts/_dna_marca.py https://cliente.com.br")
        sys.exit(1)
    d = extrair_de_url(u)
    print(json.dumps(d, ensure_ascii=False, indent=2))
