---
tipo: design
tema: white studio — modelo de negócio e precificação da plataforma white-label para agências
data: 2026-07-26
status: valores fechados — apresentação comercial pendente
autor: Andreik + Claude
camada: negócio (modelo econômico)
depende-de: docs/superpowers/specs/2026-07-21-distribuicao-plataforma-agencias-design.md
cambio-de-referencia: US$ 1 = R$ 6,00
---

# white studio — modelo de negócio e precificação

Fecha a lacuna deixada em aberto pelo design de distribuição de 2026-07-21, que definiu
o canal (agências), a entrega (white-label) e a estrutura de receita, mas deixou os
números para "calibração de campo".

**Nome do produto: white studio.** Substitui o nome de trabalho "smark Studio" usado na
apresentação de 21/07. A plataforma é marca própria, separada da vitrine "assessoria" do
site canônico.

---

## Seção 1 — A oferta

```
ENTRADA · R$ 2.000 em 2×
  formação completa, metodologia, plataforma com a marca do parceiro,
  ativação dos 2 primeiros clientes

MENSALIDADE · R$ 630
  tecnologia rodando, 2 clientes-marca inclusos

CLIENTE ADICIONAL · 30% da referência de R$ 547 = R$ 164,10
  o parceiro cobra do cliente dele o quanto quiser; o excedente é dele

REAJUSTE · todo mês de fevereiro
  IPCA acumulado + variações tributárias, aplicado sobre a mensalidade
  E sobre o valor de referência de R$ 547
```

**Frase de venda:** *"Dois mil pra entrar, 630 por mês com dois clientes, e 30% de cada
cliente novo. O que você cobrar acima da tabela é seu."*

**Os R$ 547 são régua interna, não o preço do parceiro.** O cálculo é sempre sobre 547,
independentemente do que ele cobra. Isso elimina auditoria: a smark nunca precisa saber o
faturamento dele. Na prática o valor é fixo (R$ 164,10) e o percentual é a forma de
explicá-lo — e de reajustá-lo junto com a referência.

**Reajustar a referência (e não só a mensalidade) é o que protege a margem no longo prazo:**
a base sobe com o mercado e os 30% acompanham sem renegociação.

### Natureza jurídica — decisão firmada

Contrato de **licença de uso de software + prestação de serviço de treinamento**.
Não é franquia. A palavra "franquia" não aparece em nenhum material.

Motivo: a Lei 13.966/2019 exige Circular de Oferta de Franquia entregue 10 dias antes da
assinatura ou de qualquer pagamento. Descumprir permite ao parceiro anular o contrato e
exigir devolução corrigida de tudo que pagou. Como o modelo **não cede marca** (o
white-label entrega a marca do parceiro), estruturar como licença mantém a relação em
direito civil comum — sem COF e sem obrigação contínua. Montar franquia formal custaria
R$ 15–40k em jurídico, incompatível com um alvo de 15–30 parceiros.

*Validar com advogado antes do primeiro contrato assinado.*

---

## Seção 2 — Custo de produção (COGS)

Fonte: `design-system/custos/geracoes.jsonl` + `design-system/tokens/perfis-imagem.json`.
Pipeline de dois tiers (Era C), implementado e verificado em `scripts/_perfil.py`.

| Tier | Modelo | US$ | R$ (×6) | Publicável |
|---|---|---|---|---|
| rascunho | Seedream 4.5 | 0,04 | R$ 0,24 | não |
| final | Gemini 3 Pro Image 4K | 0,24 | R$ 1,44 | sim |

| Fluxo | US$/post | R$/post |
|---|---|---|
| 1 rascunho + 1 final | 0,28 | R$ 1,68 |
| **2 rascunhos + 1 final (usado na modelagem)** | **0,32** | **R$ 1,92** |
| 3 finais (sem disciplina) | 0,72 | R$ 4,32 |

Modelamos com R$ 1,92 — não com o melhor caso — porque o histórico do vault mostra
1,8 gerações por post entregue, ou seja, o operador itera na prática.

