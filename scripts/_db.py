#!/usr/bin/env python3
"""Postgres — multi-marca produção (Railway DATABASE_URL).

Schema:
  marca              — cadastro de marcas/clientes
  post               — posts do editor (1 linha por post)
  post_frame         — frames/cards do carrossel
  canal_conexao      — tokens OAuth Instagram/LinkedIn por marca
  publicacao_log     — histórico de publicações
  nota_publicacao    — notas .md do vault (opcional)
  arte_blob          — bytes das imagens (fundo web + arte final), endereçados por sha256

Sem DATABASE_URL: no-op (sistema usa arquivos).
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Optional

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS marca (
  slug            TEXT PRIMARY KEY,
  nome            TEXT NOT NULL DEFAULT '',
  handle          TEXT NOT NULL DEFAULT '',
  acento          TEXT NOT NULL DEFAULT '',
  acento_claro    TEXT NOT NULL DEFAULT '',
  base_escura     TEXT NOT NULL DEFAULT '',
  wordmark        TEXT NOT NULL DEFAULT '',
  glyph           TEXT NOT NULL DEFAULT '',
  segmento        TEXT NOT NULL DEFAULT '',
  site            TEXT NOT NULL DEFAULT '',
  papel           TEXT NOT NULL DEFAULT 'cliente',
  gradiente       TEXT NOT NULL DEFAULT '',
  meta            JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post (
  id              BIGSERIAL PRIMARY KEY,
  marca           TEXT NOT NULL REFERENCES marca(slug) ON DELETE CASCADE,
  slug            TEXT NOT NULL,
  titulo          TEXT NOT NULL DEFAULT '',
  size            TEXT NOT NULL DEFAULT '1080x1350',
  status          TEXT NOT NULL DEFAULT 'rascunho',
  caption         TEXT NOT NULL DEFAULT '',
  canais          JSONB NOT NULL DEFAULT '["instagram"]',
  payload         JSONB NOT NULL DEFAULT '{}',
  agendado_para   TIMESTAMPTZ,
  aprovado_em     TIMESTAMPTZ,
  aprovado_por    TEXT NOT NULL DEFAULT '',
  publicado_em    TIMESTAMPTZ,
  tentativas      INT NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (marca, slug)
);
-- O índice de agenda NÃO entra aqui: numa base que já existe, o CREATE TABLE
-- acima é no-op e a coluna `agendado_para` só nasce nos ALTER lá embaixo. Um
-- CREATE INDEX sobre coluna inexistente aborta o lote INTEIRO — inclusive os
-- ALTER que ainda viriam. Foi exatamente o que travou a migração em produção.

-- Trilha de quem mexeu no status. O aceite do cliente é a peça mais sensível do
-- fluxo: precisa ficar registrado quem aprovou, quando e com que comentário —
-- senão vira a palavra de um contra a do outro.
CREATE TABLE IF NOT EXISTS post_evento (
  id              BIGSERIAL PRIMARY KEY,
  marca           TEXT NOT NULL,
  slug            TEXT NOT NULL,
  de              TEXT NOT NULL DEFAULT '',
  para            TEXT NOT NULL,
  por             TEXT NOT NULL DEFAULT 'time',
  comentario      TEXT NOT NULL DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_post_evento ON post_evento (marca, slug, created_at DESC);

CREATE TABLE IF NOT EXISTS post_frame (
  id              BIGSERIAL PRIMARY KEY,
  post_id         BIGINT NOT NULL REFERENCES post(id) ON DELETE CASCADE,
  n               INT NOT NULL DEFAULT 1,
  headline        TEXT NOT NULL DEFAULT '',
  sub             TEXT NOT NULL DEFAULT '',
  cta             TEXT NOT NULL DEFAULT '',
  tema            TEXT NOT NULL DEFAULT 'claro',
  bg              TEXT NOT NULL DEFAULT '',
  bgmode          TEXT NOT NULL DEFAULT 'claro',
  payload         JSONB NOT NULL DEFAULT '{}',
  UNIQUE (post_id, n)
);

CREATE TABLE IF NOT EXISTS canal_conexao (
  marca           TEXT NOT NULL REFERENCES marca(slug) ON DELETE CASCADE,
  canal           TEXT NOT NULL DEFAULT 'instagram',
  payload         JSONB NOT NULL DEFAULT '{}',
  username        TEXT,
  user_id         TEXT,
  conectado       BOOLEAN NOT NULL DEFAULT false,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (marca, canal)
);

CREATE TABLE IF NOT EXISTS publicacao_log (
  id              BIGSERIAL PRIMARY KEY,
  marca           TEXT NOT NULL,
  canal           TEXT NOT NULL DEFAULT 'instagram',
  post_id         BIGINT REFERENCES post(id) ON DELETE SET NULL,
  status          TEXT NOT NULL,
  media_id        TEXT,
  image_path      TEXT,
  image_url       TEXT,
  caption         TEXT,
  detalhe         JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nota_publicacao (
  id              BIGSERIAL PRIMARY KEY,
  marca           TEXT NOT NULL,
  canal           TEXT NOT NULL DEFAULT 'instagram',
  path            TEXT NOT NULL UNIQUE,
  titulo          TEXT NOT NULL DEFAULT '',
  frontmatter     JSONB NOT NULL DEFAULT '{}',
  body            TEXT NOT NULL DEFAULT '',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Imagens vivem aqui porque o deploy do Railway NÃO carrega as artes (limite de
-- upload). Endereçadas por sha256 do conteúdo: mesmo fundo em vários posts = 1 linha,
-- e a URL /bg/<sha>.jpg pode ser cacheada pra sempre (o conteúdo nunca muda).
CREATE TABLE IF NOT EXISTS arte_blob (
  sha             TEXT PRIMARY KEY,
  kind            TEXT NOT NULL DEFAULT 'bg',
  mime            TEXT NOT NULL DEFAULT 'image/jpeg',
  w               INT NOT NULL DEFAULT 0,
  h               INT NOT NULL DEFAULT 0,
  bytes           BYTEA NOT NULL,
  origem          TEXT NOT NULL DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_marca ON post (marca, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_arte_blob_kind ON arte_blob (kind, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_frame_post ON post_frame (post_id, n);
CREATE INDEX IF NOT EXISTS idx_publicacao_marca ON publicacao_log (marca, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nota_marca ON nota_publicacao (marca, canal);
"""


