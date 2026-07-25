# Motor de Imagem Calibrado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar o motor de fundo de IA por um roteador governado — modelo calibrado por família de marca, telemetria de custo por geração e acervo de referências que realimenta as gerações seguintes.

**Architecture:** Três módulos novos e pequenos entram entre o orquestrador e a rede: `_perfil.py` (lê o contrato e resolve modelo/resolução/seed), `_provedor.py` (única peça que fala HTTP, com backends OpenRouter e OpenAI, e que normaliza qualquer saída para PNG) e `_ledger.py` (append-only de custo). `openai_image.py` vira orquestrador fino e mantém a CLI atual intacta. A fase 2 acrescenta `_acervo.py`, que injeta peças aprovadas como `input_references` — **é ele, e não a seed, que garante a consistência visual.**

**Tech Stack:** Python 3 stdlib apenas (`urllib`, `json`, `hashlib`, `base64`) — o vault não usa dependências externas. Testes em pytest 9.0.3 (já instalado).

## Global Constraints

- **Sem dependências novas.** HTTP cru via `urllib.request`, igual ao resto de `scripts/`.
- **CLI preservada.** Todo comando documentado em `shared/direcao-de-arte.md`, `.claude/commands/` e `editor_server.py:974` continua funcionando sem argumento novo.
- **Chave nunca em linha de comando.** Só via `.env` na raiz ou variável de ambiente.
- **Nada quebra sem crédito.** Falha de saldo (402), auth (401) ou rede na OpenRouter cai para o suplente OpenAI, com aviso em stderr.
- **Modelo default:** `google/gemini-3-pro-image` (backend `openrouter`, **US$ 0,244/imagem em 4K** medido). Suplente: `gpt-image-1.5` no backend `openai` direto.
- **`bytedance-seed/seedream-4.5` está BANIDO do roster.** Reprovado no bake-off de 2026-07-24: com o prompt real do `_direcao` ele tipografa o próprio prompt na arte (renderizou `#9A4DFF`, `#F4F2FB`, `85mm`, 時裝, "BAZATUR" e corpo de texto falso) mesmo com `NEGATIVE: no text, no letters, no words` explícito. Não reintroduzir sem novo bake-off aprovado.
- **Resolução única: `4K`.** Medido no modelo default: 1K e 2K custam US$ 0,135; **4K custa US$ 0,244**. Escolhemos 4K com o custo na mão (decisão do usuário, 2026-07-25): o compositor renderiza a 2x — 2160x2700 no feed, 2160x3840 no story — e ainda aplica zoom/crop, então um fundo 2K (~2048 px) entraria ampliado e amolecido. **Não existe tier de rascunho barato:** trocar de modelo para baratear destrói a fidelidade de enquadramento que o compositor precisa, e a única alavanca de resolução custa nitidez. O plano não implementa tiers.
- **Seed é consultiva, não garantia.** O modelo default não suporta `seed` (aceita e ignora — duas chamadas idênticas devolveram composições diferentes). A seed determinística continua sendo calculada, gravada nos metadados e usada pelo `--reroll`, mas só é ENVIADA ao provedor quando o roster marca `suporta_seed: true` para aquele modelo. Quem garante consistência é o acervo (`input_references`), validado empiricamente.
- **Formato de saída é imprevisível.** A mesma chamada devolveu `image/jpeg` numa execução e `image/png` na outra. `_provedor` normaliza tudo para PNG antes de devolver — a convenção `![[arte/<slug>.png]]` (regra 6 do CLAUDE.md) depende disso.
- **Arquivos que NÃO podem ser modificados:** `scripts/compositor.py`, `scripts/_direcao.py`, `scripts/_paleta.py`, `scripts/estudio.py`.
- **pt-BR** em mensagens de usuário, docstrings e commits.

---

### Task 1: Contrato de perfis e resolver

**Files:**
- Create: `design-system/tokens/perfis-imagem.json`
- Create: `scripts/_perfil.py`
- Test: `tests/test_perfil.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `carregar(path=None) -> dict` — lê o JSON do contrato.
  - `familia_de(marca, cfg) -> str` — nome da família que contém a marca; `"smark"` se não achar.
  - `calcular_seed(familia, slug, tipo, reroll=0) -> int` — determinística, faixa `[0, 2**31)`.
  - `aspect_de_size(size) -> str` — `"1024x1536"` → `"2:3"`.
  - `capacidades(modelo, cfg) -> dict` — entrada do roster para o modelo; `{}` se fora do roster.
  - `resolver(marca, slug="", tipo="", reroll=0, size="1024x1536", cfg=None) -> dict` com as chaves exatas: `familia`, `modelo`, `provider`, `resolution`, `aspect_ratio`, `seed`, `enviar_seed`, `suplente_modelo`, `suplente_provider`, `nao_calibrado`, `acervo_ativo`, `acervo_dir`, `acervo_max`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_perfil.py
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _perfil  # noqa: E402


def test_familia_agrupa_as_tres_marcas():
    cfg = _perfil.carregar()
    assert _perfil.familia_de("smark", cfg) == "smark"
    assert _perfil.familia_de("provider-max", cfg) == "smark"
    assert _perfil.familia_de("elever-ai", cfg) == "smark"


def test_marca_desconhecida_cai_na_familia_padrao():
    cfg = _perfil.carregar()
    assert _perfil.familia_de("cliente-novo", cfg) == "smark"


def test_seed_e_deterministica():
    a = _perfil.calcular_seed("smark", "churn-invisivel", "dor")
    b = _perfil.calcular_seed("smark", "churn-invisivel", "dor")
    assert a == b
    assert 0 <= a < 2 ** 31


def test_seed_muda_por_slug_e_por_reroll():
    base = _perfil.calcular_seed("smark", "post-a", "dor")
    assert _perfil.calcular_seed("smark", "post-b", "dor") != base
    assert _perfil.calcular_seed("smark", "post-a", "dor", reroll=1) == base + 1


def test_aspect_de_size():
    assert _perfil.aspect_de_size("1024x1536") == "2:3"
    assert _perfil.aspect_de_size("1024x1024") == "1:1"
    assert _perfil.aspect_de_size("1536x1024") == "3:2"


def test_resolver_familia_nao_calibrada_usa_suplente():
    cfg = _perfil.carregar()
    cfg["familias"]["smark"]["modelo"] = None
    r = _perfil.resolver("smark", slug="x", tipo="manifesto", cfg=cfg)
    assert r["nao_calibrado"] is True
    assert r["modelo"] == "gpt-image-1.5"
    assert r["provider"] == "openai"


def test_resolver_usa_modelo_calibrado_quando_existe():
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["modelo"] == "google/gemini-3-pro-image"
    assert r["provider"] == "openrouter"
    assert r["resolution"] == "4K"
    assert r["nao_calibrado"] is False


def test_seed_nao_e_enviada_para_modelo_sem_suporte():
    """gemini-3-pro-image aceita `seed` e ignora. Não mentir no corpo da requisição."""
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["seed"] > 0            # continua calculada, vai pros metadados
    assert r["enviar_seed"] is False


def test_seed_e_enviada_para_modelo_com_suporte():
    cfg = _perfil.carregar()
    cfg["_base"]["roster"]["modelo-ficticio"] = {
        "provider": "openrouter", "suporta_seed": True, "max_refs": 4}
    cfg["familias"]["smark"]["modelo"] = "modelo-ficticio"
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["enviar_seed"] is True


def test_acervo_max_respeita_o_teto_do_modelo():
    """O contrato pede 20 refs, mas o gemini aceita no máximo 14. Vence o menor."""
    cfg = _perfil.carregar()
    r = _perfil.resolver("smark", slug="x", tipo="dor", cfg=cfg)
    assert r["acervo_max"] == 14


def test_seedream_esta_banido_do_roster():
    """Reprovado no bake-off: tipografa o prompt na arte. Ver Global Constraints."""
    cfg = _perfil.carregar()
    assert "bytedance-seed/seedream-4.5" not in cfg["_base"]["roster"]


def test_contrato_tem_roster_e_acervo():
    cfg = _perfil.carregar()
    assert "google/gemini-3-pro-image" in cfg["_base"]["roster"]
    assert cfg["_base"]["acervo"]["max_refs"] == 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_perfil.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named '_perfil'`

