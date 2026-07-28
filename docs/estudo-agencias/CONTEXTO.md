# Contexto — estudo de distribuição via agências (white studio)

Registro do que foi decidido, por quê, e o que ficou aberto. Escrito para que qualquer
sessão futura (ou pessoa) retome sem depender da memória de uma conversa.

**Última atualização:** 2026-07-28

---

## 1. A ideia, em uma frase

Licenciar o motor de produção de mídia do vault smark como plataforma **white-label** para
agências pequenas, que revendem sob a própria marca. Nós fornecemos tecnologia, método e
treinamento; a agência fornece a distribuição e o relacionamento com o cliente final.

Origem estratégica: `docs/superpowers/specs/2026-07-21-distribuicao-plataforma-agencias-design.md`.
A premissa era "software virou commodity — o valor migra para quem tem distribuição".

---

## 2. O modelo, como está fechado

| Item | Valor | Observação |
|---|---|---|
| Entrada | **R$ 2.000** | em até 2×; treinamento, método, setup, infra, acompanhamento dos 2 primeiros |
| Mensalidade | **R$ 630** | inclui até 2 clientes-marca |
| Cliente adicional | **30% de R$ 547 = R$ 164,10** | a partir do 3º |
| Régua de revenda | **R$ 547/mês** | preço sugerido; o parceiro pode cobrar mais e fica com a diferença |
| Reajuste | IPCA + impostos, **todo fevereiro** | previsto em contrato |
| Câmbio de referência | **US$ 1 = R$ 6,00** | usado em todo cálculo de COGS |

Natureza jurídica: **licenciamento white-label, não franquia.** Chamar de franquia acionaria
a Lei 13.966/2019 (COF obrigatória 10 dias antes da assinatura, sob pena de anulação do
contrato e devolução de valores). A palavra "franquia" não aparece em material nenhum.

Documentação completa: `MODELO-DE-NEGOCIO.md` · Spec: `/specs/2026-07-26-white-studio-modelo-negocio-design.md`

---

## 3. Como chegamos aqui — a trilha de decisão

**Restrição de partida (do usuário):** o modelo não pode exigir explicação. "Eu quero que o
cliente entenda de cara." Isso matou toda estrutura em escada com limite de artes.

**Primeira proposta (v1, 21/07):** planos escalonados, R$ 2.997 de setup + R$ 1.197/mês até
3 marcas + R$ 297 por marca extra. Descartada por excesso de números. Mantida em
`studio.html` como histórico.

**Proposta do usuário (a que virou modelo):** R$ 2.000 + R$ 630 + % por cliente novo.
Percentual foi de 10% → 20% → **30%**, subido depois que o P&L mostrou que 10% dava
apenas R$ 1.188 de lucro (4%) com 20 parceiros.

**Duas descobertas que mudaram o cálculo:**

1. **Custo de imagem é ruído.** O carrossel reaproveita um `bg.png` só — o custo é por post,
   não por arte. Deu **R$ 1,92/post** medido. Limitar artes era resolver o problema errado.
2. **O custo humano é 2,1× o custo de IA.** A margem real se decide no atendimento, não na
   API. Daí as travas operacionais serem de escopo humano, não de volume de imagem.

**As duas evoluções que salvaram a margem:** subir a participação para 30% e produtizar o
onboarding. Levaram o resultado com 20 parceiros de R$ 1.188 (4%) para **R$ 13.396 (37%)**.

---

## 4. Segmentos e GTM

Três segmentos escolhidos por matriz de confiança ponderada (8 avaliados):
**provedores de internet · contabilidades · franquias**.

Critério que eliminou os demais: o studio entrega **linha visual de post estático
recorrente**. Segmento sem esse padrão não é atendido bem pela ferramenta.

Distinção que invalidou a lista original de 8 segmentos do White ERP: aqueles são
**verticais do cliente final**, não **compradores da licença**. Quem compra é a agência que
atende aquela vertical.

Meta: **5 licenças em 30 dias.** Plano completo em `SEGMENTOS-E-GTM.md`.

---

## 5. Confronto com a tese "services-as-software" (28/07)

Analisamos o reel de @allesinisgalli e rastreamos até a fonte (Julien Bek, Sequoia, 05/03/2026).
Relatório completo em `TESE-SERVICES-AS-SOFTWARE.md`. Em resumo:

