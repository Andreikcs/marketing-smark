# -*- coding: utf-8 -*-
"""TESTE (não vai pro site): 3 variações da linha 'por objetivo' na nossa cara (claro/roxo, voz simples).
V1 menu de cards · V2 faixas detalhadas · V3 objetivo→time. Gera 3 PNGs em docs/time-de-ia-mockup/."""
import os, subprocess
OUT="/Users/andreik/smark/docs/time-de-ia-mockup"; os.makedirs(OUT,exist_ok=True)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GRAD="linear-gradient(155deg,#9A4DFF 0%,#2A1CA8 100%)"
# 5 objetivos, voz de gente. (rótulo, dor, bullets, quem faz, prova)
G=[
 ("PRA DAR CONTA","Cliente chegando e você não dá conta",
   ["Atende todo cliente que chama, dia e noite, no WhatsApp","Vê quem é cliente de verdade","Anota tudo no seu sistema sozinho","Passa pro vendedor só quem tá quente pra fechar"],
   "o Atendente","23 prontos por dia"),
 ("PRA TRAZER MAIS","Quer mais cliente chegando pro time",
   ["Vai atrás de cliente novo sozinho","Separa quem tem cara de fechar","Entrega mais oportunidade pro comercial","Deixa tudo registrado"],
   "o Caçador · o Olheiro","64 novos por mês"),
 ("PRA RENDER MAIS","Tem dinheiro parado na sua base",
   ["Acha cliente parado (planilha, sistema, lista)","Manda a oferta certa no WhatsApp","Oferece o plano melhor pra quem pode pagar"],
   "o Garimpeiro · o Mensageiro","R$ 84k de volta"),
 ("PRA SEGURAR","Quer parar de perder cliente",
   ["Fala antes do contrato vencer e renova","Mantém o cliente na base","Engaja com campanha no WhatsApp"],
   "o Renovador","38 renovados por mês"),
 ("DO SEU JEITO","Sua necessidade é diferente",
   ["A smark faz um diagnóstico grátis, estuda o seu caso e monta o funcionário sob medida pra você."],
   "a smark · assessoria","diagnóstico grátis"),
]
def bullets(items): return "".join('<div class="b"><span class="ck">✓</span>%s</div>'%t for t in items)

# ---------- V1: menu de cards (3 + 2) ----------
def card(g,i):
    rot,dor,its,quem,prova=g
    cls="card big" if i==4 else "card"
    return ('<div class="%s"><div class="lab">%s</div><div class="h">%s</div>%s'
            '<div class="ft"><span class="who">%s</span><span class="pv">%s</span></div></div>')%(cls,rot,dor,bullets(its),quem,prova)
V1="""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:1280px;height:980px;background:#F4F2FB;padding:54px 60px}
.eye{text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:3px}
h1{text-align:center;font-size:46px;font-weight:800;letter-spacing:-1px;margin:10px 0 6px;color:#100D1C}
.sub{text-align:center;color:#4A4560;font-size:18px;margin-bottom:38px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.card{background:#fff;border:1px solid #e6e2f0;border-radius:20px;padding:26px;box-shadow:0 12px 36px rgba(42,28,168,.06);display:flex;flex-direction:column}
.card.big{grid-column:span 3;flex-direction:row;align-items:center;gap:30px;background:linear-gradient(120deg,#fff, #f3eefc)}
.lab{color:#8B3CF7;font-weight:800;font-size:13px;letter-spacing:1.5px}
.h{font-size:24px;font-weight:800;color:#100D1C;margin:6px 0 14px;line-height:1.15}
.b{display:flex;gap:9px;font-size:15px;color:#3a3450;margin-bottom:9px;line-height:1.35}.b .ck{color:#8B3CF7;font-weight:800}
.ft{margin-top:auto;padding-top:14px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #efeaf8}
.who{font-size:13px;color:#6B6680;font-weight:600}.pv{background:#efeaf8;color:#8B3CF7;font-weight:700;font-size:13px;padding:5px 12px;border-radius:999px}
.card.big .h{margin:0}.card.big .ft{border:none;padding:0;margin:0;flex-direction:column;align-items:flex-end;gap:8px}
.card.big .mid{flex:1}
</style></head><body>
<div class="eye">ESCOLHA PELO SEU OBJETIVO</div><h1>Por onde você quer começar?</h1>
<div class="sub">Você não contrata um robô — escolhe o resultado. A turma de IA faz o resto.</div>
<div class="grid">__CARDS__</div></body></html>"""
# montar: 3 normais + 1 normal + 1 big. Ajusto o big (índice 4) com layout horizontal:
cards_html=""
for i,g in enumerate(G):
    if i==4:
        rot,dor,its,quem,prova=g
        cards_html+=('<div class="card big"><div class="mid"><div class="lab">%s</div><div class="h">%s</div>%s</div>'
                     '<div class="ft"><span class="who">%s</span><span class="pv">%s</span></div></div>')%(rot,dor,bullets(its),quem,prova)
    else:
        cards_html+=card(g,i)