- [ ] **Step 3: Create the contract file**

```json
{
  "_base": {
    "provider": "openrouter",
    "resolution": "4K",
    "roster": {
      "google/gemini-3-pro-image": {
        "provider": "openrouter",
        "suporta_seed": false,
        "max_refs": 14,
        "custo_medido_usd": 0.244,
        "nota": "default. 1K/2K/4K custam o mesmo. Robusto ao prompt do _direcao."
      },
      "google/gemini-2.5-flash-image": {
        "provider": "openrouter",
        "suporta_seed": false,
        "max_refs": 3,
        "custo_medido_usd": null,
        "nota": "candidato barato, ainda sem bake-off aprovado."
      },
      "gpt-image-1.5": {
        "provider": "openai",
        "suporta_seed": false,
        "max_refs": 0,
        "custo_medido_usd": null,
        "nota": "suplente. Sem resolution/aspect_ratio — usa size/quality."
      }
    },
    "banidos": {
      "bytedance-seed/seedream-4.5":
        "bake-off 2026-07-24: tipografa o prompt na arte (hex, 85mm, 時裝, texto falso) mesmo com NEGATIVE explícito."
    },
    "suplente": { "modelo": "gpt-image-1.5", "provider": "openai" },
    "acervo": { "ativo": false, "max_refs": 20, "dir": null }
  },
  "familias": {
    "smark": {
      "marcas": ["smark", "provider-max", "elever-ai"],
      "registro": "abstrato-material",
      "modelo": "google/gemini-3-pro-image",
      "calibrado_em": "2026-07-24",
      "acervo": { "ativo": false, "dir": "design-system/acervo/smark" }
    }
  },
  "familia_padrao": "smark"
}
```

- [ ] **Step 4: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Resolve o perfil de imagem de uma marca: família, modelo, seed e acervo.

Fonte única: design-system/tokens/perfis-imagem.json. Nenhuma decisão estética
mora em código — só no contrato. Ver docs/superpowers/specs/2026-07-24-motor-de-imagem-calibrado-design.md
"""
import hashlib
import json
import os
from math import gcd

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRATO = os.path.join(VAULT, "design-system", "tokens", "perfis-imagem.json")


def carregar(path=None):
    """Lê o contrato de perfis. Erro explícito se estiver ausente ou inválido."""
    p = path or CONTRATO
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def familia_de(marca, cfg):
    """Nome da família que contém `marca`; a família padrão se não houver correspondência."""
    for nome, fam in (cfg.get("familias") or {}).items():
        if marca in (fam.get("marcas") or []):
            return nome
    return cfg.get("familia_padrao", "smark")


def calcular_seed(familia, slug, tipo, reroll=0):
    """Seed determinística: mesma entrada, mesma imagem. `reroll` varia de propósito."""
    chave = f"{familia}:{slug}:{tipo}".encode("utf-8")
    base = int(hashlib.sha256(chave).hexdigest()[:8], 16) % (2 ** 31)
    return base + int(reroll or 0)


def aspect_de_size(size):
    """'1024x1536' -> '2:3'. Devolve '' se não der pra interpretar."""
    try:
        w, h = str(size).lower().split("x")
        w, h = int(w), int(h)
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    except Exception:
        return ""


def capacidades(modelo, cfg):
    """Entrada do roster pro modelo (suporta_seed, max_refs, provider). {} se fora do roster."""
    return ((cfg.get("_base", {}).get("roster") or {}).get(modelo)) or {}


def resolver(marca, slug="", tipo="", reroll=0, size="1024x1536", cfg=None):
    """Devolve tudo que o orquestrador precisa pra chamar o provedor.

    Não existe tier: 1K/2K/4K custam o mesmo no modelo default, então a
    resolução é única e vem de `_base.resolution`.
    """
    cfg = cfg or carregar()
    base = cfg.get("_base", {})
    familia = familia_de(marca, cfg)
    fam = (cfg.get("familias") or {}).get(familia, {})

    modelo = fam.get("modelo")
    nao_calibrado = not modelo
    suplente = fam.get("suplente") or base.get("suplente") or {}

    if nao_calibrado:
        modelo = suplente.get("modelo", "gpt-image-1.5")

    cap = capacidades(modelo, cfg)
    provider = cap.get("provider") or fam.get("provider") or base.get("provider", "openrouter")

    acervo_base = base.get("acervo", {})
    acervo_fam = fam.get("acervo", {})
    acervo_dir = acervo_fam.get("dir") or acervo_base.get("dir")
    # O teto do contrato nunca pode passar do que o modelo aceita.
    teto = int(cap.get("max_refs", 0) or 0)
    acervo_max = min(int(acervo_base.get("max_refs", 20)), teto) if teto else 0

    return {
        "familia": familia,
        "modelo": modelo,
        "provider": provider,
        "resolution": base.get("resolution", "4K"),
        "aspect_ratio": aspect_de_size(size),
        "seed": calcular_seed(familia, slug, tipo, reroll),
        "enviar_seed": bool(cap.get("suporta_seed", False)),
        "suplente_modelo": suplente.get("modelo", "gpt-image-1.5"),
        "suplente_provider": suplente.get("provider", "openai"),
        "nao_calibrado": nao_calibrado,
        "acervo_ativo": bool(acervo_fam.get("ativo", acervo_base.get("ativo", False))),
        "acervo_dir": os.path.join(VAULT, acervo_dir) if acervo_dir else "",
        "acervo_max": acervo_max,
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_perfil.py -v`
Expected: PASS — 12 passed

- [ ] **Step 6: Commit**

```bash
git add design-system/tokens/perfis-imagem.json scripts/_perfil.py tests/test_perfil.py
git commit -m "feat: contrato de perfis de imagem e resolver (família, modelo, capacidades)"
```

---

### Task 2: Ledger de custo

**Files:**
- Create: `scripts/_ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: nada.
- Produces: `registrar(evento: dict, path=None) -> str` — anexa uma linha JSON, cria o diretório se preciso, devolve o caminho do ledger. Acrescenta `data` (ISO) se ausente. Nunca levanta exceção para o chamador.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ledger.py
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _ledger  # noqa: E402


def test_registra_uma_linha_por_evento(tmp_path):
    alvo = str(tmp_path / "sub" / "geracoes.jsonl")
    _ledger.registrar({"marca": "smark", "custo_usd": 0.04}, path=alvo)
    _ledger.registrar({"marca": "elever-ai", "custo_usd": 0.04}, path=alvo)
    linhas = open(alvo, encoding="utf-8").read().strip().split("\n")
    assert len(linhas) == 2
    assert json.loads(linhas[0])["marca"] == "smark"


def test_acrescenta_data_automaticamente(tmp_path):
    alvo = str(tmp_path / "g.jsonl")
    _ledger.registrar({"marca": "smark"}, path=alvo)
    ev = json.loads(open(alvo, encoding="utf-8").read().strip())
    assert "data" in ev and ev["data"].startswith("20")


def test_preserva_data_informada(tmp_path):
    alvo = str(tmp_path / "g.jsonl")
    _ledger.registrar({"data": "2020-01-01T00:00:00", "marca": "smark"}, path=alvo)
    ev = json.loads(open(alvo, encoding="utf-8").read().strip())
    assert ev["data"] == "2020-01-01T00:00:00"


def test_falha_de_escrita_nao_propaga(tmp_path):
    # diretório inexistente E sem permissão de criação → não pode explodir
    _ledger.registrar({"marca": "smark"}, path="/proc/impossivel/g.jsonl")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_ledger.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named '_ledger'`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Ledger append-only de gerações de imagem: uma linha JSON por chamada.

Base do custo por peça, por marca e por campanha. Nunca derruba a geração:
se não conseguir escrever, avisa em stderr e segue."""
import datetime
import json
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_PADRAO = os.path.join(VAULT, "design-system", "custos", "geracoes.jsonl")


