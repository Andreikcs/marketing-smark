# -*- coding: utf-8 -*-
"""Home da smark (porta 7001) — direção desenhada pelo usuário, re-skin no branding smark
(claro default + faixa de dados escura, roxo, APEX, voz nova). Rodar: python3 sites/_build_smark.py"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
GRAD = "linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
APEX = '<svg viewBox="0 0 100 100" width="34" height="34"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>'
APEX_SM = '<svg viewBox="0 0 100 100" width="28" height="28"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>'

STATS = [("11%","das empresas já operam com <b>funcionários de IA</b> em produção","Deloitte","2025"),
         ("62%","estão <b>colocando</b> funcionários de IA nos processos","McKinsey","2025"),
         ("40%","<b>mais qualidade</b> nas entregas com apoio de IA","BCG + Harvard","2024")]
MODELOS = [("Elever AI","Um vendedor de IA no WhatsApp que atende seus clientes dia e noite — e nunca deixa ninguém sem resposta. Você só fecha.","Produto · vendas e atendimento"),
           ("Provider Max","Um funcionário de IA que renova os contratos dos seus clientes — sozinho, dia e noite, sem contratar mais gente.","Produto · renovação e receita")]
PERGUNTAS = [("1","Pra quê?","O resultado que você quer: ganhar mais, gastar menos ou render mais."),
             ("2","Onde?","Em qual parte da empresa: vender, entregar ou administrar."),
             ("3","Como?","A IA ajuda e você decide — ou faz sozinha e você confere.")]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
:root{--grad:__GRAD__;--ink:#100D1C;--sub:#4A4560;--bg:#F4F2FB;--card:#fff;--acc:#8B3CF7;--line:#e6e2f0}
body{background:var(--bg);color:var(--ink)}
.wrap{max-width:1180px;margin:0 auto;padding:0 32px}
.v{color:var(--acc)} .dot{color:var(--acc)}
a{color:inherit;text-decoration:none;cursor:pointer}
html{scroll-behavior:smooth}
nav{position:sticky;top:0;z-index:10;background:rgba(244,242,251,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;justify-content:space-between;padding:18px 0;position:relative}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:33px;letter-spacing:-1.5px}
.chip{width:46px;height:46px;border-radius:13px;background:var(--grad);display:flex;align-items:center;justify-content:center}
.links{display:flex;gap:30px;color:#5a5668;font-weight:600;font-size:15px;position:absolute;left:50%;transform:translateX(-50%)}
.btn{background:var(--grad);color:#fff;font-weight:700;font-size:15px;padding:12px 22px;border-radius:11px;display:inline-block}
.navitem{position:relative;display:inline-flex;align-items:center}
.svc-trigger{cursor:pointer}
.mega{position:absolute;top:100%;left:50%;transform:translateX(-50%) translateY(6px);padding-top:16px;opacity:0;visibility:hidden;transition:opacity .18s ease,transform .18s ease;z-index:60;pointer-events:none}
.navitem:hover .mega,.navitem.open .mega{opacity:1;visibility:visible;transform:translateX(-50%) translateY(0);pointer-events:auto}
.mega-card{display:flex;width:660px;background:#fff;border:1px solid #e6e2f0;border-radius:20px;box-shadow:0 30px 70px rgba(42,28,168,.20);overflow:hidden}
.mega-list{width:47%;padding:20px;border-right:1px solid #efeaf8;display:flex;flex-direction:column;gap:4px}
.mm{display:flex;align-items:center;gap:12px;font-weight:800;font-size:17px;color:#100D1C;padding:11px 12px;border-radius:12px;cursor:pointer;transition:.15s;line-height:1.2}
.mm svg{border-radius:7px;flex:0 0 auto}
.mm:hover,.mm.on{background:#f4f2fb;color:#7c3aed}
.mm-div{height:1px;background:#efeaf8;margin:6px 6px}
.mega-desc{flex:1;padding:24px 22px;display:flex;flex-direction:column;justify-content:center}
.mm-panel{display:none}.mm-panel.on{display:block}
.mm-panel h5{font-weight:800;font-size:17px;color:#100D1C;margin-bottom:10px}
.mm-panel p{color:#4A4560;font-weight:500;font-size:15px;line-height:1.55}
.mm-more{color:#7c3aed;font-weight:700;font-size:14px;display:inline-block;margin-top:14px;cursor:pointer}
.btn.lg{font-size:18px;padding:17px 30px;border-radius:14px}
.btn.ghost{background:transparent;border:2px solid #cfc8e6;color:var(--ink)}
section{padding:96px 0}
.hero{text-align:center;min-height:calc(100vh - 96px);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 0}
.pill{display:inline-block;background:#efeaf8;border:1px solid var(--line);color:var(--acc);font-weight:700;font-size:14px;padding:9px 18px;border-radius:999px;margin-bottom:30px}
h1{font-family:'Archivo';font-weight:800;text-transform:uppercase;font-size:50px;line-height:1.06;letter-spacing:-1.5px;margin:0 auto 22px;max-width:1060px;white-space:nowrap}
@media(max-width:1100px){h1{font-size:46px}}
.lead{font-size:24px;color:var(--sub);line-height:1.45;max-width:760px;margin:0 auto 36px}
.lead .rot{position:relative;display:inline-grid;vertical-align:bottom;text-align:left}
.lead .rot>span{grid-area:1/1;color:var(--acc);font-weight:800;white-space:nowrap;opacity:0;animation:rot 9s infinite}
.lead .rot>span:nth-child(2){animation-delay:3s}
.lead .rot>span:nth-child(3){animation-delay:6s}
@keyframes rot{0%{opacity:0;transform:translateY(10px)}3.5%{opacity:1;transform:translateY(0)}30%{opacity:1;transform:translateY(0)}34%{opacity:0;transform:translateY(-10px)}100%{opacity:0}}
.logo-inline{display:inline-flex;align-items:center;gap:9px;font-weight:800;letter-spacing:-1px;vertical-align:middle}
.lchip{width:40px;height:40px;border-radius:11px;background:var(--grad);display:inline-flex;align-items:center;justify-content:center}
.wmlogo{font-weight:800;letter-spacing:-1px;color:var(--ink)}
.ctas{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.band{background:var(--card);border-top:1px solid var(--line);border-bottom:1px solid var(--line);text-align:center;padding:64px 0}
.band p{font-size:34px;font-weight:700;line-height:1.3;max-width:820px;margin:0 auto}
.dark{background:#15101f;color:#fff}
.dark .pill{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.14);color:#c9b8ff}
.eye{font-weight:800;font-size:13px;letter-spacing:2px;color:var(--acc);margin-bottom:16px}
.sec-h{font-family:'Anton';text-transform:uppercase;font-size:50px;letter-spacing:1px;text-align:center;max-width:840px;margin:0 auto 12px}
.sec-s{text-align:center;color:var(--sub);font-size:20px;margin-bottom:46px}
.dark .sec-s{color:#b9aee0}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:48px}
.stat{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.10);border-radius:20px;padding:34px}
.stat .big{font-family:'Anton';font-size:74px;line-height:1;color:#fff;margin-bottom:16px}
.stat .big .v{color:#A472FF}
.stat p{color:#c9c2dd;font-size:18px;line-height:1.4}.stat b{color:#fff}
.src{margin-top:22px;display:flex;gap:10px;align-items:center;font-size:13px;color:#9a93ad}
.src .yr{background:rgba(164,114,255,.16);color:#c9b8ff;border-radius:8px;padding:3px 9px;font-weight:700}
.mods{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:46px}
.mod{background:var(--card);border:1px solid var(--line);border-radius:22px;overflow:hidden}
.mod .top{height:150px;background:var(--grad);position:relative}
.mod .top .ic{position:absolute;left:28px;bottom:-26px;width:60px;height:60px;border-radius:16px;background:#fff;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:28px}
.mod .bd{padding:42px 30px 30px}
.mod .tag{font-size:13px;font-weight:700;color:var(--acc);letter-spacing:1px}
.mod h3{font-size:26px;margin:6px 0 10px}.mod p{color:var(--sub);font-size:17px;line-height:1.5;margin-bottom:18px}
.mod .more{font-weight:800;color:var(--acc)}
.mod.pro .top{height:130px}
.pro-head{position:relative;z-index:2;margin:-40px 24px 0;display:inline-flex;align-items:center;gap:13px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:9px 20px 9px 9px}
.pro-head svg{border-radius:13px;flex:0 0 auto}
.pro-name{font-weight:800;font-size:23px;color:#100D1C;letter-spacing:-.5px}
.mod.pro .bd{padding:20px 30px 30px}
.ptags{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:18px 0 22px}
.ptag-lbl{font-weight:800;color:#6B6680;font-size:13.5px;margin-right:4px}
.ptag{background:#f4f2fb;border:1px solid #e6e2f0;color:#5a3a9c;font-weight:700;font-size:13px;padding:7px 13px;border-radius:999px;white-space:nowrap}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:46px}
.step{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px}
.step .num{width:44px;height:44px;border-radius:12px;background:var(--grad);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:19px;margin-bottom:14px}
.step h4{font-size:21px;margin-bottom:6px}.step p{color:var(--sub);font-size:16px;line-height:1.45}
.cta{background:var(--grad);color:#fff;text-align:center}
.cta h2{font-family:'Anton';text-transform:uppercase;font-size:54px;margin-bottom:26px}
footer{background:#0e0b16;color:#9a93ad;padding:46px 0;font-size:14px}
.foot-in{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}.foot-in .pl{color:#fff;font-weight:700}
.obj{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.ocard{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:26px;box-shadow:0 12px 36px rgba(42,28,168,.06);display:flex;flex-direction:column}
.ocard.wide{grid-column:span 3;flex-direction:row;align-items:center;gap:30px;background:linear-gradient(120deg,#fff,#f3eefc)}
.ocard .lab{color:var(--acc);font-weight:800;font-size:13px;letter-spacing:1.5px}
.ocard h3{font-size:23px;font-weight:800;margin:6px 0 14px;line-height:1.15}
.ocard .b{display:flex;gap:9px;font-size:15px;color:#3a3450;margin-bottom:9px;line-height:1.35}.ocard .b .ck{color:var(--acc);font-weight:800}
.ocard .ft{margin-top:auto;padding-top:14px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #efeaf8}
.who{font-size:13px;color:#6B6680;font-weight:600}.pv{background:#efeaf8;color:var(--acc);font-weight:700;font-size:13px;padding:5px 12px;border-radius:999px;white-space:nowrap}
.ocard.wide .ft{border:none;padding:0;flex-direction:column;align-items:flex-end;gap:8px}.ocard.wide h3{margin:0}.ocard.wide .mid{flex:1}
.carwrap{position:relative;margin-top:18px;overflow:hidden;border-radius:24px}
.cartrack{display:flex;transition:transform .6s cubic-bezier(.6,.05,.2,1)}
.slide{min-width:100%;display:flex;gap:44px;align-items:center;padding:14px 8px}
.slide .sl{flex:1}
.persona{display:flex;flex-direction:column;justify-content:center}
.phead{display:flex;align-items:center;gap:16px;margin-bottom:24px}
.pav{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:26px;color:#c9a4ff;flex:0 0 auto;background:#241a40}
.pav.hi{background:linear-gradient(155deg,#9A4DFF,#2A1CA8);color:#fff}
.pname{font-weight:800;font-size:28px;color:#100D1C;line-height:1.1;letter-spacing:-.5px}
.prole{color:#6B6680;font-size:16px;margin-top:3px}
.pfunc-lbl{color:#8a83a0;font-size:14px}
.pfunc{font-weight:800;font-size:20px;color:#100D1C;margin:3px 0 18px}
.pjargao{color:var(--acc);font-style:italic;font-weight:700;font-size:21px;margin-bottom:18px}
.pbio{color:#4A4560;font-size:17px;line-height:1.55}
.slide .role{color:var(--acc);font-weight:800;font-size:15px;letter-spacing:.5px;margin-bottom:6px}
.slide h3{font-size:38px;font-weight:800;letter-spacing:-1px;line-height:1.06;margin-bottom:14px}
.slide .sd{font-size:19px;color:var(--sub);margin-bottom:20px;line-height:1.4}
.slide .b{display:flex;gap:10px;font-size:16px;color:#241f33;margin-bottom:11px}.slide .b .ck{color:var(--acc);font-weight:800}
.slide-ft{display:flex;justify-content:space-between;align-items:center;margin-top:18px;padding-top:14px;border-top:1px solid #ddd5f0;max-width:560px}
.slide-ft .who{font-size:14px;color:#6B6680;font-weight:600}.slide-ft .pv{background:#fff;color:var(--acc);font-weight:700;font-size:14px;padding:6px 14px;border-radius:999px}
.panel{width:520px;background:#14101e;border-radius:22px;padding:26px;color:#fff;min-height:360px;display:flex;flex-direction:column;box-shadow:0 30px 70px rgba(20,12,40,.28)}
.charwrap{width:520px;display:flex;align-items:center;justify-content:center}
.char{width:460px;height:460px;object-fit:contain;mix-blend-mode:multiply}
.dots3{margin-bottom:14px}.dots3 i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px}
.pl{color:#9a93ad;font-size:12px;font-weight:700;letter-spacing:1.5px;margin-bottom:14px}
.carnav{display:flex;align-items:center;justify-content:center;gap:18px;margin-top:28px}
.cardots{display:flex;gap:9px}.cardots b{width:9px;height:9px;border-radius:50%;background:#d3cce6;cursor:pointer;transition:.3s}.cardots b.on{width:26px;border-radius:6px;background:var(--acc)}
.arrowbtn{width:46px;height:46px;border-radius:50%;border:1px solid var(--line);background:#fff;color:var(--ink);font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center}
@media(max-width:880px){h1{font-size:34px;white-space:normal}.stats,.mods,.steps,.obj{grid-template-columns:1fr}.band p{font-size:26px}.slide{flex-direction:column}.panel,.charwrap{width:100%}.char{width:100%;height:auto}}
"""

