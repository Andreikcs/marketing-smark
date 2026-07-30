#!/usr/bin/env python3
"""Canais sociais por marca/cliente (multi-tenant).

Cada marca conecta o PRÓPRIO Instagram (e, no futuro, LinkedIn) via OAuth.
Tokens ficam em `.secrets/canais/<marca>/` (gitignored) — nunca no vault público.

Instagram (Graph API com Instagram Login — 2025/2026):
  1. OAuth authorize → code
  2. code → short-lived token
  3. short → long-lived (60 dias) + refresh
  4. Publicar: create media container → media_publish
     (conta Business/Creator; permissão instagram_business_content_publish)

Modo fake (default sem app real):
  CANAIS_MODE=fake  ou  INSTAGRAM_APP_ID vazio
  → simula a janela de login e grava tokens de mentira.
  Amanhã: preencha INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET no .env e
  CANAIS_MODE=auto|real — o mesmo fluxo troca pro Meta de verdade.

LinkedIn: estrutura pronta (status "em breve"), sem OAuth ainda.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
SECRETS_DIR = os.path.join(VAULT, ".secrets", "canais")
PENDING_DIR = os.path.join(VAULT, ".secrets", "oauth_pending")

CANAIS = ("instagram", "linkedin")

# Scopes Instagram Business Login (nomes novos pós-2025)
IG_SCOPES = [
    "instagram_business_basic",
    "instagram_business_content_publish",
]

# Meta endpoints
IG_AUTHORIZE = "https://www.instagram.com/oauth/authorize"
IG_TOKEN = "https://api.instagram.com/oauth/access_token"
IG_GRAPH = "https://graph.instagram.com"


# ── env / modo ──────────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    v = (os.environ.get(key) or "").strip()
    if v:
        return v
    # fallback .env do vault
    env_path = os.path.join(VAULT, ".env")
    if os.path.isfile(env_path):
        try:
            for line in open(env_path, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, val = line.split("=", 1)
                if k.strip() == key:
                    return val.strip().strip('"').strip("'")
        except OSError:
            pass
    return default


def _norm_redirect(uri: str) -> str:
    """Mesma string no authorize e no exchange (Meta é pedante)."""
    u = (uri or "").strip()
    if len(u) > 8 and u.endswith("/"):
        u = u.rstrip("/")
    return u


def ig_app_config() -> dict:
    """Credenciais do app Meta (uma app da smark; clientes só autorizam).

    Em Railway, se INSTAGRAM_REDIRECT_URI não estiver setado, monta a partir
    de RAILWAY_PUBLIC_DOMAIN (HTTPS) — evita o erro clássico de redirect 127.0.0.1.

    Instagram Login: client_id = Instagram App ID; secret = Instagram App Secret
    (Business login settings) — não misturar com IDs/secrets de outro app.
    """
    redirect = (
        _env("INSTAGRAM_REDIRECT_URI")
        or _env("META_IG_REDIRECT_URI")
        or ""
    )
    if not redirect:
        pub = (_env("RAILWAY_PUBLIC_DOMAIN") or _env("PUBLIC_HOSTS") or "").split(",")[0].strip()
        if pub:
            if not pub.startswith("http"):
                pub = "https://" + pub
            redirect = pub.rstrip("/") + "/oauth/instagram/callback"
        else:
            redirect = "http://127.0.0.1:8765/oauth/instagram/callback"
    # Instagram Login exige o Instagram App ID (Business login settings),
    # NÃO o App ID do Facebook. Se só tiver o FB ID, a Meta retorna
    # "Invalid platform app".
    app_id = (
        _env("INSTAGRAM_PLATFORM_APP_ID")
        or _env("INSTAGRAM_APP_ID")
        or _env("META_IG_APP_ID")
    )
    return {
        "app_id": str(app_id or "").strip(),
        "app_secret": (_env("INSTAGRAM_APP_SECRET") or _env("META_IG_APP_SECRET") or "").strip(),
        "redirect_uri": _norm_redirect(redirect),
    }


def modo_instagram() -> str:
    """fake | real — real só se houver App ID e secret."""
    forced = (_env("CANAIS_MODE") or "auto").lower()
    cfg = ig_app_config()
    has_app = bool(cfg["app_id"] and cfg["app_secret"])
    if forced == "fake":
        return "fake"
    if forced == "real":
        return "real" if has_app else "fake"
    # auto
    return "real" if has_app else "fake"


# ── storage ─────────────────────────────────────────────────────────────────

def _marca_dir(marca: str) -> str:
    d = os.path.join(SECRETS_DIR, marca)
    os.makedirs(d, exist_ok=True)
    return d


def _path_token(marca: str, canal: str) -> str:
    return os.path.join(_marca_dir(marca), f"{canal}.json")


def _path_log(marca: str, canal: str) -> str:
    return os.path.join(_marca_dir(marca), f"{canal}_publish_log.jsonl")


def _load_json(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _path_conta(canal: str, user_id: str) -> str:
    """Onde o token de UMA conta mora. Uma conta serve N marcas."""
    d = os.path.join(SECRETS_DIR, "_contas")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{canal}-{user_id}.json")


def _persist_canal(marca: str, canal: str, data: dict) -> None:
    """Token na conta, vínculo na marca — arquivo local + Postgres.

    Duas marcas no mesmo Instagram é cenário normal (um dono, duas empresas).
    Antes o payload inteiro era copiado por marca: o refresh renovava uma cópia
    e a outra vencia calada, e cada marca exigia um OAuth novo na mesma conta.
    """
    user_id = str(data.get("user_id") or "").strip()
    if user_id and data.get("connected"):
        _save_json(_path_conta(canal, user_id), data)
        _save_json(_path_token(marca, canal),
                   {"canal": canal, "conta_user_id": user_id,
                    "username": data.get("username") or "",
                    "vinculado_em": _now_iso()})
    else:
        # token fake ou conexão pela metade: não há conta pra apontar
        _save_json(_path_token(marca, canal), data)
    try:
        import _db
        if _db.disponivel():
            _db.canal_salvar(marca, canal, data)
    except Exception:
        pass


def _load_canal(marca: str, canal: str) -> dict:
    """Prefere Postgres em produção; fallback arquivo.

    No arquivo, uma marca pode ser só um vínculo (`conta_user_id`) — nesse caso
    o token vem de `_contas/`. Arquivo legado (payload inteiro na marca) é
    promovido a conta na primeira leitura, pra ninguém precisar reconectar.
    """
    try:
        import _db
        if _db.disponivel():
            p = _db.canal_carregar(marca, canal)
            if p:
                return p
    except Exception:
        pass
    raw = _load_canal_arquivo(marca, canal)
    ja_e_conta = bool(raw.pop("_de_conta", False))   # marcador interno, não vaza
    uid = str(raw.get("user_id") or "").strip()
    if raw.get("connected") and uid and not ja_e_conta:
        try:
            _persist_canal(marca, canal, raw)  # migra: vira conta + vínculo
        except OSError:
            pass  # migrar é otimização; o payload em mãos já serve
    return raw


def _load_canal_arquivo(marca: str, canal: str) -> dict:
    """Só disco, sem banco: resolve o vínculo lendo `_contas/` do lado.

    Existe porque `status_todas` roda esta leitura 2× por marca. Chamar o
    `_load_canal` inteiro ali custava uma ida ao Postgres por marca × canal —
    com 13 marcas atrás do proxy do Railway, 47 s de espera pro painel pintar.
    """
    raw = _load_json(_path_token(marca, canal))
    link = str(raw.get("conta_user_id") or "").strip()
    if link:
        conta = _load_json(_path_conta(canal, link))
        if conta:
            conta = dict(conta)
            conta["_de_conta"] = True   # já é conta: não tentar migrar de novo
            return conta
    return raw


def contas_conectadas(canal: str = "instagram") -> list:
    """Contas disponíveis pra reuso + quais marcas já publicam por cada uma.

    É o que permite "conectar uma vez, usar em várias marcas": o /config lista
    isto em vez de mandar o usuário pro login de novo.

    Banco E disco somam, nunca um OU o outro: a gravação no Postgres pode falhar
    calada (proxy do Railway fora do ar) enquanto o arquivo local ficou correto.
    Se o banco fosse a única palavra, a conta acabada de conectar sumiria da tela
    e o usuário seria mandado pra um OAuth que não precisava.
    """
    achadas, ordem = {}, []

    def _pousar(uid, item):
        if not uid:
            return
        if uid in achadas:
            juntas = set(achadas[uid]["marcas"]) | set(item["marcas"])
            achadas[uid]["marcas"] = sorted(juntas)
            return
        achadas[uid] = item
        ordem.append(uid)

    try:
        import _db
        if _db.disponivel() and hasattr(_db, "contas_todas"):
            for c in _db.contas_todas(canal):
                p = c.get("payload") or {}
                uid = str(c.get("user_id") or "").strip()
                _pousar(uid, {
                    "canal": canal,
                    "user_id": uid,
                    "username": c.get("username") or p.get("username") or "",
                    "nome": p.get("nome") or "",
                    "picture": p.get("picture") or "",
                    "expira_em": p.get("expira_em") or "",
                    "modo": p.get("modo") or ("real" if p.get("access_token") else ""),
                    "permissoes": list(p.get("permissoes") or []),
                    "marcas": sorted(set(c.get("marcas") or [])),
                })
    except Exception:
        pass

    d = os.path.join(SECRETS_DIR, "_contas")
    if os.path.isdir(d):
        for nome in sorted(os.listdir(d)):
            if not nome.startswith(canal + "-") or not nome.endswith(".json"):
                continue
            p = _load_json(os.path.join(d, nome))
            uid = str(p.get("user_id") or "").strip()
            _pousar(uid, {
                "canal": canal, "user_id": uid,
                "username": p.get("username") or "", "nome": p.get("nome") or "",
                "picture": p.get("picture") or "", "expira_em": p.get("expira_em") or "",
                "modo": p.get("modo") or ("real" if p.get("access_token") else ""),
                "permissoes": list(p.get("permissoes") or []),
                "marcas": sorted(set(_marcas_da_conta_arquivo(canal, uid))),
            })
    return [achadas[u] for u in ordem]


def _marcas_da_conta_arquivo(canal: str, user_id: str) -> list:
    """Quem aponta pra essa conta, olhando só o disco."""
    out = []
    if not os.path.isdir(SECRETS_DIR):
        return out
    for m in sorted(os.listdir(SECRETS_DIR)):
        if m.startswith("_") or not os.path.isdir(os.path.join(SECRETS_DIR, m)):
            continue
        raw = _load_json(os.path.join(SECRETS_DIR, m, f"{canal}.json"))
        uid = str(raw.get("conta_user_id") or raw.get("user_id") or "").strip()
        if uid == str(user_id):
            out.append(m)
    return out


def marcas_da_conta(canal: str, user_id: str) -> list:
    """Todas as marcas que publicam por esta conta — banco MAIS disco.

    A união importa: quem vai ler isso é o aviso "esta conta também publica por
    X". Faltar uma marca aí é pior que sobrar — o usuário publicaria pensando
    que só uma empresa depende da conta.
    """
    achadas = set(_marcas_da_conta_arquivo(canal, user_id))
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "marcas_da_conta"):
            achadas |= set(_db.marcas_da_conta(canal, user_id) or [])
    except Exception:
        pass
    return sorted(achadas)


def vincular_marca(marca: str, canal: str, user_id: str) -> dict:
    """Liga a marca a uma conta que já existe. Sem OAuth, sem token novo."""
    canal = (canal or "instagram").lower().strip()
    if canal not in CANAIS:
        return {"ok": False, "erro": "canal inválido: %s" % canal}
    user_id = str(user_id or "").strip()
    conta = None
    for c in contas_conectadas(canal):
        if c["user_id"] == user_id:
            conta = c
            break
    if not conta:
        return {"ok": False, "erro": "conta não encontrada — conecte uma primeiro"}
    _save_json(_path_token(marca, canal),
               {"canal": canal, "conta_user_id": user_id,
                "username": conta.get("username") or "", "vinculado_em": _now_iso()})
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "marca_vincular"):
            _db.marca_vincular(marca, canal, user_id, conta.get("username") or "")
    except Exception as e:
        return {"ok": False, "erro": "vinculado no arquivo, banco recusou: %s" % e}
    return {"ok": True, "marca": marca, "canal": canal,
            "username": conta.get("username") or "",
            "marcas_da_conta": marcas_da_conta(canal, user_id)}


def esquecer_conta(canal: str, user_id: str) -> dict:
    """Apaga a conta e todos os vínculos. Exige saber quem depende dela."""
    canal = (canal or "instagram").lower().strip()
    user_id = str(user_id or "").strip()
    if not user_id:
        return {"ok": False, "erro": "user_id obrigatório"}
    marcas = marcas_da_conta(canal, user_id)
    for m in marcas:
        try:
            os.remove(_path_token(m, canal))
        except OSError:
            pass
    try:
        os.remove(_path_conta(canal, user_id))
    except OSError:
        pass
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "conta_apagar"):
            _db.conta_apagar(canal, user_id)
    except Exception:
        pass
    return {"ok": True, "canal": canal, "user_id": user_id, "desvinculou": marcas}


def _publico_de(raw: dict, canal: str) -> dict:
    """Status sem tokens — seguro pra UI."""
    if not raw or not raw.get("connected"):
        return {
            "canal": canal,
            "conectado": False,
            "status": "desconectado",
            "username": "",
            "user_id": "",
            "conectado_em": "",
            "expira_em": "",
            "modo": raw.get("modo") or "",
            "permissoes": [],
        }
    return {
        "canal": canal,
        "conectado": True,
        "status": "conectado",
        "username": raw.get("username") or "",
        "user_id": str(raw.get("user_id") or ""),
        "conectado_em": raw.get("conectado_em") or "",
        "expira_em": raw.get("expira_em") or "",
        "modo": raw.get("modo") or "fake",
        "permissoes": list(raw.get("permissoes") or []),
        "nome": raw.get("nome") or "",
        "picture": raw.get("picture") or "",
    }


def status_canal(marca: str, canal: str) -> dict:
    canal = (canal or "").lower().strip()
    if canal not in CANAIS:
        return {"canal": canal, "conectado": False, "status": "desconhecido", "erro": "canal inválido"}
    if canal == "linkedin":
        raw = _load_canal(marca, "linkedin")
        pub = _publico_de(raw, "linkedin")
        if not pub["conectado"]:
            pub["status"] = "em_breve"
            pub["aviso"] = "LinkedIn em breve — estrutura pronta, OAuth na próxima etapa."
        return pub
    raw = _load_canal(marca, canal)
    pub = _publico_de(raw, canal)
    if pub["conectado"] and pub["user_id"]:
        # quem mais publica por esta conta: a tela avisa antes de postar
        pub["marcas_da_conta"] = marcas_da_conta(canal, pub["user_id"])
    return pub


def status_marca(marca: str) -> dict:
    """Resumo de todos os canais da marca (sem secrets)."""
    return {
        "marca": marca,
        "modo_app": modo_instagram(),
        "canais": {c: status_canal(marca, c) for c in CANAIS},
    }


def status_todas(marcas: list) -> dict:
    """Status de N marcas com UMA consulta ao banco (não N × canais).

    A versão ingênua abria uma conexão por marca × canal. Com 16 marcas e o
    Postgres atrás do proxy do Railway isso dava ~65 s — e o painel local
    espera por essa resposta pra pintar a primeira linha.
    """
    marcas = list(marcas or [])
    todos = {}
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "canais_todos"):
            todos = _db.canais_todos()
    except Exception:
        todos = {}
    modo = modo_instagram()
    out = {}
    for m in marcas:
        canais = {}
        for c in CANAIS:
            raw = todos.get((m, c))
            if raw is None:
                raw = _load_canal_arquivo(m, c)   # só disco: o banco já veio inteiro acima
            pub = _publico_de(raw or {}, c)
            if c == "linkedin" and not pub["conectado"]:
                pub["status"] = "em_breve"
                pub["aviso"] = "LinkedIn em breve — estrutura pronta, OAuth na próxima etapa."
            canais[c] = pub
        out[m] = {"marca": m, "modo_app": modo, "canais": canais}
    # Quem divide conta com quem, sem uma consulta por marca: o agrupamento sai
    # do que já está em mãos. A tela precisa disso pra avisar antes de publicar.
    for c in CANAIS:
        por_conta = {}
        for m in marcas:
            uid = out[m]["canais"][c].get("user_id") or ""
            if uid:
                por_conta.setdefault(uid, []).append(m)
        for m in marcas:
            uid = out[m]["canais"][c].get("user_id") or ""
            if uid:
                out[m]["canais"][c]["marcas_da_conta"] = sorted(por_conta[uid])
    return out


def desconectar(marca: str, canal: str = "instagram") -> dict:
    """Solta ESTA marca da conta. A conta continua servindo as outras.

    Apagar a conta junto seria destruir o acesso de marcas que não pediram nada
    — quem quer isso chama `esquecer_conta`.
    """
    raw = _load_json(_path_token(marca, canal))
    uid = str(raw.get("conta_user_id") or raw.get("user_id") or "").strip()
    path = _path_token(marca, canal)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as e:
            return {"ok": False, "erro": str(e)}
    try:
        import _db
        _db.canal_apagar(marca, canal)
    except Exception:
        pass
    restantes = marcas_da_conta(canal, uid) if uid else []
    return {"ok": True, "marca": marca, "canal": canal, "conectado": False,
            "conta_user_id": uid, "conta_ainda_usada_por": restantes}


# ── OAuth state ─────────────────────────────────────────────────────────────

def _save_pending(state: str, payload: dict) -> None:
    os.makedirs(PENDING_DIR, exist_ok=True)
    payload = dict(payload)
    payload["created_at"] = time.time()
    _save_json(os.path.join(PENDING_DIR, f"{state}.json"), payload)


def _pop_pending(state: str) -> Optional[dict]:
    path = os.path.join(PENDING_DIR, f"{state}.json")
    data = _load_json(path)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass
    if not data:
        return None
    # expira em 30 min
    if time.time() - float(data.get("created_at") or 0) > 1800:
        return None
    return data


def iniciar_oauth(marca: str, canal: str = "instagram",
                  return_to: str = "/config") -> dict:
    """Gera URL de autorização (fake ou real)."""
    canal = (canal or "instagram").lower()
    if canal == "linkedin":
        return {
            "ok": False,
            "erro": "LinkedIn ainda não está disponível. Em breve.",
            "status": "em_breve",
        }
    if canal != "instagram":
        return {"ok": False, "erro": f"canal '{canal}' não suportado"}

    import _marcas  # noqa: local
    try:
        marca = _marcas.require(marca)
    except ValueError as e:
        return {"ok": False, "erro": str(e)}

    state = secrets.token_urlsafe(24)
    mode = modo_instagram()
    pending = {
        "marca": marca,
        "canal": canal,
        "return_to": return_to or "/config",
        "mode": mode,
    }

    if mode == "fake":
        _save_pending(state, pending)
        url = f"/oauth/instagram/fake?state={urllib.parse.quote(state)}"
        return {
            "ok": True,
            "url": url,
            "mode": "fake",
            "marca": marca,
            "aviso": "App Meta ainda não configurado — fluxo de autenticação simulado.",
        }

    cfg = ig_app_config()
    if not cfg["app_id"] or not cfg["redirect_uri"]:
        return {"ok": False, "erro": "INSTAGRAM_APP_ID / REDIRECT_URI ausentes no ambiente"}
    # URL Meta — só params oficiais. redirect_uri idêntico no exchange (salvo no pending).
    redirect = cfg["redirect_uri"]
    params = {
        "client_id": cfg["app_id"],
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": ",".join(IG_SCOPES),
        "state": state,
    }
    meta_url = IG_AUTHORIZE + "?" + urllib.parse.urlencode(params)
    pending["meta_url"] = meta_url
    pending["redirect_uri"] = redirect
    pending["app_id"] = cfg["app_id"]
    _save_pending(state, pending)
    # página intermediária com branding Smark (Meta controla a tela do Instagram)
    bridge = (
        f"/oauth/instagram/start?state={urllib.parse.quote(state)}"
        f"&marca={urllib.parse.quote(marca)}"
    )
    return {
        "ok": True,
        "url": bridge,           # UI branded primeiro
        "meta_url": meta_url,    # URL real Meta (bridge redireciona)
        "mode": "real",
        "marca": marca,
        "redirect_uri": cfg["redirect_uri"],
        "app_id": cfg["app_id"],
    }


def peek_pending(state: str) -> Optional[dict]:
    """Lê pending sem consumir (bridge OAuth)."""
    path = os.path.join(PENDING_DIR, f"{state}.json")
    data = _load_json(path)
    if not data:
        return None
    if time.time() - float(data.get("created_at") or 0) > 1800:
        return None
    return data


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _expira_iso(seconds: int) -> str:
    return datetime.fromtimestamp(time.time() + max(0, int(seconds)),
                                  tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def conectar_fake(state: str, username: str, nome: str = "") -> dict:
    """Conclui OAuth fake (usuário 'autorizou' no formulário local)."""
    username = re_slug_user((username or "").strip().lstrip("@"))
    if not username or len(username) < 2:
        return {"ok": False, "erro": "informe o @ do Instagram Business/Creator", "keep_state": True}
    # só consome o state depois de validar o @
    pending = _pop_pending(state)
    if not pending:
        return {"ok": False, "erro": "sessão OAuth expirada — tente Conectar de novo"}
    marca = pending["marca"]
    token = {
        "connected": True,
        "modo": "fake",
        "canal": "instagram",
        "marca": marca,
        "username": username,
        "nome": (nome or username).strip(),
        "user_id": f"fake_{secrets.token_hex(6)}",
        "access_token": f"IGQWfake.{secrets.token_hex(24)}",
        "token_type": "bearer",
        "permissoes": list(IG_SCOPES),
        "conectado_em": _now_iso(),
        "expira_em": _expira_iso(60 * 24 * 3600),  # 60 dias
        "expires_in": 60 * 24 * 3600,
        "picture": "",
        "return_to": pending.get("return_to") or "/config",
    }
    _persist_canal(marca, "instagram", token)
    return {
        "ok": True,
        "marca": marca,
        "username": username,
        "return_to": token["return_to"],
        "publico": _publico_de(token, "instagram"),
    }


def re_slug_user(u: str) -> str:
    u = u.strip().lstrip("@")
    out = []
    for ch in u:
        if ch.isalnum() or ch in "._":
            out.append(ch)
    return "".join(out)[:60] or "conta"


# Erro da Meta traduzido. Sem isso a tela mostra só "falha ao criar container"
# e some com o code/fbtrace — que é a única coisa que o suporte da Meta aceita.
_META_DICAS = {
    (200, "api access blocked"): (
        "o APP da Meta está bloqueado/restrito (não é o post nem a arte — até "
        "leitura simples falha). Abra o painel do app e veja se há aviso de "
        "restrição ou se ele saiu do modo Live."),
    (190, ""): (
        "token inválido ou expirado — reconecte a conta no /config."),
    (101, ""): (
        "app id/secret não conferem, ou o app não existe mais."),
    (10, ""): (
        "falta a permissão instagram_business_content_publish — reconecte "
        "pedindo publicação."),
    (100, ""): (
        "a Meta recusou algum campo (normalmente a image_url: precisa ser "
        "HTTPS público, JPEG, que ela consiga baixar)."),
    (4, ""): ("limite de chamadas da Meta — espere e tente de novo."),
    (9, ""): ("limite de publicações da conta (25 posts/24h)."),
}


def _meta_erro_legivel(j: dict, msg: str) -> str:
    """Mensagem da Meta + code + fbtrace + o que fazer, em pt-BR."""
    err = j.get("error") if isinstance(j.get("error"), dict) else {}
    code = err.get("code")
    sub = err.get("error_subcode")
    trace = err.get("fbtrace_id") or j.get("fbtrace_id")
    dica = ""
    baixo = (msg or "").strip().lower().rstrip(".")
    for (c, m), d in _META_DICAS.items():
        if c == code and (not m or m == baixo):
            dica = d
            break
    partes = [msg or "erro sem mensagem"]
    marca = []
    if code is not None:
        marca.append(f"code {code}" + (f"/{sub}" if sub else ""))
    if trace:
        marca.append(f"trace {trace}")
    if marca:
        partes.append("[" + " · ".join(marca) + "]")
    if dica:
        partes.append("→ " + dica)
    return " ".join(partes)


def _http_json(method: str, url: str, data: Optional[dict] = None,
               form: bool = False, multipart: bool = False) -> dict:
    headers = {"User-Agent": "smark-canais/1.0"}
    body = None
    if data is not None:
        if multipart:
            # Docs Meta usam curl -F → multipart/form-data (não x-www-form-urlencoded)
            boundary = "----SmarkFormBoundary" + secrets.token_hex(12)
            chunks = []
            for k, v in data.items():
                chunks.append(
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
                    f"{v}\r\n"
                )
            chunks.append(f"--{boundary}--\r\n")
            body = "".join(chunks).encode("utf-8")
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        else:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            j = json.loads(err_body)
        except Exception:
            j = {"error_message": err_body[:400]}
        msg = (
            (j.get("error") or {}).get("message")
            if isinstance(j.get("error"), dict)
            else j.get("error_message") or j.get("error") or err_body[:300]
        )
        # Instagram às vezes manda error_type + error_message no root
        if not msg or msg == err_body[:300]:
            msg = j.get("error_message") or j.get("error_type") or msg
        raise RuntimeError(
            f"Instagram API HTTP {e.code}: {_meta_erro_legivel(j, msg)}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"falha de rede Instagram: {e}") from e


def _exchange_code(app_id: str, secret: str, redirect: str, code: str) -> dict:
    """POST token — UMA tentativa multipart (docs Meta curl -F).

    Não retentar com outro encoding: se o code for aceito e depois falhar,
    a 2ª tentativa queima com 'authorization code has been used'.
    """
    payload = {
        "client_id": app_id,
        "client_secret": secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect,
        "code": code,
    }
    return _http_json("POST", IG_TOKEN, payload, multipart=True)


# resultados de callback (anti F5 / double-hit no code)
_RESULT_DIR = os.path.join(VAULT, ".secrets", "oauth_results")


def save_oauth_result(result: dict) -> str:
    """Persiste resultado e devolve id curto p/ redirect sem code na URL."""
    os.makedirs(_RESULT_DIR, exist_ok=True)
    rid = secrets.token_urlsafe(12)
    path = os.path.join(_RESULT_DIR, f"{rid}.json")
    payload = dict(result)
    payload["_ts"] = time.time()
    _save_json(path, payload)
    return rid


def load_oauth_result(rid: str) -> Optional[dict]:
    if not rid or "/" in rid or ".." in rid:
        return None
    path = os.path.join(_RESULT_DIR, f"{rid}.json")
    data = _load_json(path)
    if not data:
        return None
    # expira em 10 min
    if time.time() - float(data.get("_ts") or 0) > 600:
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    return data


def trocar_code_real(code: str, state: str) -> dict:
    """Callback real: code → tokens long-lived + perfil."""
    pending = _pop_pending(state)
    if not pending:
        return {
            "ok": False,
            "erro": (
                "Sessão OAuth expirada ou code já processado. "
                "Volte em Config → Instagram e conecte de novo "
                "(não recarregue a URL do callback)."
            ),
        }
    marca = pending["marca"]
    cfg = ig_app_config()
    # CRÍTICO: redirect_uri do exchange = o do authorize (do pending / meta_url)
    redirect = pending.get("redirect_uri") or cfg["redirect_uri"]
    if not redirect and pending.get("meta_url"):
        try:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(pending["meta_url"]).query)
            redirect = (q.get("redirect_uri") or [""])[0]
        except Exception:
            redirect = ""
    redirect = _norm_redirect(redirect or cfg["redirect_uri"])
    app_id = str(pending.get("app_id") or cfg["app_id"]).strip()
    secret = cfg["app_secret"]
    code = (code or "").strip()
    if code.endswith("#_"):
        code = code[:-2]
    code = code.strip()

    # 1) short-lived — UMA chamada only (code é one-shot)
    try:
        short = _exchange_code(app_id, secret, redirect, code)
    except RuntimeError as e:
        err = str(e)
        if "has been used" in err.lower():
            return {
                "ok": False,
                "erro": (
                    "Este código de autorização já foi usado (página recarregada ou clique duplo). "
                    "Volte ao Config e clique no Instagram de novo — não use o botão Voltar do browser."
                ),
            }
        return {
            "ok": False,
            "erro": (
                f"{err}\n\n"
                f"redirect: {redirect}\nclient_id: {app_id}\n"
                "Confira Instagram App Secret no Railway e URI na Meta. "
                "Sempre reinicie o fluxo pelo Config."
            ),
        }
    # resposta pode vir como {data:[{access_token,user_id,...}]} ou flat
    if isinstance(short.get("data"), list) and short["data"]:
        short = short["data"][0]
    access = short.get("access_token")
    user_id = str(short.get("user_id") or short.get("id") or "")
    if not access:
        return {"ok": False, "erro": "Instagram não devolveu access_token", "raw": short}

    # 2) long-lived
    long_url = (
        f"{IG_GRAPH}/access_token?"
        + urllib.parse.urlencode({
            "grant_type": "ig_exchange_token",
            "client_secret": cfg["app_secret"],
            "access_token": access,
        })
    )
    try:
        long_t = _http_json("GET", long_url)
        if long_t.get("access_token"):
            access = long_t["access_token"]
            expires_in = int(long_t.get("expires_in") or 5184000)
        else:
            expires_in = 3600
    except Exception:
        expires_in = 3600

    # 3) perfil
    username, nome, picture = "", "", ""
    try:
        me_url = (
            f"{IG_GRAPH}/me?"
            + urllib.parse.urlencode({
                "fields": "id,username,name,profile_picture_url,account_type",
                "access_token": access,
            })
        )
        me = _http_json("GET", me_url)
        user_id = str(me.get("id") or user_id)
        username = me.get("username") or ""
        nome = me.get("name") or username
        picture = me.get("profile_picture_url") or ""
    except Exception as e:
        # ainda salva o token; username pode ser preenchido depois
        username = username or f"user_{user_id[-6:]}" if user_id else "instagram"

    perms = short.get("permissions") or IG_SCOPES
    if isinstance(perms, str):
        perms = [p.strip() for p in perms.split(",") if p.strip()]

    token = {
        "connected": True,
        "modo": "real",
        "canal": "instagram",
        "marca": marca,
        "username": username,
        "nome": nome,
        "user_id": user_id,
        "access_token": access,
        "token_type": "bearer",
        "permissoes": perms,
        "conectado_em": _now_iso(),
        "expira_em": _expira_iso(expires_in),
        "expires_in": expires_in,
        "picture": picture,
        "return_to": pending.get("return_to") or "/config",
    }
    _persist_canal(marca, "instagram", token)
    return {
        "ok": True,
        "marca": marca,
        "username": username,
        "return_to": token["return_to"],
        "publico": _publico_de(token, "instagram"),
    }


def testar_conexao(marca: str, canal: str = "instagram") -> dict:
    """Pergunta pra Meta se a conta responde — leitura, não publica nada.

    Existe porque erro de app bloqueado só aparecia na hora de publicar, com
    a peça já pronta. Aqui a resposta vem antes, e com o motivo em português.
    """
    if canal != "instagram":
        return {"ok": False, "erro": "canal %s ainda não tem teste" % canal}
    raw = token_bruto(marca, canal) or {}
    if not raw.get("access_token"):
        return {"ok": False, "erro": "Instagram não conectado nesta marca."}
    if raw.get("modo") == "fake":
        return {"ok": True, "modo": "fake", "username": raw.get("username") or "",
                "aviso": "Conta simulada — não fala com a Meta."}
    try:
        me = _http_json(
            "GET",
            "%s/me?fields=id,username&access_token=%s"
            % (IG_GRAPH, urllib.parse.quote(raw["access_token"])))
    except Exception as e:
        return {"ok": False, "modo": "real", "erro": str(e),
                "username": raw.get("username") or ""}
    return {"ok": True, "modo": "real", "user_id": me.get("id") or "",
            "username": me.get("username") or raw.get("username") or ""}


def token_bruto(marca: str, canal: str = "instagram") -> dict:
    """Uso interno (publish). Nunca expor na API HTTP."""
    return _load_canal(marca, canal)


def conta_bruta(canal: str, user_id: str) -> dict:
    """Token de uma conta, direto — sem passar por marca."""
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "conta_carregar"):
            p = _db.conta_carregar(canal, user_id)
            if p:
                return p
    except Exception:
        pass
    return _load_json(_path_conta(canal, str(user_id)))


def _persist_conta(canal: str, data: dict) -> None:
    """Grava o token da conta nos dois lugares. Os vínculos não mudam."""
    uid = str(data.get("user_id") or "").strip()
    if not uid:
        return
    _save_json(_path_conta(canal, uid), data)
    try:
        import _db
        if _db.disponivel() and hasattr(_db, "conta_salvar"):
            _db.conta_salvar(canal, data)
    except Exception:
        pass


def refresh_token_se_preciso(marca: str) -> dict:
    """Renova o token da CONTA usada por esta marca.

    A renovação é por conta, não por marca: se duas marcas dividem o Instagram,
    um refresh serve as duas. Antes, com o payload copiado por marca, renovava-se
    uma cópia e a outra vencia sem ninguém ver.
    """
    raw = token_bruto(marca, "instagram")
    uid = str(raw.get("user_id") or "").strip()
    if raw.get("connected") and uid:
        return refresh_conta_se_preciso("instagram", uid)
    return {"ok": False, "erro": "não conectado"}


def refresh_conta_se_preciso(canal: str, user_id: str) -> dict:
    """Renova long-lived se faltar < 7 dias. No-op em fake."""
    raw = conta_bruta(canal, user_id)
    if not raw.get("connected"):
        return {"ok": False, "erro": "não conectado"}
    if raw.get("modo") == "fake":
        return {"ok": True, "skipped": True, "modo": "fake"}
    exp = raw.get("expira_em") or ""
    try:
        # se ainda tem mais de 7 dias, não renova
        if exp:
            # parse simples
            from datetime import datetime as dt
            exp_dt = dt.strptime(exp.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            if (exp_dt - datetime.now(timezone.utc)).total_seconds() > 7 * 86400:
                return {"ok": True, "skipped": True}
    except Exception:
        pass
    access = raw.get("access_token")
    if not access:
        return {"ok": False, "erro": "sem token"}
    url = (
        f"{IG_GRAPH}/refresh_access_token?"
        + urllib.parse.urlencode({
            "grant_type": "ig_refresh_token",
            "access_token": access,
        })
    )
    try:
        j = _http_json("GET", url)
    except Exception as e:
        return {"ok": False, "erro": str(e)}
    if j.get("access_token"):
        raw["access_token"] = j["access_token"]
        raw["expires_in"] = int(j.get("expires_in") or raw.get("expires_in") or 5184000)
        raw["expira_em"] = _expira_iso(raw["expires_in"])
        raw["refreshed_em"] = _now_iso()
        _persist_conta(canal, raw)
        return {"ok": True, "expira_em": raw["expira_em"],
                "marcas": marcas_da_conta(canal, user_id)}
    return {"ok": False, "erro": "refresh sem access_token", "raw": j}


# ── publish ─────────────────────────────────────────────────────────────────

def _log_publish(marca: str, canal: str, evento: dict) -> None:
    path = _path_log(marca, canal)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    evento = dict(evento)
    evento.setdefault("em", _now_iso())
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def base_publica() -> str:
    """Origem HTTPS pela qual o mundo externo enxerga este servidor."""
    base = (_env("PUBLIC_BASE_URL") or _env("RAILWAY_PUBLIC_DOMAIN") or "").strip().rstrip("/")
    if base and not base.startswith("http"):
        base = "https://" + base
    return base


def url_publica_da_arte(sha: str) -> str:
    """URL que a Meta usa pra baixar a arte. Vazia se não dá pra montar.

    É `/arte/<sha>.jpg`, servido do Postgres — nunca um caminho do vault. O
    servidor não expõe o disco pra internet, então URL de arquivo vira 404 no
    lado da Meta e o post falha sem explicação clara.
    """
    sha = (sha or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{16,64}", sha):
        return ""
    base = base_publica()
    return f"{base}/arte/{sha}.jpg" if base else ""


def publicar_instagram(marca: str, *,
                       image_path: str = "",
                       image_url: str = "",
                       image_sha: str = "",
                       caption: str = "",
                       dry_run: bool = False) -> dict:
    """Publica imagem no feed Instagram da marca.

    Fake: grava outbox + log (sem chamar Meta).
    Real: Content Publishing API (exige image_url público HTTPS).

    `image_sha` é o caminho preferido: a Meta baixa a arte de
    `<base>/arte/<sha>.jpg`, servida pelo Postgres. O antigo `image_path`
    montava a URL a partir de um caminho de ARQUIVO — que não existe no
    servidor, então a Meta tomava 404 e o post falhava. Mesma doença que
    quebrava a galeria, no segundo lugar.
    """
    import _marcas  # noqa
    try:
        marca = _marcas.require(marca)
    except ValueError as e:
        return {"ok": False, "erro": str(e)}

    raw = token_bruto(marca, "instagram")
    if not raw.get("connected") or not raw.get("access_token"):
        return {"ok": False, "erro": "Instagram não conectado nesta marca. Vá em Config → Conectar."}

    caption = (caption or "")[:2200]
    abs_img = ""
    if image_path:
        abs_img = image_path if os.path.isabs(image_path) else os.path.join(VAULT, image_path)
        if not os.path.isfile(abs_img):
            return {"ok": False, "erro": f"imagem não encontrada: {image_path}"}

    if raw.get("modo") == "fake" or dry_run or modo_instagram() == "fake":
        outbox = os.path.join(
            VAULT, "marcas", marca, "publicacoes", "social", "instagram", "_outbox"
        )
        os.makedirs(outbox, exist_ok=True)
        job_id = secrets.token_hex(4)
        meta = {
            "id": job_id,
            "modo": "fake",
            "username": raw.get("username"),
            "caption": caption,
            "image_path": image_path or "",
            "image_url": image_url or "",
            "em": _now_iso(),
            "status": "queued_fake",
            "nota": "Simulação — app real publicará de verdade quando INSTAGRAM_APP_ID estiver no .env",
        }
        _save_json(os.path.join(outbox, f"{job_id}.json"), meta)
        # copia referência da arte se existir
        if abs_img and os.path.isfile(abs_img):
            try:
                import shutil
                ext = os.path.splitext(abs_img)[1] or ".png"
                shutil.copy2(abs_img, os.path.join(outbox, f"{job_id}{ext}"))
            except OSError:
                pass
        _log_publish(marca, "instagram", {"acao": "publicar_fake", **meta})
        return {
            "ok": True,
            "modo": "fake",
            "job_id": job_id,
            "username": raw.get("username"),
            "aviso": "Publicação simulada (app fake). Arquivo em _outbox/.",
            "outbox": f"marcas/{marca}/publicacoes/social/instagram/_outbox/{job_id}.json",
        }

    # REAL
    refresh_token_se_preciso(marca)
    raw = token_bruto(marca, "instagram")
    access = raw["access_token"]
    ig_user = raw.get("user_id")
    if not ig_user:
        return {"ok": False, "erro": "user_id Instagram ausente — reconecte a conta"}
    # Meta baixa a imagem por HTTPS público.
    if not image_url and image_sha:
        image_url = url_publica_da_arte(image_sha)
    if not image_url:
        return {
            "ok": False,
            "erro": (
                "Publicação real exige URL pública HTTPS da imagem "
                "(Meta baixa a arte do link). Faltou image_sha — a arte precisa "
                "estar no Postgres. Confira PUBLIC_BASE_URL no Railway."
            ),
        }
    # Nunca mandar a Meta buscar um caminho de arquivo: em produção não existe
    # e o post falha com um 404 difícil de diagnosticar do lado de lá.
    if "/marcas/" in image_url:
        return {
            "ok": False,
            "erro": ("URL da arte aponta pra arquivo do vault (%s). A Meta não "
                     "enxerga o disco do servidor — use image_sha." % image_url),
        }

    # 1) container
    try:
        create_url = f"{IG_GRAPH}/{ig_user}/media"
        container = _http_json("POST", create_url, {
            "image_url": image_url,
            "caption": caption,
            "access_token": access,
        }, form=True)
    except Exception as e:
        _log_publish(marca, "instagram", {"acao": "erro_container", "erro": str(e)})
        try:
            import _db
            _db.publicacao_log(marca, "instagram", "erro_container",
                               image_url=image_url, caption=caption, detalhe={"erro": str(e)})
        except Exception:
            pass
        return {"ok": False, "erro": f"falha ao criar container: {e}"}

    creation_id = container.get("id")
    if not creation_id:
        return {"ok": False, "erro": "sem creation_id", "raw": container}

    # 2) publish
    try:
        pub_url = f"{IG_GRAPH}/{ig_user}/media_publish"
        published = _http_json("POST", pub_url, {
            "creation_id": creation_id,
            "access_token": access,
        }, form=True)
    except Exception as e:
        _log_publish(marca, "instagram", {
            "acao": "erro_publish", "creation_id": creation_id, "erro": str(e),
        })
        return {"ok": False, "erro": f"falha ao publicar: {e}", "creation_id": creation_id}

    media_id = published.get("id")
    _log_publish(marca, "instagram", {
        "acao": "publicar_ok",
        "media_id": media_id,
        "creation_id": creation_id,
        "username": raw.get("username"),
    })
    try:
        import _db
        _db.publicacao_log(
            marca, "instagram", "publicado",
            media_id=media_id, image_path=image_path, image_url=image_url,
            caption=caption, detalhe={"creation_id": creation_id},
        )
    except Exception:
        pass
    return {
        "ok": True,
        "modo": "real",
        "media_id": media_id,
        "username": raw.get("username"),
        "creation_id": creation_id,
        "image_url": image_url,
    }


def html_oauth_bridge(marca: str, meta_url: str, state: str = "") -> str:
    """Tela smark antes de ir ao Instagram — deixa claro o que vai acontecer.

    A Meta controla 100% as telas de login/captcha do Instagram (não customizáveis
    como o OAuth do Claude). Aqui só contextualizamos a marca e o Smark Studio.
    """
    marca = marca or "esta marca"
    return f"""<!doctype html>