def database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if "railway.internal" in url and not os.environ.get("RAILWAY_ENVIRONMENT"):
        pub = (os.environ.get("DATABASE_PUBLIC_URL") or "").strip()
        if pub:
            return pub
    if not url:
        return (os.environ.get("DATABASE_PUBLIC_URL") or "").strip()
    return url


def disponivel() -> bool:
    return bool(database_url())


_SCHEMA_OK = False


@contextmanager
def conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    c = psycopg2.connect(
        database_url(),
        cursor_factory=RealDictCursor,
        connect_timeout=8,
        options="-c statement_timeout=30000",
    )
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


_MIGRATIONS = """
-- colunas que podem faltar se o schema foi criado em versão antiga
ALTER TABLE publicacao_log ADD COLUMN IF NOT EXISTS post_id BIGINT REFERENCES post(id) ON DELETE SET NULL;
ALTER TABLE post ADD COLUMN IF NOT EXISTS caption TEXT NOT NULL DEFAULT '';
ALTER TABLE post ADD COLUMN IF NOT EXISTS canais JSONB NOT NULL DEFAULT '["instagram"]';
ALTER TABLE post ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}';
ALTER TABLE post_frame ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}';
ALTER TABLE marca ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{}';
ALTER TABLE marca ADD COLUMN IF NOT EXISTS gradiente TEXT NOT NULL DEFAULT '';
ALTER TABLE marca ADD COLUMN IF NOT EXISTS papel TEXT NOT NULL DEFAULT 'cliente';
ALTER TABLE canal_conexao ADD COLUMN IF NOT EXISTS username TEXT;
ALTER TABLE canal_conexao ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE canal_conexao ADD COLUMN IF NOT EXISTS conectado BOOLEAN NOT NULL DEFAULT false;
-- fluxo de aprovação e agenda
ALTER TABLE post ADD COLUMN IF NOT EXISTS agendado_para TIMESTAMPTZ;
ALTER TABLE post ADD COLUMN IF NOT EXISTS aprovado_em TIMESTAMPTZ;
ALTER TABLE post ADD COLUMN IF NOT EXISTS aprovado_por TEXT NOT NULL DEFAULT '';
ALTER TABLE post ADD COLUMN IF NOT EXISTS publicado_em TIMESTAMPTZ;
ALTER TABLE post ADD COLUMN IF NOT EXISTS tentativas INT NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_post_agenda ON post (status, agendado_para)
  WHERE agendado_para IS NOT NULL;
"""


