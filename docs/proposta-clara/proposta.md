---
tipo: proposta
escopo: ecossistema (3 marcas)
origem: "Brief Reposicionamento EleverAI — Pedro Muschitz, 18/06/2026"
status: aplicado
criado: 2026-06-22
aplicado: 2026-06-23
---

# Proposta — Ecossistema mais claro (menos dark)

> **✅ APLICADO em 2026-06-23.** Claro virou o tema-padrão do sistema; APEX redesenhado (v3); paletas, comandos e docs ajustados.
> Origem: brief de reposicionamento do EleverAI (Pedro Muschitz).
>
> **Decisões resolvidas:** (1) claro default também no social — sim; (2) base clara mantida em `#F4F2FB` (off-white lavanda, igual ao render aprovado) — pra trocar por branco puro `#FFFFFF`, é 1 linha em `tokens.json` → `tema_claro.base`; (3) aplicado nas **3 marcas**.

## 1. O que o brief muda

| Brief diz | Hoje | Vira |
|---|---|---|
| Nunca prometer venda/faturamento | Elever já em "qualificação" | Reforçar: **substituição de função (SDR) + custo**, nunca "vendas" |
| Largar jargão "agente de IA" | "funcionário de IA" | No público: **"vendedor/pré-vendedor no WhatsApp"** |
| Criança de 7 anos entende | Headlines simples | Vira **trava de qualidade** (como palavras-proibidas) |
| Troca de custo já existente | Falamos em ganho | "**pelo preço de um estagiário**", "sem contratar mais gente" |
| Fundo branco padrão; dark é datado | **Escuro é default** (60/40) | **Inverter: claro vira o default público** |
| Uma proposta de valor | Elever mistura assessoria/treino | Vitrine = **só o produto**; Smark-assessoria vira endosso |

## 2. Proposta de valor (modelo "uma frase")

- **Elever AI:** *Um pré-vendedor que trabalha 24h, 7 dias por semana — pelo preço de um estagiário. Atende todo lead na hora, no WhatsApp, e entrega ele pronto pra fechar.*
- **Provider Max:** *Renova, recupera e expande sua base no automático — recupera contrato vencido e faz upgrade de planos sem precisar contratar mais gente*
- **Smark (mãe):** *IA que pluga no que você já tem — sem trocar seu sistema, seu time ou seus processos.* (assessoria/treino saem da vitrine do produto → conversa direta.)

## 3. Paleta proposta (claro = default)

```yaml
# Mantém o roxo das 3 marcas; inverte o tema-padrão pra claro e usa branco real na base.
claro:                      # DEFAULT da vitrine pública
  base:       "#FFFFFF"     # branco puro (brief 5.1)
  superficie: "#F4F2FB"     # off-white lavanda p/ cards/seções
  texto:      "#100D1C"
  acento:     "#8B3CF7"     # roxo (mesmo das 3 marcas)
  apoio:      "#6B6878"
escuro:                     # RESERVADO: UI do produto, bastidor "tech", minoria do feed
  base:    "#0B0B0B"
  texto:   "#FFFFFF"
  acento:  "#A472FF"
```

Mix do feed inverte: ~70% claro / 30% escuro. Diferença entre marcas segue no **símbolo**, não na cor.

## 4. Teste A/B — claro (A) vs escuro (B)

### Elever AI
| A — claro (proposta) | B — escuro (atual) |
|---|---|
| ![[01-elever-claro.png]] | ![[01-elever-escuro.png]] |

### Provider Max
| A — claro (proposta) | B — escuro (atual) |
|---|---|
| ![[02-provider-max-claro.png]] | ![[02-provider-max-escuro.png]] |

### Smark
| A — claro (proposta) | B — escuro (atual) |
|---|---|
| ![[03-smark-claro.png]] | ![[03-smark-escuro.png]] |

## 5. Headlines padrão (regra criança-7-anos)

**Elever AI**
- Um vendedor no WhatsApp que **nunca dorme.**
- Pré-vendedor 24/7 pelo preço de um **estagiário.**
- Pare de perder cliente por **falta de resposta.**
- 10x mais leads qualificados, **sem contratar.**

**Provider Max**
- Renova sua base no **automático.**
- Recupera contrato vencido **sozinho.**
- Sua receita já existe — só está **parada.**

**Smark**
- IA que pluga no que você **já tem.**
- Você não precisa trocar o que **funciona.**
- IA sem método não **escala.**

## 6. Adaptações (se aprovado — nada feito ainda)

1. `identidade-visual.md` (3 marcas): bloco `claro` com base branca; default → claro.
2. `direcao-de-arte.md` + `compositor.py`: aliviar/desligar a grade (duotone+vinheta+grão) no claro — é a textura "datada" que o brief critica.
3. Elever `posicionamento`/`brand-voice`/`do-and-dont`: reframe SDR+custo; proibir prometer venda; trocar "agente de IA" por "vendedor".
4. `shared/voz-grupo.md`: jargão "agente/automação/sistema" fora da 1ª impressão + regra criança-7-anos.
5. `arquitetura-marca.md`: regra "uma proposta de valor na vitrine".
6. `formatos-canais.md`/`padroes-instagram.md`: tema claro como default.

## 7. Decisões pendentes
1. Claro default no social também, ou só site/apresentação? (recomendo: social também)
2. Branco puro `#FFFFFF` ou off-white `#F4F2FB` na base? (recomendo: branco base + lavanda nos cards)
3. Aplicar nas 3 marcas agora, ou só Elever primeiro?
</content>
</invoke>