def registrar(evento, path=None):
    """Anexa `evento` ao ledger. Devolve o caminho usado."""
    alvo = path or LEDGER_PADRAO
    ev = dict(evento)
    ev.setdefault("data", datetime.datetime.now().isoformat(timespec="seconds"))
    try:
        os.makedirs(os.path.dirname(alvo), exist_ok=True)
        with open(alvo, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"AVISO: não foi possível gravar no ledger ({e})", file=sys.stderr)
    return alvo
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_ledger.py -v`
Expected: PASS — 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/_ledger.py tests/test_ledger.py
git commit -m "feat: ledger append-only de custo por geração"
```

---

### Task 3: Provedor HTTP (OpenRouter + OpenAI)

**Files:**
- Create: `scripts/_provedor.py`
- Test: `tests/test_provedor.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `class ErroProvedor(Exception)` com atributo `.codigo` (int ou `None`).
  - `para_png(raw: bytes) -> bytes` — devolve PNG. Passa direto se já for PNG; converte se for JPEG; devolve intacto com aviso em stderr se não reconhecer.
  - `gerar(prompt, modelo, provider, chaves, *, resolution=None, aspect_ratio=None, seed=None, size=None, quality=None, refs=None, timeout=180) -> dict` com chaves `png` (bytes, **sempre PNG**), `custo_usd` (float ou `None`), `modelo`, `provider`.
  - `chaves` é `{"openrouter": str|None, "openai": str|None}`.
  - `refs` é lista de data-URLs (`str`), só usada no backend `openrouter`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_provedor.py
import base64
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _provedor  # noqa: E402

PNG = base64.b64encode(b"fake-png-bytes").decode()


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _captura(monkeypatch, payload):
    """Substitui urlopen e devolve a lista onde os requests caem."""
    vistos = []

    def fake(req, timeout=None):
        vistos.append(req)
        return _Resp(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return vistos


def test_openrouter_envia_resolution_e_devolve_custo(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.135}})
    r = _provedor.gerar("um prompt", "google/gemini-3-pro-image", "openrouter",
                        {"openrouter": "k1"}, resolution="4K", aspect_ratio="4:5")
    assert r["png"] == b"fake-png-bytes"
    assert r["custo_usd"] == 0.135
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["resolution"] == "4K"
    assert corpo["aspect_ratio"] == "4:5"
    assert "seed" not in corpo          # não foi pedida — não vai no corpo
    assert "openrouter.ai" in vistos[0].full_url


def test_openrouter_envia_seed_quando_pedida(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.04}})
    _provedor.gerar("p", "m", "openrouter", {"openrouter": "k1"}, seed=99)
    assert json.loads(vistos[0].data.decode())["seed"] == 99


def test_openai_envia_size_e_quality_e_nao_manda_seed(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}]})
    r = _provedor.gerar("p", "gpt-image-1.5", "openai", {"openai": "k2"},
                        size="1024x1536", quality="high", seed=99)
    assert r["png"] == b"fake-png-bytes"
    assert r["custo_usd"] is None
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["size"] == "1024x1536"
    assert corpo["quality"] == "high"
    assert "seed" not in corpo
    assert "api.openai.com" in vistos[0].full_url


def test_refs_viram_input_references_no_openrouter(monkeypatch):
    vistos = _captura(monkeypatch, {"data": [{"b64_json": PNG}], "usage": {"cost": 0.04}})
    _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"},
                    refs=["data:image/png;base64,AAA", "data:image/png;base64,BBB"])
    corpo = json.loads(vistos[0].data.decode())
    assert corpo["input_references"] == ["data:image/png;base64,AAA", "data:image/png;base64,BBB"]


def test_sem_chave_levanta_erro_provedor():
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": None})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert "OPENROUTER_API_KEY" in str(e)


def test_http_402_vira_erro_provedor_com_codigo(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 402, "Payment Required", {},
                                     __import__("io").BytesIO(b'{"error":{"message":"sem credito"}}'))

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert e.codigo == 402


def test_resposta_sem_imagem_vira_erro_provedor(monkeypatch):
    _captura(monkeypatch, {"data": []})
    try:
        _provedor.gerar("p", "m", "openrouter", {"openrouter": "k"})
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor as e:
        assert "sem imagem" in str(e)


def test_png_passa_intacto():
    raw = b"\x89PNG\r\n\x1a\n" + b"resto"
    assert _provedor.para_png(raw) == raw


def test_jpeg_vira_png():
    """A MESMA chamada devolveu jpeg numa execução e png na outra. Normalizar sempre."""
    jpeg = _JPEG_1PX
    saida = _provedor.para_png(jpeg)
    assert saida.startswith(b"\x89PNG\r\n\x1a\n")


def test_bytes_irreconheciveis_passam_intactos():
    assert _provedor.para_png(b"fake-png-bytes") == b"fake-png-bytes"
```

Acrescente esta constante logo abaixo de `PNG = ...` no topo do arquivo de teste — é um JPEG real de 1x1 pixel:

```python
_JPEG_1PX = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAA"
    "AAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_provedor.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named '_provedor'`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Única peça que fala HTTP com fornecedor de imagem.

Dois backends atrás da mesma interface:
  - openrouter → POST /api/v1/images  (seed, resolution, aspect_ratio, input_references, custo)
  - openai     → POST /v1/images/generations (size, quality; sem seed, sem custo na resposta)

Também normaliza a saída pra PNG: a MESMA chamada ao gemini-3-pro-image devolveu
image/jpeg numa execução e image/png na outra, e a regra 6 do CLAUDE.md exige .png.

