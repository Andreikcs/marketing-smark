---
tipo: design
tema: motor de imagem calibrado por família de marca (OpenRouter + perfis + acervo)
data: 2026-07-24
status: design aprovado — corrigido pelo bake-off de 2026-07-24
autor: Andreik + Claude
origem: avaliação da OpenRouter como camada de roteamento de modelos de imagem
camada: sistema (motor de geração de arte)
depende-de: docs/superpowers/specs/2026-07-21-distribuicao-plataforma-agencias-design.md
---

# Motor de imagem calibrado por família de marca

> ## ⚠️ ERRATA — bake-off executado em 2026-07-24
>
> O spec abaixo foi escrito **antes** de gerar uma única imagem. O bake-off com
> chave paga (US$ 0,57 gastos) derrubou quatro premissas. **Onde este bloco e o
> corpo do spec divergirem, vale este bloco** — e o plano
> (`docs/superpowers/plans/2026-07-24-motor-de-imagem-calibrado.md`) já está corrigido.
>
> **1. `bytedance-seed/seedream-4.5` está reprovado e banido.** A Seção 3 o elegia
> "o único qualificado" com base na tabela de capacidades. Com o prompt real do
> `_direcao`, ele **tipografa o próprio prompt na arte**: renderizou `#9A4DFF`,
> `#F4F2FB`, `85mm`, caracteres chineses (時裝), "BAZATUR", "Brandia" e corpo de
> texto falso — mesmo com `NEGATIVE: no text, no letters, no words, no numbers`
> explícito, e também com prompt curto. Falha dura no critério 3 da Seção 6.
>
> **2. O default é `google/gemini-3-pro-image`.** Quatro gerações, zero texto
> espúrio, paleta exata, terço inferior limpo, robusto ao prompt atual (não exige
> reescrever `_direcao`). US$ 0,244/imagem em 4K medido (1K e 2K sairiam por 0,135).
>
> **3. Seed não é reprodutibilidade — o acervo é a consistência.** A Seção 4
> inteira parte de "mesma seed, mesma imagem". O modelo default **não suporta
> `seed`**: aceita o parâmetro e ignora. Duas chamadas idênticas devolveram
> composições diferentes. A seed continua sendo calculada, gravada nos metadados e
> usada pelo `--reroll`, mas só é **enviada** quando o roster marca
> `suporta_seed: true`. O que de fato trava o registro visual é o **acervo**
> (`input_references`), e isso foi **validado**: gerar com uma peça aprovada como
> referência produziu composição nova com o mesmo material, mesma luz e mesma
> paleta. O fosso da Seção 6 se confirma; a promessa de determinismo da Seção 4, não.
>
> **4. Tiers morreram.** A Seção 4 mantinha `rascunho`/`final` por latência e
> fidelidade. Medido: **1K e 2K custam o mesmo (US$ 0,135); 4K custa US$ 0,244** — a medição original só comparou 1K e 2K e concluiu errado que resolução não afeta custo. Ainda assim não há
> rascunho barato sem trocar de modelo, e trocar de modelo destrói a fidelidade de
> enquadramento que o compositor precisa. Resolução passa a ser única (`4K`).
>
> **5. Achado operacional:** o formato de saída é imprevisível — a **mesma** chamada
> devolveu `image/jpeg` numa execução e `image/png` na outra. `_provedor` normaliza
> tudo para PNG (via `sips`), porque a regra 6 do `CLAUDE.md` depende do `.png`.

## Contexto e origem

Hoje o fundo de IA sai de um único motor fixo: `gpt-image-1.5`, `1024x1536`, qualidade `high`, cravado em `scripts/openai_image.py`. Isso produz três problemas que só ficaram visíveis quando fomos avaliar a OpenRouter:

1. **Custo alto e cego.** ~US$ 0,20 por imagem, 179 gerações no último mês (≈ US$ 36/mês), sem nenhum registro de custo por peça. A OpenAI não devolve custo em dólar na resposta.
2. **Não é reprodutível.** A Images API da OpenAI não aceita `seed`. Rodar o mesmo comando duas vezes dá duas imagens diferentes. A consistência que o vault tem hoje vem inteiramente das camadas determinísticas (`_direcao.py`, `_paleta.py`, `compositor.py`) — o fundo sempre foi a parte instável.
3. **Um modelo só para todas as marcas.** Não há como encaixar o motor no registro visual de cada cliente — limitação que bloqueia a tese de licenciamento pra agências do spec de 2026-07-21.