stats_html = "".join(
  '<div class="stat"><div class="big"><span class="v">%s</span></div><p>%s</p><div class="src">%s<span class="yr">%s</span></div></div>'%(n,d,s,y)
  for n,d,s,y in STATS)
def _prodicon(kind, ids, box):
    gid=kind+ids
    grad='<linearGradient id="'+gid+'" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9A4DFF"/><stop offset="1" stop-color="#2A1CA8"/></linearGradient>'
    if kind=='ele':
        sym='<g transform="scale(0.76)"><path fill="#fff" d="M50 4 C54 34 66 46 96 50 C66 54 54 66 50 96 C46 66 34 54 4 50 C34 46 46 34 50 4 Z"/></g>'
    else:
        sym='<g transform="scale(0.76)" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"><circle cx="50" cy="71" r="7" fill="#fff" stroke="none"/><path d="M37 61 Q50 46 63 61"/><path d="M27 52 Q50 27 73 52"/><path d="M17 43 Q50 10 83 43"/></g>'
    return '<svg width="'+str(box)+'" height="'+str(box)+'" viewBox="0 0 76 76" style="display:block"><defs>'+grad+'</defs><rect width="76" height="76" rx="18" fill="url(#'+gid+')"/>'+sym+'</svg>'
# versão simplificada (só 7009) — linguagem mais direta/curta
MODELOS_V2 = [("Elever AI","Responde todo cliente no WhatsApp, dia e noite. Ninguém fica sem resposta — e você só fecha.","Vende e atende no WhatsApp"),
              ("Provider Max","Chama seus clientes e renova os contratos sozinho, dia e noite. Sem precisar de mais gente.","Renova contratos sozinho")]