**O carrossel usa um fundo só.** O custo de IA é por post, não por arte: uma peça de
7 slides consome uma geração. Confirmado na estrutura das pastas de arte (`bg.png` único).

---

## Seção 3 — Unit economics

```
UM CLIENTE ADICIONAL, POR MÊS (20 posts)
  entra ....... R$ 164,10
  sai ......... R$  38,40
  ────────────────────────
  sobra ....... R$ 125,70   ·  77%
```

Margem por parceiro, mês cheio (20 posts por cliente):

| Clientes | Receita | COGS IA | Margem |
|---|---|---|---|
| 2 (base) | R$ 630,00 | R$ 76,80 | 88% |
| 5 | R$ 1.122,30 | R$ 192,00 | 83% |
| 8 | R$ 1.614,60 | R$ 307,20 | 81% |
| 15 | R$ 2.763,30 | R$ 576,00 | 79% |

A margem estabiliza em ~80% e não se deteriora com o crescimento do parceiro — o furo
que existia na versão de 10% do royalty.

---

## Seção 4 — P&L e ponto de equilíbrio

Premissas: 20 parceiros, 8 clientes cada, 20 posts por cliente/mês, onboarding
produtizado, hora interna a R$ 150, estrutura fixa de R$ 12.000/mês.

```
RECEITA
  base (20 × 630) ........................  R$ 12.600
  clientes extras (20 × 6 × 164,10) ......  R$ 19.692
  entradas (2 novos/mês) .................  R$  4.000
                                            ──────────
                                            R$ 36.292

CUSTOS
  IA de imagem (3.200 posts × 1,92) ......  R$  6.144
  copy/LLM ...............................  R$  1.152
  suporte (0,5h × 20 × 150) ..............  R$  1.500
  onboarding 2 novos (2h cada) ...........  R$    600
  infra ..................................  R$  1.500
  estrutura fixa .........................  R$ 12.000
                                            ──────────
                                            R$ 22.896

LUCRO ....................................  R$ 13.396  ·  37%
```

Em 30 parceiros × 10 clientes: receita R$ 64.284, lucro **R$ 30.454 (47%)**.

| Métrica | Valor |
|---|---|
| Break-even (parceiro médio de 8 clientes) | **12 parceiros** |
| Break-even (parceiro médio de 5 clientes) | 17 parceiros |
| Margem de contribuição por parceiro | R$ 1.174,80/mês |
| Payback do CAC | imediato — a entrada cobre aquisição + onboarding |
| LTV (churn de 24 meses) | R$ 28.195 |
| LTV / CAC | 10× |

**Composição do custo:** o humano (suporte + onboarding) só deixa de dominar o COGS
porque o onboarding é produtizado. Sem isso, os mesmos 20 parceiros custam R$ 7.500/mês
a mais e o lucro cai para R$ 5.896 (16%) — e a operação não passa de 20 parceiros sem
contratar.

---

## Seção 5 — Travas operacionais

**1. Qualificação: mínimo de 2 clientes.**
Parceiro com 1 cliente fatura R$ 547 e paga R$ 630 — perde dinheiro e cancela. Só entra
quem tem 2 clientes ativos ou pipeline concreto. É a regra de venda mais importante do
modelo.

**2. Rascunho é o default do Estúdio.**
O tier final deve exigir um clique consciente ("aprovar para publicação"). Se o parceiro
iterar no final, o COGS mensal vai de R$ 6.144 para R$ 13.824 — **R$ 92.160/ano decididos
por um valor-padrão de interface.**

**3. Copy/LLM precisa entrar no ledger.**
Hoje o custo de geração de texto no Estúdio não é medido. É o único componente de COGS
invisível, e escala por parceiro.

**4. Gate anti-texto depende de tesseract instalado.**
Sem ele, rascunho poluído pode ser promovido. Em operação multi-parceiro isso vira dano
de marca no cliente final do parceiro.

---