Este design resolve os três e converte o terceiro em diferencial competitivo.

### Fatos levantados na sessão (verificados via API da OpenRouter, 2026-07-24)

| Modelo | seed | refs | retrato 4:5 | resoluções | custo |
|---|---|---|---|---|---|
| `bytedance-seed/seedream-4.5` | ✅ | 14 | ✅ | 1K / 2K / 4K | US$ 0,04/imagem (plano) |
| `black-forest-labs/flux.2-pro` | ✅ | 8 | ❌ | sem controle | US$ 0,03/MP |
| `google/gemini-3-pro-image` | ❌ | 14 | ✅ | 1K / 2K | ~US$ 0,134/imagem |
| `openai/gpt-image-2` | ❌ | 16 | ❌ | sem controle | ~US$ 0,19/imagem |
| `recraft/recraft-v4.1-vector` | ❌ | 1 | ❌ | SVG | US$ 0,08/imagem |

A varredura completa dos 40 modelos e o descarte de cada candidato estão na Seção 2.

Outros fatos:

- **Nenhum modelo de imagem tem tier gratuito** na OpenRouter (verificado nos 40 modelos com saída de imagem). Geração sem custo não existe.
- **A OpenRouter não desconta o preço do modelo.** Repassa a tabela do fornecedor e cobra ~5% na compra de crédito. A economia vem da escolha de modelo, não do roteador.
- **`openai_image.py` é chamado por subprocess** (`editor_server.py:974`, `lancamento_server.py:46`, slash commands). Trocar o motor por dentro não toca compositor, direção nem editor — confirma a aposta do spec de 21/07.

---

## Seção 1 — Princípio: roteador governado

O requisito tem duas metades que puxam em direções opostas: manter a consistência da marca **e** deixar o sistema escolher sozinho. Um roteador que escolhe modelo livremente destrói consistência, porque cada modelo tem estética própria.

> **Princípio: auto-ajuste no eixo de custo e recuperação. Nunca no eixo estético.**

| O sistema decide sozinho | O sistema nunca decide |
|---|---|
| Tier (rascunho vs. final), pelo contexto da chamada | Qual modelo gera a arte final da família |
| Resolução e proporção, por canal (`shared/formatos-canais.md`) | Paleta e tema |
| Suplente quando o modelo cai, recusa ou dá timeout | Conceito visual |
| Retry com prompt suavizado em recusa de conteúdo | Se pode gerar sem a trava de paleta |

Tudo que é estético mora no **contrato** (Seção 3) e só muda por decisão humana registrada.

---

## Seção 2 — Eixo de calibração: registro visual, por família

### O eixo não é segmento

A hipótese inicial era mapear segmento → modelo (clínica → X, tecnologia → Y). Ela não se sustenta: uma clínica pode querer fotografia humana acolhedora **ou** ilustração vetorial limpa — modelos opostos. Uma empresa de tecnologia, abstrato texturizado **ou** escritório fotorreal. O segmento não determina nada.

**O que determina é o registro visual**, que já está descrito em `marcas/<marca>/branding/identidade-visual.md`.

### Requisitos duros e o que o catálogo oferece

O sistema impõe quatro requisitos não-negociáveis ao modelo: **seed** (reprodutibilidade, Seção 4), **proporção retrato 4:5** (`shared/formatos-canais.md`), **múltiplas referências** (acervo, Seção 6) e **escada de resolução** (tiers).

Varredura dos 40 modelos com saída de imagem da OpenRouter (2026-07-24):

| Modelo | seed | 4:5 | refs | escada | Veredito |
|---|---|---|---|---|---|
| **`bytedance-seed/seedream-4.5`** | ✅ | ✅ | 14 | 1K/2K/4K | **único que atende os quatro** |
| `black-forest-labs/flux.2-*` | ✅ | ❌ | 8 | ❌ | Sem qualquer controle de proporção ou resolução — incompatível com `formatos-canais.md` |
| `google/gemini-3-pro-image` | ❌ | ✅ | 14 | ✅ | Sem seed |
| `openai/gpt-image-*` (via roteador) | ❌ | ❌ | 16 | ❌ | Perde o `size` que hoje entrega `1024x1536` |
| `krea/krea-2-*` | ✅ | ✅ | 1 | só 1K | Uma referência só |
| `recraft/*` | ❌ | ❌ | 1 | ❌ | Só serve para peça vetorial |
| `riverflow/*`, `grok`, `mai-image` | ❌ | — | — | — | Sem seed |

