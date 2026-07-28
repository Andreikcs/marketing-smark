# Prompt para produzir a proposta no claude.ai/design

Cole o bloco abaixo inteiro. Ele é autocontido — traz a identidade, a estrutura e o texto
final, então não depende de o Design conhecer o vault.

**Antes de colar:** troque `[NOME DO ESCRITÓRIO]` pelo cliente real. Se for gerar a versão
genérica, troque por `seu escritório`.

**Depois de gerar:** as três peças de exemplo entram como imagem. Suba artes de
contabilidade de verdade — o placeholder do Design não convence ninguém.

---

```
Crie uma proposta comercial de uma página, em HTML único e autocontido, para a smark
vender serviço de social media a um escritório de contabilidade.

═══════════════════════════════════════════════════════════════
CONTEXTO DA VENDA (não escreva isso na peça, use pra calibrar o tom)
═══════════════════════════════════════════════════════════════

Quem lê é o dono de uma contabilidade. Hoje uma funcionária dele reserva um tempo da
semana, usa IA pra montar as artes e publica. Funciona, e o custo em dinheiro é quase
zero — porque o salário dela já está pago.

Então a proposta NÃO ganha por preço. Ganha mostrando o que essa rotina cobra sem
aparecer: a hora de alguém que foi contratado pra outra coisa, um padrão visual que muda
toda semana, e um feed que morre justamente na semana de fechamento.

Regra de ouro do tom: nunca, em nenhum momento, dar a entender que o material atual é
ruim ou que a pessoa faz mal feito. Ela provavelmente é próxima do dono. O ângulo é
sempre "isso não deveria estar no colo dela".

═══════════════════════════════════════════════════════════════
IDENTIDADE VISUAL — use exatamente estes valores
═══════════════════════════════════════════════════════════════

Marca: smark. (sempre em minúsculo, com o ponto final)

Tema CLARO é o padrão. Fundo claro, texto escuro, roxo como acento.

Cores:
  fundo .................. #F4F2FB
  cartão ................. #FFFFFF
  texto .................. #100D1C
  texto secundário ....... #4A4560
  texto de apoio ......... #6B6680
  roxo (acento principal)  #8B3CF7
  roxo claro ............. #A472FF
  lime (acento secundário) #C6F24E   ← use com muita parcimônia, só em 1 detalhe
  faixa escura ........... #050D1A   ← capa e uma seção de contraste
  gradiente .............. linear-gradient(155deg,#8B3CF7 0%,#050D1A 100%)

Tipografia (carregue do Google Fonts):
  Títulos ....... Anton — caixa alta, entrelinha apertada, letter-spacing negativo
  Corpo ......... Archivo

Raio de canto: 16px
Regra de acento: o roxo colore PALAVRAS dentro do título, nunca um bloco ou caixa atrás
do texto. Entrelinha bem apertada nos títulos grandes.

Layout: largura máxima ~960px, seções generosas separadas por linha fina, respiro alto.
Precisa funcionar no celular e imprimir bem em PDF (inclua @media print).

═══════════════════════════════════════════════════════════════
ESTRUTURA E TEXTO
═══════════════════════════════════════════════════════════════

1) CAPA — fundo escuro (#050D1A) com um brilho roxo difuso no canto superior direito

   Etiqueta: "Proposta para [NOME DO ESCRITÓRIO]"
   Sobretítulo: "Social media · produção e publicação"
   Título: "O conteúdo de vocês sai da semana de alguém."
   Apoio: "A gente assume a produção e a publicação das redes do escritório. Você aprova,
   a gente faz. Ninguém aí dentro precisa parar o que estava fazendo."

   Rodapé da capa, em 4 colunas:
     Preparado por: smark.   |   Serviço: Produção + publicação
     Início: Em até 7 dias   |   Fidelidade: Nenhuma

2) ONDE VOCÊS ESTÃO HOJE

   Título: "Funciona. Mas depende de uma pessoa ter tempo."
   Apoio: "Hoje alguém do escritório reserva um espaço da semana, monta as artes com ajuda
   de IA e publica. Isso já é mais do que a maioria dos escritórios faz — e o mérito é de
   quem faz. O ponto não é a pessoa nem a ferramenta. É o que essa rotina cobra sem
   aparecer na conta."

   Três cartões, cada um com um ícone simples em quadrado roxo claro:
   • "Sai do trabalho de verdade" — Quem faz as artes foi contratado pra outra coisa. Cada
     hora ali é uma hora fora da função, e ninguém soma essas horas no fim do mês.
   • "O padrão muda toda semana" — Cada peça sai de um jeito: outra cor, outra fonte, outro
     estilo. Quem vê de fora não guarda a marca do escritório, guarda posts soltos.
   • "Para na pior semana" — Fechamento, prazo de entrega, cliente em cima: é quando o
     conteúdo some. E é exatamente quando o escritório mais deveria estar aparecendo.

3) COMO PASSA A FUNCIONAR

   Título: "Cinco passos. Você entra em um."
   Apoio: "O único momento que exige vocês é a aprovação — e ela leva minutos, do celular."

   Cinco passos numerados na horizontal (empilhados no celular):
   1. Pauta do mês — A gente traz os temas: prazos, obrigações, dúvidas que os clientes de
      vocês mais mandam.
   2. Você aprova — Uma lista curta, uma resposta. Corta o que não faz sentido, acrescenta
      o que quiser.
   3. A gente produz — Arte e legenda no padrão do escritório, peça por peça.
   4. Você confere — Tudo passa por vocês antes de ir ao ar. Nada é publicado sem seu ok.
   5. A gente publica — No dia e na hora certos, toda semana, sem ninguém precisar lembrar.

4) PLANOS — dois cartões lado a lado, o segundo destacado

   Título: "Dois tamanhos. Escolha pelo ritmo."
   Apoio: "A diferença entre eles é frequência. Tudo que é serviço — pauta, legenda,
   aprovação, publicação — está nos dois."

   ┌ PLANO PRESENÇA ─────────────────────────────┐
   │ 8 peças por mês · 2 publicações por semana   │
   │ R$ 297/mês  ·  = R$ 37,12 por peça publicada │
   │ • 8 artes no padrão visual do escritório     │
   │ • Legenda escrita para cada peça             │
   │ • Pauta mensal com os temas da vez           │
   │ • Publicação agendada no Instagram           │
   │ • 1 rodada de ajuste por peça                │
   │ • Aprovação pelo celular, sem reunião        │
   └──────────────────────────────────────────────┘

   ┌ PLANO CONSISTÊNCIA ── selo "Recomendado" ────┐  ← borda roxa, sombra mais alta
   │ 12 peças por mês · 3 publicações por semana  │
   │ R$ 397/mês  ·  = R$ 33,08 por peça publicada │
   │ • 12 artes no padrão visual do escritório    │
   │ • Legenda escrita para cada peça             │
   │ • Pauta mensal com os temas da vez           │
   │ • Publicação agendada no Instagram           │
   │ • 1 carrossel por mês — o formato que mais   │
   │   segura atenção                             │
   │ • Calendário do setor contábil — prazos e    │
   │   obrigações já mapeados no mês              │
   │ • Relatório mensal simples: o que saiu e     │
   │   como performou                             │
   │ • 2 rodadas de ajuste por peça               │
   └──────────────────────────────────────────────┘

   Abaixo dos cartões, em texto pequeno: "Sem taxa de implantação. Sem fidelidade."

5) COMPARATIVO — tabela limpa, cabeçalho em roxo bem claro

   Título: "O que muda entre um e outro."
   Linhas: Peças por mês (8 / 12) · Publicações por semana (2 / 3) · Arte no padrão do
   escritório (✓ / ✓) · Legenda escrita (✓ / ✓) · Pauta mensal (✓ / ✓) · Publicação
   agendada (✓ / ✓) · Carrossel mensal (— / ✓) · Calendário do setor contábil (— / ✓) ·
   Relatório mensal (— / ✓) · Rodadas de ajuste (1 / 2) · Investimento mensal (R$ 297 /
   R$ 397)

6) PADRÃO DE ENTREGA — três peças quadradas lado a lado

   Título: "Peça de escritório, não post de IA."
   Apoio: "O texto é escrito e montado em camada nítida — não é imagem gerada com letra
   torta. Dá pra ler no celular, no feed, sem apertar os olhos."

   Deixe três espaços quadrados (proporção 1:1) para eu inserir as artes depois.
   Legendas: "feed · tema claro", "feed · destaque", "capa de carrossel".

7) O QUE A GENTE NÃO PROMETE — bloco de fundo escuro (#050D1A), cantos arredondados

   Esta seção é o coração da confiança. Não suavize o texto.

   Título: "O que a gente não promete."
   • Não prometemos venda. Post não fecha contrato sozinho, e quem garante isso está
     vendendo sonho. O que a gente garante é presença constante, no padrão, sem consumir o
     tempo de ninguém aí dentro.
   • Não publicamos nada sem você ver. Tudo passa por aprovação. Se algo não pode ser dito,
     não vai ao ar.
   • Não prendemos ninguém. Sem fidelidade e sem multa. Se em dois meses vocês acharem que
     não vale, é só avisar.
   • As peças são de vocês. Saindo ou ficando, tudo que foi produzido continua sendo do
     escritório.

8) PERGUNTAS — acordeão

   • "A gente já faz internamente. Por que pagar?" → Some as horas que a pessoa gasta por
     semana e multiplique pelo custo dela. Na maioria dos escritórios esse número passa do
     valor do plano — e ela volta a fazer o que foi contratada pra fazer. Fora que aqui não
     para em semana de fechamento.
   • "Vocês entendem de contabilidade?" → A gente entende do calendário e da linguagem:
     prazos, obrigações, as dúvidas que se repetem. E nada vai ao ar sem a aprovação de
     vocês, justamente porque quem tem a palavra final sobre o conteúdo técnico é o
     escritório.
   • "Quanto tempo isso vai tomar da nossa equipe?" → Minutos por semana. Uma aprovação da
     pauta no início do mês e um ok nas peças. É conversa de WhatsApp, não reunião.
   • "E se a gente não gostar de uma arte?" → Você pede o ajuste e a gente refaz. Está
     incluso no plano — uma rodada no Presença, duas no Consistência.
   • "Precisamos dar acesso às nossas redes?" → Sim, para agendar as publicações. É um
     acesso de parceiro, que vocês tiram quando quiserem, sem depender da gente.
   • "Dá pra aumentar o volume depois?" → Dá, a qualquer momento. Muita gente começa no
     Presença e sobe quando vê o feed andando sozinho.

9) FECHO — fundo com o gradiente roxo→escuro, centralizado

   Frase grande: "Vocês aprovam. O resto é com a gente."
   ("O resto é com a gente" recebe um grifo suave em roxo)
   Apoio: "Escolhendo o plano hoje, a primeira pauta chega em até 7 dias e a primeira
   publicação sai na semana seguinte. Sem taxa de implantação."

10) RODAPÉ — faixa escura, tipografia mono pequena
    Esquerda: "smark. · produção e publicação de conteúdo"
    Direita: "proposta para [NOME DO ESCRITÓRIO] · válida por 15 dias"

═══════════════════════════════════════════════════════════════
REGRAS QUE NÃO PODEM SER QUEBRADAS
═══════════════════════════════════════════════════════════════

1. Português do Brasil. Linguagem de conversa, que um contador de 55 anos entenda sem
   reler. Frases curtas.

2. Jargão proibido: alavancar, sinergia, exponencial, transformação digital, disrupção,
   engajamento, awareness, branding, ROI, funil, performance, escalar, otimizar,
   "posicionamento estratégico". Se precisar do conceito, diga com palavra comum.

3. NUNCA prometer venda, cliente novo, faturamento ou resultado comercial. Nem no título,
   nem em número, nem por insinuação. O que se vende é constância, padrão e tempo
   devolvido. A seção 7 existe justamente pra deixar isso explícito.

4. Nada de estatística inventada. Zero "87% das empresas" ou "3x mais alcance". Se não
   está no texto acima, não entra.

5. Nenhuma frase que critique quem produz o conteúdo hoje.

6. HTML único, sem dependência externa além das fontes do Google. CSS na própria página.
   Sem framework. Precisa abrir sozinho num navegador e imprimir bem em PDF.
```
