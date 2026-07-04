# -*- coding: utf-8 -*-
"""COLAB smark × Scudo Seguros — anúncio de parceria (assessoria tecnológica).
Lidera a smark (roxo, APEX, voz da assessoria); Scudo em destaque (foto real + cores).
Gera story 9:16, post 4:5, carrossel 4:5 (3 cards) em docs/scudo/arte/."""
import os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"arte"); os.makedirs(OUT,exist_ok=True)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
F1="file://"+os.path.join(HERE,"fotos","foto1.jpg")
F2="file://"+os.path.join(HERE,"fotos","foto2.jpg")
GRAD="linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
ROXO="#8B3CF7"; ROXOC="#A472FF"; BLUE="#1a4db5"; TEAL="#2d8f72"
FONTS="@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@600;700;800;900&display=swap');"
RESET="*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}"
APEX='<svg viewBox="0 0 100 100" width="34" height="34"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>'
# lockup co-marca: smark. ✕ SCUDO Seguros  (dark = sobre foto / light = sobre card claro)
def lock(dark=True):
    smk='#fff' if dark else '#100D1C'; smkd='#C9B8FF' if dark else ROXO
    scd='#fff' if dark else BLUE; seg='#9fe0c8' if dark else TEAL
    x='#cdbff5' if dark else '#b3a9d0'
    return ('<div style="display:flex;align-items:center;gap:16px">'
            '<div style="display:flex;align-items:center;gap:10px"><div style="width:46px;height:46px;border-radius:13px;background:'+GRAD+';display:flex;align-items:center;justify-content:center">'+APEX+'</div>'
            '<span style="font-weight:900;font-size:30px;letter-spacing:-1px;color:'+smk+'">smark<span style="color:'+smkd+'">.</span></span></div>'
            '<span style="font-size:26px;font-weight:700;color:'+x+'">×</span>'
            '<span style="font-weight:900;font-size:26px;letter-spacing:1px;color:'+scd+'">SCUDO <span style="font-weight:700;color:'+seg+'">Seguros</span></span></div>')

STORY="""<!doctype html><html><head><meta charset='utf-8'><style>__F____R__
body{width:1080px;height:1920px;position:relative;overflow:hidden}
.bg{position:absolute;inset:0;background:url('__F1__') center/cover}
.grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,10,40,.55) 0%,rgba(20,10,40,.15) 24%,transparent 42%,rgba(15,8,30,.86) 80%,rgba(15,8,30,.97) 100%)}
.top{position:absolute;top:60px;left:60px}
.pill{display:inline-block;background:__ROXO__;color:#fff;font-weight:800;font-size:24px;letter-spacing:2px;padding:12px 22px;border-radius:999px}
.ct{position:absolute;left:60px;right:60px;bottom:170px}
.bar{width:60px;height:7px;background:__ROXOC__;border-radius:4px;margin-bottom:24px}
h1{font-family:'Anton';text-transform:uppercase;color:#fff;font-size:92px;line-height:.98;text-shadow:0 6px 30px rgba(0,0,0,.6)}
.sub{color:#e7e1f7;font-size:32px;font-weight:600;margin-top:24px;line-height:1.35}
.foot{position:absolute;left:60px;right:60px;bottom:60px}
</style></head><body>
<div class="bg"></div><div class="grad"></div>
<div class="top"><span class="pill">NOVA PARCERIA</span></div>
<div class="ct"><div class="bar"></div><h1>Tradição que ganhou <span style="color:__ROXOC__">tecnologia.</span></h1>
<div class="sub">A smark agora cuida da evolução tecnológica da Scudo Seguros — 30 anos de história + IA no que já funciona.</div></div>
<div class="foot">__LOCKD__</div>
</body></html>"""

POST="""<!doctype html><html><head><meta charset='utf-8'><style>__F____R__
body{width:1080px;height:1350px;position:relative;overflow:hidden}
.bg{position:absolute;inset:0;background:url('__F2__') center 16%/cover}
.grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,10,40,.45) 0%,transparent 32%,rgba(15,8,30,.85) 78%,rgba(15,8,30,.97) 100%)}
.top{position:absolute;top:52px;left:56px}
.pill{display:inline-block;background:__ROXO__;color:#fff;font-weight:800;font-size:22px;letter-spacing:2px;padding:11px 20px;border-radius:999px}
.ct{position:absolute;left:56px;right:56px;bottom:150px}
h1{font-family:'Anton';text-transform:uppercase;color:#fff;font-size:80px;line-height:.97;text-shadow:0 6px 30px rgba(0,0,0,.55)}
.sub{color:#e7e1f7;font-size:29px;font-weight:600;margin-top:20px;line-height:1.35}
.foot{position:absolute;left:56px;right:56px;bottom:50px}
</style></head><body>
<div class="bg"></div><div class="grad"></div>
<div class="top"><span class="pill">NOVA PARCERIA</span></div>
<div class="ct"><h1>Tradição que ganhou <span style="color:__ROXOC__">tecnologia.</span></h1>
<div class="sub">A Scudo Seguros, com 30 anos de mercado, agora tem a smark cuidando da sua evolução tecnológica.</div></div>
<div class="foot">__LOCKD__</div>
</body></html>"""