**Conclusão (INVALIDADA pelo bake-off — ver ERRATA):** `seedream-4.5` parecia o único qualificado *na tabela de capacidades*. O bake-off o reprovou na estética. A lição a guardar: **capacidade declarada não é qualificação** — nenhum modelo entra no roster sem gerar imagem com o prompt real.

### Roster resultante

| Registro visual | Modelo | Papel |
|---|---|---|
| `abstrato-material`, `fotografico-editorial` | `bytedance-seed/seedream-4.5` | Default de toda família |
| `ilustracao-vetor` | `recraft/recraft-v4.1-vector` | Exceção: peça vetorial (ícone, moldura). Retrato e seed não se aplicam. US$ 0,08 |
| `personagem-fotorreal` | `google/gemini-3-pro-image` | Exceção sob justificativa: quando consistência de rosto pesa mais que reprodutibilidade. **Sem seed** — registrar no perfil |
| — | `openai/gpt-image-1.5` | **Suplente**, sempre pelo backend OpenAI direto (via roteador perderia o `size`) |

### Honestidade sobre a calibração por marca

A calibração por registro visual está certa como **arquitetura**, mas hoje ela resolve para o mesmo modelo em quase todo caso — o catálogo só oferece um qualificado. O valor presente do contrato é o ritual de bake-off, o suplente declarado e estar pronto quando mais modelos ganharem seed + proporção. A discriminação real por família aparece hoje apenas nas duas exceções (vetor e personagem).

Registrar isso evita vender internamente uma capacidade que ainda não discrimina.

### A unidade é a família, não a marca

`shared/arquitetura-marca.md` exige fio condutor visual entre a mãe e os produtos ("uma plataforma smark"). Calibrar `smark`, `provider-max` e `elever-ai` separadamente permitiria três modelos diferentes e desfaria o parentesco.

> **Regra: um perfil por família de marcas.** A família compartilha modelo, registro e roster. Varia paleta, conceito e acento. Cada cliente novo de agência é uma família nova.

### Prateleira curada

O roster ativo tem **1 default e 2 exceções**, não os 40 do catálogo. Habilitar tudo multiplica modos de falha, depreciação e superfície de suporte sem ganho. Modelo fora do roster exige alteração explícita do contrato — nunca acontece por roteamento automático.

---

## Seção 3 — O contrato: `design-system/tokens/perfis-imagem.json`

Camada nova, declarativa, com um lugar só de verdade. Convive com `tokens.json` (mesma pasta, mesma natureza: configuração, não artefato de conteúdo — a regra 4 do `CLAUDE.md` trata de *entregáveis*, que continuam sendo markdown).

```json
{
  "_base": {
    "provider": "openrouter",
    "roster": [
      "bytedance-seed/seedream-4.5",
      "recraft/recraft-v4.1-vector",
      "google/gemini-3-pro-image"
    ],
    "tiers": {
      "rascunho": { "resolution": "1K" },
      "final":    { "resolution": "4K" }
    },
    "acervo": { "ativo": false, "max_refs": 20, "dir": null }
  },
  "familias": {
    "smark": {
      "marcas": ["smark", "provider-max", "elever-ai"],
      "registro": "abstrato-material",
      "modelo": null,
      "suplente": { "modelo": "gpt-image-1.5", "provider": "openai" },
      "calibrado_em": null,
      "seed_base": "smark",
      "acervo": { "ativo": false, "dir": "design-system/acervo/smark" }
    }
  }
}
```

**Semântica:**

- `modelo: null` → família não calibrada. O resolver usa o `suplente`, imprime aviso visível e marca `nao_calibrado: true` no ledger. Nunca falha silenciosamente.
- `calibrado_em` → data do bake-off que fixou o modelo. Alimenta a checagem de depreciação (Seção 7).
- `acervo.ativo: false` → o campo **nasce na fase 1** mas só é lido na fase 2. Isso evita migração de contrato depois.
- Famílias herdam `_base` e sobrescrevem só o que difere.

