---
tipo: design
tema: distribuição da plataforma de mídia via agências (white-label)
data: 2026-07-21
status: design aprovado — aguardando revisão do spec
autor: Andreik + Claude
origem: tese "software virou commodity, valor migra pra distribuição; o centro de distribuição é separável do produto"
camada: negócio (modelo de distribuição)
depende-de: spec futuro — Camada 3 (sistema: motor multi-agência hospedado)
---

# Distribuição da plataforma de mídia via agências (white-label)

## Contexto e origem

Este design nasce da tese (mensagem encaminhada, 2026-07-20):

> Software virou commodity — qualquer um monta um produto funcional com IA rápido. Quando algo fica abundante, o valor migra pra parte que continua escassa: **distribuição** (chegar no cliente, confiança, presença, instalação, suporte, cobrança, relacionamento). E o centro de distribuição é **separável do produto** — a mesma rede que vende um software vende qualquer outro.

Aplicada ao ativo da smark, a leitura é: o vault de geração de mídia **é** software (portanto commodity-side), mas o que ele embrulha — a linha de produção confiável de peças — é o lado ainda escasso. E as **agências** são centros de distribuição que já existem (cada uma com ~5 clientes, relacionamento, cobrança, confiança). A jogada é plugar o produto (a plataforma) na distribuição que já existe (as agências), em vez de construir distribuição do zero.

### Fatos que fundamentam o design (levantados na sessão)
- **Distribuição da smark hoje = zero canal.** Só fundadores + rede pessoal.
- **Produto entregável via playbook** sem os fundadores na linha de frente (destravador do handoff).
- **Rede-alvo real, mas relação distante** — precisa ser conquistada; e o alvo se ampliou de "uma rede de franquias" para **agências em geral**.
- **Dor da agência é aguda e recorrente:** horas e horas em arte, presa ao tamanho da equipe, não escala. Pain-killer, não vitamina.
- **Modelo de entrega escolhido: white-label** (motor invisível). A agência entrega como se fosse dela; a smark é o motor por baixo.

---

## Seção 1 — O que a smark vira (base estratégica)

A smark deixa de só *usar* a linha de produção de mídia e passa a **licenciá-la como motor invisível** para agências. A agência entrega arte pros clientes dela como se fosse dela; por baixo roda o motor smark.

**Posição na tese:** parar de disputar o lado abundante ("gerar imagem", que qualquer um monta) e vender o lado escasso — a **linha de produção confiável** (2 camadas, direção de arte, gate de marca), **mantida atualizada** pela smark. A distribuição é das agências; a smark é o motor.

**A troca do white-label:** sem selo na peça, o moat **não é marca**. Ele vem de três pilares — o design inteiro gira em blindá-los:

1. **Profundidade do motor** — pipeline de 2 camadas + direção de arte que ninguém replica num fim de semana.
2. **Custo de troca** — o contexto de marca dos clientes de cada agência (voz, paleta, histórico de peças) passa a *morar* no sistema. Quanto mais usa, mais caro sair.
3. **Atualização contínua** — a smark absorve a corrida de modelos pra agência não ter que absorver.

**Consequência de identidade:** a plataforma vira **produto de marca própria** (nome próprio ou neutro), separada da vitrine "assessoria" do site-canônico. Dois negócios, duas vozes, sem contaminar — e o motor pode, na Fase 2, virar o canal pelo qual as agências revendem os funcionários de IA.

---

## Seção 2 — A oferta concreta

**O produto embrulhado.** Hoje o motor existe em pedaços no vault (`openai_image.py` → fundo, `compositor.py` → texto/moldura, `_direcao.py` → direção, `revisar.py` → gate, `editor_server.py` → editor). Pra agência vira **uma coisa só**: um estúdio web onde ela cria uma marca-cliente e produz peças em minutos. Nunca vê "script", "prompt" ou "modelo" — vê gerar e editar.

**Fluxo de valor (o que a agência sente):**
1. **Cadastra o cliente uma vez** — logo, paleta, voz, formatos de canal. É o onboarding e a origem do custo de troca.
2. **Pede uma peça** — briefing curto → motor gera fundo (direção nível agência) + aplica texto nítido em 2 camadas + passa no gate de marca. Sai peça vendável, não "post de IA".
3. **Ajusta no editor** — o Super Editor por frame (`editor_server.py`), agora multi-cliente.
4. **Baixa/entrega** — tamanho certo por canal; a agência põe a marca dela.

**Ganho na linguagem da agência:** produz em minutos o que leva horas; atende mais clientes com a mesma equipe; para de depender do designer sênior pra consistência; escala sem inchar folha.

