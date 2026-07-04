# -*- coding: utf-8 -*-
"""Gera as 3 home one-page (smark, provider-max, elever-ai) a partir de um template único.
Fonte de DNA: cores/gradiente do tokens.json (replicados aqui), frases-mãe dos posicionamentos.
Rodar: python3 sites/_build.py  → escreve sites/<marca>/index.html
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
GRAD = "linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
SYM = {
"smark": '<svg viewBox="0 0 100 100" width="34" height="34"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>',
"provider-max": '<svg viewBox="0 0 100 100" width="34" height="34" style="color:#fff"><circle cx="50" cy="71" r="7" fill="currentColor"/><path d="M37 61 Q50 46 63 61" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M27 52 Q50 27 73 52" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M17 43 Q50 10 83 43" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/></svg>',
"elever-ai": '<svg viewBox="0 0 100 100" width="32" height="32"><path fill="#fff" d="M50 4 C54 34 66 46 96 50 C66 54 54 66 50 96 C46 66 34 54 4 50 C34 46 46 34 50 4 Z"/></svg>',
}
def acc(s):
    while "*" in s:
        s = s.replace("*", '<span class="v">', 1).replace("*", "</span>", 1)
    return s

CFG = {
"smark": dict(port=7001, wm='smark<span class="dot">.</span>', nav=["Método","Produtos","Cases","Sobre"],
  eye="ASSESSORIA TECNOLÓGICA",
  h1=["A GENTE FAZ A IA","TRABALHAR DE","*VERDADE.*"],
  sub="Assessoria tecnológica para crescer com eficiência e escala — sem trocar o que já funciona.",
  c1="Quero um diagnóstico", c2="Ver o método",
  hero_card='<div class="kl">O MÉTODO</div><div class="kh">3 perguntas antes de comprar IA</div>'
    + ''.join('<div class="st"><span class="num">%s</span><span>%s</span></div>'%(i,t) for i,t in
      [("1","Pra quê? ganhar mais · gastar menos"),("2","Onde? vender · entregar · administrar"),("3","Como? a IA faz e você confere")]),
  prob_h="O cemitério de projetos de IA",
  prob_b="A empresa compra a ferramenta da moda, liga no WhatsApp e espera mágica. Seis meses depois: robô parado, time ignorando, zero retorno. <b>Não é a tecnologia que falha — é a falta de método.</b>",
  sol_h="Método que faz a IA virar resultado",
  sol_cards=[("Diagnóstico","A gente acha onde a IA encaixa na sua operação — sem achismo."),
             ("Implantação","Em volta do que você já tem. Sem trocar o que funciona."),
             ("Rotina","Um número pra acompanhar. Sem número, IA é enfeite.")],
  steps=[("1","Pra quê?","Você escolhe o resultado: ganhar mais, gastar menos ou render mais."),
         ("2","Onde?","Em qual parte da empresa: vender, entregar ou administrar."),
         ("3","Como?","A IA ajuda e você decide — ou faz sozinha e você confere."),
         ("4","Rotina","Vira um número e uma reunião curta toda semana.")],
  cost_h="Sem método × Com método", cost_lt_h="Comprou a ferramenta da moda",
  cost_lt=["Robô parado em 6 meses","Time ignora","Zero retorno"],
  cost_rt_h="Entrou com a smark", cost_rt=["Método antes da ferramenta","Um número pra acompanhar","Resultado em semanas, não em PowerPoint"],
  faq=[("Vocês trocam meu sistema?","Não. A gente constrói em volta do que você já tem."),
       ("Quanto tempo até dar resultado?","Da ideia ao ar em semanas — quando pluga no que já existe, o ganho aparece rápido."),
       ("Preciso entender de IA?","Não. Você conta a dor; a gente cuida do método.")],
  cta_h="Onde a IA encaixa na sua operação?", cta_b="Quero um diagnóstico gratuito"),

"provider-max": dict(port=7002, wm='Provider <span class="v">Max</span>', nav=["O funcionário","Como funciona","Cases"],
  eye="PARA PROVEDORES DE INTERNET",
  h1=["UM FUNCIONÁRIO QUE","RENOVA SEUS","CONTRATOS *SOZINHO.*"],
  sub="Dia e noite, sem você contratar mais gente.",
  c1="Quero ver na minha base", c2="Como funciona",
  hero_card='<div class="kc"><span class="av"></span><div><div class="kt">Funcionário de IA</div><div class="ks">renovando contratos…</div></div></div>'
    + ''.join('<div class="row"><b>✓</b> %s</div>'%t for t in ["Contrato #4821 renovado","Cliente avisado no WhatsApp","Plano melhor oferecido"]),
  prob_h="O dinheiro que já é seu, parado",
  prob_b="Todo mês tem contrato vencendo, cliente quase saindo e gente que podia pagar um plano melhor. Ninguém dá conta de falar com cada um, um por um. <b>Aí o dinheiro escorre — sem você nem ver.</b>",
  sol_h="O funcionário que executa",
  sol_cards=[("Renova","Renova o contrato antes do cliente pensar em sair."),
             ("Recupera","Traz de volta quem já estava indo embora."),
             ("Oferece o plano melhor","Acha quem pode pagar mais e oferece na hora certa.")],
  steps=[("1","Conecta","No programa que você já usa pra controlar os clientes."),
         ("2","Fala","Com cada cliente, no WhatsApp, em português de gente."),
         ("3","Executa","Renova, recupera e oferece o plano melhor — sozinho."),
         ("4","Mostra","Registra tudo e te mostra o resultado.")],
  cost_h="Pelo preço de um funcionário", cost_lt_h="Contratar mais gente",
  cost_lt=["Salário + treinamento","Falta, adoece, tira férias","Dá conta de poucos por dia"],
  cost_rt_h="O funcionário de IA", cost_rt=["Dia e noite, sem folga","Não falta, não esquece","Fala com a base inteira"],
  faq=[("Funciona com o meu sistema?","Sim — conversa com o programa que você já usa."),
       ("Preciso de equipe de TI?","Não. Ele entra sem virar projeto."),
       ("Em quanto tempo vejo resultado?","Em 2 a 3 meses.")],
  cta_h="Quer ver quanto tá parado na sua base?", cta_b="Quero ver na minha base"),

"elever-ai": dict(port=7003, wm='Elever <span class="v">AI</span>', nav=["O vendedor","Como funciona","Cases"],
  eye="ATENDIMENTO 24/7 NO WHATSAPP",
  h1=["UM VENDEDOR NO","WHATSAPP QUE","*NUNCA DORME.*"],
  sub="Atende todo cliente na hora — pelo preço de um estagiário.",
  c1="Quero atender 24/7", c2="Ver na prática",
  hero_card='<div class="kd">hoje, 22:47</div>'
    + '<div class="bub in">Oi, vocês têm esse sofá em couro?</div>'
    + '<div class="bub out">Temos sim! Em 3 cores. Quer que eu separe um pra você ver amanhã?</div>'
    + '<div class="kf">respondido em 4 segundos</div>',
  prob_h="O cliente que chama 22h e some",
  prob_b="Ele manda mensagem de noite, no domingo, na madrugada. De manhã, já fechou com quem respondeu primeiro. <b>Não foi falta de cliente. Foi falta de resposta.</b>",
  sol_h="O vendedor que não dorme",
  sol_cards=[("Atende na hora","Responde todo cliente na hora, dia e noite."),
             ("Separa o joio","Vê quem é cliente de verdade e quem é só curioso."),
             ("Não esquece ninguém","Volta a falar com quem sumiu, no tempo certo.")],
  steps=[("1","O cliente chama","No WhatsApp, a qualquer hora."),
         ("2","A IA atende","Tira a dúvida e entende o que ele quer."),
         ("3","Te avisa","Quando o cliente é bom e vale sua ligação."),
         ("4","Você fecha","O trabalho chato já foi feito.")],
  cost_h="Pelo preço de um estagiário", cost_lt_h="Contratar um atendente",
  cost_lt=["Horário, folga e férias","Esquece de voltar a falar","Não dá conta da madrugada"],
  cost_rt_h="O vendedor de IA", cost_rt=["24 horas, todo dia","Não esquece nenhum cliente","Atende no segundo em que chega"],
  faq=[("É robô?","Não — conversa de verdade, como gente."),
       ("Funciona pro meu negócio?","Loja, clínica, concessionária, imobiliária — qualquer venda que passa pelo WhatsApp."),
       ("A IA fecha a venda?","Ela atende e prepara. Quem fecha é você.")],
  cta_h="Quer um vendedor que não falta?", cta_b="Quero atender 24/7"),
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
:root{--grad:__GRAD__;--ink:#100D1C;--sub:#4A4560;--bg:#F4F2FB;--card:#fff;--acc:#8B3CF7;--line:#e6e2f0}
body{background:var(--bg);color:var(--ink)}
.wrap{max-width:1180px;margin:0 auto;padding:0 32px}
.v{color:var(--acc)} .dot{color:var(--acc)}
a{color:inherit;text-decoration:none}
nav{position:sticky;top:0;z-index:10;background:rgba(244,242,251,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;justify-content:space-between;padding:18px 0}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:24px;letter-spacing:-1px}
.chip{width:46px;height:46px;border-radius:13px;background:var(--grad);display:flex;align-items:center;justify-content:center}
.links{display:flex;gap:26px;color:#5a5668;font-weight:600;font-size:15px}
.btn{background:var(--grad);color:#fff;font-weight:700;font-size:15px;padding:12px 22px;border-radius:11px;display:inline-block;cursor:pointer}
.btn.lg{font-size:18px;padding:17px 30px;border-radius:14px}
.btn.ghost{background:transparent;border:2px solid #cfc8e6;color:var(--ink)}
section{padding:90px 0}
.eye{font-weight:800;font-size:13px;letter-spacing:2px;color:var(--acc);margin-bottom:18px}
.hero{display:flex;gap:48px;align-items:center;padding:72px 0 80px}
.hero .left{flex:1}
h1{font-family:'Anton';text-transform:uppercase;font-size:76px;line-height:.96;letter-spacing:1px;margin-bottom:24px}
.lead{font-size:23px;color:var(--sub);line-height:1.45;max-width:94%;margin-bottom:32px}
.ctas{display:flex;gap:13px;flex-wrap:wrap}
.kard{width:430px;background:var(--card);border-radius:22px;padding:26px;box-shadow:0 30px 70px rgba(42,28,168,.13)}
.kl{font-size:13px;font-weight:700;color:var(--acc);letter-spacing:1px}
.kh{font-weight:800;font-size:21px;margin:6px 0 12px}
.st{display:flex;gap:12px;align-items:center;padding:12px 0;border-top:1px solid #eee;font-weight:600;font-size:15px}
.num{width:28px;height:28px;border-radius:8px;background:var(--grad);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex:0 0 auto}
.kc{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.av{width:38px;height:38px;border-radius:50%;background:var(--grad)} .kt{font-weight:700;font-size:15px}.ks{font-size:12px;color:#8a8696}
.row{background:var(--bg);border-radius:12px;padding:12px 14px;margin-bottom:8px;font-size:14px}.row b{color:var(--acc)}
.kd{font-size:12px;color:#8a8696;text-align:center;margin-bottom:10px}
.bub{border-radius:14px;padding:11px 14px;margin-bottom:8px;font-size:15px;max-width:82%}
.bub.in{background:var(--bg);border-bottom-left-radius:4px}
.bub.out{background:var(--grad);color:#fff;margin-left:auto;border-bottom-right-radius:4px}
.kf{font-size:12px;color:var(--acc);text-align:right;font-weight:700}
.sec-h{font-family:'Anton';text-transform:uppercase;font-size:46px;letter-spacing:1px;margin-bottom:14px;max-width:760px}
.prob{background:#15101f;color:#fff}
.prob .sec-h{font-size:54px} .prob p{font-size:22px;color:#cfc8e6;max-width:780px;line-height:1.5}.prob b{color:#fff}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:40px}
.c3{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px}
.c3 h3{font-size:21px;margin-bottom:8px} .c3 p{color:var(--sub);font-size:16px;line-height:1.5}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:40px}
.step .num{width:42px;height:42px;border-radius:12px;font-size:18px;margin-bottom:14px}
.step h4{font-size:19px;margin-bottom:6px}.step p{color:var(--sub);font-size:15px;line-height:1.45}
.cost{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:40px}
.ccol{border-radius:18px;padding:30px} .col.bad{background:#f0edf7;border:1px solid var(--line)}
.col.good{background:var(--grad);color:#fff}
.col h3{font-size:20px;margin-bottom:16px}.col li{list-style:none;padding:9px 0;font-size:17px;display:flex;gap:10px}
.col.bad li::before{content:"—";color:#b3aac9}.col.good li::before{content:"✓";font-weight:800}
.faq{max-width:820px;margin:40px auto 0}
.qa{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 24px;margin-bottom:12px}
.qa h4{font-size:18px;margin-bottom:6px}.qa p{color:var(--sub);font-size:16px}
.cta{background:var(--grad);color:#fff;text-align:center}
.cta h2{font-family:'Anton';text-transform:uppercase;font-size:50px;margin-bottom:26px}
footer{background:#0e0b16;color:#9a93ad;padding:46px 0;font-size:14px}
.foot-in{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.foot-in .pl{color:#fff;font-weight:700}
@media(max-width:880px){.hero{flex-direction:column}.kard{width:100%}h1{font-size:54px}.cards3,.steps,.cost{grid-template-columns:1fr}}
"""