<html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Conectar Instagram · Smark Studio</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:linear-gradient(160deg,#0b0618 0%,#1a0b2e 45%,#2a1c4a 100%);color:#f4f0ff}}
  .card{{width:min(420px,92vw);background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
    border-radius:20px;padding:28px 26px;backdrop-filter:blur(12px);
    box-shadow:0 24px 60px rgba(0,0,0,.45)}}
  .brand{{display:flex;align-items:center;gap:10px;margin-bottom:18px}}
  .logo{{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#8b3cf7,#5b2fd6);
    display:grid;place-items:center;font-weight:800;font-size:18px}}
  .brand b{{font-size:15px;letter-spacing:-.02em}}
  .brand span{{display:block;font-size:11px;color:#b8a8d8;font-weight:500}}
  h1{{font-size:20px;margin:0 0 8px;line-height:1.25}}
  p{{font-size:14px;color:#cfc2e8;line-height:1.5;margin:0 0 14px}}
  ul{{margin:0 0 20px;padding-left:18px;color:#cfc2e8;font-size:13px;line-height:1.55}}
  ul li{{margin-bottom:6px}}
  .btn{{display:block;width:100%;text-align:center;padding:14px 16px;border:0;border-radius:14px;
    font-size:15px;font-weight:700;color:#fff;text-decoration:none;cursor:pointer;
    background:linear-gradient(90deg,#f58529,#dd2a7b,#8134af,#515bd4)}}
  .btn:hover{{filter:brightness(1.06)}}
  .hint{{font-size:11px;color:#9a8bb8;margin-top:14px;line-height:1.45;text-align:center}}
  .marca{{display:inline-block;background:rgba(139,60,247,.25);color:#e8d8ff;padding:3px 10px;
    border-radius:999px;font-size:12px;font-weight:600;margin-bottom:12px}}
</style>
</head><body>
<div class=card>
  <div class=brand>
    <div class=logo>S</div>
    <div><b>Smark Studio</b><span>Autorização de canais</span></div>
  </div>
  <div class=marca>Marca · {_esc(marca)}</div>
  <h1>Autorizar o Smark Studio a publicar no Instagram</h1>
  <p>Você será levado ao Instagram (Meta) para entrar com a conta
  <b>Business ou Creator</b> desta marca e permitir a conexão.</p>
  <ul>
    <li>O Smark Studio pede só permissão para <b>identificar a conta</b> e <b>publicar posts</b> que você aprovar no editor.</li>
    <li>Não postamos nada sem você clicar em Publicar.</li>
    <li>As telas de login/captcha são da <b>Meta</b> — não dá para customizar o visual delas.</li>
  </ul>
  <a class=btn id=go href="{_esc(meta_url)}">Continuar com Instagram</a>
  <p class=hint>Depois de autorizar, a Meta deve te devolver para o Smark Studio.
  Se cair no feed do Instagram sem voltar, a conta precisa ser profissional e estar
  como testador do app (modo Development).<br>
  Clique no botão acima — não redirecionamos sozinhos.</p>
</div>
</body></html>"""


def html_fake_login(state: str, marca: str = "", erro: str = "") -> str:
    """Página que simula a janela de autorização do Instagram."""
    marca = marca or "?"
    err = f'<div class="err">{_esc(erro)}</div>' if erro else ""
    return f"""<!doctype html>
<html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Conectar Instagram · smark (fake)</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:linear-gradient(145deg,#0f0c29,#302b63 45%,#24243e);color:#111}}
  .card{{width:min(400px,92vw);background:#fff;border-radius:20px;padding:28px 26px 24px;
    box-shadow:0 24px 60px rgba(0,0,0,.35)}}
  .ig{{width:56px;height:56px;border-radius:14px;margin:0 auto 14px;display:grid;place-items:center;
    background:radial-gradient(circle at 30% 107%,#fdf497 0%,#fdf497 5%,#fd5949 45%,#d6249f 60%,#285AEB 90%)}}
  .ig svg{{width:30px;height:30px;fill:#fff}}
  h1{{font-size:18px;margin:0 0 4px;text-align:center}}
  .sub{{font-size:13px;color:#666;text-align:center;margin:0 0 18px;line-height:1.4}}
  label{{display:block;font-size:12px;font-weight:600;color:#444;margin:0 0 6px}}
  input{{width:100%;padding:12px 14px;border:1px solid #ddd;border-radius:12px;font-size:15px;margin-bottom:12px}}
  input:focus{{outline:none;border-color:#d6249f;box-shadow:0 0 0 3px rgba(214,36,159,.15)}}
  button{{width:100%;padding:13px;border:0;border-radius:12px;font-size:15px;font-weight:700;color:#fff;
    background:linear-gradient(90deg,#f58529,#dd2a7b,#8134af,#515bd4);cursor:pointer}}
  button:hover{{filter:brightness(1.05)}}
  .badge{{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;
    background:#fff3cd;color:#856404;padding:3px 8px;border-radius:999px;margin-bottom:12px}}
  .wrap-badge{{text-align:center}}
  .err{{background:#fde8e8;color:#b00020;padding:10px 12px;border-radius:10px;font-size:13px;margin-bottom:12px}}
  .hint{{font-size:11px;color:#888;text-align:center;margin-top:14px;line-height:1.4}}
  a{{color:#8134af}}
</style></head><body>
<form class=card method=POST action="/oauth/instagram/fake">
  <div class=ig>
    <svg viewBox="0 0 24 24"><path d="M7 2h10a5 5 0 015 5v10a5 5 0 01-5 5H7a5 5 0 01-5-5V7a5 5 0 015-5zm0 2a3 3 0 00-3 3v10a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H7zm5 3.5A4.5 4.5 0 1112 16a4.5 4.5 0 010-9zm0 2A2.5 2.5 0 1014.5 12 2.5 2.5 0 0012 7.5zM17.5 6a1 1 0 11-1 1 1 1 0 011-1z"/></svg>
  </div>
  <div class=wrap-badge><span class=badge>Modo simulado · app fake</span></div>
  <h1>Autorizar smark Studio</h1>
  <p class=sub>Marca <b>{_esc(marca)}</b> quer publicar no Instagram Business/Creator desta conta.</p>
  {err}
  <input type=hidden name=state value="{_esc(state)}">
  <label>Usuário do Instagram (@)</label>
  <input name=username placeholder="clinica.alemdoolhar" required autocomplete=username>
  <label>Nome de exibição (opcional)</label>
  <input name=nome placeholder="Além do Olhar Chapecó">
  <button type=submit>Autorizar e conectar</button>
  <p class=hint>Amanhã, com o App real da Meta no <code>.env</code>, esta tela
  vira o login oficial do Instagram. Tokens ficam só em <code>.secrets/canais/</code>.</p>
</form>
</body></html>"""


def _esc(s: str) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def html_oauth_done(ok: bool, marca: str = "", username: str = "",
                    erro: str = "", return_to: str = "/config") -> str:
    if ok:
        dest = return_to or "/config"
        if "canais=" not in dest:
            sep = "&" if "?" in dest else "?"
            dest = f"{dest}{sep}canais=ok&marca={urllib.parse.quote(marca)}"
        return f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta http-equiv="refresh" content="2;url={_esc(dest)}">
<title>Instagram conectado · Smark Studio</title>
<style>
body{{font-family:system-ui;display:grid;place-items:center;min-height:100vh;margin:0;
  background:linear-gradient(160deg,#0b0618,#1a0b2e);color:#f4f0ff}}
.card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:20px;
  padding:32px 28px;text-align:center;max-width:400px;width:92vw}}
.ok{{color:#6dcf8a;font-weight:800;font-size:18px;margin-bottom:8px}}
.sub{{color:#cfc2e8;font-size:14px;line-height:1.45}}
a{{color:#d4b8ff}}
</style></head><body>
<div class=card>
  <div class=ok>✓ Conta autorizada no Smark Studio</div>
  <p class=sub>Instagram <b>@{_esc(username)}</b> vinculado à marca <b>{_esc(marca)}</b>.<br>
  A bolinha do ícone IG deve ficar <b style="color:#34c759">verde</b> no card.</p>
  <p class=sub style="margin-top:16px;font-size:12px;color:#9a8bb8">Voltando ao painel…</p>
  <p><a href="{_esc(dest)}">Abrir Configurações agora</a></p>
</div></body></html>"""
    return f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<title>Falha · Smark Studio</title>
<style>
body{{font-family:system-ui;display:grid;place-items:center;min-height:100vh;margin:0;
  background:linear-gradient(160deg,#0b0618,#1a0b2e);color:#f4f0ff}}
.card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:20px;
  padding:32px 28px;text-align:center;max-width:420px;width:92vw}}
.err{{color:#f08080;font-weight:800;font-size:18px;margin-bottom:8px}}
.sub{{color:#cfc2e8;font-size:14px;line-height:1.5}}
a{{color:#d4b8ff}}
code{{font-size:12px;background:rgba(0,0,0,.3);padding:2px 6px;border-radius:6px}}
</style></head><body>
<div class=card>
  <div class=err>Não foi possível conectar</div>
  <p class=sub">{_esc(erro)}</p>
  <p class=sub style="font-size:12px;color:#9a8bb8;margin-top:12px">
  Dicas: conta <b>Business/Creator</b> · app em Development exige o usuário em
  <b>Funções do app / Instagram testers</b> · redirect na Meta deve ser o HTTPS do Railway.
  </p>
  <p style="margin-top:18px"><a href="/config">Voltar ao Smark Studio</a></p>
</div></body></html>"""