**Três níveis de entrega (decisão: oferecer os três):**
- **Self-service (padrão)** — a agência opera sozinha. Máxima margem, custo marginal ~zero.
- **Assistido (pago)** — estúdio + smark revisa/refina lote no início até a agência pegar a mão.
- **Sob demanda (fallback, pago)** — casos difíceis / agência sem braço: manda briefing, smark entrega. Não escala, segura contas grandes, vira upsell.

**Fronteira do que a smark NÃO entrega (decisão firmada):** entrega **motor e craft**; a agência entrega **relacionamento, estratégia de conteúdo do cliente dela, e aprovação final**. **A smark não fala com o cliente-final da agência** — esse é o centro de distribuição *dela*, de propósito. Preserva o white-label e mantém a smark como motor, não concorrente da agência.

**Dependência honesta:** tudo pressupõe motor **multi-cliente e hospedado**. Hoje é local-only. O `editor_server.py` já é multi-marca no osso, mas virar "cada agência na sua conta, clientes isolados" é a **Fase 0 / Camada 3** — pré-requisito, não parte desta seção.

---

## Seção 3 — Modelo econômico

**Forma da receita: assinatura recorrente por agência, ancorada no valor que ela captura — não no custo da smark.** O preço tem que ser fração óbvia do que a agência cobra dos clientes dela, de modo que a conta feche sozinha ("pago X, economizo Y horas, atendo 2 clientes a mais"). Menor que uma diária de designer → decisão trivial.

**Estrutura em 3 camadas:**
1. **Assinatura-base por agência** — acesso ao estúdio + N marcas-cliente + volume de peças. Receita recorrente previsível. Ancorada em "custa menos que meio designer júnior".
2. **Expansão por uso** — marcas-cliente e/ou pacotes de peças acima da base. Cresce junto com o sucesso da agência, sem esforço proporcional da smark.
3. **Serviço (margem alta, opcional)** — os níveis assistido/sob-demanda, cobrados por lote. Segura contas grandes; degrau pra Fase 2.

**Por que recorrência, não avulso:** o custo de troca só vira dinheiro se a relação for contínua. Assinatura transforma o moat em fluxo de caixa; avulso jogaria o ativo fora.

**Unit economics (estrutura, valores a calibrar):**
- **Custo variável por peça** = API de imagem + compute do compositor. Baixo e caindo. Regra: *a assinatura-base sozinha paga o custo variável do teto de volume dela* — nenhuma agência dá prejuízo nem no uso máximo.
- **Custo de servir (o perigo real)** = suporte + onboarding. É o que mata margem em B2B white-label, não a API. Por isso self-service é padrão e assistido é **pago** — nunca subsidiar mão de obra da smark dentro da base.
- **Alavanca:** ~5 clientes por agência. 20 agências = 100 marcas no motor com time pequeno. Margem melhora com escala (motor é o mesmo; só o suporte cresce, e é pago à parte).

**Métrica-norte: marcas-cliente ativas rodando peças/mês** (não nº de agências). Mede custo de troca real e receita de expansão. Agência com 5 marcas ativas há 6 meses praticamente não sai.

**Anti-padrão a evitar:** preço-por-peça como modelo principal — alinha ao custo (commodity) e faz a agência racionar uso. Uso entra só como **expansão acima da base**.

---

## Seção 4 — O moat na prática

No white-label, sem marca na peça, o moat é a única coisa que impede a troca por concorrente ou por "monto sozinho".

**Pilar 1 — Profundidade do motor.**
- **Pipeline de 2 camadas** (fundo IA + texto/moldura HTML/CSS nítido a 2x): concorrente que gera texto dentro da imagem entrega texto borrado; a smark entrega tipografia perfeita. Diferença visível na primeira peça.
- **Direção de arte estruturada** (`_direcao.py`: conceito por tipo + composição por layout + cor estrita) + **grade de acabamento** (duotone+vinheta+grão). Anos de gosto codificado, não um prompt.
- **Defesa ativa:** núcleo fechado. A agência usa o resultado, nunca o "como". Prompt de direção e lógica de composição = segredo industrial, nunca expostos nem documentados pro cliente.

**Pilar 2 — Custo de troca (o mais forte a longo prazo).**
- Cada marca-cliente deposita ativo: voz, paleta, formatos, **e histórico de peças aprovadas**. Mais peças → motor "conhece" mais a marca → entrega mais consistente.
- **Defesa ativa:** o sistema **aprende por marca** — cada peça aprovada refina o contexto daquela marca-cliente. Sair após 6 meses = recomeçar o contexto de 5 clientes do zero. **(Prioridade confirmada na sessão — é o que transforma "ferramenta legal" em "não consigo sair".)**
- Complemento: **calendário/painel de produção por agência** (`painel.py` no osso). Operação inteira da agência morando no painel → trocar de motor é trocar de sistema operacional.