def init_schema() -> dict:
    global _SCHEMA_OK
    if not disponivel():
        return {"ok": False, "erro": "DATABASE_URL ausente"}
    if _SCHEMA_OK:
        return {"ok": True, "schema": "cached"}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(_SCHEMA)
            cur.execute(_MIGRATIONS)
    _SCHEMA_OK = True
    return {"ok": True, "schema": "marca,post,post_evento,post_frame,canal_conexao,"
                                  "publicacao_log,nota_publicacao,arte_blob"}


# ── fluxo de aprovação ────────────────────────────────────────────────────────
#
# Um post caminha assim:
#
#   rascunho ──enviar──► revisao ──cliente aprova──► aprovado ──marca data──► agendado
#                          ▲  │                         │                        │
#            (time edita)   │  └──cliente pede ajuste──► ajuste                   │
#                          └──────────────────────────────┘                       │
#                                                    publicado ◄──worker/manual───┘
#
# A regra que dá segurança ao cliente: **só sai de `aprovado` pra `agendado` ou
# `publicado`**. Não existe caminho de rascunho direto pro ar.
#
# `salvo` é o estado que o editor já usava antes deste fluxo existir ("terminei
# de montar a peça", botão Salvar) e vale pra maioria dos 48 posts do vault. Ele
# entra aqui como etapa interna — sem isso todo post existente começaria fora da
# máquina de estados e nenhuma transição seria permitida.
STATUS_VALIDOS = ("rascunho", "salvo", "revisao", "ajuste", "aprovado", "agendado",
                  "publicado", "erro")

# Rótulos de tela. Ficam aqui pra que servidor, painel e worker falem a mesma
# língua — em pt-BR, do jeito que o cliente entende.
STATUS_LABEL = {
    "rascunho":  "Rascunho",
    "salvo":     "Pronto",
    "revisao":   "Em revisão",
    "ajuste":    "Pedido de ajuste",
    "aprovado":  "Aprovado",
    "agendado":  "Agendado",
    "publicado": "Publicado",
    "erro":      "Falhou",
}

TRANSICOES = {
    "rascunho":  ("salvo", "revisao", "aprovado"),   # aprovado = a própria smark assina
    "salvo":     ("revisao", "aprovado", "rascunho"),
    "revisao":   ("aprovado", "ajuste", "rascunho"),
    "ajuste":    ("revisao", "salvo", "rascunho"),
    "aprovado":  ("agendado", "publicado", "rascunho", "ajuste"),
    "agendado":  ("publicado", "aprovado", "erro", "ajuste"),
    "erro":      ("agendado", "aprovado", "rascunho"),
    "publicado": (),                            # fim de linha; duplicar pra refazer
}


def transicao_ok(de: str, para: str) -> bool:
    de = (de or "rascunho").strip() or "rascunho"
    return para in TRANSICOES.get(de, ())