Nenhuma decisão de modelo ou estética mora aqui — isso é do _perfil.py."""
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

URL_OPENROUTER = "https://openrouter.ai/api/v1/images"
URL_OPENAI = "https://api.openai.com/v1/images/generations"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"


def para_png(raw):
    """Garante PNG na saída. Passa direto se já for; converte se for JPEG.

    Sem dependência nova: usa `sips`, que vem no macOS. Se não der pra converter,
    devolve os bytes originais e avisa — melhor uma arte com extensão errada do
    que nenhuma arte.
    """
    if not raw or raw.startswith(MAGIC_PNG):
        return raw
    if not raw.startswith(MAGIC_JPEG):
        print("AVISO: formato de imagem não reconhecido; gravando como veio",
              file=sys.stderr)
        return raw
    try:
        d = tempfile.mkdtemp(prefix="smark-img-")
        src, dst = os.path.join(d, "i.jpg"), os.path.join(d, "o.png")
        with open(src, "wb") as f:
            f.write(raw)
        r = subprocess.run(["/usr/bin/sips", "-s", "format", "png", src, "--out", dst],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(dst):
            with open(dst, "rb") as f:
                return f.read()
        raise RuntimeError(r.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        print(f"AVISO: falha ao converter JPEG->PNG ({e}); gravando o JPEG original",
              file=sys.stderr)
        return raw


class ErroProvedor(Exception):
    """Falha ao gerar imagem. `codigo` traz o status HTTP quando houver."""

    def __init__(self, mensagem, codigo=None):
        super().__init__(mensagem)
        self.codigo = codigo


def _postar(url, corpo, chave, timeout):
    req = urllib.request.Request(
        url, data=json.dumps(corpo).encode("utf-8"),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        bruto = urllib.request.urlopen(req, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "ignore")[:400]
        raise ErroProvedor(f"HTTP {e.code}: {detalhe}", codigo=e.code)
    except Exception as e:
        raise ErroProvedor(f"falha de rede: {e}")
    return json.loads(bruto.decode("utf-8"))


def gerar(prompt, modelo, provider, chaves, *, resolution=None, aspect_ratio=None,
          seed=None, size=None, quality=None, refs=None, timeout=180):
    """Gera uma imagem e devolve {'png', 'custo_usd', 'modelo', 'provider'}."""
    if provider == "openrouter":
        chave = (chaves or {}).get("openrouter")
        if not chave:
            raise ErroProvedor("OPENROUTER_API_KEY ausente (.env na raiz do vault)")
        corpo = {"model": modelo, "prompt": prompt}
        if resolution:
            corpo["resolution"] = resolution
        if aspect_ratio:
            corpo["aspect_ratio"] = aspect_ratio
        if seed is not None:
            corpo["seed"] = int(seed)
        if refs:
            corpo["input_references"] = list(refs)
        url = URL_OPENROUTER
    elif provider == "openai":
        chave = (chaves or {}).get("openai")
        if not chave:
            raise ErroProvedor("OPENAI_API_KEY ausente (.env na raiz do vault)")
        corpo = {"model": modelo, "prompt": prompt, "n": 1}
        if size:
            corpo["size"] = size
        if quality:
            corpo["quality"] = quality
        url = URL_OPENAI
    else:
        raise ErroProvedor(f"provider desconhecido: {provider}")

    payload = _postar(url, corpo, chave, timeout)

    try:
        b64 = payload["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError):
        raise ErroProvedor(f"resposta sem imagem: {json.dumps(payload)[:300]}")

    custo = None
    try:
        custo = float(payload["usage"]["cost"])
    except (KeyError, TypeError, ValueError):
        pass

    return {"png": para_png(base64.b64decode(b64)), "custo_usd": custo,
            "modelo": modelo, "provider": provider}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_provedor.py -v`
Expected: PASS — 10 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/_provedor.py tests/test_provedor.py
git commit -m "feat: provedor de imagem com backends OpenRouter e OpenAI"
```

---

### Task 4: Metadados da arte com modelo, seed e custo

**Files:**
- Modify: `scripts/_sidecar.py:19-34`
- Test: `tests/test_sidecar.py`

**Interfaces:**
- Consumes: nada.
- Produces: `meta_block(out_png, meta)` passa a reconhecer as chaves `seed`, `custo_usd`, `provider`, `suplente_usado` além das atuais (`modelo`, `qualidade`, `tamanho`, `paleta`). Campos vazios continuam saindo como linha vazia — o formato existente não muda.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sidecar.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _sidecar  # noqa: E402


def test_mantem_campos_existentes():
    bloco = _sidecar.meta_block("/x/arte/01.png", {"modelo": "gpt-image-1.5",
                                                   "qualidade": "high",
                                                   "tamanho": "1024x1536",
                                                   "paleta": "roxo"})
    assert "arte: arte/01.png" in bloco
    assert "arte-modelo: gpt-image-1.5" in bloco
    assert "arte-proporcao: 2:3" in bloco
    assert "embed-no-corpo: ![[arte/01.png]]" in bloco


def test_inclui_campos_novos():
    bloco = _sidecar.meta_block("/x/arte/01.png", {
        "modelo": "google/gemini-3-pro-image", "tamanho": "1024x1536",
        "seed": 12345, "custo_usd": 0.135,
        "provider": "openrouter", "suplente_usado": False})
    assert "arte-seed: 12345" in bloco
    assert "arte-custo-usd: 0.135" in bloco
    assert "arte-provider: openrouter" in bloco
    assert "arte-suplente: false" in bloco


def test_suplente_true_sai_como_true():
    bloco = _sidecar.meta_block("/x/a.png", {"suplente_usado": True})
    assert "arte-suplente: true" in bloco
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_sidecar.py -v`
Expected: FAIL — `test_inclui_campos_novos` falha com `assert 'arte-seed: 12345' in bloco`

- [ ] **Step 3: Write minimal implementation**

Substituir o corpo de `meta_block` em `scripts/_sidecar.py` por:

```python
def meta_block(out_png, meta):
    """Retorna um bloco YAML (campos arte-*) + a linha de embed, pra colar na nota do post."""
    today = datetime.date.today().isoformat()
    size = meta.get("tamanho", "")
    fn = os.path.basename(out_png)
    custo = meta.get("custo_usd", "")
    supl = meta.get("suplente_usado", "")
    return "\n".join([
        "----- METADADOS DA ARTE (cole no frontmatter + corpo da nota do post) -----",
        f"arte: arte/{fn}",
        f"arte-modelo: {meta.get('modelo', '')}",
        f"arte-provider: {meta.get('provider', '')}",
        f"arte-qualidade: {meta.get('qualidade', '')}",
        f"arte-tamanho: {size}",
        f"arte-proporcao: {_aspect(size)}",
        f"arte-seed: {meta.get('seed', '')}",
        f"arte-paleta: {meta.get('paleta', '')}",
        f"arte-custo-usd: {custo if custo != '' else ''}",
        f"arte-suplente: {str(supl).lower() if supl != '' else ''}",
        f"arte-gerada-em: {today}",
        f"embed-no-corpo: ![[arte/{fn}]]",
    ])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_sidecar.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/_sidecar.py tests/test_sidecar.py
git commit -m "feat: metadados da arte com provider, seed e custo"
```

---

### Task 5: Orquestrador — `openai_image.py` usando perfil, provedor e ledger

**Files:**
- Modify: `scripts/openai_image.py` (reescrita do `main()` e do bloco HTTP, linhas 42-110)
- Test: `tests/test_openai_image.py`

**Interfaces:**
- Consumes: `_perfil.resolver`, `_provedor.gerar`, `_provedor.ErroProvedor`, `_ledger.registrar`, `_sidecar.meta_block`, `_direcao.construir`, `_paleta.aplicar_guard`.
- Produces:
  - `carregar_chaves(env) -> dict` — `{"openrouter": ..., "openai": ...}` a partir de `.env` + ambiente.
  - `gerar_com_suplente(prompt, perfil, chaves, size, quality, refs=None) -> dict` — tenta o modelo do perfil; em `ErroProvedor` tenta o suplente uma vez. Devolve o dict do provedor acrescido de `suplente_usado: bool`.
  - Novos flags de CLI: `--reroll N` (default 0), `--provider {auto,openrouter,openai}` (default `auto`), `--slug TEXTO`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_openai_image.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _provedor  # noqa: E402
import openai_image  # noqa: E402


def test_carregar_chaves_le_env_e_ambiente(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "do-ambiente")
    ch = openai_image.carregar_chaves({"OPENAI_API_KEY": "do-arquivo"})
    assert ch["openrouter"] == "do-ambiente"
    assert ch["openai"] == "do-arquivo"


def test_usa_o_modelo_do_perfil_quando_da_certo(monkeypatch):
    chamadas = []

    def fake(prompt, modelo, provider, chaves, **kw):
        chamadas.append(modelo)
        return {"png": b"x", "custo_usd": 0.04, "modelo": modelo, "provider": provider}

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "google/gemini-3-pro-image", "provider": "openrouter",
              "resolution": "4K", "aspect_ratio": "2:3", "seed": 7,
              "suplente_modelo": "gpt-image-1.5", "suplente_provider": "openai"}
    r = openai_image.gerar_com_suplente("p", perfil, {"openrouter": "k"}, "1024x1536", "high")
    assert chamadas == ["google/gemini-3-pro-image"]
    assert r["suplente_usado"] is False


def test_cai_no_suplente_quando_o_principal_falha(monkeypatch):
    chamadas = []

    def fake(prompt, modelo, provider, chaves, **kw):
        chamadas.append(modelo)
        if modelo == "google/gemini-3-pro-image":
            raise _provedor.ErroProvedor("sem credito", codigo=402)
        return {"png": b"y", "custo_usd": None, "modelo": modelo, "provider": provider}

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "google/gemini-3-pro-image", "provider": "openrouter",
              "resolution": "4K", "aspect_ratio": "2:3", "seed": 7,
              "suplente_modelo": "gpt-image-1.5", "suplente_provider": "openai"}
    r = openai_image.gerar_com_suplente("p", perfil, {"openai": "k"}, "1024x1536", "high")
    assert chamadas == ["google/gemini-3-pro-image", "gpt-image-1.5"]
    assert r["suplente_usado"] is True
    assert r["png"] == b"y"


def test_valida_modelo_contra_o_roster():
    cfg = __import__("_perfil").carregar()
    roster = cfg["_base"]["roster"]
    assert openai_image.fora_do_roster("modelo/inventado", roster, "gpt-image-1.5") is True
    assert openai_image.fora_do_roster("google/gemini-3-pro-image", roster, "gpt-image-1.5") is False
    assert openai_image.fora_do_roster("gpt-image-1.5", roster, "gpt-image-1.5") is False


def test_falha_dos_dois_propaga_erro(monkeypatch):
    def fake(prompt, modelo, provider, chaves, **kw):
        raise _provedor.ErroProvedor("caiu", codigo=500)

    monkeypatch.setattr(_provedor, "gerar", fake)
    perfil = {"modelo": "m1", "provider": "openrouter", "resolution": "4K",
              "aspect_ratio": "2:3", "seed": 1,
              "suplente_modelo": "m2", "suplente_provider": "openai"}
    try:
        openai_image.gerar_com_suplente("p", perfil, {}, "1024x1536", "high")
        assert False, "deveria ter levantado"
    except _provedor.ErroProvedor:
        pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_openai_image.py -v`
Expected: FAIL com `AttributeError: module 'openai_image' has no attribute 'carregar_chaves'`

- [ ] **Step 3: Write minimal implementation**

Substituir, em `scripts/openai_image.py`, o bloco de imports/constantes e todo o `main()` por:

```python
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
    """True se o modelo não está no roster do contrato nem é o suplente declarado.

    `roster` é o dict de capacidades (`_base.roster`); basta testar as chaves."""
    return modelo not in (roster or {}) and modelo != suplente


def gerar_com_suplente(prompt, perfil, chaves, size, quality, refs=None):
    """Tenta o modelo do perfil; em falha, uma tentativa no suplente."""
    try:
        r = _provedor.gerar(prompt, perfil["modelo"], perfil["provider"], chaves,
                            resolution=perfil.get("resolution"),
                            aspect_ratio=perfil.get("aspect_ratio"),
                            seed=perfil.get("seed") if perfil.get("enviar_seed") else None,
                            size=size, quality=quality, refs=refs)
        r["suplente_usado"] = False
        return r
    except _provedor.ErroProvedor as e:
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
    ap.add_argument("--reroll", type=int, default=0, help="varia a seed de propósito")
    ap.add_argument("--slug", default="", help="slug do post — entra na seed determinística")
    ap.add_argument("--marca", default="")
    ap.add_argument("--canal", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--paleta", default="")
    ap.add_argument("--headline", default="")
    ap.add_argument("--post", default="")
    ap.add_argument("--legenda-file", default="")
    ap.add_argument("--no-guard", action="store_true", help="desliga a trava de paleta (cor on-brand)")
    ap.add_argument("--direcao", action="store_true", help="monta o prompt do fundo via _direcao (nível agência)")
    ap.add_argument("--tipo", default="", help="tipo do post (manifesto/dor/prova/cta...)")
    ap.add_argument("--tema", default="escuro", help="escuro | claro")
    ap.add_argument("--conceito", default="", help="sobrescreve a metáfora visual")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file and not args.direcao:
        sys.exit("ERRO: informe --prompt, --prompt-file ou --direcao")
    if args.direcao and not args.prompt and not args.prompt_file:
        import _direcao
        prompt = _direcao.construir(args.marca, args.tipo, args.tema, args.headline, args.conceito)
    else:
        prompt = args.prompt
        if args.prompt_file:
            prompt = open(args.prompt_file, "r", encoding="utf-8").read().strip()
    prompt = aplicar_guard(prompt, args.paleta, not args.no_guard)

    env = load_env(os.path.join(VAULT, ".env"))
    chaves = carregar_chaves(env)

    slug = args.slug or os.path.splitext(os.path.basename(args.out))[0]
    perfil = _perfil.resolver(args.marca or "smark", slug=slug,
                              tipo=args.tipo, reroll=args.reroll, size=args.size)
    if args.model:
        roster = _perfil.carregar().get("_base", {}).get("roster", {})
        if fora_do_roster(args.model, roster, perfil["suplente_modelo"]):
            sys.exit(f"ERRO: '{args.model}' não está no roster do contrato "
                     f"(design-system/tokens/perfis-imagem.json).\n"
                     f"Roster: {', '.join(roster)} | suplente: {perfil['suplente_modelo']}")
        perfil["modelo"] = args.model
    if args.provider != "auto":
        perfil["provider"] = args.provider
    if perfil["nao_calibrado"]:
        print(f"AVISO: família '{perfil['familia']}' sem calibração — usando suplente "
              f"{perfil['modelo']}. Rode scripts/calibrar.py.", file=sys.stderr)

    try:
        r = gerar_com_suplente(prompt, perfil, chaves, args.size, args.quality)
    except _provedor.ErroProvedor as e:
        sys.exit(f"ERRO: {e}")

    out = args.out if os.path.isabs(args.out) else os.path.join(VAULT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(r["png"])

    _ledger.registrar({
        "familia": perfil["familia"], "marca": args.marca, "slug": slug,
        "tipo": args.tipo, "modelo": r["modelo"],
        "provider": r["provider"], "seed": perfil["seed"],
        "resolucao": perfil["resolution"], "custo_usd": r["custo_usd"],
        "ok": True, "suplente_usado": r["suplente_usado"],
        "nao_calibrado": perfil["nao_calibrado"], "arquivo": os.path.basename(out),
    })

    print(f"OK: {out}  ({r['modelo']} via {r['provider']}, "
          f"seed={perfil['seed']}, custo=${r['custo_usd'] if r['custo_usd'] is not None else '?'})")
    print(meta_block(out, {"modelo": r["modelo"], "provider": r["provider"],
                           "qualidade": args.quality,
                           "tamanho": args.size, "paleta": args.paleta,
                           "seed": perfil["seed"], "custo_usd": r["custo_usd"],
                           "suplente_usado": r["suplente_usado"]}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_openai_image.py -v`
Expected: PASS — 5 passed

Run: `cd /Users/andreik/smark && python3 scripts/openai_image.py --out /tmp/x.png --prompt "teste" --model modelo/inventado`
Expected: sai com `ERRO: 'modelo/inventado' não está no roster do contrato` e código ≠ 0

- [ ] **Step 5: Verificar que a CLI antiga não quebrou**

Run: `cd /Users/andreik/smark && python3 scripts/openai_image.py --help`
Expected: a ajuda lista `--out --prompt --prompt-file --size --quality --model --provider --reroll --slug --marca ... --direcao --tipo --tema --conceito` sem erro.

Run: `cd /Users/andreik/smark && python3 scripts/openai_image.py --out /tmp/regressao.png --direcao --marca smark --tipo manifesto --tema claro`
Expected: gera o PNG via `google/gemini-3-pro-image` na OpenRouter (a família já vem calibrada no contrato), custo ~US$ 0,244 impresso na linha OK. Confirmar com `ls -la /tmp/regressao.png`, `file /tmp/regressao.png` (tem que dizer **PNG**, mesmo se a API devolver JPEG) e `tail -1 design-system/custos/geracoes.jsonl`.

- [ ] **Step 6: Commit**

```bash
git add scripts/openai_image.py tests/test_openai_image.py
git commit -m "feat: openai_image usa perfil, provedor e ledger; seed e suplente"
```

---

### Task 6: `openai_edit.py` no mesmo provedor e ledger

**Files:**
- Modify: `scripts/openai_edit.py:24-25, 82-105`
- Test: `tests/test_openai_edit.py`

**Interfaces:**
- Consumes: `_ledger.registrar`.
- Produces: `openai_edit.py` grava no mesmo ledger e imprime custo quando houver. A edição continua no backend OpenAI (multipart com `input_fidelity`, que o roteador não expõe) — a mudança é só de telemetria.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_openai_edit.py
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


def test_openai_edit_importa_ledger():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "openai_edit.py"),
                 encoding="utf-8").read()
    assert "import _ledger" in fonte
    assert "_ledger.registrar" in fonte
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_openai_edit.py -v`
Expected: FAIL com `assert 'import _ledger' in fonte`

- [ ] **Step 3: Write minimal implementation**

Em `scripts/openai_edit.py`, junto dos outros imports locais (perto de `from _paleta import aplicar_guard`), acrescentar:

```python
import _ledger  # noqa: E402
```

E, logo depois da linha que grava o PNG de saída (antes do `print("OK: ...")`), acrescentar:

```python
    _ledger.registrar({
        "familia": "", "marca": getattr(args, "marca", ""), "slug": "",
        "tipo": "edit", "modelo": model, "provider": "openai",
        "seed": None, "resolucao": args.size, "custo_usd": None,
        "ok": True, "suplente_usado": False, "nao_calibrado": False,
        "arquivo": os.path.basename(out),
    })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_openai_edit.py -v`
Expected: PASS — 1 passed

Run: `cd /Users/andreik/smark && python3 scripts/openai_edit.py --help`
Expected: ajuda sem erro de import.

- [ ] **Step 5: Commit**

```bash
git add scripts/openai_edit.py tests/test_openai_edit.py
git commit -m "feat: openai_edit registra no ledger de custo"
```

---

### Task 7: Bake-off de calibração

**Files:**
- Create: `scripts/calibrar.py`
- Test: `tests/test_calibrar.py`

**Interfaces:**
- Consumes: `_perfil`, `_provedor`, `_direcao`, `_paleta`, `_ledger`.
- Produces:
  - `candidatos(cfg) -> list[str]` — o roster do contrato.
  - `fixar(familia, modelo, data, path=None) -> dict` — grava `modelo` e `calibrado_em` no contrato e devolve o cfg atualizado.
  - CLI: `python3 scripts/calibrar.py --familia smark --marca smark [--tipos manifesto,dor,prova] [--fixar MODELO]`. Sem `--fixar`, gera as variantes em `design-system/calibracao/<familia>/<modelo-sanitizado>-<tipo>.png` e imprime os critérios de avaliação. Com `--fixar`, só grava a escolha no contrato.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_calibrar.py
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _perfil  # noqa: E402
import calibrar  # noqa: E402


def test_candidatos_vem_do_roster():
    cfg = _perfil.carregar()
    assert "google/gemini-3-pro-image" in calibrar.candidatos(cfg)


def test_fixar_grava_modelo_e_data(tmp_path):
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    cfg = calibrar.fixar("smark", "google/gemini-3-pro-image", "2026-07-24", path=alvo)
    assert cfg["familias"]["smark"]["modelo"] == "google/gemini-3-pro-image"
    assert cfg["familias"]["smark"]["calibrado_em"] == "2026-07-24"
    gravado = json.load(open(alvo, encoding="utf-8"))
    assert gravado["familias"]["smark"]["modelo"] == "google/gemini-3-pro-image"


def test_fixar_recusa_modelo_fora_do_roster(tmp_path):
    origem = _perfil.CONTRATO
    alvo = str(tmp_path / "perfis-imagem.json")
    shutil.copy(origem, alvo)
    try:
        calibrar.fixar("smark", "modelo/inventado", "2026-07-24", path=alvo)
        assert False, "deveria ter recusado"
    except ValueError as e:
        assert "roster" in str(e)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_calibrar.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'calibrar'`

- [ ] **Step 3: Write minimal implementation**

```python
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
    """Grava modelo e calibrado_em no contrato. Recusa modelo fora do roster."""
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
            seed = _perfil.calcular_seed(args.familia, "calibracao", tipo)
            cap = _perfil.capacidades(modelo, cfg)
            prompt = aplicar_guard(
                _direcao.construir(args.marca, tipo, args.tema, "", ""), args.paleta, True)
            out = os.path.join(destino, f"{_sanitizar(modelo)}-{tipo}.png")
            try:
                r = _provedor.gerar(
                    prompt, modelo, cap.get("provider", "openrouter"), chaves,
                    resolution="2K", aspect_ratio="4:5",
                    seed=seed if cap.get("suporta_seed") else None,
                    size="1024x1536", quality="high")
            except _provedor.ErroProvedor as e:
                print(f"FALHOU {modelo} / {tipo}: {e}", file=sys.stderr)
                falhas += 1
                continue
            with open(out, "wb") as f:
                f.write(r["png"])
            _ledger.registrar({"familia": args.familia, "marca": args.marca,
                               "slug": "calibracao", "tipo": tipo,
                               "modelo": modelo, "provider": cap.get("provider", "openrouter"),
                               "seed": seed,
                               "resolucao": "2K", "custo_usd": r["custo_usd"], "ok": True,
                               "suplente_usado": False, "nao_calibrado": True,
                               "arquivo": os.path.basename(out)})
            print(f"OK: {out}  (custo=${r['custo_usd']})")

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_calibrar.py -v`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/calibrar.py tests/test_calibrar.py
git commit -m "feat: bake-off de calibração por família"
```

---

### Task 8: Acervo de referências (fase 2 — núcleo)

**Files:**
- Create: `scripts/_acervo.py`
- Create: `scripts/acervo.py`
- Modify: `scripts/openai_image.py` (função `main()`, bloco de geração)
- Test: `tests/test_acervo.py`

**Interfaces:**
- Consumes: `_perfil.resolver`.
- Produces:
  - `listar(acervo_dir, max_refs=20) -> list[str]` — caminhos `.png`, mais recentes primeiro, limitado a `max_refs`.
  - `adicionar(png_path, acervo_dir) -> str` — copia a peça pro acervo com prefixo de data, devolve o destino.
  - `remover(nome, acervo_dir) -> bool`.
  - `como_data_urls(paths) -> list[str]` — `data:image/png;base64,...`.
  - CLI `acervo.py`: `add <png> --marca smark`, `list --marca smark`, `rm <nome> --marca smark`.
  - `openai_image.py` ganha `--sem-acervo` (desliga a injeção) e passa `refs` quando `perfil["acervo_ativo"]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_acervo.py
import base64
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _acervo  # noqa: E402


def _png(p, conteudo=b"\x89PNG-fake"):
    open(p, "wb").write(conteudo)
    return p


def test_listar_devolve_mais_recentes_primeiro(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    a = _png(str(d / "2026-01-01-a.png"))
    time.sleep(0.01)
    b = _png(str(d / "2026-01-02-b.png"))
    assert _acervo.listar(str(d)) == [b, a]


def test_listar_respeita_o_teto(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    for i in range(5):
        _png(str(d / f"p{i}.png"))
        time.sleep(0.01)
    assert len(_acervo.listar(str(d), max_refs=3)) == 3


def test_listar_diretorio_inexistente_devolve_vazio(tmp_path):
    assert _acervo.listar(str(tmp_path / "nao-existe")) == []


def test_listar_ignora_nao_png(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    _png(str(d / "ok.png"))
    open(str(d / "leia.md"), "w").write("x")
    assert len(_acervo.listar(str(d))) == 1


def test_adicionar_copia_com_prefixo_de_data(tmp_path):
    origem = _png(str(tmp_path / "arte.png"))
    d = str(tmp_path / "acervo")
    destino = _acervo.adicionar(origem, d)
    assert os.path.exists(destino)
    assert os.path.basename(destino).endswith("-arte.png")
    assert len(_acervo.listar(d)) == 1


def test_remover(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    _png(str(d / "x.png"))
    assert _acervo.remover("x.png", str(d)) is True
    assert _acervo.remover("x.png", str(d)) is False


def test_como_data_urls(tmp_path):
    p = _png(str(tmp_path / "a.png"), b"abc")
    urls = _acervo.como_data_urls([p])
    assert urls[0] == "data:image/png;base64," + base64.b64encode(b"abc").decode()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_acervo.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named '_acervo'`

- [ ] **Step 3: Write `_acervo.py`**

```python
#!/usr/bin/env python3
"""Acervo de peças-referência por família de marca.