def _build_mods(modelos):
    return "".join(
      '<div class="mod"><div class="top"><div class="ic">%s</div></div><div class="bd"><div class="tag">%s</div><h3>%s</h3><p>%s</p><a class="more">Saiba mais →</a></div></div>'%(ic,tag,t,d)
      for (t,d,tag),ic in zip(modelos,[_prodicon('ele','c',42),_prodicon('pm','c',42)]))
mods_html = _build_mods(MODELOS)
mods_html_v2 = _build_mods(MODELOS_V2)
# NOVO layout de card de produto (7001): ícone+nome juntos, eyebrow, descrição e tags de segmento
PRODS = [
  ('ele','Elever AI','CRM com IA + Funcionário de WhatsApp integrado','Atende 24/7 no WhatsApp, filtra e anota no CRM. Atende todos, anota tudo.','Ideal para:',['Loja de móveis','Automobilístico','Serviços e consultorias','Mentorias e educação empresarial']),
  ('pm','Provider Max','Plataforma de inteligência comercial','Chama seus clientes, faz upgrades de plano e renova contratos. Sem precisar de mais gente.','Exclusivo para:',['Provedores de internet']),
]
def _build_prodcards(prods):
    out=''
    for kind,name,eye,desc,lbl,tags in prods:
        tg='<span class="ptag-lbl">'+lbl+'</span>'+''.join('<span class="ptag">'+t+'</span>' for t in tags)
        out+=('<div class="mod pro"><div class="top"></div>'
          '<div class="pro-head">'+_prodicon(kind,'pc',52)+'<span class="pro-name">'+name+'</span></div>'
          '<div class="bd"><div class="tag">'+eye+'</div><p>'+desc+'</p>'
          '<div class="ptags">'+tg+'</div><a class="more">Saiba mais →</a></div></div>')
    return out
prodcards_html = _build_prodcards(PRODS)
PASSOS = [("A","Avaliação","Avaliamos junto com você o seu caso."),("P","Planejamento","Planejamos a solução sob medida para você aprovar."),("I","Implantação","Iniciamos a execução do projeto conforme definido."),("S","Solução","Solução personalizada e entregue.")]
steps_html = "".join('<div class="step"><div class="num">%s</div><h4>%s</h4><p>%s</p></div>'%(n,t,d) for n,t,d in PASSOS)

# ---- seção "Por onde você quer começar?" (objetivos) ----
OBJ=[
 ("PRA DAR CONTA","Para times comerciais que buscam melhorar a eficiência comercial e escalar suas operações",["Processo de pré-vendas para o seu caso","Funções completas de SDR de pré-vendas","Atende todos os seus contatos em qualquer dia ou horário","Faz follow-up, não esquece de nenhum lead","Preenche o CRM automaticamente"],"","23 prontos por dia",False),
 ("PRA TRAZER MAIS","Para times comerciais que querem mais volume e velocidade",["Funções completas de profissional BDR","Processo de prospecção ativa para o seu caso","Busca, analisa, prioriza e registra no CRM","Lead score e anotações comerciais","Painel completo de controle e indicadores"],"","64 novos por mês",False),
 ("PRA RENDER MAIS","Para times de relacionamento e receita que buscam fidelizar clientes",["Recupera base de contatos esquecida","Recupera, renova e fideliza receita de contratos","Funções de Customer Success e relacionamento","Painel de indicadores que mostram oportunidades de receita parada na base de clientes"],"","R$ 84k de volta",False),
 ("DO SEU JEITO","Sua necessidade é diferente",["A smark faz um diagnóstico grátis, estuda o seu caso e monta o funcionário sob medida pra você."],"","diagnóstico grátis",True),
]
def _ob(o):
    rot,dor,its,quem,prova,wide=o
    b="".join('<div class="b"><span class="ck">✓</span>%s</div>'%t for t in its)
    if wide:
        return '<div class="ocard wide"><div class="mid"><div class="lab">%s</div><h3>%s</h3>%s</div><div class="ft"><span class="who">%s</span><span class="pv">%s</span></div></div>'%(rot,dor,b,quem,prova)
    return '<div class="ocard"><div class="lab">%s</div><h3>%s</h3>%s<div class="ft"><span class="who">%s</span><span class="pv">%s</span></div></div>'%(rot,dor,b,quem,prova)
obj_html="".join(_ob(o) for o in OBJ)

# ---- carrossel de funcionários (com painel-prova) ----
def _bar(l,v,p,hi=False):
    col="#A472FF" if hi else "#3a3358"; tv="#A472FF" if hi else "#cfc8e6"
    return '<div style="margin-bottom:13px"><div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px"><span style="color:#c9c2dd">%s</span><span style="color:%s;font-weight:700">%s</span></div><div style="height:11px;border-radius:6px;background:#221c33"><div style="height:11px;border-radius:6px;width:%d%%;background:%s"></div></div></div>'%(l,tv,v,p,col)
def _trio(items):
    c="".join('<div style="flex:1;background:#1c1730;border:1px solid #2a2440;border-radius:13px;padding:14px 12px;text-align:center"><div style="font-size:25px;font-weight:800;color:%s">%s</div><div style="font-size:11px;color:#9a93ad;margin-top:3px">%s</div></div>'%(c2,v,l) for v,l,c2 in items)
    return '<div style="display:flex;gap:10px;margin:4px 0 16px">%s</div>'%c
def _bub(side,txt,tag=""):
    if side=="in":
        return '<div style="background:#221c33;color:#e8e4f2;border-radius:13px 13px 13px 4px;padding:10px 13px;font-size:14px;max-width:80%;margin-bottom:8px">'+txt+'</div>'
    t=('<span style="background:#1e3a2a;color:#69d49a;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px">'+tag+'</span>') if tag else ''
    return '<div style="background:'+GRAD+';color:#fff;border-radius:13px 13px 4px 13px;padding:10px 13px;font-size:14px;max-width:82%;margin-left:auto;margin-bottom:8px">'+txt+t+'</div>'