## Seção 6 — ROI do parceiro (argumentos de venda)

**Gancho principal:** *"Seu limite hoje não é falta de cliente. É quem faz a arte."*

### Argumento 1 — cada cliente novo entra quase inteiro no bolso dele

```
  recebe ...... R$ 547
  paga ........ R$ 164
  ─────────────────────
  fica com .... R$ 383   ·  70%
```

Dez clientes a mais = R$ 3.830/mês de lucro novo, sem contratar.

### Argumento 2 — ele para de pagar por arte

| Perfil | Custo hoje | Com o white studio | Economia/mês |
|---|---|---|---|
| 3 clientes (freelancer a R$ 80/post) | R$ 4.800 | R$ 794 | R$ 4.006 |
| 8 clientes (designer CLT + freela) | R$ 6.250 | R$ 1.615 | R$ 4.635 |
| 15 clientes (2 designers) | R$ 8.500 | R$ 2.763 | R$ 5.737 |

Payback da entrada: **menos de 15 dias** em qualquer perfil.

### Argumento 3 — quanto maior ele fica, melhor fica

```
  2 clientes ......... 42%
  3 clientes ......... 52%
  5 clientes ......... 59%
  8 clientes ......... 63%
 15 clientes ......... 66%
```

Raro e vendável: quase todo custo de agência piora com escala. Aqui melhora.

### Objeções e respostas

| Objeção | Resposta |
|---|---|
| "Já uso Canva" | "Canva te dá a tela em branco. Quem faz a arte continua sendo você." |
| "Vou perder qualidade" | "O texto é vetor nítido, não imagem de IA. Compare lado a lado." |
| "E se eu quiser sair?" | "Sai quando quiser. Sem multa, sem fidelidade." |
| "Meu cliente vai saber que é IA?" | "É a sua marca do começo ao fim. A gente não aparece." |
| "É caro" | "R$ 164 por cliente. Um post de freelancer custa R$ 80. Você faz 20." |
| "Não sei operar" | "Formação inclusa, e ativamos seus 2 primeiros clientes com você." |

**Regra de comunicação:** o ROI vendido é redução de custo e ganho de capacidade — ambos
verificáveis. Nunca prometer faturamento ou resultado de vendas do cliente final.

---

## Riscos conhecidos

1. **Amostra de custo pequena.** O ledger tem 7 linhas e o tier rascunho tem n=1. Gerar
   50–100 amostras por tier (custo ~US$ 15) antes de tratar a tabela como definitiva.
2. **Reajuste por IPCA não cobre câmbio.** Testado: a R$ 8,00/US$ a margem do cliente
   extra cai de 77% para 69% — absorvível. Vira problema apenas acima de R$ 10.
3. **Concentração.** Com 20 parceiros, perder 3 = −15% da receita. Sem fidelidade
   contratual (decisão consciente), a receita é volátil.
4. **Transferência de método.** O treinamento entrega a parte replicável do negócio; o
   que retém é a tecnologia. Reforça a prioridade do moat de aprendizado por marca.
5. **Dependência de fornecedor.** Produção depende de crédito no OpenRouter; o suplente
   OpenAI é vulnerável a hard limit de billing.

## Não-objetivos

- Não define a arquitetura do motor multi-agência (Fase 0, spec técnico separado).
- Não altera o site canônico nem a vitrine "assessoria".
- Não cria automação de venda ou CRM.
- Não define território ou exclusividade por região.

## Pontos em aberto

- Registro de marca e domínio para "white studio" (INPI / disponibilidade).
- Amostragem de custo por tier antes de congelar a tabela pública.
- Redação do contrato de licença + serviço (revisão jurídica).

## Próximo passo

Reescrever a apresentação comercial (`docs/estudo-agencias/studio.html`) sobre este
modelo: preços novos, calculadora de ROI com a fórmula nova, seção da curva de margem do
parceiro e seção de transparência do reajuste. A apresentação é uma renderização deste
spec, não uma segunda fonte de verdade.
