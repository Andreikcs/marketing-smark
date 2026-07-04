---
tipo: playbook-instagram
escopo: todas-as-marcas
versao: 1.1
atualizado: 2026-06-23
fontes-referencia: ["@v4company", "@g4.business", "@weagleai (Pedro Muschitz)", "37signals", "Pipefy", "Conta Azul", "Linear", "thoughtbot"]
herda-de: "[[shared/voz-grupo]]"
---

# Playbook de Instagram — Grupo Smark

Destilado de craft de Instagram, traduzido para a voz do grupo. O `/post-instagram` consulta este arquivo para decidir **hook, formato e visual**. Os exemplos usam a Smark; cada marca troca a dor e o vocabulário, mantendo o princípio.

## Princípio mestre

> **Roubar a forma, rejeitar a substância.**

As contas que mais engajam no Instagram B2B brasileiro (V4, G4, Weagle) dominam o *craft de hook e formato*. Mas vivem de hype, métrica inflada, provocação-insulto e founder-popstar — o oposto da `[[shared/voz-grupo]]`. A gente pega a engenharia do hook e do formato deles e veste com **honestidade**. Se um post poderia ter sido feito por uma startup barulhenta genérica, ele falhou.

---

## 1. Anatomia do hook

- **As 3 primeiras palavras carregam tudo.** Em display, a frase tem que parar o dedo antes de qualquer contexto.
- **Trava da criança de 7 anos** (decisão 2026-06-23): toda headline/peça pública precisa ser entendida por uma criança de 7 anos. É critério de **conversão, não estético** — se uma criança não pega na hora, reescreve.
- **Nomeie a FUNÇÃO, não a ferramenta.** Na headline diz **o que o funcionário faz**, nunca o nome técnico da tecnologia. "Um funcionário que atende seu cliente 24/7" / "alguém que responde na hora quem te chama" — nunca "agente de IA" / "automação" / "sistema" / "plataforma". A vitrine inteira passa pelo **tradutor DE→PARA** e pela **classe técnica proibida** em `[[shared/voz-grupo]]` (lead→"cliente que te chama", follow-up→"voltar a falar", IXC/ERP/CRM→"o programa que você já usa" etc.).
- **Camada importa** (ver `[[shared/voz-grupo]]` → arquitetura de 2 camadas): produto (Provider Max / Elever) vende **o funcionário** em linguagem de criança de 7 anos; smark (a mãe) vende **método e resultado** — registro um pouco mais "consultoria", mas ainda sem jargão de ferramenta e **sem prometer venda/faturamento**.
- **Uma ideia por hook.** Se precisa de duas linhas pra entender, não é hook.
- **Subhook entre parênteses** ancora ou suaviza a afirmação forte. Ex: "SUA EMPRESA TEM IA *(e ainda funciona na idade da pedra)*".
- **Verde-limão (ou cor de acento) na palavra que vira a chave** — a palavra que carrega a virada da frase.

**Tipos de hook que usamos:**

| Tipo | Quando | Exemplo Smark |
|---|---|---|
| Reconhecimento de dor | Topo de funil, awareness | "QUEM CUIDA DISSO É O FULANO" |
| Objeção derrubada | Quebrar a crença que trava a venda | "NÃO PRECISA TROCAR SEU ERP" |
| Cena concreta | Narrativa, dia a dia | "SEGUNDA DE MANHÃ, ALGUÉM ABRE A PLANILHA DE NOVO" |
| Número honesto | Prova com contexto | "3 DIAS POR MÊS NISSO. TODO MÊS." |
| Pergunta seca | Engajamento, identificação | "AINDA ATUALIZA PLANILHA À MÃO?" |

**Nunca:** hook que insulta o leitor ("você é burro se..."), promessa absoluta, número de vaidade sem contexto, **promessa de venda/faturamento** ("vai vender mais", "aumenta o faturamento"). Em vez disso ancore em **função, custo, 24/7 e simplicidade** — e em **troca de custo** ("pelo preço de um estagiário", "sem contratar mais gente").

---

## 2. Formatos de post (com quando usar)