Cada arte aprovada e marcada entra aqui e passa a alimentar as gerações
seguintes via input_references. É o ativo que compõe juros: um concorrente
com o mesmo modelo e o mesmo prompt não tem as peças que esta marca aprovou.

Curadoria é obrigatória — só entra o que foi marcado à mão. Teto em max_refs."""
import base64
import datetime
import os
import shutil


def listar(acervo_dir, max_refs=20):
    """PNGs do acervo, mais recentes primeiro, limitados a `max_refs`."""
    if not acervo_dir or not os.path.isdir(acervo_dir):
        return []
    itens = [os.path.join(acervo_dir, n) for n in os.listdir(acervo_dir)
             if n.lower().endswith(".png")]
    itens.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return itens[:max_refs]


def adicionar(png_path, acervo_dir):
    """Copia a peça pro acervo com prefixo de data. Devolve o destino."""
    if not os.path.exists(png_path):
        raise FileNotFoundError(png_path)
    os.makedirs(acervo_dir, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    destino = os.path.join(acervo_dir, f"{hoje}-{os.path.basename(png_path)}")
    shutil.copy2(png_path, destino)
    return destino


def remover(nome, acervo_dir):
    """Remove uma peça do acervo pelo nome do arquivo. True se removeu."""
    alvo = os.path.join(acervo_dir, os.path.basename(nome))
    if os.path.exists(alvo):
        os.remove(alvo)
        return True
    return False


def como_data_urls(paths):
    """Converte caminhos de PNG em data-URLs pro input_references."""
    urls = []
    for p in paths:
        with open(p, "rb") as f:
            urls.append("data:image/png;base64," + base64.b64encode(f.read()).decode())
    return urls
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_acervo.py -v`
Expected: PASS — 7 passed

- [ ] **Step 5: Write the CLI `acervo.py`**

```python
#!/usr/bin/env python3
"""Curadoria do acervo de peças-referência.

  python3 scripts/acervo.py list --marca smark
  python3 scripts/acervo.py add marcas/smark/.../arte/01.png --marca smark
  python3 scripts/acervo.py rm 2026-07-24-01.png --marca smark