def proximos(de: str) -> tuple:
    """Pra onde este post pode ir. A UI monta os botões a partir disto."""
    return TRANSICOES.get((de or "rascunho").strip() or "rascunho", ())


def mudar_status(marca: str, slug: str, para: str, *, por: str = "time",
                 comentario: str = "", agendado_para=None, forcar: bool = False) -> dict:
    """Muda o status de um post respeitando as transições e registrando quem foi."""
    para = (para or "").strip()
    if para not in STATUS_VALIDOS:
        return {"ok": False, "erro": "status inválido: %s" % para}
    if not disponivel():
        return {"ok": False, "erro": "sem banco"}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT status FROM post WHERE marca=%s AND slug=%s", (marca, slug))
            row = cur.fetchone()
            if not row:
                return {"ok": False, "erro": "post não encontrado"}
            de = row[0] if not isinstance(row, dict) else row["status"]
            de = de or "rascunho"
            if de == para:
                return {"ok": True, "de": de, "para": para, "sem_mudanca": True}
            if not forcar and not transicao_ok(de, para):
                return {"ok": False, "erro": "transição não permitida: %s → %s" % (de, para),
                        "de": de}
            sets = ["status=%s", "updated_at=NOW()"]
            vals = [para]
            if para == "aprovado":
                sets += ["aprovado_em=NOW()", "aprovado_por=%s"]
                vals.append(por or "")
            if para == "agendado":
                if not agendado_para:
                    return {"ok": False, "erro": "agendar exige data/hora"}
                sets.append("agendado_para=%s")
                vals.append(agendado_para)
                sets.append("tentativas=0")
            if para == "publicado":
                sets += ["publicado_em=NOW()", "agendado_para=NULL"]
            if para in ("rascunho", "ajuste"):
                sets.append("agendado_para=NULL")
            vals += [marca, slug]
            cur.execute("UPDATE post SET %s WHERE marca=%%s AND slug=%%s" % ",".join(sets), vals)
            cur.execute(
                "INSERT INTO post_evento (marca, slug, de, para, por, comentario) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (marca, slug, de, para, por or "", (comentario or "")[:2000]))
    return {"ok": True, "de": de, "para": para}


def aplicar_status(marca: str, slug: str, para: str, *, por: str = "",
                   aprovado_em=None, agendado_para=None, publicado_em=None,
                   aprovado_por=None, comentario: str = "", de: str = "") -> dict:
    """Grava status + datas do fluxo direto na linha do post, e o evento junto.

    Por que não deixar o upsert em lote fazer isso: o lote passa por
    `_ensure_marca_cur` e reescreve os frames de 48 posts numa transação só. Sob
    dois escritores (Mac + app no Railway) ele bate em lock na tabela `marca` e
    o savepoint desfaz **aquele** post — em produção isso apareceu como
    "aprovei e voltou pra Pronto no dia seguinte", porque o boot reconstrói o
    editor.json a partir do banco. Aprovação de cliente não pode viajar de
    carona num batch que às vezes cai.

    Este UPDATE toca uma linha, uma tabela, sem índice novo. É rápido e sozinho.
    """
    if not disponivel():
        return {"ok": False, "erro": "sem banco"}
    sets = ["status=%s", "updated_at=NOW()"]
    vals: list = [para]
    for col, val in (("aprovado_em", aprovado_em), ("agendado_para", agendado_para),
                     ("publicado_em", publicado_em)):
        if val is not None:
            sets.append("%s=%%s" % col)
            vals.append(val or None)     # "" limpa a data
    # `por` é o autor do evento; `aprovado_por` é a coluna. None = não mexe,
    # "" = limpa (voltou atrás, a aprovação não vale mais).
    quem = aprovado_por if aprovado_por is not None else (por or None)
    if quem is not None:
        sets.append("aprovado_por=%s")
        vals.append(quem[:120])       # coluna é NOT NULL DEFAULT '': limpar é '', não NULL
    if para == "agendado":
        sets.append("tentativas=0")
    vals += [marca, slug]
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute("UPDATE post SET %s WHERE marca=%%s AND slug=%%s"
                            % ",".join(sets), vals)
                n = cur.rowcount
                cur.execute(
                    "INSERT INTO post_evento (marca, slug, de, para, por, comentario) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (marca, slug, de or "", para, por or "time", (comentario or "")[:2000]))
        return {"ok": n > 0, "linhas": n}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


def registrar_evento(marca: str, slug: str, de: str, para: str, *,
                     por: str = "time", comentario: str = "") -> bool:
    """Grava a mudança na trilha, sem tocar no post.

    Existe separado de `mudar_status` porque no Mac quem manda no status é o
    `editor.json` — o banco recebe o post inteiro pelo upsert. A trilha, essa
    sim, só existe aqui: é o que responde "quem aprovou e quando".
    """
    if not disponivel():
        return False
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute(
                    "INSERT INTO post_evento (marca, slug, de, para, por, comentario) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (marca, slug, de or "", para, por or "", (comentario or "")[:2000]))
        return True
    except Exception:
        return False


def eventos_do_post(marca: str, slug: str, limite: int = 50) -> list:
    if not disponivel():
        return []
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT de, para, por, comentario, created_at FROM post_evento "
                "WHERE marca=%s AND slug=%s ORDER BY created_at DESC LIMIT %s",
                (marca, slug, int(limite)))
            return [dict(r) for r in cur.fetchall()]


def posts_vencidos(agora=None, limite: int = 20) -> list:
    """Posts agendados cuja hora chegou. É o que o worker publica.

    Só devolve `agendado` — um post que voltou pra ajuste some da fila sozinho.
    """
    if not disponivel():
        return []
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT marca, slug, titulo, caption, payload, agendado_para, tentativas "
                "FROM post WHERE status='agendado' AND agendado_para IS NOT NULL "
                "AND agendado_para <= COALESCE(%s, NOW()) "
                "ORDER BY agendado_para ASC LIMIT %s", (agora, int(limite)))
            return [dict(r) for r in cur.fetchall()]


def _ensure_marca_cur(cur, slug: str, meta: Optional[dict] = None) -> None:
    if not slug:
        return
    meta = meta or {}
    cur.execute(
        """
        INSERT INTO marca (slug, nome, handle, acento, acento_claro, base_escura,
                          wordmark, glyph, segmento, site, papel, gradiente, meta, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,NOW())
        ON CONFLICT (slug) DO UPDATE SET
          nome=COALESCE(NULLIF(EXCLUDED.nome,''), marca.nome),
          handle=COALESCE(NULLIF(EXCLUDED.handle,''), marca.handle),
          acento=COALESCE(NULLIF(EXCLUDED.acento,''), marca.acento),
          acento_claro=COALESCE(NULLIF(EXCLUDED.acento_claro,''), marca.acento_claro),
          base_escura=COALESCE(NULLIF(EXCLUDED.base_escura,''), marca.base_escura),
          wordmark=COALESCE(NULLIF(EXCLUDED.wordmark,''), marca.wordmark),
          glyph=COALESCE(NULLIF(EXCLUDED.glyph,''), marca.glyph),
          segmento=COALESCE(NULLIF(EXCLUDED.segmento,''), marca.segmento),
          site=COALESCE(NULLIF(EXCLUDED.site,''), marca.site),
          papel=COALESCE(NULLIF(EXCLUDED.papel,''), marca.papel),
          gradiente=COALESCE(NULLIF(EXCLUDED.gradiente,''), marca.gradiente),
          meta=marca.meta || EXCLUDED.meta,
          updated_at=NOW()
        """,
        (
            slug,
            meta.get("nome") or slug,
            meta.get("handle") or ("@" + slug.replace("-", "")),
            meta.get("acento") or "",
            meta.get("acento_claro") or "",
            meta.get("base_escura") or "",
            meta.get("wordmark") or "",
            str(meta.get("glyph") if meta.get("glyph") is not None else "")[:8],
            meta.get("segmento") or "",
            meta.get("site") or "",
            meta.get("papel") or "cliente",
            meta.get("gradiente") or "",
            json.dumps(meta, ensure_ascii=False),
        ),
    )


def ensure_marca(slug: str, meta: Optional[dict] = None) -> None:
    if not disponivel() or not slug:
        return
    with conn() as c:
        with c.cursor() as cur:
            _ensure_marca_cur(cur, slug, meta)


def _upsert_post_cur(cur, post: dict, marcas_ok: Optional[set] = None) -> Optional[int]:
    marca = (post.get("marca") or "smark").strip()
    slug = (post.get("slug") or "").strip()
    if not slug:
        return None
    if marcas_ok is None or marca not in marcas_ok:
        _ensure_marca_cur(cur, marca)
        if marcas_ok is not None:
            marcas_ok.add(marca)
    frames = post.get("frames") or []
    canais = post.get("canais") or ["instagram"]
    payload = {k: v for k, v in post.items() if k not in ("frames",)}
    # As datas do fluxo viajam no payload (JSONB) e também em colunas próprias.
    # A duplicação é de propósito: o worker de agenda pergunta "o que vence
    # agora?" por índice — dentro do JSONB isso seria varredura de tabela.
    cur.execute(
        """
        INSERT INTO post (marca, slug, titulo, size, status, caption, canais, payload,
                          agendado_para, aprovado_em, aprovado_por, publicado_em, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,NOW())
        ON CONFLICT (marca, slug) DO UPDATE SET
          titulo=EXCLUDED.titulo,
          size=EXCLUDED.size,
          caption=EXCLUDED.caption,
          canais=EXCLUDED.canais,
          payload=EXCLUDED.payload,
          updated_at=NOW()
        RETURNING id
        """,
        (
            marca,
            slug,
            post.get("titulo") or slug,
            post.get("size") or "1080x1350",
            post.get("status") or "rascunho",
            post.get("caption") or "",
            json.dumps(canais, ensure_ascii=False),
            json.dumps(payload, ensure_ascii=False),
            post.get("agendado_para") or None,
            post.get("aprovado_em") or None,
            post.get("aprovado_por") or "",
            post.get("publicado_em") or None,
        ),
    )
    row = cur.fetchone()
    post_id = int(row["id"])
    cur.execute("DELETE FROM post_frame WHERE post_id=%s", (post_id,))
    for i, fr in enumerate(frames):
        n = int(fr.get("n") or (i + 1))
        cur.execute(
            """
            INSERT INTO post_frame (post_id, n, headline, sub, cta, tema, bg, bgmode, payload)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            """,
            (
                post_id,
                n,
                fr.get("headline") or "",
                fr.get("sub") or "",
                fr.get("cta") or "",
                fr.get("tema") or "claro",
                fr.get("bg") or "",
                fr.get("bgmode") or fr.get("tema") or "claro",
                json.dumps(fr, ensure_ascii=False),
            ),
        )
    return post_id


def upsert_post(post: dict) -> Optional[int]:
    """Insere/atualiza 1 post + frames. Devolve post_id."""
    if not disponivel():
        return None
    with conn() as c:
        with c.cursor() as cur:
            return _upsert_post_cur(cur, post)


def upsert_posts_batch(posts: list) -> dict:
    """Upsert de N posts numa única conexão/transação (rápido)."""
    import sys
    if not disponivel():
        return {"ok": False, "erro": "sem DB", "n": 0}
    if not posts:
        return {"ok": True, "n": 0}
    ok = 0
    err = 0
    marcas_ok: set = set()
    with conn() as c:
        with c.cursor() as cur:
            for p in posts:
                try:
                    cur.execute("SAVEPOINT sp_post")
                    if _upsert_post_cur(cur, p, marcas_ok):
                        ok += 1
                    cur.execute("RELEASE SAVEPOINT sp_post")
                except Exception as e:
                    err += 1
                    try:
                        cur.execute("ROLLBACK TO SAVEPOINT sp_post")
                    except Exception:
                        pass
                    print(f"  DB batch upsert {p.get('slug')}: {e}", file=sys.stderr)
    return {"ok": err == 0, "n": ok, "erros": err}


def load_posts_as_editor() -> dict:
    """Reconstrói editor.json a partir do DB (fonte canônica em produção)."""
    if not disponivel():
        return {"posts": []}
    # schema só na 1ª vez do processo
    init_schema()
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT id, payload, marca, slug, titulo, size, status, caption, canais, "
                "agendado_para, aprovado_em, aprovado_por, publicado_em "
                "FROM post ORDER BY updated_at DESC"
            )
            rows = cur.fetchall() or []
            if not rows:
                return {"posts": [], "version": 2, "source": "postgres"}
            ids = [r["id"] for r in rows]
            # 1 query de frames p/ todos os posts (evita N+1 — era a lentidão do /dados)
            cur.execute(
                "SELECT post_id, payload, n FROM post_frame "
                "WHERE post_id IN %s ORDER BY post_id, n",
                (tuple(ids),),
            )
            frs_all = cur.fetchall() or []
            by_post: dict = {}
            for f in frs_all:
                pl = f["payload"]
                if isinstance(pl, str):
                    pl = json.loads(pl)
                by_post.setdefault(f["post_id"], []).append(
                    pl if isinstance(pl, dict) else {"n": f["n"]}
                )
            posts = []
            for r in rows:
                p = r["payload"]
                if isinstance(p, str):
                    p = json.loads(p)
                if not isinstance(p, dict):
                    p = {}
                canais = r["canais"]
                if isinstance(canais, str):
                    canais = json.loads(canais or "[]")
                p.update({
                    "marca": r["marca"],
                    "slug": r["slug"],
                    "titulo": r["titulo"],
                    "size": r["size"],
                    "status": r["status"],
                    "caption": r["caption"] or p.get("caption") or "",
                    "canais": canais if isinstance(canais, list) else ["instagram"],
                    "frames": by_post.get(r["id"]) or [],
                })
                # Coluna manda sobre payload: quem publica é o worker, e ele só
                # carimba a coluna. Se o payload vencesse, a data de publicação
                # sumiria no primeiro save vindo do editor.
                for _c in ("agendado_para", "aprovado_em", "publicado_em"):
                    _v = r.get(_c)
                    p[_c] = _v.isoformat() if hasattr(_v, "isoformat") else (_v or "")
                p["aprovado_por"] = r.get("aprovado_por") or ""
                posts.append(p)
            return {"posts": posts, "version": 2, "source": "postgres"}


