# Qualidade fiel com multi-marca / cliente externo

**Objetivo:** abrir o sistema para outras marcas **sem** virar “gerador genérico de IA”.  
A smark/Provider Max/Elever devem continuar no mesmo nível de craft; o cliente novo sobe ao **mesmo padrão**, não puxa o padrão para baixo.

Este documento é **regra de implementação** (ainda não é código). Qualquer PR de multi-marca deve respeitar.

---

## 1. O que “qualidade fiel” significa aqui

| Camada | Fiel = |
|--------|--------|
| **Tipografia** | Texto **sempre** no compositor (HTML/CSS 2×), nunca tipografado pela IA no fundo |
| **Fundo** | Direção de arte estruturada (conceito + composição + cor), não prompt de uma linha |
| **Cor** | Paleta da **marca ativa** (estrita), sem matizes aleatórios |
| **Logo / selo** | Asset da marca, posição e regras de uso, não inventado pela IA |
| **Voz** | Brand-voice + gate de jargão/promessa (revisar) |
| **Publicável** | Só peça que passou nos gates; rascunho Seedream **não** é entrega final |
| **Custo** | Rastreável por marca (ledger) |
| **Isolamento** | Arte/contexto de um cliente **não** vaza no de outro |

---

## 2. Invariantes (não negociar)

1. **Pipeline de 2 camadas permanece**  
   Fundo IA → compositor. Proibido “uma API, texto na imagem” como caminho de produção.

2. **Seedream só como rascunho**  
   Prompt **curto** (`construir_rascunho`). Entrega ao cliente = **final** (Gemini 4K) ou rascunho que passou gate + promoção explícita a final.

3. **Gate de texto em rascunho**  
   Poluição de briefing na arte = não publicável.

4. **Marca sem branding completo ≠ marca pronta**  
   Não gerar lote “oficial” até existir no mínimo:
   - slug  
   - logo (ou wordmark)  
   - paleta (primária + fundo claro/escuro)  
   - voz (1 parágrafo + proibidos)  
   - 1 peça de referência aprovada (olho humano)

5. **Trocar cor ≠ trocar só um hex no CSS**  
   Precisa alimentar: tokens/compositor + direção de arte (cor estrita) + UI do editor.

6. **Família de motor de imagem**  
   Cliente externo herda o **mesmo roster/calibração** (Seedream rascunho + Gemini final), salvo bake-off que prove outro modelo **melhor** naquela marca. Não “modelo barato diferente por cliente” sem teste.

7. **smark / provider-max / elever-ai não regredem**  
   Testes de regressão: gerar 1 peça por marca canônica após qualquer mudança de multi-marca.

---

## 3. Checklist de onboarding de marca (qualidade)

Antes da **primeira entrega paga**:

| # | Item | Como validar |
|---|------|----------------|
| 1 | Pasta `marcas/<slug>/branding/` mínima | Arquivos existem |
| 2 | Logo nítido (PNG/SVG) | Visual no export |
| 3 | Paleta (2–4 cores + claro/escuro) | Sem cor “aleatória” no fundo |
| 4 | Voz + proibidos | `revisar.py` não explode de ⚠️ |
| 5 | 3 peças-piloto aprovadas pelo cliente | Olho humano |
| 6 | 1 fundo final Gemini (não só Seedream) | `tier=final` |
| 7 | Ledger com `marca=<slug>` | Custo rastreável |
| 8 | (Opcional) 2 peças no acervo ★ | Consistência da 4ª peça em diante |

**Bloqueio de produção em lote** se 1–4 falharem.

---

## 4. O que a implementação multi-marca **deve** fazer

| Deve | Não deve |
|------|----------|
| Lista de marcas dinâmica (filesystem ou registry) | Hardcode só smark/PM/Elever |
| Isolar `arte/` e acervo por slug | Misturar refs de clientes |
| Carregar paleta/logo por marca no compositor | Manter roxo smark em todo mundo |
| Manter defaults de **qualidade** (4K final, direção, gate) | Relaxar qualidade para “baratear cliente” |
| Testes: resolver marca nova + regressão 3 canônicas | Só testar marca nova |
| Fallback: marca sem paleta → **erro explícito**, não smark silencioso | `safe_marca` forçar smark sem aviso |

---

## 5. Regressão de qualidade (a rodar após cada mudança)

```bash
# suíte
python3 -m pytest tests/ -q

# (quando existir) smoke de marca canônica
# python3 scripts/openai_image.py --marca smark --tier final --direcao ... --out /tmp/reg-smark.png
# python3 scripts/openai_image.py --marca provider-max --tier final ...
# python3 scripts/openai_image.py --marca elever-ai --tier final ...
```

Critérios de aceite visual (olho):

- [ ] Sem texto/hex/“85mm” no fundo  
- [ ] Terço inferior utilizável para headline  
- [ ] Cor da marca dominante (não paleta errada)  
- [ ] Logo legível, não distorcido  
- [ ] Tipografia do compositor nítida  

---

## 6. Relação com o backup

Se multi-marca degradar o craft ou quebrar o vault:

```bash
git fetch origin
git checkout main
git reset --hard backup/pre-multimarca-2026-07-27
# ver BACKUP-PRE-MULTIMARCA.md
```

---

## 7. Resumo

**Backup** protege o sistema inteiro.  
**Estas regras** protegem a **qualidade** quando o sistema aceitar outras marcas.

Implementação multi-marca só deve começar com:

1. Tag/branch de backup ativa (feita)  
2. Este checklist como critério de PR  
3. Autorização explícita do Sprint 1 (marcas dinâmicas + nova-marca + paleta/logo no compositor)