TPL = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style></head><body>
<nav><div class="wrap nav-in">
  <div class="brand"><div class="chip">__SYM__</div>__WM__</div>
  <div class="links">__LINKS__</div>
  <a class="btn">Falar no WhatsApp</a>
</div></nav>

<header class="wrap hero">
  <div class="left">
    <div class="eye">__EYE__</div>
    <h1>__H1__</h1>
    <div class="lead">__SUB__</div>
    <div class="ctas"><a class="btn lg">__C1__</a><a class="btn lg ghost">__C2__</a></div>
  </div>
  <div class="kard">__HEROCARD__</div>
</header>

<section class="prob"><div class="wrap">
  <div class="eye">O PROBLEMA</div>
  <div class="sec-h">__PROBH__</div>
  <p>__PROBB__</p>
</div></section>

<section><div class="wrap">
  <div class="eye">O QUE A GENTE FAZ</div>
  <div class="sec-h">__SOLH__</div>
  <div class="cards3">__SOLCARDS__</div>
</div></section>

<section style="background:#fff"><div class="wrap">
  <div class="eye">COMO FUNCIONA</div>
  <div class="sec-h">Simples assim</div>
  <div class="steps">__STEPS__</div>
</div></section>

<section><div class="wrap">
  <div class="eye">A CONTA FECHA</div>
  <div class="sec-h">__COSTH__</div>
  <div class="cost">
    <div class="col bad"><h3>__COSTLTH__</h3><ul>__COSTLT__</ul></div>
    <div class="col good"><h3>__COSTRTH__</h3><ul>__COSTRT__</ul></div>
  </div>