---

## Seção 4 — Tiers e seed determinística  
> **SUPERSEDIDA pela ERRATA no topo.** Não existem tiers e a seed não é garantia. Mantida como registro do raciocínio original.

### Por que rascunho só funciona no mesmo modelo

Rascunhar num modelo e finalizar em outro **não previne nada**: modelos diferentes têm latentes diferentes, então o rascunho não prevê o enquadramento do final. E o enquadramento é exatamente o que o `compositor.py` precisa saber — onde cai o espaço negativo pro texto entrar.

> **Rascunho e final são o mesmo modelo, mesma seed, resoluções diferentes.** É isso que torna o tier útil em vez de decorativo.

Isso descarta modelos sem seed do papel de default e é o principal motivo técnico do roster escolhido.

### Seed determinística

```
seed = int(sha256(f"{familia}:{slug}:{tipo}").hexdigest()[:8], 16) % 2**31
seed_efetiva = seed + reroll        # --reroll N, default 0
```

Consequências:

- O mesmo post sempre gera a mesma imagem. Regerar deixa de ser roleta.
- Variar vira ato explícito (`--reroll 1`), não acidente.
- Rascunho aprovado → final é a **mesma imagem** com mais resolução.

### O tier não é alavanca de custo — e isso é deliberado

`seedream-4.5` cobra **US$ 0,04 por imagem, plano**, em 1K ou 4K. Rascunho não economiza dinheiro; economiza **tempo de iteração** (1K gera bem mais rápido) e entrega **previsão fiel** do enquadramento. O tier é mantido por esses dois motivos, não por custo.

Toda a economia vem da troca de modelo, não do escalonamento.

**Ganho colateral:** o final pode sair em **4K pelo mesmo preço**. Hoje o fundo é gerado em 1024×1536; passar a gerar em 4K e reduzir na composição dá nitidez extra sem custo.

### Custo projetado

Base: 180 gerações/mês, perfil `seedream-4.5` a US$ 0,04 plano, + ~5% de taxa de crédito da OpenRouter.

| | Hoje | Proposto |
|---|---|---|
| Custo/mês | US$ 36,00 | **≈ US$ 7,60** |
| Resolução do fundo final | 1024×1536 | **4K** |
| Rascunho prevê o final | ❌ | ✅ |
| Regerar reproduz a arte | ❌ | ✅ |
| Custo por peça visível | ❌ | ✅ |

---

## Seção 5 — Telemetria de custo

A OpenRouter devolve `usage.cost` em dólar a cada chamada. Dois destinos:

1. **Bloco de metadados da nota** (`_sidecar.py`, que já grava modelo/qualidade/tamanho): acrescenta `modelo`, `seed`, `tier`, `custo_usd`, `suplente_usado`.
2. **Ledger append-only** em `design-system/custos/geracoes.jsonl`, uma linha por geração:

```json
{"data":"2026-07-24T14:03:11","familia":"smark","marca":"smark","slug":"...",
 "tipo":"manifesto","tier":"final","modelo":"bytedance-seed/seedream-4.5",
 "seed":183472911,"resolucao":"4K","custo_usd":0.04,"ok":true,
 "suplente_usado":false,"nao_calibrado":false}
```

O ledger é a base pra custo por marca, por campanha e por mês — o número que falta pra precificar o licenciamento pra agências.

---

## Seção 6 — O fosso: acervo de referências (fase 2, fundação na fase 1)

**Escolher bem o modelo não é fosso.** Qualquer concorrente chama o mesmo Seedream com a mesma chave. Acesso a modelo é commodity e tende a ficar mais commodity.

O que não se copia é o **acúmulo**:

| Camada | Existe hoje | Copiável |
|---|---|---|
| Direção estruturada (`_direcao.py`) | ✅ | Sim, com esforço |
| Trava de paleta (`_paleta.py`) | ✅ | Sim |
| Compositor determinístico | ✅ | Difícil — é onde mora o reconhecimento de marca |
| **Acervo de referências aprovadas** | ❌ | **Não** |

> **Cada arte aprovada vira referência da próxima.** Na peça 5, o modelo recebe 4 exemplos do que aquela marca é; na peça 50, recebe as melhores 20. O prompt deixa de ser descrição e passa a ser *"mais desse acervo"*.

