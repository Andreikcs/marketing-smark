#!/usr/bin/env python3
"""Postgres opcional — produção multi-cliente (Railway DATABASE_URL).

Se DATABASE_URL não existir, o sistema continua em arquivos (.secrets/, vault).
Schema mínimo para:
  - conexões de canais (tokens Instagram por marca)
  - fila / log de publicações
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS canal_conexao (
  marca       TEXT NOT NULL,
  canal       TEXT NOT NULL DEFAULT 'instagram',
  payload     JSONB NOT NULL DEFAULT '{}',
  username    TEXT,
  user_id     TEXT,
  conectado   BOOLEAN NOT NULL DEFAULT false,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (marca, canal)
);

CREATE TABLE IF NOT EXISTS publicacao_log (
  id          BIGSERIAL PRIMARY KEY,
  marca       TEXT NOT NULL,
  canal       TEXT NOT NULL DEFAULT 'instagram',
  status      TEXT NOT NULL,
  media_id    TEXT,
  image_path  TEXT,
  image_url   TEXT,
  caption     TEXT,
  detalhe     JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publicacao_marca ON publicacao_log (marca, created_at DESC);
"""


def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or "").strip()


def disponivel() -> bool:
    return bool(database_url())


def _dsn() -> str:
    """Railway internal URL; se rodar local, prefira DATABASE_PUBLIC_URL."""
    url = database_url()
    # local dev: se host for .railway.internal e não estiver na rede Railway, use public
    if "railway.internal" in url and not os.environ.get("RAILWAY_ENVIRONMENT"):
        pub = (os.environ.get("DATABASE_PUBLIC_URL") or "").strip()
        if pub:
            return pub
    return url


@contextmanager
def conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    c = psycopg2.connect(_dsn(), cursor_factory=RealDictCursor)
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_schema() -> dict:
    if not disponivel():
        return {"ok": False, "erro": "DATABASE_URL ausente"}
    with conn() as c:
        with c.cursor() as cur:
            cur.execute(_SCHEMA)
    return {"ok": True}


def canal_salvar(marca: str, canal: str, payload: dict) -> None:
    if not disponivel():
        return
    init_schema()
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
        init_schema()
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
        init_schema()
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
