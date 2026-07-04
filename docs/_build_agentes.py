# -*- coding: utf-8 -*-
"""Mockups dos 6 funcionários de IA (slides do carrossel) — TESTE, não vai pro site.
Gera docs/time-de-ia-mockup/agente-N.png. Branding smark (claro + painel escuro, roxo)."""
import os, subprocess
OUT = "/Users/andreik/smark/docs/time-de-ia-mockup"; os.makedirs(OUT, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GRAD = "linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"

def bar(label, value, pct, hi=False):
    col = "#A472FF" if hi else "#3a3358"
    txtv = "#A472FF" if hi else "#cfc8e6"
    return ('<div style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;font-size:15px;margin-bottom:6px">'
            '<span style="color:#c9c2dd">'+label+'</span><span style="color:'+txtv+';font-weight:700">'+value+'</span></div>'
            '<div style="height:12px;border-radius:6px;background:#221c33"><div style="height:12px;border-radius:6px;width:'+str(pct)+'%;background:'+col+'"></div></div></div>')

def trio(items):  # 3 stat cards
    cells = "".join('<div style="flex:1;background:#1c1730;border:1px solid #2a2440;border-radius:14px;padding:16px 14px;text-align:center">'
                    '<div style="font-size:30px;font-weight:800;color:'+(c)+'">'+v+'</div>'
                    '<div style="font-size:12px;color:#9a93ad;margin-top:4px">'+l+'</div></div>' for v,l,c in items)
    return '<div style="display:flex;gap:12px;margin:6px 0 18px">'+cells+'</div>'

def bubble(side, txt, tag=""):
    if side=="in":
        return '<div style="background:#221c33;color:#e8e4f2;border-radius:14px 14px 14px 4px;padding:11px 14px;font-size:15px;max-width:78%;margin-bottom:8px">'+txt+'</div>'
    t = '<span style="background:#1e3a2a;color:#69d49a;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:8px">'+tag+'</span>' if tag else ''
    return '<div style="background:'+GRAD+';color:#fff;border-radius:14px 14px 4px 14px;padding:11px 14px;font-size:15px;max-width:80%;margin-left:auto;margin-bottom:8px">'+txt+t+'</div>'

def insight(t):
    return '<div style="margin-top:auto;padding-top:16px;border-top:1px solid #241e36;color:#c9c2dd;font-size:14px">💡 '+t+'</div>'

P = {
"sdr": '<div class="pl">FUNIL DE QUALIFICAÇÃO</div>'+bar("Chegaram","148",100)+bar("Qualificados","89",60)+bar("Prontos pra fechar","23",16,hi=True)+insight("só os 23 prontos vão pro seu vendedor — o resto a IA cuida"),
"bdr": '<div class="pl">PROSPECÇÃO ATIVA</div>'+trio([("210","prospectados","#fff"),("64","com fit","#A472FF"),("7,8","score médio","#fff")])+bubble("in","Empresa X — 80 funcionários, cresceu 30%")+bubble("out","Cliente com fit. Registrado pro time.","registrado"),
"mkt": '<div class="pl">CAMPANHAS — INDICADORES</div>'+bar("Campanha A · custo R$ 18/cliente","ótimo",90,hi=True)+bar("Campanha B · custo R$ 41/cliente","ok",48)+bar("Campanha C · custo R$ 96/cliente","ruim",20)+insight("Campanha A traz 3× mais cliente bom — vale investir mais"),
"wpp": '<div class="pl">CAMPANHA NO WHATSAPP</div>'+trio([("1.200","disparos","#fff"),("180","responderam","#fff"),("47","quentes","#A472FF")])+bubble("out","Oi! Tá rolando uma condição especial essa semana 👀")+bubble("in","Tenho interesse, como funciona?")+'<div style="text-align:right;color:#69d49a;font-size:13px;font-weight:700">filtrado e entregue pro time ✓</div>',
"renov": '<div class="pl">RENOVAÇÕES</div>'+trio([("124","vencendo em 30d","#fff"),("38","renovados","#A472FF"),("51","em conversa","#fff")])+bubble("out","Oi! Seu plano vence em 5 dias. Posso já renovar com a mesma condição?")+bubble("in","Pode sim, obrigado!","renovado ✓"),
"receita": '<div class="pl">RECEITA PARADA NA BASE</div>'+trio([("22","reativados","#A472FF"),("17","subiram de plano","#fff"),("R$84k","de volta","#A472FF")])+bar("Clientes parados há +90 dias","reativando",70,hi=True)+insight("o dinheiro já estava na base — só faltava quem fosse atrás"),
}

AG = [
("1","ELEVER","SDR de IA","O qualificador","Atende quem te procura, vê quem é cliente de verdade e entrega pro vendedor só quem tá pronto.",
  ["Atende e qualifica na hora","Faz o acompanhamento sem esquecer","Organiza tudo no seu sistema","Entrega só os prontos pra fechar"],"smark · Qualificação","sdr"),
("2","ELEVER","BDR de IA","O prospector","Vai atrás de cliente novo, vê quem tem cara de fechar e deixa registrado pro time trabalhar.",
  ["Prospecta cliente novo","Vê quem tem fit","Dá uma nota pra cada um","Registra pro comercial"],"smark · Prospecção","bdr"),
("3","ELEVER","Agente de Marketing de IA","O analista","Junta os números das suas campanhas num lugar só e aponta onde vale investir mais.",
  ["Conecta suas campanhas","Mostra os números num painel","Compara o que dá resultado","Sugere onde investir"],"smark · Marketing","mkt"),
("4","ELEVER","Campanhas no WhatsApp de IA","O disparador","Manda a oferta certa no WhatsApp, vê quem respondeu interessado e entrega a lista quentinha pro time.",
  ["Dispara oferta no WhatsApp","Vê quem se interessou","Filtra os quentes","Documenta pro time fechar"],"smark · Campanhas","wpp"),
("5","PROVIDER MAX","Agente de Renovação de IA","O renovador","Vê quais contratos estão vencendo, fala com o cliente no WhatsApp e renova — sozinho.",
  ["Aponta contratos a vencer","Conversa no WhatsApp","Renova sozinho","Fideliza o cliente"],"smark · Renovação","renov"),
("6","PROVIDER MAX","Agente de Receita de IA","O recuperador","Garimpa quem parou de comprar e quem pode subir de plano — e vai atrás.",
  ["Acha clientes parados","Traz de volta quem sumiu","Oferece plano melhor","Recupera receita da base"],"smark · Receita","receita"),
]

CSS = """*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800&display=swap');
body{width:1280px;height:760px;background:#F4F2FB}
.slide{width:1280px;height:760px;display:flex;align-items:center;gap:52px;padding:0 70px;position:relative}
.tag{position:absolute;top:46px;left:70px;display:flex;gap:10px;align-items:center}
.tag .t1{background:#efeaf8;border:1px solid #e6e2f0;color:#8B3CF7;font-weight:700;font-size:13px;padding:7px 14px;border-radius:999px}
.tag .t2{background:__GRAD__;color:#fff;font-weight:700;font-size:13px;padding:7px 14px;border-radius:999px}
.left{flex:1;max-width:560px}
.role{color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:1px;margin-bottom:8px}
h2{font-size:46px;font-weight:800;letter-spacing:-1px;line-height:1.05;margin-bottom:16px;color:#100D1C}
.desc{font-size:19px;color:#4A4560;line-height:1.45;margin-bottom:22px}
.b{display:flex;align-items:center;gap:10px;font-size:17px;color:#241f33;margin-bottom:12px}
.b .ck{color:#8B3CF7;font-weight:800}
.dots{font-size:0;margin-bottom:14px}.dots i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px}
.panel{width:600px;background:#14101e;border-radius:22px;padding:26px 28px;color:#fff;display:flex;flex-direction:column;min-height:430px;box-shadow:0 30px 80px rgba(20,12,40,.35)}
.ptitle{color:#9a93ad;font-size:14px;font-weight:600;margin-bottom:16px}
.pl{color:#9a93ad;font-size:12px;font-weight:700;letter-spacing:1.5px;margin-bottom:14px}
.pager{position:absolute;bottom:40px;left:70px;display:flex;gap:8px}
.pager i{width:9px;height:9px;border-radius:50%;background:#d3cce6}.pager i.on{width:26px;border-radius:6px;background:#8B3CF7}
.brand{position:absolute;top:46px;right:70px;font-weight:800;font-size:22px;letter-spacing:-1px;color:#100D1C}.brand .dot{color:#8B3CF7}
"""

TPL = """<!doctype html><html><head><meta charset="utf-8"><style>__CSS__</style></head><body>
<div class="slide">
  <div class="tag"><span class="t1">Funcionário de IA</span><span class="t2">__SQUAD__</span></div>
  <div class="brand">smark<span class="dot">.</span></div>
  <div class="left">
    <div class="role">__ROLE__</div>
    <h2>__HEAD__</h2>
    <div class="desc">__DESC__</div>
    __BULLETS__
  </div>
  <div class="panel">
    <div class="dots"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>
    <div class="ptitle">__PTITLE__</div>
    __PANEL__
  </div>
  <div class="pager">__PAGER__</div>
</div></body></html>"""

for n,squad,role,head,desc,bullets,ptitle,pkey in AG:
    bl = "".join('<div class="b"><span class="ck">✓</span>'+b+'</div>' for b in bullets)
    pager = "".join(('<i class="on"></i>' if str(i)==n else '<i></i>') for i in range(1,7))
    html = TPL
    for k,v in [("__CSS__",CSS.replace("__GRAD__",GRAD)),("__SQUAD__",squad),("__ROLE__",role.upper()),
                ("__HEAD__",head),("__DESC__",desc),("__BULLETS__",bl),("__PTITLE__",ptitle),("__PANEL__",P[pkey]),("__PAGER__",pager)]:
        html = html.replace(k,v)
    hp="/tmp/ag_%s.html"%n; open(hp,"w",encoding="utf-8").write(html)
    out="%s/agente-%s-%s.png"%(OUT,n,pkey)
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1.5",
                    "--window-size=1280,760","--virtual-time-budget=3000","--screenshot=%s"%out,"file://%s"%hp],
                   check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("OK" if os.path.exists(out) else "FAIL", out)