def _ins(t): return '<div style="margin-top:auto;padding-top:14px;border-top:1px solid #241e36;color:#c9c2dd;font-size:13px">💡 %s</div>'%t
PAN={
 "atend":'<div class="pl">FUNIL DE QUALIFICAÇÃO</div>'+_bar("Chegaram","148",100)+_bar("Qualificados","89",60)+_bar("Prontos pra fechar","23",16,True)+_ins("só os 23 prontos vão pro seu vendedor"),
 "cacador":'<div class="pl">PROSPECÇÃO ATIVA</div>'+_trio([("210","procurados","#fff"),("64","com fit","#A472FF"),("7,8","nota média","#fff")])+_bub("in","Empresa X — cresceu 30% este ano")+_bub("out","Tem cara de fechar. Registrado pro time.","registrado"),
 "olheiro":'<div class="pl">CAMPANHAS — O QUE RENDE</div>'+_bar("Anúncio A · R$ 18 por cliente","ótimo",92,True)+_bar("Anúncio B · R$ 41 por cliente","ok",48)+_bar("Anúncio C · R$ 96 por cliente","ruim",20)+_ins("o A traz 3× mais cliente bom — invista mais nele"),
 "mensageiro":'<div class="pl">OFERTA NO WHATSAPP</div>'+_trio([("1.200","mensagens","#fff"),("180","responderam","#fff"),("47","quentes","#A472FF")])+_bub("out","Oi! Rolando uma condição especial essa semana 👀")+_bub("in","Tenho interesse!","quente"),
 "renov":'<div class="pl">RENOVAÇÕES</div>'+_trio([("124","vencendo em 30d","#fff"),("38","renovados","#A472FF"),("51","em conversa","#fff")])+_bub("out","Oi! Seu plano vence em 5 dias. Renovo com a mesma condição?")+_bub("in","Pode sim, obrigado!","renovado ✓"),
 "garimpeiro":'<div class="pl">DINHEIRO PARADO NA BASE</div>'+_trio([("22","reativados","#A472FF"),("17","subiram de plano","#fff"),("R$84k","de volta","#A472FF")])+_bar("Clientes parados há +90 dias","chamando de volta",70,True)+_ins("o dinheiro já estava na base — faltava quem fosse atrás"),
}
# painel do método (3 perguntas) e painel dos dados de mercado
_metodo_rows="".join('<div style="display:flex;gap:12px;padding:11px 0;border-top:1px solid #241e36"><span style="width:28px;height:28px;border-radius:8px;background:'+GRAD+';color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex:0 0 auto">'+n+'</span><div><div style="font-weight:700;font-size:15px;color:#fff">'+t+'</div><div style="font-size:13px;color:#9a93ad">'+d+'</div></div></div>' for n,t,d in PERGUNTAS)
PAN["metodo"]='<div class="pl">ANTES DE COMPRAR IA</div>'+_metodo_rows+_ins("sem método, IA vira robô parado")
_stats_rows="".join('<div style="display:flex;align-items:baseline;gap:16px;padding:14px 0;border-top:1px solid #241e36"><span style="font-weight:800;font-size:42px;color:#A472FF;line-height:1;letter-spacing:-1px">'+n+'</span><div style="font-size:14px;color:#c9c2dd;line-height:1.35">'+d+'<div style="color:#8a83a0;font-size:12px;margin-top:3px">'+s+' · '+y+'</div></div></div>' for n,d,s,y in STATS)
PAN["dados"]='<div class="pl">DADOS DE MERCADO</div>'+_stats_rows

# ===== PAINÉIS V2 (mais visuais/profissionais) — usados só no smark-v2 (7009) =====
_C=263.9  # circunferência de r=42
def _ring(pct,big,color="#A472FF",sz=104):
    dash=round(_C*pct/100.0,1); rest=round(_C-dash,1)
    return ('<svg viewBox="0 0 100 100" width="'+str(sz)+'" height="'+str(sz)+'">'
            '<circle cx="50" cy="50" r="42" fill="none" stroke="#241e36" stroke-width="9"/>'
            '<circle cx="50" cy="50" r="42" fill="none" stroke="'+color+'" stroke-width="9" stroke-linecap="round" stroke-dasharray="'+str(dash)+' '+str(rest)+'" transform="rotate(-90 50 50)"/>'
            '<text x="50" y="57" text-anchor="middle" font-size="25" font-weight="800" fill="#fff" font-family="Archivo, sans-serif">'+big+'</text></svg>')
def _tile(big,sub,delta="",color="#fff"):
    dl=('<div style="color:#69d49a;font-size:12px;font-weight:700;margin-top:3px">&#9650; '+delta+'</div>') if delta else ''
    return '<div style="flex:1;background:#1c1730;border:1px solid #2a2440;border-radius:14px;padding:15px 10px;text-align:center"><div style="font-size:29px;font-weight:800;color:'+color+';line-height:1">'+big+'</div><div style="font-size:11px;color:#9a93ad;margin-top:4px">'+sub+'</div>'+dl+'</div>'
def _tiles(items):
    return '<div style="display:flex;gap:10px;margin:6px 0 16px">'+"".join(_tile(*it) for it in items)+'</div>'
def _funnelbar(label,val,pct,hi=False):
    bg='linear-gradient(90deg,#9A4DFF,#6d28d9)' if hi else '#241e36'
    glow='box-shadow:0 0 24px rgba(139,60,247,.45);' if hi else ''
    return '<div style="margin:0 auto 8px;width:'+str(pct)+'%;min-width:165px;background:'+bg+';border-radius:11px;padding:13px 18px;display:flex;justify-content:space-between;align-items:center;'+glow+'"><span style="font-size:14px;color:#e8e4f2;font-weight:600">'+label+'</span><span style="font-size:21px;font-weight:800;color:#fff">'+val+'</span></div>'
def _conv(t):
    return '<div style="text-align:center;color:#8a83a0;font-size:12px;margin-bottom:7px">&#8595; '+t+'</div>'
def _barchart(vals):
    return '<div style="display:flex;align-items:flex-end;gap:7px;height:60px;margin:2px 0 14px">'+"".join('<div style="flex:1;height:'+str(v)+'%;background:linear-gradient(180deg,#A472FF,#5b21b6);border-radius:5px 5px 2px 2px"></div>' for v in vals)+'</div>'
def _area():
    return ('<svg viewBox="0 0 200 60" width="100%" height="56" preserveAspectRatio="none" style="margin:4px 0 0">'
            '<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A472FF" stop-opacity=".45"/><stop offset="1" stop-color="#A472FF" stop-opacity="0"/></linearGradient></defs>'
            '<path d="M0,48 L34,44 L68,38 L102,27 L140,19 L200,6 L200,60 L0,60 Z" fill="url(#ar)"/>'
            '<path d="M0,48 L34,44 L68,38 L102,27 L140,19 L200,6" fill="none" stroke="#A472FF" stroke-width="2.5" stroke-linecap="round"/></svg>')
def _step(n,t,d,last=False):
    line='' if last else '<div style="position:absolute;left:18px;top:40px;bottom:2px;width:2px;background:#2a2440"></div>'
    return '<div style="position:relative;display:flex;gap:14px;padding-bottom:18px">'+line+'<div style="width:38px;height:38px;border-radius:11px;background:'+GRAD+';color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;flex:0 0 auto;position:relative;z-index:1">'+n+'</div><div><div style="font-weight:800;font-size:16px;color:#fff">'+t+'</div><div style="font-size:13px;color:#9a93ad;line-height:1.4">'+d+'</div></div></div>'
def _foot(txt,badge):
    return '<div style="margin-top:auto;padding-top:14px;border-top:1px solid #241e36;display:flex;justify-content:space-between;align-items:center;gap:10px"><span style="color:#c9c2dd;font-size:13px">'+txt+'</span><span style="background:rgba(164,114,255,.18);color:#c9b8ff;font-weight:700;font-size:13px;padding:5px 12px;border-radius:999px;white-space:nowrap">'+badge+'</span></div>'