Um concorrente com o mesmo modelo, o mesmo prompt e a mesma chave começa do zero — não tem as peças que **aquele cliente específico** aprovou, e não tem como ter. Isso conecta direto ao pilar 2 do spec de 21/07 ("custo de troca — o contexto de marca passa a morar no sistema").

**Curadoria é obrigatória.** Acervo que aceita tudo regride pra média. Só entra peça que (a) passou no `revisar.py` e (b) foi marcada explicitamente como peça-referência. Teto de 20, rotativo.

### Bake-off de calibração

Ritual de entrada de família. Mesma direção, mesma paleta, mesma seed, mesma resolução, nos 3 modelos do roster. Custo ≈ US$ 0,36 por família.

Critérios escritos, avaliados por pessoa:

1. Aderência à paleta ativa (sem cor fora da identidade)
2. Respeito ao espaço negativo esperado pelo compositor
3. Ausência de texto espúrio no fundo
4. Parentesco com as peças já aprovadas da família

O resultado grava `modelo` e `calibrado_em` no perfil.

---

## Seção 7 — Riscos e mitigações

| Risco | Mitigação |
|---|---|
| **Modelo depreciado** | Perfil guarda `modelo`, `suplente`, `calibrado_em`. Checagem mensal contra `/api/v1/images/models`; se sumiu, avisa e força recalibração. |
| **Drift silencioso** (provedor atualiza pesos) | Peça-âncora por família, regerada a cada 30 dias com a mesma seed. Diferença visível → alerta. Teste de regressão pra arte. |
| **Bake-off vira achismo** | Critérios fixos da Seção 6, mesmo prompt/seed/resolução nos 3 candidatos. |
| **Explosão de perfis com N clientes** | Herança de `_base`; cliente novo sobrescreve só o que difere. |
| **Acervo envenenado** | Porteiro duplo (`revisar.py` + marcação manual), teto de 20 refs, rotativo. |
| **Chave ausente / OpenRouter fora do ar** | Degradação graciosa: sem `OPENROUTER_API_KEY`, cai pro provider `openai` com aviso. O vault nunca para. |
| **Regressão nos chamadores existentes** | CLI atual preservada integralmente; `--model` continua sobrescrevendo tudo. |

---

## Seção 8 — Arquitetura e arquivos

### Componentes novos

| Arquivo | Responsabilidade | Depende de |
|---|---|---|
| `design-system/tokens/perfis-imagem.json` | Contrato declarativo | — |
| `scripts/_perfil.py` | Resolver: marca → família → modelo, tier, seed, resolução | o JSON acima |
| `scripts/_provedor.py` | Backend HTTP: OpenAI **ou** OpenRouter atrás de uma interface só | — |
| `scripts/calibrar.py` | Bake-off; grava `modelo` + `calibrado_em` | `_perfil`, `_provedor`, `_direcao` |

Cada um tem um propósito único e é testável isolado. `_provedor.py` é a única peça que sabe falar HTTP com fornecedor; `_perfil.py` é a única que sabe ler contrato; `openai_image.py` vira orquestrador fino.

### Componentes modificados

| Arquivo | Mudança |
|---|---|
| `scripts/openai_image.py` | Usa `_perfil` + `_provedor`. CLI atual preservada; ganha `--tier`, `--reroll`, `--provider` |
| `scripts/openai_edit.py` | Passa a usar `_provedor` (mesma chave, mesmo ledger) |
| `scripts/_sidecar.py` | Grava `modelo`, `seed`, `tier`, `custo_usd`, `suplente_usado` |
| `.env` | `OPENROUTER_API_KEY` |
| `CLAUDE.md` | Regras 7 e 8 refletindo perfil calibrado e tiers |

**Não muda:** `compositor.py`, `_direcao.py`, `_paleta.py`, `editor_server.py`, `estudio.py`, slash commands.

### Fluxo de dados

```
slash command / editor_server
        └─> openai_image.py  (CLI inalterada)
              ├─ _perfil.py    → família, modelo, tier, seed, resolução
              ├─ _direcao.py   → prompt estruturado        (inalterado)
              ├─ _paleta.py    → trava de cor              (inalterado)
              ├─ _provedor.py  → HTTP (openrouter | openai) → PNG + custo
              └─ _sidecar.py   → metadados + ledger
                    └─> compositor.py (texto/moldura/grade) (inalterado)
```

