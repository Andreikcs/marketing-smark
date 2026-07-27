# white studio — modelo de negócio · VERSÃO FINAL

**Documento de referência.** Consolida a oferta, os números, a economia interna e os
argumentos de venda da plataforma white-label para agências.

| | |
|---|---|
| **Produto** | white studio (antes: "smark Studio", nome de trabalho da v1) |
| **Data de fechamento dos valores** | 2026-07-26 |
| **Câmbio de modelagem** | US$ 1 = R$ 6,00 |
| **Natureza jurídica** | licença de software + prestação de serviço — **não é franquia** |
| **Spec de design** | `docs/superpowers/specs/2026-07-26-white-studio-modelo-negocio-design.md` |
| **Origem estratégica** | `docs/superpowers/specs/2026-07-21-distribuicao-plataforma-agencias-design.md` |
| **Apresentação comercial** | `white-studio.html` (v2 · atual) · `studio.html` (v1 · histórico) |

---

## 1. A oferta

```
ENTRADA · R$ 2.000 em 2× de R$ 1.000
  formação completa na metodologia
  plataforma configurada com a marca do parceiro
  ativação dos 2 primeiros clientes junto com ele

MENSALIDADE · R$ 630/mês
  tecnologia rodando e atualizada
  2 clientes-marca inclusos
  artes à vontade, sem limite por peça
  sem fidelidade, sem multa

CLIENTE ADICIONAL · 30% de R$ 547 = R$ 164,10/mês
  do 3º cliente em diante
  o parceiro cobra do cliente dele o quanto quiser

REAJUSTE · todo mês de fevereiro
  IPCA acumulado + variações tributárias
  incide sobre a mensalidade E sobre a referência de R$ 547
```

**Frase de venda:** *"Dois mil pra entrar, 630 por mês com dois clientes, e 30% de cada
cliente novo. O que você cobrar acima da tabela é seu."*

### A régua dos R$ 547

Os R$ 547 são **referência interna de cálculo, não o preço do parceiro.** O valor cobrado
é sempre 30% sobre 547 — independentemente do que ele cobra do cliente final.

Consequências, todas intencionais:

- **Não existe auditoria.** Nunca precisamos saber o faturamento do parceiro.
- **Não existe negociação por conta.** O valor é o mesmo para todos.
- **O parceiro é premiado por vender bem.** Se cobra R$ 1.200, continua pagando R$ 164,10.
- **O reajuste da referência protege a margem.** Subindo os 547 em fevereiro, os 30%
  acompanham o mercado sem renegociar contrato.

### Por que não é franquia

A Lei 13.966/2019 exige Circular de Oferta de Franquia entregue 10 dias antes da assinatura
ou de qualquer pagamento. Descumprir permite ao parceiro anular o contrato e exigir
devolução corrigida de tudo que pagou.

Como o modelo **não cede marca** — o white-label entrega a marca do parceiro —, a relação
é estruturada como licença de uso de software somada a serviço de treinamento, o que a
mantém em direito civil comum. A palavra "franquia" não aparece em nenhum material.

> Validar a minuta com advogado antes do primeiro contrato assinado.

---

## 2. Custo de produção

Fonte: `design-system/custos/geracoes.jsonl` · contrato em
`design-system/tokens/perfis-imagem.json` · pipeline de dois tiers verificado em
`scripts/_perfil.py`.

| Tier | Modelo | US$ | R$ (×6) | Publicável |
|---|---|---|---|---|
| rascunho | Seedream 4.5 | 0,04 | R$ 0,24 | não |
| final | Gemini 3 Pro Image 4K | 0,24 | R$ 1,44 | sim |

| Fluxo | US$/post | R$/post |
|---|---|---|
| 1 rascunho + 1 final | 0,28 | R$ 1,68 |
| **2 rascunhos + 1 final — usado na modelagem** | **0,32** | **R$ 1,92** |
| 3 finais (sem disciplina de tier) | 0,72 | R$ 4,32 |

Duas notas que sustentam esses números:

- **O carrossel consome um fundo só.** Uma peça de 7 slides gera uma imagem de IA; o custo
  é por post, não por arte. Confirmado na estrutura das pastas (`bg.png` único).
- **Modelamos o caso realista, não o melhor caso.** O histórico do vault mostra 1,8
  gerações por post entregue — o operador itera na prática.