V1=V1.replace("__CARDS__",cards_html)

# ---------- V2: faixas detalhadas ----------
bands=""
for rot,dor,its,quem,prova in G:
    bands+=('<div class="band"><div class="bl"><div class="lab">%s</div><div class="h">%s</div></div>'
            '<div class="bm">%s</div>'
            '<div class="br"><span class="who">%s</span><span class="pv">%s</span></div></div>')%(rot,dor,bullets(its),quem,prova)
V2="""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:1280px;height:1080px;background:#F4F2FB;padding:54px 60px}
.eye{text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:3px}
h1{text-align:center;font-size:46px;font-weight:800;letter-spacing:-1px;margin:10px 0 30px;color:#100D1C}
.band{display:flex;align-items:center;gap:28px;background:#fff;border:1px solid #e6e2f0;border-radius:18px;padding:24px 28px;margin-bottom:16px;box-shadow:0 10px 30px rgba(42,28,168,.05)}
.bl{width:280px;flex:0 0 280px}.lab{color:#8B3CF7;font-weight:800;font-size:12px;letter-spacing:1.5px}
.h{font-size:23px;font-weight:800;color:#100D1C;margin-top:5px;line-height:1.12}
.bm{flex:1}.b{display:flex;gap:8px;font-size:15px;color:#3a3450;margin-bottom:6px}.b .ck{color:#8B3CF7;font-weight:800}
.br{width:200px;flex:0 0 200px;text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:8px}
.who{font-size:13px;color:#6B6680;font-weight:700}.pv{background:__GRAD__;color:#fff;font-weight:700;font-size:14px;padding:7px 14px;border-radius:999px}
</style></head><body>
<div class="eye">ESCOLHA PELO SEU OBJETIVO</div><h1>O que você quer agora?</h1>
__BANDS__</body></html>""".replace("__GRAD__",GRAD).replace("__BANDS__",bands)

# ---------- V3: objetivo -> time ----------
def icn(p): return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+p+'</svg>'
rows=""
for rot,dor,its,quem,prova in G:
    rows+=('<div class="row"><div class="goal"><div class="lab">%s</div><div class="gh">%s</div></div>'
           '<div class="arr">→</div><div class="team"><span class="chip">%s</span><span class="pv">%s</span></div></div>')%(rot,dor,quem,prova)
V3="""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{width:1280px;height:860px;background:#F4F2FB;padding:54px 70px}
.eye{text-align:center;color:#8B3CF7;font-weight:800;font-size:14px;letter-spacing:3px}
h1{text-align:center;font-size:46px;font-weight:800;letter-spacing:-1px;margin:10px 0 6px;color:#100D1C}
.sub{text-align:center;color:#4A4560;font-size:18px;margin-bottom:34px}
.row{display:flex;align-items:center;gap:24px;background:#fff;border:1px solid #e6e2f0;border-radius:16px;padding:22px 28px;margin-bottom:14px;box-shadow:0 8px 24px rgba(42,28,168,.05)}
.goal{flex:1;display:flex;align-items:center;gap:16px}
.lab{background:__GRAD__;color:#fff;font-weight:800;font-size:12px;letter-spacing:1px;padding:8px 14px;border-radius:10px;white-space:nowrap}
.gh{font-size:22px;font-weight:700;color:#100D1C}
.arr{color:#c1b4e6;font-size:26px;font-weight:800}
.team{width:420px;flex:0 0 420px;display:flex;align-items:center;justify-content:space-between;gap:14px}
.chip{background:#efeaf8;color:#5a3a9c;font-weight:800;font-size:16px;padding:9px 16px;border-radius:12px}
.pv{color:#8B3CF7;font-weight:700;font-size:14px}
</style></head><body>
<div class="eye">DO OBJETIVO AO FUNCIONÁRIO</div><h1>Seu objetivo escolhe o time</h1>
<div class="sub">Diz o que você quer — a gente já sabe qual funcionário de IA entra.</div>
__ROWS__</body></html>""".replace("__GRAD__",GRAD).replace("__ROWS__",rows)

for name,html,w,h in [("variacao-1-objetivos",V1,1280,980),("variacao-2-faixas",V2,1280,1080),("variacao-3-mapa",V3,1280,860)]:
    hp="/tmp/%s.html"%name; open(hp,"w",encoding="utf-8").write(html)
    out="%s/%s.png"%(OUT,name)
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1.5",
                    "--window-size=%d,%d"%(w,h),"--virtual-time-budget=3000","--screenshot=%s"%out,"file://%s"%hp],
                   check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("OK" if os.path.exists(out) else "FAIL", out)