1. **Reconhecimento de dor ("O Padrão")** — carrossel com as 4 dores. *"Você se reconhece em qual?"* É o nosso pão com manteiga e a versão honesta da provocação do G4.
2. **Autoridade / "com quem você fala"** — versão honesta do "por que confiar na V4". Mostra os 4 sócios, o "atende o telefone", parceiro-não-vendedor. Prova = competência e caso real, **nunca** "+8.5 BI".
3. **Storytelling / analogia** — lição de negócio via história (a la G4 com Blockbuster/Santos Dumont). Ex: "a empresa que trocou o ERP inteiro e parou a operação". Honesto e didático.
4. **How-to / educativo** — ensina algo prático de tecnologia/IA/automação que prepara a venda. Sem prometer milagre.
5. **Honestidade sobre limitação** — post curto-provocativo: "nem tudo precisa de IA", "às vezes a planilha bem feita ganha".
6. **Newsjacking** — comenta lançamento de IA/tech sob a ótica "**o que isso muda na sua operação**". Com parcimônia, e sempre amarrado ao negócio do leitor.
7. **Bastidor / parceiro** — foto real dos sócios, diagnóstico, "a gente disse pra não comprar nada ainda".

### 2.1 Mapa: assunto → modelo → visual

Quando o briefing chega, classifique o assunto e use este mapa como **default**. É padrão, mas flexível: se o conteúdo pedir, desvie e justifique no preview.

| Assunto do briefing | Formato ideal (default) | Tratamento visual | Alternativa |
|---|---|---|---|
| Processo / operação / retrabalho | Reconhecimento de dor ("O Padrão") | Carrossel, foto real, 1 número honesto | Cena concreta |
| IA / automação / ferramenta | How-to educativo **ou** newsjacking | Captura de tela limpa + 1 dado | Honestidade sobre limitação |
| Vendas / autoridade / "por que a gente" | "Com quem você fala" | Foto dos sócios, grafismo sóbrio | Quote/posição |
| Legado / decisão de tecnologia errada | Storytelling / analogia | 1 imagem-conceito, serif display | Reconhecimento de dor |
| Capacitação / treinamento | How-to educativo | Carrossel didático | Bastidor |
| Bastidor / cultura / diagnóstico | Bastidor / parceiro | Foto real do time/trabalho | Autoridade |

A **paleta, tipografia e regras de arte** vêm sempre de `marcas/<marca>/branding/identidade-visual.md` (paleta ativa). Este mapa decide o **formato e o tratamento**; o arquivo de identidade decide a **cor e o estilo**.

---

## 3. Banco de hooks (por pilar)

Matéria-prima pronta pro `/post-instagram` adaptar — não usar literal sempre, variar.

**Diferencial "constrói em volta":**
- "O ERP NÃO PRECISA SER TROCADO"
- "O CRM NÃO PRECISA SER JOGADO FORA"
- "A GENTE CONSTRÓI EM VOLTA DO QUE VOCÊ JÁ TEM"
- "TROCAR TUDO É O CONSELHO MAIS CARO QUE TE DERAM"

**Dor 1 — sistema faz quase tudo:**
- "O SISTEMA FAZ QUASE TUDO *(menos a parte que importa)*"
- "VOCÊ PAGOU POR UM SISTEMA COMPLETO. RECEBEU 90%."

**Dor 2 — dependência de pessoa-chave:**
- "QUEM CUIDA DISSO É O FULANO"
- "SE O FULANO SAIR, VIRA CRISE?"

**Dor 3 — time em trabalho manual:**
- "GENTE BOA E CARA FAZENDO TRABALHO DE ROBÔ"
- "SEU TIME PERDE DIAS FAZENDO ISSO"

**Dor 4 — automação:**
- "AINDA ATUALIZA PLANILHA À MÃO?"
- "ISSO AQUI DÁ PRA AUTOMATIZAR. POR QUE NÃO?"

**Autoridade / parceiro:**
- "COM QUEM VOCÊ FALA DE VERDADE"
- "PARCEIRO, NÃO VENDEDOR DE SISTEMA"

**Honestidade:**
- "NEM TUDO PRECISA DE IA"
- "ÀS VEZES A PLANILHA GANHA"

---

## 4. Sistema visual