---

## 3. Economia por parceiro

### Cliente adicional

```
  entra ....... R$ 164,10
  sai ......... R$  38,40   (20 posts × R$ 1,92)
  ────────────────────────
  sobra ....... R$ 125,70   ·  77%
```

### Mês cheio, por tamanho do parceiro

| Clientes | Receita | COGS IA | Margem |
|---|---|---|---|
| 2 (só a base) | R$ 630,00 | R$ 76,80 | 88% |
| 5 | R$ 1.122,30 | R$ 192,00 | 83% |
| 8 | R$ 1.614,60 | R$ 307,20 | 81% |
| 15 | R$ 2.763,30 | R$ 576,00 | 79% |

A margem **estabiliza em ~80%** e não se deteriora conforme o parceiro cresce — problema
que existia na versão de 10% do royalty, descartada.

---

## 4. P&L e ponto de equilíbrio

Premissas: 20 parceiros · 8 clientes cada · 20 posts por cliente/mês · onboarding
produtizado · hora interna a R$ 150 · estrutura fixa de R$ 12.000/mês.

```
RECEITA
  base (20 × 630) ........................  R$ 12.600
  clientes extras (20 × 6 × 164,10) ......  R$ 19.692
  entradas (2 novos por mês) .............  R$  4.000
                                            ──────────
                                            R$ 36.292

CUSTOS
  IA de imagem (3.200 posts × 1,92) ......  R$  6.144
  copy / LLM .............................  R$  1.152
  suporte (0,5h × 20 × 150) ..............  R$  1.500
  onboarding de 2 novos (2h cada) ........  R$    600
  infra ..................................  R$  1.500
  estrutura fixa .........................  R$ 12.000
                                            ──────────
                                            R$ 22.896

LUCRO ....................................  R$ 13.396  ·  37%
```

### Cenários

| Parceiros | Clientes/parceiro | Receita | Lucro | Margem |
|---|---|---|---|---|
| 10 | 6 | R$ 16.864 | −R$ 722 | prejuízo |
| **20** | **8** | **R$ 36.292** | **R$ 13.396** | **37%** |
| 30 | 10 | R$ 64.284 | R$ 30.454 | 47% |

### Indicadores

| Métrica | Valor |
|---|---|
| Break-even (parceiro médio de 8 clientes) | **12 parceiros** |
| Break-even (parceiro médio de 5 clientes) | 17 parceiros |
| Margem de contribuição por parceiro | R$ 1.174,80/mês |
| Payback do CAC | imediato — a entrada cobre aquisição + onboarding |
| LTV (churn de 24 meses) | R$ 28.195 |
| LTV / CAC | 10× (saudável é acima de 3×) |

**O onboarding produtizado não é opcional.** Sem ele, os mesmos 20 parceiros custam
R$ 7.500/mês a mais e o lucro cai para R$ 5.896 (16%) — e a operação não passa de 20
parceiros sem contratar.

---

## 5. Travas operacionais

**1. Mínimo de 2 clientes para vender.**
Parceiro com 1 cliente fatura R$ 547 e paga R$ 630 — perde dinheiro e cancela no mês 2.
Só entra quem tem 2 clientes ativos ou pipeline concreto. É a regra de qualificação mais
importante do modelo.

**2. Rascunho é o default do Estúdio.**
O tier final precisa exigir um clique consciente ("aprovar para publicação"). Se o parceiro
iterar no final, o COGS mensal vai de R$ 6.144 para R$ 13.824 — **R$ 92.160/ano decididos
por um valor-padrão de interface.**

**3. Copy/LLM precisa entrar no ledger.**
Hoje o custo de geração de texto no Estúdio não é medido. É o único componente de COGS
invisível, e escala por parceiro.

**4. Gate anti-texto depende de tesseract instalado.**
Sem ele, rascunho poluído pode ser promovido — vira dano de marca no cliente final do
parceiro.

---

## 6. Argumentos de venda

**Gancho principal:** *"Seu limite hoje não é falta de cliente. É quem faz a arte."*

### Argumento 1 — cada cliente novo entra quase inteiro no bolso dele

```
  recebe ...... R$ 547
  paga ........ R$ 164
  ─────────────────────
  fica com .... R$ 383   ·  70%
```

Dez clientes a mais = **R$ 3.830/mês de lucro novo, sem contratar ninguém.**

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