</div></section>

<section style="background:#fff"><div class="wrap">
  <div class="eye">PERGUNTAS FREQUENTES</div>
  <div class="sec-h">Direto ao ponto</div>
  <div class="faq">__FAQ__</div>
</div></section>

<section class="cta"><div class="wrap">
  <h2>__CTAH__</h2>
  <a class="btn lg ghost" style="border-color:rgba(255,255,255,.6);color:#fff">__CTAB__</a>
</div></section>

<footer><div class="wrap foot-in">
  <div class="pl">uma plataforma smark.</div>
  <div>smarktech.com.br · @__HANDLE__</div>
</div></footer>
</body></html>"""

HANDLES = {"smark":"smark","provider-max":"providermax","elever-ai":"eleverai"}
NAMES = {"smark":"smark — assessoria tecnológica","provider-max":"Provider Max","elever-ai":"Elever AI"}

for marca, c in CFG.items():
    h1 = "<br>".join(acc(l) for l in c["h1"])
    links = "".join('<a>%s</a>'%l for l in c["nav"])
    solcards = "".join('<div class="c3"><h3>%s</h3><p>%s</p></div>'%(t,d) for t,d in c["sol_cards"])
    steps = "".join('<div class="step"><div class="num">%s</div><h4>%s</h4><p>%s</p></div>'%(n,t,d) for n,t,d in c["steps"])
    costlt = "".join('<li>%s</li>'%x for x in c["cost_lt"])
    costrt = "".join('<li>%s</li>'%x for x in c["cost_rt"])
    faq = "".join('<div class="qa"><h4>%s</h4><p>%s</p></div>'%(q,a) for q,a in c["faq"])
    html = TPL
    repl = [("__CSS__",CSS.replace("__GRAD__",GRAD)),("__TITLE__",NAMES[marca]),("__SYM__",SYM[marca]),
            ("__WM__",c["wm"]),("__LINKS__",links),("__EYE__",c["eye"]),("__H1__",h1),("__SUB__",c["sub"]),
            ("__C1__",c["c1"]),("__C2__",c["c2"]),("__HEROCARD__",c["hero_card"]),
            ("__PROBH__",c["prob_h"]),("__PROBB__",c["prob_b"]),("__SOLH__",c["sol_h"]),("__SOLCARDS__",solcards),
            ("__STEPS__",steps),("__COSTH__",c["cost_h"]),("__COSTLTH__",c["cost_lt_h"]),("__COSTLT__",costlt),
            ("__COSTRTH__",c["cost_rt_h"]),("__COSTRT__",costrt),("__FAQ__",faq),
            ("__CTAH__",c["cta_h"]),("__CTAB__",c["cta_b"]),("__HANDLE__",HANDLES[marca])]
    for k,v in repl:
        html = html.replace(k,v)
    d = os.path.join(HERE, marca); os.makedirs(d, exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(html)
    print("OK", marca, "porta", c["port"])
