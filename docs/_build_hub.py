# -*- coding: utf-8 -*-
"""Hub radial do Time de IA — smark no centro, 6 funcionários em 2 arcos (Elever topo / Provider Max base).
TESTE, não vai pro site. Gera docs/time-de-ia-mockup/hub-radial.png."""
import os, math, subprocess
OUT="/Users/andreik/smark/docs/time-de-ia-mockup"; os.makedirs(OUT,exist_ok=True)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GRAD="linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
W,H=1280,1120; CX,CY=640,600; R=340
APEX='<svg viewBox="0 0 100 100" width="46" height="46"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>'
def ic(p): return '<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="#8B3CF7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>'
ICON={
 "sdr": ic('<path d="M3 5h18l-7 8v6l-4-2v-4z"/>'),
 "bdr": ic('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5" fill="#8B3CF7"/>'),
 "mkt": ic('<path d="M5 19V11M12 19V5M19 19V14"/>'),
 "wpp": ic('<path d="M4 5h16v10H8l-4 4z"/>'),
 "renov": ic('<path d="M3 12a9 9 0 0 1 15-6.7M21 12a9 9 0 0 1-15 6.7"/><path d="M18 3.5V8h-4.5M6 20.5V16h4.5"/>'),
 "receita": ic('<circle cx="12" cy="12" r="9"/><path d="M9.5 8.5h3.2a2 2 0 0 1 0 4H9.5M9.5 8.5V16M9.5 12.5l3.8 3.5"/>'),
}
# (chave, role, função, icone, arco)  — ângulo em graus horário a partir do topo
NODES=[
 ("sdr","SDR","atende e qualifica","sdr",-30,"E"),
 ("bdr","BDR","prospecta e registra","bdr",30,"E"),
 ("mkt","Marketing","lê suas campanhas","mkt",-62,"E"),
 ("wpp","Campanhas","oferta no WhatsApp","wpp",62,"E"),
 ("renov","Renovação","renova o contrato","renov",-152,"P"),
 ("receita","Receita","recupera a base","receita",152,"P"),
]
def pos(a):
    r=math.radians(a); return CX+R*math.sin(r), CY-R*math.cos(r)
lines=""; nodes_html=""
for key,role,fn,icn,ang,arc in NODES:
    x,y=pos(ang)
    lines+='<line x1="%d" y1="%d" x2="%.0f" y2="%.0f" stroke="#c9b8ff" stroke-width="2" stroke-dasharray="3 7"/>'%(CX,CY,x,y)
    nodes_html+=('<div class="node" style="left:%.0fpx;top:%.0fpx">'
                 '<div class="circ">%s</div><div class="role">%s</div><div class="fn">%s</div></div>')%(x,y,ICON[icn],role,fn)
# arcos (rótulos) e anéis
ringssvg='<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#dcd4f3" stroke-width="1.5" stroke-dasharray="2 9"/>'%(CX,CY,R)
ringssvg+='<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#e7e1f7" stroke-width="1.5"/>'%(CX,CY,R-150)

HTML="""<!doctype html><html><head><meta charset="utf-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:__W__px;height:__H__px;background:radial-gradient(60% 50% at 50% 52%,#efe9fb 0%,#F4F2FB 70%);position:relative;overflow:hidden}
.top{position:absolute;top:54px;width:100%;text-align:center}
.eye{color:#8B3CF7;font-weight:800;font-size:15px;letter-spacing:3px}
.sub{color:#4A4560;font-size:18px;margin-top:8px}
svg.lay{position:absolute;inset:0}
.hub{position:absolute;left:__CX__px;top:__CY__px;transform:translate(-50%,-50%);width:236px;height:236px;border-radius:50%;background:#fff;box-shadow:0 30px 80px rgba(42,28,168,.18),0 0 0 10px rgba(139,60,247,.06);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;z-index:3}
.hub .chip{width:78px;height:78px;border-radius:20px;background:__GRAD__;display:flex;align-items:center;justify-content:center}
.hub .wm{font-weight:800;font-size:26px;letter-spacing:-1px;color:#100D1C}.hub .wm .d{color:#8B3CF7}
.node{position:absolute;transform:translate(-50%,-50%);width:200px;text-align:center;z-index:2}
.circ{width:92px;height:92px;border-radius:50%;background:#fff;border:2px solid #d9ccf7;box-shadow:0 14px 34px rgba(42,28,168,.10);display:flex;align-items:center;justify-content:center;margin:0 auto 12px}
.role{font-weight:800;font-size:19px;color:#100D1C}.fn{font-size:14px;color:#6B6680;margin-top:2px}
.arc{position:absolute;width:100%;text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:2px}
.arc small{display:block;color:#9a93ad;font-weight:600;letter-spacing:0;font-size:13px;margin-top:2px}
</style></head><body>
<div class="top"><div class="eye">SEU TIME DE IA</div><div class="sub">a casa no centro · um funcionário de IA por frente</div></div>
<svg class="lay" width="__W__" height="__H__">__RINGS____LINES__</svg>
<div class="arc" style="top:300px">ELEVER<small>a frente comercial</small></div>
<div class="arc" style="top:980px">PROVIDER MAX<small>a carteira de clientes</small></div>
<div class="hub"><div class="chip">__APEX__</div><div class="wm">smark<span class="d">.</span></div></div>
__NODES__
</body></html>"""
for k,v in [("__W__",str(W)),("__H__",str(H)),("__CX__",str(CX)),("__CY__",str(CY)),("__GRAD__",GRAD),
            ("__APEX__",APEX),("__RINGS__",ringssvg),("__LINES__",lines),("__NODES__",nodes_html)]:
    HTML=HTML.replace(k,v)
hp="/tmp/hub.html"; open(hp,"w",encoding="utf-8").write(HTML)
out=OUT+"/hub-radial.png"
subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1.5",
                "--window-size=%d,%d"%(W,H),"--virtual-time-budget=3000","--screenshot=%s"%out,"file://%s"%hp],
               check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print("OK" if os.path.exists(out) else "FAIL", out)
