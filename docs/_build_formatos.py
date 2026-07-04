# -*- coding: utf-8 -*-
"""TESTE (não vai pro site): 2 formatos de apresentar o Time de IA com nomes de gente.
A = grade de crachás · B = trilha do caminho do cliente. Gera 2 PNGs em docs/time-de-ia-mockup/."""
import os, subprocess
OUT="/Users/andreik/smark/docs/time-de-ia-mockup"; os.makedirs(OUT,exist_ok=True)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GRAD="linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
def ic(p,c="#fff"): return '<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="'+c+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>'
PATHS={"sdr":'<path d="M3 5h18l-7 8v6l-4-2v-4z"/>',"bdr":'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5" fill="currentfill"/>',
 "mkt":'<path d="M5 19V11M12 19V5M19 19V14"/>',"wpp":'<path d="M4 5h16v10H8l-4 4z"/>',
 "renov":'<path d="M3 12a9 9 0 0 1 15-6.7M21 12a9 9 0 0 1-15 6.7"/><path d="M18 3.5V8h-4.5M6 20.5V16h4.5"/>',
 "receita":'<circle cx="12" cy="12" r="9"/><path d="M9.5 8.5h3.2a2 2 0 0 1 0 4H9.5M9.5 8.5V16M9.5 12.5l3.8 3.5"/>',
 "fecha":'<path d="M8 13l2 2 3-4M4 7h16v11H4z"/><path d="M9 7V5h6v2"/>'}
def icon(k,c="#fff"): return ic(PATHS[k].replace("currentfill",c),c)
# chave: (nome, frase criança, prova, squad)
A={"sdr":("o Atendente","Atende quem chega e te avisa quando o cliente já quer comprar.","23 prontos hoje","ELEVER"),
   "bdr":("o Caçador","Vai atrás de cliente novo e traz quem tem cara de fechar.","64 achados","ELEVER"),
   "mkt":("o Olheiro","Olha seus anúncios e diz quais estão trazendo gente boa.","3× a melhor","ELEVER"),
   "wpp":("o Mensageiro","Manda a oferta no WhatsApp e vê quem se animou.","47 quentes","ELEVER"),
   "renov":("o Renovador","Fala com o cliente antes do plano acabar e renova sozinho.","38 renovados","PROVIDER MAX"),
   "receita":("o Garimpeiro","Acha quem parou de comprar e chama de volta.","R$ 84k de volta","PROVIDER MAX")}

# ---------- FORMATO A: crachás ----------
cards=""
for k in ["sdr","bdr","mkt","wpp","renov","receita"]:
    nome,frase,prova,squad=A[k]
    cards+=('<div class="card"><div class="av">%s</div>'
            '<div class="sq">%s</div><div class="nm">%s</div>'
            '<div class="fr">%s</div><div class="pv">%s</div></div>')%(icon(k),squad,nome,frase,prova)
A_HTML="""<!doctype html><html><head><meta charset="utf-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:1280px;height:900px;background:#F4F2FB;padding:56px 64px}
.eye{text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:3px}
h1{text-align:center;font-size:44px;font-weight:800;letter-spacing:-1px;margin:10px 0 6px;color:#100D1C}
.sub{text-align:center;color:#4A4560;font-size:18px;margin-bottom:40px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.card{background:#fff;border:1px solid #e6e2f0;border-radius:20px;padding:26px;box-shadow:0 14px 40px rgba(42,28,168,.07)}
.av{width:70px;height:70px;border-radius:18px;background:__GRAD__;display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.sq{font-size:11px;font-weight:800;letter-spacing:1.5px;color:#9a8ec9}
.nm{font-size:26px;font-weight:800;color:#100D1C;margin:2px 0 8px}
.fr{font-size:16px;color:#4A4560;line-height:1.4;min-height:66px}
.pv{display:inline-block;margin-top:8px;background:#efeaf8;color:#8B3CF7;font-weight:700;font-size:14px;padding:6px 14px;border-radius:999px}
</style></head><body>
<div class="eye">SUA EQUIPE DE IA</div><h1>Conheça os funcionários</h1>
<div class="sub">Cada um cuida de uma parte — e nenhum tira férias.</div>
<div class="grid">__CARDS__</div></body></html>""".replace("__GRAD__",GRAD).replace("__CARDS__",cards)

# ---------- FORMATO B: trilha ----------
ORDER=[("mkt",False),("bdr",False),("sdr",False),("wpp",False),("fecha",True),("renov",False),("receita",False)]
TINY={"mkt":"anúncios","bdr":"acha cliente","sdr":"atende e separa","wpp":"manda a oferta","renov":"renova","receita":"recupera"}
stations=""
for i,(k,is_fecha) in enumerate(ORDER):
    if is_fecha:
        st=('<div class="st"><div class="c fecha">%s</div><div class="snm">VOCÊ FECHA</div><div class="stiny">a venda é sua</div></div>')%icon("fecha")
    else:
        nome=A[k][0]; st=('<div class="st"><div class="c">%s</div><div class="snm">%s</div><div class="stiny">%s</div></div>')%(icon(k,"#8B3CF7"),nome,TINY[k])
    stations+=st
    if i<len(ORDER)-1: stations+='<div class="arrow">→</div>'
B_HTML="""<!doctype html><html><head><meta charset="utf-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:1480px;height:560px;background:#F4F2FB;padding:48px 48px;display:flex;flex-direction:column}
.eye{text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:3px}
h1{text-align:center;font-size:42px;font-weight:800;letter-spacing:-1px;margin:8px 0 4px;color:#100D1C}
.sub{text-align:center;color:#4A4560;font-size:18px;margin-bottom:36px}
.brackets{display:flex;justify-content:space-between;max-width:1300px;margin:0 auto 8px;width:100%}
.bk{font-size:12px;font-weight:800;letter-spacing:1.5px;color:#9a8ec9}
.track{display:flex;align-items:flex-start;justify-content:center;gap:6px;flex:1}
.st{width:150px;text-align:center}
.c{width:78px;height:78px;border-radius:50%;background:#fff;border:2px solid #d9ccf7;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;box-shadow:0 10px 26px rgba(42,28,168,.08)}
.c.fecha{background:__GRAD__;border:none;box-shadow:0 16px 36px rgba(120,60,255,.32)}
.snm{font-weight:800;font-size:17px;color:#100D1C}.stiny{font-size:13px;color:#6B6680;margin-top:2px}
.arrow{color:#c1b4e6;font-size:26px;font-weight:700;margin-top:24px}
</style></head><body>
<div class="eye">O CAMINHO DO CLIENTE</div><h1>Do primeiro oi à renovação</h1>
<div class="sub">Os funcionários se passam o cliente — e você só entra pra fechar.</div>
<div class="brackets"><span class="bk">◖ TRAZEM E PREPARAM</span><span class="bk">VOCÊ</span><span class="bk">CUIDAM DA BASE ◗</span></div>
<div class="track">__STATIONS__</div></body></html>""".replace("__GRAD__",GRAD).replace("__STATIONS__",stations)

for name,html,w,h,scale in [("formato-A-crachas",A_HTML,1280,900,1.5),("formato-B-trilha",B_HTML,1480,560,1.3)]:
    hp="/tmp/%s.html"%name; open(hp,"w",encoding="utf-8").write(html)
    out="%s/%s.png"%(OUT,name)
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=%s"%scale,
                    "--window-size=%d,%d"%(w,h),"--virtual-time-budget=3000","--screenshot=%s"%out,"file://%s"%hp],
                   check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("OK" if os.path.exists(out) else "FAIL", out)