def _funnel():
    cx=180.0
    def hw(v): return 42+128*(v/148.0)   # meia-largura por valor
    h1,h2,h3=hw(148),hw(89),hw(23); sp=44.0
    def band(yt,yb,wt,wb,fill,flt=""):
        p=('<path d="M'+str(round(cx-wt,1))+','+str(yt)+' L'+str(round(cx+wt,1))+','+str(yt)
           +' L'+str(round(cx+wb,1))+','+str(yb)+' L'+str(round(cx-wb,1))+','+str(yb)+' Z" fill="'+fill+'"/>')
        return ('<g filter="url(#fglow)">'+p+'</g>') if flt else p
    def tx(y,t,sz,fill,wt="800"):
        return '<text x="180" y="'+str(y)+'" text-anchor="middle" font-family="Archivo, sans-serif" font-weight="'+wt+'" font-size="'+str(sz)+'" fill="'+fill+'">'+t+'</text>'
    def cv(y,t):
        return ('<text x="332" y="'+str(y)+'" text-anchor="end" font-family="Archivo, sans-serif" font-weight="700" font-size="12.5" fill="#9a93ad">'+t+'</text>')
    return ('<svg viewBox="0 0 360 232" width="100%" style="display:block;margin:6px 0 4px">'
      '<defs>'
      '<linearGradient id="fa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#352e63"/><stop offset="1" stop-color="#463a8c"/></linearGradient>'
      '<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5837a6"/><stop offset="1" stop-color="#6d28d9"/></linearGradient>'
      '<linearGradient id="fc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9047f5"/><stop offset="1" stop-color="#b873ff"/></linearGradient>'
      '<filter id="fglow" x="-60%" y="-60%" width="220%" height="220%"><feDropShadow dx="0" dy="0" stdDeviation="8" flood-color="#9333ea" flood-opacity="0.6"/></filter>'
      '</defs>'
      +band(8,78,h1,h2,'url(#fa)')
      +band(86,156,h2,h3,'url(#fb)')
      +band(164,226,h3,sp,'url(#fc)','glow')
      +tx(40,'148',26,'#fff')+tx(60,'Chegaram',12.5,'#cdc5e4','600')
      +tx(118,'89',26,'#fff')+tx(138,'Qualificados',12.5,'#e1d6f6','600')
      +tx(197,'23',25,'#fff')+tx(216,'Prontos',12.5,'#f1ebff','600')
      +cv(86,'↓ 60%')+cv(164,'↓ 26%')
      +'</svg>')

# ===== 3 ESTILOS de comparativo (avaliação no 7009 — 1 por card) =====
def _circ(ok):
    if ok: return '<span style="width:23px;height:23px;border-radius:50%;background:#8B3CF7;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex:0 0 auto;box-shadow:0 0 12px rgba(139,60,247,.5)">✓</span>'
    return '<span style="width:23px;height:23px;border-radius:50%;background:#332d47;color:#8f88a3;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex:0 0 auto">✕</span>'
# A — Antes / Depois em 2 colunas (estilo do exemplo)
def _cmpA(before,after,comlbl="Com funcionário de IA"):
    def it(t,ok): return '<div style="display:flex;gap:11px;align-items:center;margin-bottom:14px">'+_circ(ok)+'<span style="font-size:13.5px;color:'+('#eceafc' if ok else '#8f88a3')+';line-height:1.3">'+t+'</span></div>'
    L='<div style="background:#191524;border:1px solid #241e36;border-radius:16px;padding:18px 16px 6px"><div style="font-weight:800;font-size:14px;color:#8f88a3;margin-bottom:16px">Sem funcionário de IA</div>'+"".join(it(t,False) for t in before)+'</div>'
    R='<div style="background:linear-gradient(160deg,rgba(124,58,237,.20),rgba(124,58,237,.05));border:1.5px solid rgba(139,60,247,.55);border-radius:16px;padding:18px 16px 6px;box-shadow:0 0 30px rgba(139,60,247,.14)"><div style="font-weight:800;font-size:14px;color:#fff;margin-bottom:16px">'+comlbl+'</div>'+"".join(it(t,True) for t in after)+'</div>'
    return '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:2px">'+L+R+'</div>'
# B — transformação "de → para" em linha
def _cmpB(rows):
    head='<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px"><span style="font-weight:800;font-size:13px;color:#8f88a3">Uma pessoa</span><span style="color:#a472ff;font-size:15px;font-weight:800">→</span><span style="font-weight:800;font-size:13px;color:#fff;background:linear-gradient(135deg,#7c3aed,#9333ea);padding:5px 13px;border-radius:999px">Funcionário de IA</span></div>'
    body="".join('<div style="display:flex;align-items:center;gap:12px;padding:11px 0;border-top:1px solid #241e36"><span style="flex:1;font-size:13px;color:#8a83a0">'+b+'</span><span style="color:#a472ff;font-size:17px;font-weight:800">→</span><span style="flex:1.05;font-size:13.5px;color:#eceafc;font-weight:700">'+a+'</span></div>' for b,a in rows)
    return head+body
# C — custo em destaque + benefícios
def _cmpC(chips):
    hero=('<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:2px 0 14px">'
      '<div style="background:#191524;border:1px solid #241e36;border-radius:16px;padding:18px 12px;text-align:center"><div style="font-size:12px;color:#8f88a3;font-weight:700;margin-bottom:8px">Uma pessoa</div><div style="font-size:29px;font-weight:800;color:#8f88a3;text-decoration:line-through;text-decoration-color:#e0645f">R$ 5 mil</div><div style="font-size:12px;color:#6b6480;margin-top:6px">/mês + encargos</div></div>'
      '<div style="background:linear-gradient(160deg,rgba(124,58,237,.22),rgba(124,58,237,.05));border:1.5px solid rgba(139,60,247,.55);border-radius:16px;padding:18px 12px;text-align:center;box-shadow:0 0 30px rgba(139,60,247,.14)"><div style="font-size:12px;color:#c9b8ff;font-weight:700;margin-bottom:8px">Funcionário de IA</div><div style="font-size:29px;font-weight:800;color:#fff">uma fração</div><div style="font-size:12px;color:#c9b8ff;margin-top:6px">sem encargos</div></div>'
      '</div>')
    ch="".join('<span style="background:rgba(124,58,237,.13);border:1px solid rgba(139,60,247,.34);color:#eceafc;font-size:12.5px;font-weight:600;padding:8px 13px;border-radius:999px"><b style="color:#a472ff">✓</b> '+c+'</span>' for c in chips)
    return hero+'<div style="display:flex;flex-wrap:wrap;gap:9px">'+ch+'</div>'

# tagline de 4 tempos (destaque em roxo)
def _tag(parts):
    seg="".join(('<span style="color:#c9a4ff">'+t+'</span>' if hi else t) for t,hi in parts)
    return '<div style="margin-top:auto;padding-top:16px;border-top:1px solid #241e36;font-size:16px;font-weight:800;color:#fff;line-height:1.45;letter-spacing:-.2px">'+seg+'</div>'

PAN2={}
# Versão A (Antes/Depois) padronizada · dados de salário reais (pesquisa 2025/26) · 4 itens: salário, disponibilidade, volume, eficiência
PAN2["atend"]=(_cmpA(
    ["Salário de SDR: R$ 3 mil/mês + encargos","Atende só em horário comercial","Dá conta de ~50 leads por dia","Esquece o follow-up quando lota"],
    ["Custa uma fração, sem encargos","Atende 24/7, todo dia e feriado","Fala com centenas ao mesmo tempo","Nunca esquece — registra no CRM"],"Com a Nina no seu time")
  +_tag([("Atenda ",0),("5x mais leads",1),(". Com ",0),("3x menos custo",1),(". Em tempo real. Sem esforço.",0)]))