- **Acento por marca:** roxo `#8B3CF7` (smark primário / Elever) ou lime `#C6F24E` (Provider Max). Acento só na **palavra-chave da headline** e em CTAs.
- **Acento = palavra colorida, NUNCA bloco/caixa** atrás do texto. Entrelinha apertada. Vale nos dois temas.
- **Display (Anton) caixa-alta** para a headline; mono para labels/seções ("O PADRÃO", "SERVIÇO").
- **Foto real dos sócios e do trabalho** — não imagem de IA dramática.
- **Logo no topo**, grid consistente entre posts (template fixo do compositor).
- **Símbolos por marca (padrão único roxo):** todas em quadrado **degradé roxo→azul**, **símbolo branco**, palavra-acento do wordmark em **roxo**. smark = **APEX** (cursor) + `smark.` (ponto roxo); Provider Max = **sinal** (ondas WiFi) + `Provider Max` (“Max” roxo); Elever AI = **sparkle** + `Elever AI` (“AI” roxo). Distinção é pelo **símbolo**, não pela cor. O chip mostra o wordmark; o `@handle` fica no rodapé.
- **Rodapé padrão (todas as marcas):** `@handle` à esquerda + **`@copywriting2026`** à direita. O selo "uma plataforma smark." (produtos) vai na **legenda**, não no rodapé.
- **Etiqueta (tarja vertical):** mesma altura em todas as marcas; símbolo no topo + nome vertical, fonte do nome **auto-ajustada** pra caber centralizado (nomes longos como PROVIDER ficam um pouco menores). Simétrica e consistente — o compositor cuida.
- **CTA estilo V4:** pílula retangular no acento (caixa-alta). Com CTA, o headline limita em ~92px pra respirar. Via `--cta`.
- **Pouco texto na arte** — a headline carrega; o resto vai na legenda.

**Dois temas (mesmo modelo, invertido) — ritmo de feed ~70% claro / 30% escuro:**

| | Claro (default) | Escuro (secundário) |
|---|---|---|
| Fundo | `#F4F2FB` | `#0B0B0B` |
| Texto | `#100D1C` | `#FFFFFF` |
| Acento | roxo `#8B3CF7` · lime escurece p/ `#667D28` | roxo `#A472FF` · lime `#C6F24E` |

- **Claro** é o tom-padrão (decisão 2026-06-23); **escuro** virou paleta **secundária** — entra só sob pedido ("escuro/dark/roxo/fundo escuro") ou como contraponto pontual. Gera escuro com `--tema escuro`.
- No claro, acento claro demais pro fundo (lime) **escurece sozinho** mantendo o tom — o compositor cuida disso. Default já é `--tema claro`.
- Cores são fonte única em `design-system/tokens/tokens.json` (`fundacao`, `tema_claro`, `marcas`).
- **Fundos (IA):** sempre on-brand. Os scripts `openai_image.py` / `openai_edit.py` aplicam uma **trava de paleta** automática (base preto-quase + acento da marca; bloqueia vermelho/rosa/laranja/magenta não pedidos e cena fora da identidade). Passe `--paleta roxo|lime` pra afinar o acento. Só use `--no-guard` se o briefing pedir explicitamente outra cor.

**Nunca visualmente:** imagem AI cafona (super-herói, caverna, deadlift épico), stock genérico, poluição de texto, founder em pose de popstar.

---

## 5. Linha vermelha (o que rejeitamos das referências)

Tudo isto viola `[[shared/voz-grupo]]` e está **proibido**, mesmo que engaje:

- Métrica de vaidade inflada ("+8.5 BI", "10 milhões/ano sem contexto").
- Provocação que ofende o leitor ("a IA vai deixar as pessoas burras").
- Tom de palestrante de growth / hustle.
- Imagem de IA dramática e cafona.
- Founder-celebridade, ostentação.
- Promessa absoluta ("automatize 100%", "zero erro").

---

## 6. As referências do swipe file e o que extrair

**Energia de hook (BR, alto engajamento) — roubar forma, rejeitar tom:**
- **@v4company** → conteúdo de autoridade ("por que confiar"), hook de 3 palavras. *Evitar:* vermelho gritante, métrica inflada, hype.
- **@g4.business** → storytelling/analogia, quote card, ritmo cinematográfico. *Evitar:* provocação-insulto ao gestor, números de aspiração vazia.
- **@weagleai** → hook + subhook entre parênteses, how-to de IA. *Evitar:* imagem AI cafona, "deixa as pessoas burras", tom de salvador.

**Teto de qualidade (voz + visual sóbrio) — perseguir:**
- **37signals / Basecamp** → voz honesta, contrarian, "o que não fazemos".
- **Pipefy / Conta Azul** → dor de processo manual em pt-BR, didático.
- **Linear / thoughtbot** → visual escuro premium + posicionamento "parceiro, não fornecedor".

---

## Como o `/post-instagram` usa este playbook

1. Escolhe **1 formato** (seção 2) coerente com o briefing.
2. Puxa/adapta **1 hook** (seção 3) — varia, não repete o último post.
3. Aplica o **sistema visual** (seção 4) no briefing visual.
4. Passa o rascunho pela **linha vermelha** (seção 5) antes do preview.