def contagens() -> dict:
    if not disponivel():
        return {}
    with conn() as c:
        with c.cursor() as cur:
            out = {}
            for t in ("marca", "post", "post_frame", "canal_conexao", "publicacao_log",
                      "nota_publicacao", "arte_blob"):
                cur.execute(f"SELECT COUNT(*) AS n FROM {t}")
                out[t] = int(cur.fetchone()["n"])
            return out


# ── arte_blob (imagens) ─────────────────────────────────────────────────────

def blob_existe(shas: list) -> set:
    """Quais desses sha já estão no banco. Evita reenviar o que não mudou."""
    if not shas or not disponivel():
        return set()
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT sha FROM arte_blob WHERE sha = ANY(%s)", (list(shas),))
            return {r["sha"] for r in cur.fetchall()}


def blob_put(sha: str, data: bytes, kind: str = "bg", mime: str = "image/jpeg",
             w: int = 0, h: int = 0, origem: str = "") -> bool:
    """Grava um blob. Idempotente: sha igual = conteúdo igual, não reescreve."""
    if not disponivel() or not data:
        return False
    import psycopg2
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO arte_blob (sha, kind, mime, w, h, bytes, origem)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sha) DO NOTHING
                """,
                (sha, kind, mime, int(w), int(h), psycopg2.Binary(data), origem or ""),
            )
    return True


def blob_get(sha: str) -> Optional[dict]:
    """Devolve {bytes, mime, kind} ou None."""
    if not disponivel() or not sha:
        return None
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT sha, kind, mime, w, h, bytes FROM arte_blob WHERE sha = %s", (sha,))
            r = cur.fetchone()
            if not r:
                return None
            return {"sha": r["sha"], "kind": r["kind"], "mime": r["mime"],
                    "w": r["w"], "h": r["h"], "bytes": bytes(r["bytes"])}


def blob_stats() -> dict:
    if not disponivel():
        return {}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT kind, COUNT(*) AS n, COALESCE(SUM(LENGTH(bytes)),0) AS b "
                "FROM arte_blob GROUP BY kind"
            )
            return {r["kind"]: {"n": int(r["n"]), "bytes": int(r["b"])} for r in cur.fetchall()}


# ── canais (tokens) ─────────────────────────────────────────────────────────

def canal_salvar(marca: str, canal: str, payload: dict) -> None:
    if not disponivel():
        return
    ensure_marca(marca)
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO canal_conexao (marca, canal, payload, username, user_id, conectado, updated_at)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s, NOW())
                ON CONFLICT (marca, canal) DO UPDATE SET
                  payload = EXCLUDED.payload,
                  username = EXCLUDED.username,
                  user_id = EXCLUDED.user_id,
                  conectado = EXCLUDED.conectado,
                  updated_at = NOW()
                """,
                (
                    marca,
                    canal,
                    json.dumps(payload, ensure_ascii=False),
                    payload.get("username") or "",
                    str(payload.get("user_id") or ""),
                    bool(payload.get("connected")),
                ),
            )