Raro e vendável: quase todo custo de agência piora com escala (mais gente, mais gestão).
Aqui melhora. É o argumento que fecha o sócio cético. Agência tradicional trabalha com
20% a 30% de margem.

### Objeções e respostas

| Objeção | Resposta |
|---|---|
| "Já uso Canva" | "Canva te dá a tela em branco. Quem faz a arte continua sendo você." |
| "Vou perder qualidade" | "O texto é camada nítida, não imagem de IA. Compare lado a lado." |
| "E se eu quiser sair?" | "Sai quando quiser. Sem multa, sem fidelidade." |
| "Meu cliente vai saber que é IA?" | "É a sua marca do começo ao fim. A gente não aparece." |
| "É caro" | "R$ 164 por cliente. Um post de freelancer custa R$ 80. Você faz 20." |
| "Não sei operar" | "Formação inclusa, e ativamos seus 2 primeiros clientes com você." |
| "E se eu cobrar mais de R$ 547?" | "Deve cobrar. Os 30% incidem sempre sobre 547, não sobre o seu preço." |

### Regra de comunicação

O ROI vendido é **redução de custo e ganho de capacidade** — ambos verificáveis.
**Nunca prometer faturamento ou resultado de vendas do cliente final.**

---

## 7. Fórmula da calculadora de ROI

Usada na apresentação (`white-studio.html`):

```
posts          = clientes × posts_por_cliente
custo_hoje     = posts × preço_por_arte
custo_studio   = 630 + máx(0, clientes − 2) × 164,10
economia       = custo_hoje − custo_studio
payback_dias   = 2000 ÷ economia × 30
lucro_p/cliente_novo = 547 − 164,10 = 382,90
```

Faixas dos controles: clientes 2–25 · posts por cliente 4–40 · preço por arte R$ 25–150.

---

## 8. Riscos conhecidos

1. **Amostra de custo pequena.** O ledger tem 7 linhas e o tier rascunho tem n=1. Gerar
   50–100 amostras por tier (custo ~US$ 15) antes de tratar a tabela como definitiva.
   *Decisão em 2026-07-26: avaliar depois.*
2. **IPCA não cobre câmbio.** Testado: a R$ 8,00/US$ a margem do cliente extra cai de 77%
   para 69% — absorvível. Vira problema apenas acima de R$ 10.
3. **Concentração.** Com 20 parceiros, perder 3 = −15% da receita. Sem fidelidade
   contratual (decisão consciente), a receita é volátil.
4. **Transferência de método.** O treinamento entrega a parte replicável do negócio; o que
   retém é a tecnologia. Reforça a prioridade do moat de aprendizado por marca.
5. **Dependência de fornecedor.** A produção depende de crédito no OpenRouter; o suplente
   OpenAI é vulnerável a hard limit de billing.

---

## 9. Histórico de versões

### v1 — 2026-07-21 · descartada (mantida como registro)
`studio.html` · nome de trabalho "smark Studio"

```
Setup ............ R$ 2.997 (única)
Base ............. R$ 1.197/mês, até 3 marcas
Marca extra ...... R$ 297/mês
```

Também previa planos em escada com limite de artes por plano. **Por que caiu:** quatro
números na oferta e duas dimensões de limite (marcas + artes), exigindo reunião de
explicação. Limitar artes não protegia margem — o custo de imagem é ruído perto da
receita —, então o limite só gerava dúvida e freava o uso.

Esta versão viveu apenas no `/tmp` da sessão e foi recuperada do transcript em 2026-07-26.

### v2 — 2026-07-26 · atual
`white-studio.html` · nome "white studio"

```
Entrada .......... R$ 2.000 em 2×
Mensalidade ...... R$ 630/mês, 2 clientes inclusos
Cliente extra .... 30% de R$ 547 = R$ 164,10
Reajuste ......... IPCA + impostos, todo fevereiro
```

Modelo de licença com participação por cliente. Uma dimensão só (quantos clientes),
artes à vontade, e o crescimento do parceiro puxa a receita junto.

**Caminho até aqui:** partiu de uma escada de três planos por número de clientes, passou
por uma proposta de 10% por cliente (descartada — a margem derretia conforme o parceiro
crescia, o oposto do objetivo) e fechou em 30% com reajuste anual.