PAN2["cacador"]=(_cmpA(
    ["Salário de BDR: R$ 4,5 mil/mês + comissão","Prospecta só em horário comercial","Aborda ~30 empresas por dia","Ritmo irregular, esquece de anotar"],
    ["Custa uma fração, sem comissão","Prospecta 24/7, sem parar","Busca e qualifica centenas por dia","Ritmo constante, registra no CRM"],"Com o Téo no seu time")
  +_tag([("Prospecte ",0),("5x mais",1),(". Com ",0),("3x menos custo",1),(". Em menos tempo. Sem esforço.",0)]))
PAN2["garimpeiro"]=(_cmpA(
    ["Salário de CS: R$ 3 mil/mês + encargos","Age só em horário comercial","Acompanha só parte da base","Foca no urgente, esquece o parado"],
    ["Custa uma fração, sem encargos","Age 24/7, na hora certa","Varre a base inteira, sem exceção","Acha todo dinheiro parado e vai atrás"],"Com a Clara no seu time")
  +_tag([("Recupere ",0),("5x mais receita",1),(". Com ",0),("3x menos custo",1),(". Sem deixar na mesa. Sem esforço.",0)]))
PAN2["metodo"]=('<div class="pl">ANTES DE COMPRAR IA</div>'
  +_step("1","Pra quê?","Ganhar mais, gastar menos ou render mais.")
  +_step("2","Onde?","Vender, entregar ou administrar.")
  +_step("3","Como?","A IA ajuda e você decide — ou faz e você confere.",True)
  +_foot("💡 sem método, IA vira robô parado","diagnóstico · 30 min"))
def _datarow(pct,d,s,y,color="#A472FF"):
    return '<div style="display:flex;align-items:center;gap:18px;padding:11px 0;border-top:1px solid #241e36">'+_ring(pct,str(pct)+'%',color,86)+'<div style="font-size:14px;color:#c9c2dd;line-height:1.35">'+d+'<div style="color:#8a83a0;font-size:12px;margin-top:3px">'+s+' · '+y+'</div></div></div>'
PAN2["dados"]=('<div class="pl">DADOS DE MERCADO</div>'
  +_datarow(11,STATS[0][1],STATS[0][2],STATS[0][3])
  +_datarow(62,STATS[1][1],STATS[1][2],STATS[1][3])
  +_datarow(40,STATS[2][1],STATS[2][2],STATS[2][3]))

PANMAP=["atend","cacador","garimpeiro","metodo"]  # objetivo -> painel
def _cslide(label,head,bs,quem,prova,pk,desc="",pan=None):
    pan=pan if pan is not None else PAN
    b="".join('<div class="b"><span class="ck">✓</span>'+x+'</div>' for x in bs)
    sd='<div class="sd">'+desc+'</div>' if desc else ''
    ft='<div class="slide-ft"><span class="who">'+quem+'</span><span class="pv">'+prova+'</span></div>' if (quem or prova) else ''
    right='<div class="panel"><div class="dots3"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>'+pan[pk]+'</div>'
    return '<div class="slide"><div class="sl"><div class="role">'+label+'</div><h3>'+head+'</h3>'+sd+b+ft+'</div>'+right+'</div>'
_DESC="Não é tendência — é como milhares de empresas já operam e estão resolvendo problemas de pessoas, eficiência e escala."
def _build_slides(pan):
    return "".join(_cslide(rot,dor,its,quem,prova,PANMAP[i],pan=pan) for i,(rot,dor,its,quem,prova,wide) in enumerate(OBJ))
slides_html=_build_slides(PAN2)     # 7001 — painéis novos (comparativo Versão A)
slides_html_v2=_build_slides(PAN2)  # 7009 — painéis novos (melhorados)
cardots_html="".join(('<b class="on"></b>' if k==0 else '<b></b>') for k in range(len(OBJ)))

PAGE = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>smark — assessoria tecnológica</title>
<style>__CSS____V2CSS__</style></head><body class="__BODYCLASS__">
<nav><div class="wrap nav-in">
  <div class="brand"><span class="wm">smark<span class="dot">.</span></span></div>
  <div class="links"><span class="navitem" id="svcitem"><a class="svc-trigger">Serviços</a><div class="mega"><div class="mega-card"><div class="mega-list"><a class="mm on" data-k="func" onmouseover="mmShow(this)">Funcionários de IA</a><a class="mm" data-k="asse" onmouseover="mmShow(this)">Assessoria tecnológica</a><div class="mm-div"></div><a class="mm" data-k="parc" onmouseover="mmShow(this)">Parceiros</a></div><div class="mega-desc"><div class="mm-panel on" data-k="func"><h5>Funcionários de IA</h5><p>Funcionários de IA de nível sênior com salário de estagiário — que executam tarefas pontuais, processos completos ou funções inteiras.</p><a class="mm-more" href="#funcionarios" onclick="mmClose()">Saiba mais →</a></div><div class="mm-panel" data-k="asse"><h5>Assessoria tecnológica</h5><p>Nosso time de consultores e engenheiros de IA trabalha com você na construção de projetos personalizados.</p><a class="mm-more" href="#assessoria" onclick="mmClose()">Saiba mais →</a></div><div class="mm-panel" data-k="parc"><h5>Programa de parceiros smark.</h5><p>Nossos parceiros entregam tecnologia com a sua marca personalizada e comissão recorrente.</p><a class="mm-more">Saiba mais →</a></div></div></div></div></span><span class="navitem" id="prditem"><a class="svc-trigger">Produtos</a><div class="mega"><div class="mega-card"><div class="mega-list"><a class="mm on" data-k="elever" onmouseover="mmShow(this)">__ELEICONM__<span>Elever AI</span></a><a class="mm" data-k="provider" onmouseover="mmShow(this)">__PMICONM__<span>Provider Max</span></a></div><div class="mega-desc"><div class="mm-panel on" data-k="elever"><h5>Elever AI</h5><p>Um vendedor de IA no WhatsApp que atende seus clientes dia e noite — e nunca deixa ninguém sem resposta. Você só fecha.</p><a class="mm-more">Saiba mais →</a></div><div class="mm-panel" data-k="provider"><h5>Provider Max</h5><p>Um funcionário de IA que renova os contratos dos seus clientes — sozinho, dia e noite, sem contratar mais gente.</p><a class="mm-more">Saiba mais →</a></div></div></div></div></span></div>
  <a class="btn">Conversar →</a>
</div></nav>

<header class="wrap hero">
  <div class="pill">Redução de custos, eficiência e escala.</div>
  <h1>Cada departamento da sua empresa pode<br>ganhar um novo funcionário de <span class="v">IA.</span></h1>
  <div class="lead">Pra executar sozinho — <span class="rot"><span>uma tarefa pontual.</span><span>um processo completo.</span><span>uma função inteira.</span></span></div>
  <div class="ctas"><a class="btn lg">Conversar com a smark →</a><a class="btn lg ghost">Saber mais</a></div>
</header>
__CHIPS__


__FUNCSECTION__

<section><div class="wrap">
  <div class="eye" style="text-align:center">NOSSOS PRODUTOS SÃO</div>
  <div class="sec-h">Soluções prontas</div>
  <div class="sec-s">Para conectar em seu negócio.</div>
  <div class="mods">__MODS__</div>
</div></section>

<section id="assessoria" style="background:#fff;scroll-margin-top:80px"><div class="wrap">
  <div class="eye" style="text-align:center">DO SEU JEITO</div>
  <div class="sec-h">Assessoria tecnológica</div>
  <div class="sec-s">Nosso time de consultores e engenheiros de IA trabalha com você na construção de projetos personalizados.</div>
  <div class="steps">__STEPS__</div>
</div></section>