**Pilar 3 — Atualização contínua.**
- Modelo de imagem muda a cada trimestre; a agência quer que "continue bom" sem acompanhar.
- **Defesa ativa:** a smark absorve a troca de modelo por baixo (o vault já isola: `openai_image.py` é uma camada; trocar o motor de imagem não toca compositor nem direção). A agência paga e a qualidade sobe sozinha. É vender *"nunca ficar desatualizado"* — só existe com recorrência.

**Moat combinado:** um concorrente copia o gerador. Não copia, ao mesmo tempo, o craft da pipeline **+** os 6 meses de contexto de 5 clientes **+** a promessa de sempre atualizado. Os três juntos prendem.

**Risco residual (honesto):** agência grande e sofisticada pode internalizar tudo. O moat segura a **long tail** (pequenas/médias, sem time de IA próprio) — a maioria do mercado. Enterprise que ameaça internalizar retém-se com o nível "serviço" e, na Fase 2, com os agentes. Prender a base larga; monetizar o topo com serviço.

---

## Seção 5 — Faseamento

Cada fase só destrava depois que a anterior prova valor.

**Fase 0 — Pré-requisito técnico (sem isso nada liga).**
Transformar o vault local-only em **motor hospedado multi-agência**: cada agência na conta dela, clientes isolados. Osso já existe (`editor_server.py` multi-marca, `painel.py`, scripts em camadas). É a **Camada 3 (sistema)** — vira spec técnico próprio. O design de negócio dorme até a Fase 0 existir. **Não vender antes de conseguir servir.**

**Fase 1 — Wedge: aterrar agências com a plataforma de mídia.**
- Alvo: agências pequenas/médias (long tail que o moat prende).
- PoC: **1 agência-piloto** rodando 5 marcas-cliente reais por 60–90 dias. Valida self-service, mede horas economizadas, calibra preço.
- Marco de saída: a agência **renova sozinha e indica outra** (sinal de que o custo de troca começou a morder).
- Depois: abrir pra 5–10 agências. Crescer por indicação (agência confia em agência), não por mídia paga.

**Fase 2 — Expansão: agentes de IA pelo mesmo canal.**
- Agência já vive dentro do motor → canal pronto pros funcionários de IA (Nina/Clara/Téo), revendidos pros mesmos clientes dela.
- White-label pode relaxar de propósito: revender agentes como "powered by smark" pra emprestar credibilidade. Ticket alto, mesma distribuição.
- Casa com o Caminho C original: a plataforma foi o piloto barato que provou o handoff; os agentes são a monetização pesada sobre a rede validada.

**Fase 3 — Rede: distribuição da distribuição.**
- Dezenas de agências no motor → a smark vira a camada que **conecta** agências: biblioteca de estilos compartilhada, benchmark de performance, possível marketplace de peças/formatos.
- Ativo final da tese: não só produto plugável, mas a **rede** — o escasso que "leva anos e não dá pra gerar com IA". Negócio genuinamente difícil de atacar.

**Disciplina que amarra (risco nº1 do faseamento):** não parar na Fase 1. 10 agências felizes de mídia é confortável e nunca constrói o ativo durável. **Gate explícito:** Fase 1 só é "vencida" com dado de renovação + indicação — e aí forçar a Fase 2.

---

## Decisões firmadas nesta sessão
- Camada de foco: **negócio** (distribuição).
- Produto de entrada: **a plataforma de mídia** (wedge); agentes de IA como **expansão** (Fase 2).
- Canal: **agências** (rede que já existe), começando por 1 piloto.
- Modelo de entrega: **white-label** (motor invisível) + três níveis (self-service padrão, assistido/sob-demanda pagos).
- Fronteira: **smark não fala com o cliente-final da agência**.
- Receita: **assinatura-base + expansão por uso + serviço opcional**; métrica-norte = **marcas-cliente ativas/mês**.
- Prioridade de moat: **Pilar 2 (aprendizado por marca)**.

## Não-objetivos deste design
- Não define a arquitetura técnica do motor multi-tenant (é a **Fase 0 / Camada 3**, spec separado).
- Não define preços numéricos finais (calibração de campo na Fase 1).
- Não altera o site-canônico nem a vitrine "assessoria" da smark (a plataforma é marca própria à parte).
- Não cria automação de venda/CRM — crescimento por indicação na Fase 1.

## Próximos passos
1. Revisão deste spec pelo Andreik.
2. Plano de implementação (writing-plans) — provavelmente começando pela **Fase 0** (spec técnico do motor multi-agência), já que o negócio dorme até ela existir.