C1="""<!doctype html><html><head><meta charset='utf-8'><style>__F____R__
body{width:1080px;height:1350px;position:relative;overflow:hidden}
.bg{position:absolute;inset:0;background:url('__F1__') center 12%/cover}
.grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,10,40,.5) 0%,transparent 30%,rgba(15,8,30,.86) 78%,rgba(15,8,30,.97) 100%)}
.top{position:absolute;top:52px;left:56px}.pill{display:inline-block;background:__ROXO__;color:#fff;font-weight:800;font-size:22px;letter-spacing:2px;padding:11px 20px;border-radius:999px}
.ar{position:absolute;top:54px;right:56px;color:#fff;font-weight:800;font-size:24px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);padding:9px 18px;border-radius:999px}
.ct{position:absolute;left:56px;right:56px;bottom:150px}
h1{font-family:'Anton';text-transform:uppercase;color:#fff;font-size:84px;line-height:.98}
.foot{position:absolute;left:56px;right:56px;bottom:50px}
</style></head><body>
<div class="bg"></div><div class="grad"></div>
<div class="top"><span class="pill">NOVA PARCERIA</span></div><div class="ar">ARRASTA →</div>
<div class="ct"><h1>A Scudo escolheu a <span style="color:__ROXOC__">smark.</span></h1></div>
<div class="foot">__LOCKD__</div>
</body></html>"""

# Cards 2 e 3: identidade smark CLARA (lavanda/roxo)
C2="""<!doctype html><html><head><meta charset='utf-8'><style>__F____R__
body{width:1080px;height:1350px;background:#F4F2FB;padding:80px 72px;position:relative}
.eye{color:__ROXO__;font-weight:800;letter-spacing:2px;font-size:22px;margin-bottom:18px}
h1{font-family:'Anton';text-transform:uppercase;color:#100D1C;font-size:82px;line-height:1}
.sub{color:#4A4560;font-size:30px;font-weight:600;margin:24px 0 40px;line-height:1.42;max-width:92%}
.b{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #e6e2f0;border-radius:16px;padding:20px 22px;margin-bottom:16px;box-shadow:0 10px 30px rgba(42,28,168,.05)}
.b .ic{width:46px;height:46px;border-radius:12px;background:__GRAD__;flex:0 0 auto}
.b .t{font-weight:800;font-size:22px;color:#100D1C}.b .d{color:#6B6680;font-size:17px}
.foot{position:absolute;left:72px;bottom:54px}
</style></head><body>
<div class="eye">O QUE MUDA</div>
<h1>A gente soma — não <span style="color:__ROXO__">troca o que funciona.</span></h1>
<div class="sub">A Scudo tem 30 anos e uma operação sólida. A smark entra pra modernizar com método — tecnologia e IA plugadas no que já existe.</div>
<div class="b"><div class="ic"></div><div><div class="t">Atendimento</div><div class="d">mais rápido e disponível, no canal do cliente</div></div></div>
<div class="b"><div class="ic"></div><div><div class="t">Processos</div><div class="d">menos trabalho manual, mais tempo pro que importa</div></div></div>
<div class="b"><div class="ic"></div><div><div class="t">Dados e IA</div><div class="d">decisão com número, no lugar do achismo</div></div></div>
<div class="foot">__LOCKL__</div>
</body></html>"""

C3="""<!doctype html><html><head><meta charset='utf-8'><style>__F____R__
body{width:1080px;height:1350px;background:__GRAD__;padding:80px 72px;position:relative;color:#fff;text-align:center}
.ct{position:absolute;left:72px;right:72px;top:44%;transform:translateY(-50%)}
.eye{color:#d9c9ff;font-weight:800;letter-spacing:2px;font-size:22px;margin-bottom:18px}
h1{font-family:'Anton';text-transform:uppercase;font-size:90px;line-height:1}
.sub{color:#e7ddff;font-size:31px;font-weight:600;margin-top:22px;line-height:1.4}
.cta{display:inline-block;margin-top:40px;background:#fff;color:#2A1CA8;font-weight:900;font-size:33px;padding:22px 46px;border-radius:16px}
.chip{width:60px;height:60px;border-radius:16px;background:rgba(255,255,255,.16);display:flex;align-items:center;justify-content:center;margin:0 auto 26px}
.info{position:absolute;left:0;right:0;bottom:62px;text-align:center;color:#cbbdf2;font-size:22px;font-weight:700;letter-spacing:1px}
</style></head><body>
<div class="ct"><div class="chip">__APEX__</div><div class="eye">ASSESSORIA TECNOLÓGICA</div>
<h1>Sua empresa também quer evoluir?</h1>
<div class="sub">Tecnologia e IA com método — pra crescer com eficiência e escala, sem trocar o que já funciona.</div>
<div class="cta">Fala com a smark →</div></div>
<div class="info">smark. · uma plataforma smark · @smark</div>
</body></html>"""

REPL=[("__F__",FONTS),("__R__",RESET),("__F1__",F1),("__F2__",F2),("__GRAD__",GRAD),("__ROXO__",ROXO),("__ROXOC__",ROXOC),
      ("__APEX__",APEX),("__LOCKD__",lock(True)),("__LOCKL__",lock(False))]
JOBS=[("story",STORY,1080,1920),("post",POST,1080,1350),("carrossel-1",C1,1080,1350),("carrossel-2",C2,1080,1350),("carrossel-3",C3,1080,1350)]
for name,html,w,h in JOBS:
    for k,v in REPL: html=html.replace(k,v)
    hp="/tmp/scudo_%s.html"%name; open(hp,"w",encoding="utf-8").write(html)
    out="%s/%s.png"%(OUT,name)
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1",
                    "--window-size=%d,%d"%(w,h),"--virtual-time-budget=4000","--screenshot=%s"%out,"file://%s"%hp],
                   check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("OK" if os.path.exists(out) else "FAIL", out)