**O que se confirmou:** estamos no mesmo eixo estratégico, escolhemos um setor que a própria
tese cita (contabilidade), nosso pricing híbrido é o padrão real do mercado (outcome pricing
é praticado por só 3,8%), e nossa margem projetada (~80% no COGS de imagem) está 20–30 pontos
**acima** do benchmark AI-native (50–60%).

**O que ficou exposto:**
- capturamos o orçamento de **software** (R$ 164) enquanto o parceiro captura o de **mão de obra**
- estamos armando o intermediário que a tese diz que será comprimido → risco de desintermediação
- cada licença vendida encarece um futuro movimento nosso de vender direto (dilema do inovador)
- os níveis "assistido" e "sob demanda" do spec de 21/07 — o nosso autopilot — nunca foram precificados

**Decisão de 28/07: a proposta não muda.** Preços, segmentos e GTM seguem como estão. Da
análise foi incorporado só o que amadurece sem mexer na oferta:

| O quê | Onde entrou |
|---|---|
| Argumento 4 — "o que te diferencia deixou de ser a arte" | `MODELO-DE-NEGOCIO.md` §6, GTM §4.5 (fechamento), apresentação (close + FAQ) |
| Duas objeções novas (IA acaba com a agência / vocês vão vender direto?) | `MODELO-DE-NEGOCIO.md` §6 |
| Trava 5 — cláusula de não-concorrência com o parceiro | `MODELO-DE-NEGOCIO.md` §5 + termo no contrato da apresentação |
| Riscos 6 e 7 — desintermediação e custo de opção futura | `MODELO-DE-NEGOCIO.md` §8, apenas para observação |
| Benchmark de margem AI-native (50–60%) como referência | `MODELO-DE-NEGOCIO.md` §4 |
| Critério 5 de validação — anotar o preço real cobrado do cliente final | `SEGMENTOS-E-GTM.md` §4.7 |
| Risco 7 do GTM — não levar o argumento de posicionamento cedo demais | `SEGMENTOS-E-GTM.md` §5 |

**O trilho B (vender o trabalho pronto direto ao cliente final) NÃO entrou no plano.**
Fica registrado como risco a observar e decisão de mês 3. O critério 5 de validação existe
justamente para que essa decisão futura tenha dado real em vez de premissa — sem custar
nada agora.

**Correção de fato importante:** o "1 dólar de software para 6 de serviço" do reel é citação
real de Bek, mas refere-se a *todo* gasto com serviços. Em IA especificamente, Gartner 2026
mostra **1,3 : 1**. E para cada US$ 1 que sai de folha, só US$ 0,03 entra em IA.

---

## 6. Artefatos

| Arquivo | O que é |
|---|---|
| `index.html` | índice do estudo (servido em `/`) |
| `white-studio.html` | apresentação comercial v2 — atual |
| `studio.html` | apresentação v1 — histórico, não sobrescrever |
| `MODELO-DE-NEGOCIO.md` | referência completa: oferta, COGS, P&L, travas, objeções |
| `SEGMENTOS-E-GTM.md` | matriz de confiança + plano de 30 dias |
| `TESE-SERVICES-AS-SOFTWARE.md` | análise da tese Sequoia vs. nosso modelo |
| `CONTEXTO.md` | este arquivo |
| `serve.py` | servidor local; renderiza `.md` e força charset utf-8 |
| `prototipo-white-studio/` | protótipo clicável do app |
| `*_template.html` | fontes dos HTML (as artes são injetadas em base64 na build) |

**Subir o estudo:** `python3 docs/estudo-agencias/serve.py` → http://localhost:8791

> `serve.py` existe porque o `python3 -m http.server` manda `Content-type` sem charset, o
> navegador cai em latin-1 e todo acento quebra. Foi essa a causa do "encoding quebrado" —
> os arquivos sempre estiveram em UTF-8 válido.

---

## 7. Em aberto

| # | Pendência | Peso |
|---|---|---|
| 1 | Anterioridade de "white studio" no INPI e em domínio | alto — antes de imprimir material |
| 2 | Quem executa as 12 abordagens/dia do GTM | alto — o plano não roda sem isso |
| 3 | Amostragem de custo real por faixa de uso | médio — hoje é projeção |
| 4 | Decidir sobre o trilho B (autopilot direto) | médio — decisão do mês 3, com o dado do critério 5 na mão |
| 5 | ~~Cláusula de não-concorrência~~ | **resolvida em 28/07** — trava 5 do modelo, entra no contrato |
| 6 | Precificar níveis "assistido" e "sob demanda" | médio |