__FAQ__
<section class="cta"><div class="wrap">
  <h2>Vamos conversar?</h2>
  <a class="btn lg ghost" style="border-color:rgba(255,255,255,.6);color:#fff">Conversar com a smark →</a>
</div></section>

<footer><div class="wrap foot-in"><div class="pl">uma plataforma smark.</div><div>smarktech.com.br · @smark</div></div></footer>
<script>(function(){var t=document.getElementById('cartrack');if(!t)return;var d=document.querySelectorAll('#cardots b'),n=t.children.length,i=0,tm;
function go(k){i=(k+n)%n;t.style.transform='translateX(-'+i*100+'%)';d.forEach(function(x,j){x.classList.toggle('on',j===i)});}
function nx(){go(i+1)}function rs(){clearInterval(tm);tm=setInterval(nx,5000)}
document.getElementById('cnext').onclick=function(){nx();rs()};document.getElementById('cprev').onclick=function(){go(i-1);rs()};
d.forEach(function(x,j){x.onclick=function(){go(j);rs()}});
var w=document.getElementById('carwrap');w.onmouseenter=function(){clearInterval(tm)};w.onmouseleave=rs;rs();})();</script>
<script>
function mmShow(el){var it=el.closest('.navitem');if(!it)return;var k=el.getAttribute('data-k');it.querySelectorAll('.mm').forEach(function(e){e.classList.toggle('on',e===el)});it.querySelectorAll('.mm-panel').forEach(function(e){e.classList.toggle('on',e.getAttribute('data-k')===k)});}
function mmClose(){document.querySelectorAll('.navitem').forEach(function(it){it.classList.remove('open')});}
(function(){document.querySelectorAll('.navitem').forEach(function(it){var tr=it.querySelector('.svc-trigger');if(!tr)return;tr.addEventListener('click',function(e){e.preventDefault();var was=it.classList.contains('open');mmClose();if(!was)it.classList.add('open');});});document.addEventListener('click',function(e){if(!e.target.closest('.navitem'))mmClose();});})();
</script>
</body></html>"""

# ===== incrementos inspirados no Ordo (SÓ no smark-v2, pra avaliação) =====
def _ico(p):
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>'
_SEGS=[
  (_ico('<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><path d="M12 20h.01"/>'),"Provedores de internet"),
  (_ico('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),"Clínicas &amp; saúde"),
  (_ico('<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>'),"Varejo &amp; comércio"),
  (_ico('<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'),"Serviços &amp; consultorias"),
  (_ico('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),"Imobiliárias"),
  (_ico('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),"Times comerciais"),
]
CHIPS_HTML=('<section class="segs"><div class="wrap"><div class="seg-kicker">Menos custo. <span class="v">Mais resultado.</span> No automático.</div>'
  '<div class="seg-eye">PRA QUEM É</div><div class="chips">'+"".join('<span class="segchip">'+ic+t+'</span>' for ic,t in _SEGS)+'</div></div></section>')
_FAQS=[
  ("Funcionário de IA vai substituir a minha equipe?","Não. Ele cuida do trabalho repetitivo e operacional pra sua equipe focar no que importa. Você no comando, ele na execução."),
  ("Preciso trocar o sistema que já uso?","Não. A IA pluga no que você já tem — sem virar tudo de cabeça pra baixo."),
  ("Em quanto tempo eu vejo resultado?","A gente faz um diagnóstico grátis e monta o funcionário sob medida. Os primeiros ganhos aparecem rápido."),
  ("É difícil de usar?","Não. Você fala em português comum; ele executa e te mostra o resultado."),
  ("E se eu quiser ajustar depois?","Ajusta quando quiser. É o seu funcionário, do seu jeito."),
]
FAQ_HTML=('<section class="faq"><div class="wrap"><div class="eye" style="text-align:center">PERGUNTAS FREQUENTES</div>'
  '<div class="sec-h">Ainda com dúvida? Normal.</div><div class="faqlist">'
  +"".join('<details><summary>'+q+'<span class="fq-x">+</span></summary><p>'+a+'</p></details>' for q,a in _FAQS)+'</div></div></section>')
V2CSS=(".segs{padding:44px 0 4px}.segs .wrap{text-align:center}"
  ".seg-kicker{font-family:'Anton',sans-serif;text-transform:uppercase;font-size:36px;line-height:1;color:#100D1C;letter-spacing:.5px;margin-bottom:22px}"
  ".seg-eye{font-weight:800;font-size:13px;letter-spacing:2px;color:var(--acc);margin-bottom:16px}"
  ".chips{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;max-width:840px;margin:0 auto}"
  ".segchip{flex:0 0 auto;white-space:nowrap;display:inline-flex;align-items:center;gap:9px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:11px 18px;font-weight:700;font-size:15px;color:#3a3450;box-shadow:0 6px 18px rgba(42,28,168,.05)}"
  ".segchip svg{flex:0 0 auto}"
  ".faq{background:#fff}.faq .wrap{max-width:820px}.faqlist{margin-top:32px;display:flex;flex-direction:column;gap:12px}"
  "details{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:2px 22px}"
  "details[open]{border-color:#d8ccf5;box-shadow:0 10px 30px rgba(42,28,168,.06)}"
  "summary{list-style:none;cursor:pointer;font-weight:800;font-size:18px;color:#100D1C;padding:18px 0;display:flex;justify-content:space-between;align-items:center;gap:16px}"
  "summary::-webkit-details-marker{display:none}"
  ".fq-x{color:var(--acc);font-size:26px;font-weight:400;line-height:1;transition:.2s;flex:0 0 auto}details[open] .fq-x{transform:rotate(45deg)}"
  "details p{color:var(--sub);font-size:16px;line-height:1.55;padding:0 0 20px}"
  # camada visual premium (7009)
  "body.v2{background:#f2f0fa}"
  "body.v2::before{content:'';position:fixed;inset:0;background:radial-gradient(1150px 740px at 50% -10%,rgba(139,60,247,.16),transparent 60%),radial-gradient(820px 640px at 94% 26%,rgba(124,58,237,.09),transparent 55%),radial-gradient(700px 560px at 4% 62%,rgba(90,58,200,.06),transparent 55%);pointer-events:none;z-index:0}"
  "body.v2 nav,body.v2 header,body.v2 section,body.v2 footer{position:relative;z-index:1}"
  "body.v2 nav{background:rgba(242,240,250,.82)}"
  "body.v2 h1{letter-spacing:-2.2px}"
  "body.v2 .pill{background:rgba(255,255,255,.78);box-shadow:0 6px 22px rgba(139,60,247,.10);backdrop-filter:blur(8px)}"
  "body.v2 .btn.lg{box-shadow:0 14px 34px rgba(124,58,237,.34);transition:transform .16s ease,box-shadow .16s ease}"
  "body.v2 .btn.lg:hover{transform:translateY(-2px);box-shadow:0 20px 46px rgba(124,58,237,.46)}"
  "body.v2 .btn.ghost{background:rgba(255,255,255,.72);border-color:#e0dbef;backdrop-filter:blur(8px)}"
  "body.v2 .btn.ghost:hover{background:#fff;transform:translateY(-2px)}"
  "body.v2 .eye{display:inline-block;background:rgba(139,60,247,.10);padding:7px 15px;border-radius:999px}"
  "body.v2 .sec-h{letter-spacing:.5px}.body.v2 .sec-s{font-size:20px}"
  "body.v2 section{padding:104px 0}"
  "body.v2 .mod{box-shadow:0 24px 56px rgba(42,28,168,.10);border-color:#ece8f6;transition:transform .18s ease,box-shadow .18s ease}"
  "body.v2 .mod:hover{transform:translateY(-5px);box-shadow:0 34px 70px rgba(42,28,168,.16)}"
  "body.v2 .mod .top{height:120px;background:linear-gradient(150deg,#9A4DFF,#5b21b6 58%,#2A1CA8)}"
  "body.v2 .step{box-shadow:0 14px 36px rgba(42,28,168,.07);border-color:#ece8f6;transition:transform .16s ease,box-shadow .16s ease}"
  "body.v2 .step:hover{transform:translateY(-4px);box-shadow:0 24px 48px rgba(42,28,168,.14);border-color:#ddd2f4}"
  "body.v2 #funcionarios{background-color:transparent}"
  "body.v2 .carwrap{background:#fff;border:1px solid #ece8f6;box-shadow:0 40px 90px rgba(42,28,168,.13);padding:44px 46px;margin-top:26px}"
  "body.v2 .slide{padding:8px 4px}"
  "body.v2 .arrowbtn{box-shadow:0 8px 22px rgba(42,28,168,.12)}"
  "body.v2 .cta{background:radial-gradient(130% 140% at 50% -25%,#9A4DFF,#2A1CA8 66%);position:relative;overflow:hidden}"
  "body.v2 .cta::after{content:'';position:absolute;inset:0;background:radial-gradient(760px 360px at 50% 0%,rgba(255,255,255,.16),transparent 70%);pointer-events:none}"
  "body.v2 .cta .wrap{position:relative;z-index:1}"
  "body.v2 .pro-head{box-shadow:0 12px 30px rgba(42,28,168,.10)}"
  "body.v2 .segchip{box-shadow:0 8px 20px rgba(42,28,168,.06);transition:transform .14s ease}body.v2 .segchip:hover{transform:translateY(-2px)}")

FUNC_CAROUSEL=('<section id="funcionarios" style="background-color:#efeaf8;scroll-margin-top:80px"><div class="wrap">'
  '<div class="eye" style="text-align:center">ESCOLHA PELO SEU OBJETIVO</div><div class="sec-h">Por onde você quer começar?</div>'
  '<div class="sec-s">Funcionários de nível sênior pelo salário de estagiário.</div>'
  '<div class="carwrap" id="carwrap"><div class="cartrack" id="cartrack">__CAROUSEL__</div></div>'
  '<div class="carnav"><button class="arrowbtn" id="cprev">‹</button><div class="cardots" id="cardots">__CARDOTS__</div><button class="arrowbtn" id="cnext">›</button></div>'
  '</div></section>')
# perfil-persona (coluna clara, estilo rede social) + painel escuro de comparação (direita)
PERSONAS=[
  ('N','Nina','a que atende primeiro','Recebe todo mundo que chama, a qualquer hora. Responde na hora, faz as primeiras perguntas e nunca deixa ninguém no vácuo.','pré-vendas / primeiro atendimento (SDR)','Ninguém fica esperando. Nem no domingo.','atend',False),
  ('T','Téo','o que vai atrás','Procura a empresa certa o dia inteiro, separa quem tem cara de fechar e entrega a lista pronta pro seu vendedor. Não se cansa, não se distrai.','prospecção ativa (BDR)','Eu procuro. Você fecha.','cacador',False),
  ('C','Clara','a que não esquece cliente','Varre sua base inteira atrás de quem sumiu, contrato pra renovar e dinheiro parado. Lembra do cliente que você já tinha esquecido.','relacionamento e receita (CS)','Cliente não se perde. Se lembra.','garimpeiro',False),
  ('V','Vera','a que entende seu caso','A que conversa com você primeiro. Entende o que trava no seu negócio e monta o funcionário certo pro seu caso. É por ela que todo mundo começa.','diagnóstico e recepção da marca','Antes de contratar, a gente entende.','metodo',True),
]
def _pslide(av,name,role,bio,func,jargao,pk,hi):
    left=('<div class="sl persona"><div class="phead"><div class="pav'+(' hi' if hi else '')+'">'+av+'</div>'
      '<div><div class="pname">'+name+'</div><div class="prole">'+role+'</div></div></div>'
      '<div class="pfunc-lbl">a função que ocupa</div><div class="pfunc">'+func+'</div>'
      '<div class="pjargao">&ldquo;'+jargao+'&rdquo;</div><p class="pbio">'+bio+'</p></div>')
    panel='<div class="panel"><div class="dots3"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>'+PAN2[pk]+'</div>'
    return '<div class="slide">'+left+panel+'</div>'
slides_persona="".join(_pslide(*p) for p in PERSONAS)
cardots_persona="".join(('<b class="on"></b>' if k==0 else '<b></b>') for k in range(len(PERSONAS)))
# 7001: só Nina, Téo e Clara (sem Vera por hora)
slides_persona_3="".join(_pslide(*p) for p in PERSONAS[:3])
cardots_persona_3="".join(('<b class="on"></b>' if k==0 else '<b></b>') for k in range(3))
FUNC_CAROUSEL_V2=('<section id="funcionarios" style="background-color:#efeaf8;scroll-margin-top:80px"><div class="wrap">'
  '<div class="eye" style="text-align:center">ESCOLHA PELO SEU OBJETIVO</div><div class="sec-h">Por onde você quer começar?</div>'
  '<div class="sec-s">Funcionários de nível sênior pelo salário de estagiário.</div>'
  '<div class="carwrap" id="carwrap"><div class="cartrack" id="cartrack">__CAROUSEL__</div></div>'
  '<div class="carnav"><button class="arrowbtn" id="cprev">‹</button><div class="cardots" id="cardots">__CARDOTS__</div><button class="arrowbtn" id="cnext">›</button></div>'
  '</div></section>')

# 7001 = gerado por este script. (7009 = design de referência externo, ver abaixo)
for outdir, caro, isv2 in [("smark", slides_html, False)]:
    funcsec = FUNC_CAROUSEL_V2.replace("__CAROUSEL__",slides_persona).replace("__CARDOTS__",cardots_persona) if isv2 else FUNC_CAROUSEL_V2.replace("__CAROUSEL__",slides_persona_3).replace("__CARDOTS__",cardots_persona_3)
    html = PAGE
    for k,v in [("__CSS__",CSS.replace("__GRAD__",GRAD)),("__APEX__",APEX),("__APEXSM__",APEX_SM),("__STATS__",stats_html),("__MODS__",mods_html_v2 if isv2 else prodcards_html),("__STEPS__",steps_html),("__OBJ__",obj_html),("__FUNCSECTION__",funcsec),("__ELEICONM__",_prodicon('ele','m',24)),("__PMICONM__",_prodicon('pm','m',24)),("__V2CSS__",V2CSS if isv2 else ""),("__BODYCLASS__","v2" if isv2 else ""),("__CHIPS__",CHIPS_HTML if isv2 else ""),("__FAQ__",FAQ_HTML if isv2 else "")]:
        html = html.replace(k,v)
    d = os.path.join(HERE, outdir); os.makedirs(d, exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(html)
    print("OK", outdir)
# 7009 = design de referência (sites/_v2_ref.html, auto-descompactável). Copiado sem alterar o gerador do 7001.
_ref=os.path.join(HERE,"_v2_ref.html")
if os.path.exists(_ref):
    _d2=os.path.join(HERE,"smark-v2"); os.makedirs(_d2,exist_ok=True)
    open(os.path.join(_d2,"index.html"),"w",encoding="utf-8").write(open(_ref,encoding="utf-8").read())
    print("OK smark-v2 (referência)")