Só entra peça aprovada. O acervo alimenta input_references nas gerações
seguintes — peça mediana aqui puxa a qualidade das próximas pra baixo."""
import argparse
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _acervo  # noqa: E402
import _perfil  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["add", "list", "rm"])
    ap.add_argument("alvo", nargs="?", default="")
    ap.add_argument("--marca", default="smark")
    args = ap.parse_args()

    perfil = _perfil.resolver(args.marca)
    d = perfil["acervo_dir"]
    if not d:
        sys.exit(f"ERRO: família '{perfil['familia']}' sem diretório de acervo no contrato")

    if args.acao == "list":
        itens = _acervo.listar(d, perfil["acervo_max"])
        print(f"Acervo de '{perfil['familia']}' ({len(itens)}/{perfil['acervo_max']}) em {d}")
        for p in itens:
            print("  " + os.path.basename(p))
        if not perfil["acervo_ativo"]:
            print("\nAVISO: acervo INATIVO no contrato — não está sendo injetado nas gerações.")
            print("Ative com \"acervo\": {\"ativo\": true} na família em "
                  "design-system/tokens/perfis-imagem.json")
        return

    if not args.alvo:
        sys.exit(f"ERRO: '{args.acao}' precisa de um alvo")

    if args.acao == "add":
        origem = args.alvo if os.path.isabs(args.alvo) else os.path.join(VAULT, args.alvo)
        destino = _acervo.adicionar(origem, d)
        n = len(_acervo.listar(d, 10 ** 6))
        print(f"OK: {destino}")
        if n > perfil["acervo_max"]:
            print(f"AVISO: acervo com {n} peças, acima do teto de {perfil['acervo_max']}. "
                  "As mais antigas deixam de ser usadas.")
        return

    if args.acao == "rm":
        print("OK: removida" if _acervo.remover(args.alvo, d) else "nada a remover")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Ligar o acervo no `openai_image.py`**

Em `scripts/openai_image.py`, acrescentar o import junto dos outros locais:

```python
import _acervo  # noqa: E402
```

Acrescentar o flag, logo após `--reroll`:

```python
    ap.add_argument("--sem-acervo", action="store_true",
                    help="não injeta as peças-referência da família")
```

Substituir o bloco `try: r = gerar_com_suplente(...)` por:

```python
    refs = []
    if perfil["acervo_ativo"] and not args.sem_acervo:
        caminhos = _acervo.listar(perfil["acervo_dir"], perfil["acervo_max"])
        refs = _acervo.como_data_urls(caminhos)
        if refs:
            print(f"acervo: {len(refs)} peça(s) de referência da família "
                  f"'{perfil['familia']}'", file=sys.stderr)

    try:
        r = gerar_com_suplente(prompt, perfil, chaves, args.size, args.quality, refs=refs)
    except _provedor.ErroProvedor as e:
        sys.exit(f"ERRO: {e}")
```

E acrescentar `"refs": len(refs)` ao dicionário passado para `_ledger.registrar`.

- [ ] **Step 7: Run all tests**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/ -v`
Expected: PASS — todos os testes das tasks 1-8.

Run: `cd /Users/andreik/smark && python3 scripts/acervo.py list --marca smark`
Expected: imprime acervo vazio (0/20) e o aviso de acervo inativo.

- [ ] **Step 8: Commit**

```bash
git add scripts/_acervo.py scripts/acervo.py scripts/openai_image.py tests/test_acervo.py
git commit -m "feat: acervo de peças-referência alimentando input_references"
```

---

### Task 9: Marcar peça-referência pelo Super Editor

**Files:**
- Modify: `scripts/editor_server.py` (nova rota, junto das outras rotas POST perto da linha 951)
- Modify: `scripts/_editor2.html` (botão perto do fetch de `/regerar-fundo`, linha ~1118)
- Test: `tests/test_editor_acervo.py`

**Interfaces:**
- Consumes: `_acervo.adicionar`, `_acervo.listar`, `_perfil.resolver`.
- Produces: rota `POST /acervo-add` com corpo `{"marca": str, "path": str}` (path relativo ao vault) → `{"ok": true, "total": int}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_editor_acervo.py
import os


def test_rota_acervo_add_existe():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "editor_server.py"),
                 encoding="utf-8").read()
    assert '"/acervo-add"' in fonte
    assert "_acervo.adicionar" in fonte


def test_botao_no_editor():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "_editor2.html"),
                 encoding="utf-8").read()
    assert "/acervo-add" in fonte
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_editor_acervo.py -v`
Expected: FAIL com `assert '"/acervo-add"' in fonte`

- [ ] **Step 3: Acrescentar a rota no `editor_server.py`**

Localizar o import de `_sidecar`/helpers no topo do arquivo e acrescentar:

```python
import _acervo  # noqa: E402
import _perfil  # noqa: E402
```

Localizar o bloco `if path == "/regerar-fundo":` e inserir, **imediatamente antes** dele:

```python
        if path == "/acervo-add":
            try:
                marca = safe_marca(req.get("marca", "smark"))
                rel = str(req.get("path", "")).lstrip("/")
                origem = os.path.join(VAULT, rel)
                if not os.path.isfile(origem):
                    return self._send(400, {"ok": False, "erro": "arquivo não encontrado"})
                perfil = _perfil.resolver(marca)
                if not perfil["acervo_dir"]:
                    return self._send(400, {"ok": False, "erro": "família sem acervo no contrato"})
                _acervo.adicionar(origem, perfil["acervo_dir"])
                total = len(_acervo.listar(perfil["acervo_dir"], 10 ** 6))
                return self._send(200, {"ok": True, "total": total,
                                        "teto": perfil["acervo_max"],
                                        "familia": perfil["familia"]})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
```

- [ ] **Step 4: Acrescentar o botão na barra de ações do card**

Em `scripts/_editor2.html`, localizar a linha 329:

```html
        <button id=bfull>⛶ Tela cheia</button>
```

Inserir **imediatamente depois** dela:

```html
        <button id=bref title="marcar esta arte como peça-referência da marca">★ Referência</button>
```

- [ ] **Step 5: Definir e ligar o handler**

Localizar a linha 933, que hoje é:

```javascript
$('#bfull').onclick=openFull;$('#fsx').onclick=()=>document.getElementById('fsmodal').style.display='none';
```

Inserir **imediatamente antes** dela a função (usa os helpers `post()` e `frame()` já existentes nas linhas 392-393):

```javascript
async function marcarReferencia(){
  const p=post(), fr=frame();
  const art=(fr&&fr.bg)||'';
  if(!art){alert('Este card ainda não tem arte de fundo gerada.');return}
  if(!confirm('Adicionar esta arte ao acervo de referência da marca?\n\nEla vai influenciar todas as próximas gerações desta família. Só adicione peças aprovadas.'))return;
  try{
    const r=await(await fetch('/acervo-add',{method:'POST',headers:HJSON,
      body:JSON.stringify({marca:p.marca||'smark',path:art})})).json();
    if(r.ok){toast('★ No acervo de "'+r.familia+'" ('+r.total+'/'+r.teto+')')}
    else{alert('Erro: '+(r.erro||'desconhecido'))}
  }catch(e){alert('Erro: '+e.message)}
}
```

E, **na mesma linha 933**, acrescentar a ligação ao final:

```javascript
$('#bref').onclick=marcarReferencia;
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/test_editor_acervo.py -v`
Expected: PASS — 2 passed

Run: `cd /Users/andreik/smark && python3 -c "import ast; ast.parse(open('scripts/editor_server.py').read()); print('sintaxe ok')"`
Expected: `sintaxe ok`

- [ ] **Step 7: Commit**

```bash
git add scripts/editor_server.py scripts/_editor2.html tests/test_editor_acervo.py
git commit -m "feat: marcar peça-referência pelo Super Editor"
```

---

### Task 10: Documentação e regras do vault

**Files:**
- Modify: `CLAUDE.md` (regras 7 e 8)
- Modify: `shared/direcao-de-arte.md:29`
- Create: `design-system/custos/README.md`

**Interfaces:**
- Consumes: tudo das tasks anteriores.
- Produces: documentação alinhada ao motor novo.

- [ ] **Step 1: Atualizar a regra 7 do `CLAUDE.md`**

Substituir a regra 7 por:

```markdown
7. **Imagem via script.** A arte é **pipeline de 2 camadas**: o FUNDO (sem texto) por `scripts/openai_image.py` e o TEXTO/moldura por `scripts/compositor.py` (HTML/CSS nítido a 2x). Tamanho por canal em `shared/formatos-canais.md`. Cor/estilo por `marcas/<marca>/branding/identidade-visual.md` (paleta ativa). **O modelo do fundo é do contrato, não do comando:** `design-system/tokens/perfis-imagem.json` define modelo, suplente e capacidades por família de marca. Nunca crave `--model` sem motivo — o contrato existe pra manter a consistência. Calibração por `scripts/calibrar.py`.
```

- [ ] **Step 2: Acrescentar a regra 11 ao `CLAUDE.md`**

Logo após a regra 10:

```markdown
11. **Acervo, seed e custo.** Quem garante a consistência visual é o **acervo** (`scripts/acervo.py`): ele guarda as peças aprovadas de cada família e as injeta como `input_references` nas gerações seguintes — só entra peça que passou no `revisar.py` e foi marcada à mão. Cada arte aprovada deixa a próxima mais parecida com a marca; é o único ativo do sistema que não dá pra copiar. A **seed** (`família + slug + tipo`) é gravada nos metadados e serve de rótulo e de `--reroll N`, mas **não é garantia de reprodutibilidade**: o modelo default aceita `seed` e ignora. Não prometa "mesma seed, mesma imagem". Custo de cada geração fica em `design-system/custos/geracoes.jsonl`.
```

- [ ] **Step 3: Atualizar `shared/direcao-de-arte.md`**

Substituir a linha 29 (o comando de fundo dirigido) por:

```markdown
- **Fundo dirigido:** `python3 scripts/openai_image.py --out <bg.png> --direcao --marca <marca> --tipo <tipo> --tema <claro|escuro> --headline "..." [--reroll N] [--conceito "override p/ tema especial"]` — **claro é o default**; só passe `--tema escuro` sob pedido. O modelo sai do contrato (`design-system/tokens/perfis-imagem.json`), sempre em 4K (US$ 0,244; 2K sairia por 0,135 mas amolece o fundo). Não gostou do resultado? `--reroll 1`, `--reroll 2` — cada um é uma tentativa nova, ~US$ 0,244.
```

- [ ] **Step 4: Criar `design-system/custos/README.md`**

```markdown
# Custos de geração

`geracoes.jsonl` — ledger append-only, uma linha por geração de imagem.

Campos: `data`, `familia`, `marca`, `slug`, `tipo`, `modelo`, `provider`,
`seed`, `resolucao`, `custo_usd`, `refs`, `ok`, `suplente_usado`, `nao_calibrado`, `arquivo`.

`custo_usd` só vem preenchido no provider `openrouter` — a OpenAI não devolve
custo na resposta.

Total do mês:

```bash
grep '"data":"2026-07' design-system/custos/geracoes.jsonl \
  | python3 -c "import json,sys; print(round(sum((json.loads(l).get('custo_usd') or 0) for l in sys.stdin),2))"
```

Por marca:

```bash
python3 -c "
import json,collections
t=collections.Counter()
for l in open('design-system/custos/geracoes.jsonl'):
    e=json.loads(l); t[e.get('marca') or '?'] += e.get('custo_usd') or 0
for m,v in t.most_common(): print(f'{m:20s} US\$ {v:.2f}')
"
```
```

- [ ] **Step 5: Run the full suite**

Run: `cd /Users/andreik/smark && python3 -m pytest tests/ -v`
Expected: PASS — suíte inteira verde.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md shared/direcao-de-arte.md design-system/custos/README.md
git commit -m "docs: contrato de perfis, acervo e telemetria de custo nas regras do vault"
```

---

## Aceite final

Depois da Task 10, com crédito na OpenRouter (~US$ 1,20 no total):

- [ ] `python3 scripts/openai_image.py --out /tmp/a.png --direcao --marca smark --tipo manifesto --tema claro` usa `google/gemini-3-pro-image` sem aviso de não-calibrado
- [ ] `file /tmp/a.png` diz **PNG** (a API pode ter devolvido JPEG — a normalização é obrigatória)
- [ ] `tail -1 design-system/custos/geracoes.jsonl` traz `custo_usd` ≈ 0.244 e o modelo correto
- [ ] `--reroll 1` grava seed diferente no ledger
- [ ] Derrubar a rede (ou apagar `OPENROUTER_API_KEY` do ambiente) e confirmar que cai no suplente `gpt-image-1.5` com aviso em stderr, sem quebrar
- [ ] Ativar o acervo (`"ativo": true` na família), adicionar 2 peças com `acervo.py add` e confirmar a linha `acervo: 2 peça(s)` na geração seguinte
- [ ] **Teste do fosso:** gerar duas peças com o acervo ativo e confirmar a olho que compartilham material, luz e paleta com as referências — é este o mecanismo de consistência, não a seed
- [ ] `python3 scripts/calibrar.py --familia smark --marca smark` roda sem erro (bake-off segue disponível para famílias novas)