### Tratamento de erro

| Situação | Comportamento |
|---|---|
| Sem `OPENROUTER_API_KEY` | Fallback pro provider `openai`, aviso em stderr, `provider_fallback: true` no ledger |
| Modelo principal falha (HTTP/timeout/recusa) | Uma tentativa no `suplente`; marca `suplente_usado: true` |
| Recusa de conteúdo | Um retry com prompt suavizado antes de escalar pro suplente |
| Modelo fora do roster | Erro explícito, não gera |
| Família sem calibração | Gera com suplente + aviso visível + `nao_calibrado: true` |
| Falha total | Sai com código ≠ 0 e mensagem legível; nada é gravado no ledger como sucesso |

### Testes

- **`_perfil.py`** — unitário: herança de `_base`; determinismo da seed (mesma entrada → mesma seed); `--reroll` desloca; família ausente cai no default.
- **`_provedor.py`** — unitário com HTTP mockado: parse de `b64_json` e de `usage.cost`; caminho de fallback; erro de modelo fora do roster.
- **Integração** — uma geração real por provider, conferindo PNG salvo, bloco de metadados e linha no ledger.
- **Regressão** — o comando exato documentado em `shared/direcao-de-arte.md` roda sem argumento novo e produz imagem.
- **Reprodutibilidade** — duas gerações com a mesma seed no mesmo modelo, comparadas visualmente no bake-off.

---

## Seção 9 — Escopo por fase

| Fase | Entrega |
|---|---|
| **1 (esta)** | Contrato de perfis (com `acervo` já previsto) · `_provedor` OpenRouter · tiers · seed determinística · telemetria de custo · suplente automático · bake-off e calibração da família smark |
| **2** | Acervo de referências: marcação de peça-referência, alimentação em `input_references`, curadoria no Super Editor |
| **3** | Peça-âncora e detecção de drift · recalibração assistida · checagem mensal de depreciação |

---

## Seção 10 — Critérios de aceite da fase 1

1. `python3 scripts/openai_image.py --direcao --marca smark --tipo manifesto --tema claro --out /tmp/t.png` roda **sem argumento novo** e produz PNG.
2. Duas execuções do mesmo comando registram a **mesma seed**; `--reroll 1` registra seed diferente.
3. O bloco de metadados e o ledger trazem `modelo`, `seed`, `tier` e `custo_usd`.
4. Com `OPENROUTER_API_KEY` ausente, o comando **funciona** via OpenAI e avisa.
5. Modelo fora do roster falha com mensagem explícita.
6. Queda do modelo principal aciona o suplente e marca `suplente_usado: true`.
7. `calibrar.py` produz as 3 variantes lado a lado e, escolhida uma, grava `modelo` + `calibrado_em` no perfil.
8. `compositor.py` consome o fundo gerado sem nenhuma alteração.

---

## Pendências

- **`OPENROUTER_API_KEY`** — ausente. Bloqueia o bake-off (critério 7) e o teste de integração no provider novo. Os demais critérios são testáveis sem ela graças à degradação graciosa.
- **Estética do `seedream-4.5` com a direção da smark** — a escolha técnica está determinada pelos requisitos duros (Seção 2), mas ninguém viu ainda uma peça desse modelo com o prompt do `_direcao.py` e a paleta ativa. O bake-off decide se ele entra como default ou se a família precisa de exceção. Custo do teste: ~US$ 0,36.
- **Proporção exata do retrato** — `seedream-4.5` oferece `4:5` e `3:4` via `aspect_ratio`, não pixels literais. Conferir se o recorte resultante alimenta o `compositor.py` sem ajuste; se não, o `_provedor.py` normaliza no pós-processo.
- **`gpt-image` como suplente** — precisa ficar no backend OpenAI direto. Via OpenRouter o parâmetro de tamanho não é exposto e o suplente perderia o retrato, justamente no momento de falha. Validar no critério 6.
- **Modelos avaliados e descartados** — `flux.2-*` (sem controle de proporção), `riverflow`, `grok`, `mai-image`, `krea` (sem seed ou uma referência só). Registrado para não serem reavaliados sem motivo novo.