def canal_carregar(marca: str, canal: str = "instagram") -> dict:
    if not disponivel():
        return {}
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM canal_conexao WHERE marca=%s AND canal=%s",
                    (marca, canal),
                )
                row = cur.fetchone()
                if not row:
                    return {}
                p = row["payload"]
                if isinstance(p, str):
                    return json.loads(p)
                return dict(p or {})
    except Exception:
        return {}


def canais_todos() -> dict:
    """Todos os vínculos de canal numa consulta: {(marca, canal): payload}.

    O `/marcas` chamava `canal_carregar` por marca × canal — 16 marcas × 2
    canais = 32 conexões novas ao proxy do Railway, ~2s cada. O painel local
    levava 65 s pra pintar porque esperava por isso antes de renderizar.
    """
    if not disponivel():
        return {}
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute("SELECT marca, canal, payload FROM canal_conexao")
                out = {}
                for r in cur.fetchall() or []:
                    p = r["payload"]
                    if isinstance(p, str):
                        p = json.loads(p or "{}")
                    out[(r["marca"], r["canal"])] = dict(p or {})
                return out
    except Exception:
        return {}


def canal_apagar(marca: str, canal: str = "instagram") -> None:
    if not disponivel():
        return
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute(
                    "DELETE FROM canal_conexao WHERE marca=%s AND canal=%s",
                    (marca, canal),
                )
    except Exception:
        pass


def publicacao_log(marca: str, canal: str, status: str, **kw) -> None:
    if not disponivel():
        return
    try:
        with conn() as c:
            with c.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO publicacao_log
                      (marca, canal, status, media_id, image_path, image_url, caption, detalhe)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                    """,
                    (
                        marca,
                        canal,
                        status,
                        kw.get("media_id"),
                        kw.get("image_path"),
                        kw.get("image_url"),
                        kw.get("caption"),
                        json.dumps(kw.get("detalhe") or {}, ensure_ascii=False),
                    ),
                )
    except Exception:
        pass
