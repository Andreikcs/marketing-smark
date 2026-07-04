#!/usr/bin/env python3
"""LANÇAMENTO — simulação GRÁTIS (sem API). Renderiza as artes com fundo placeholder (CSS)
e monta a vitrine (lancamento.html): feed de Instagram por marca pra aprovar copy/conceito.
Depois, só nas aprovadas, geramos o fundo de IA real.
Rodar:  python3 scripts/lancamento.py   →   abre lancamento.html
"""
import json
import os
import subprocess

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPO = os.path.join(VAULT, "scripts", "compositor.py")

SYM = {
 "smark": '<svg viewBox="0 0 100 100" width="46" height="46"><path fill-rule="evenodd" fill="#fff" d="M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"/></svg>',
 "elever-ai": '<svg viewBox="0 0 100 100" width="44" height="44"><path fill="#fff" d="M50 4 C54 34 66 46 96 50 C66 54 54 66 50 96 C46 66 34 54 4 50 C34 46 46 34 50 4 Z"/></svg>',
 "provider-max": '<svg viewBox="0 0 100 100" width="46" height="46" style="color:#fff"><circle cx="50" cy="71" r="7" fill="currentColor"/><path d="M37 61 Q50 46 63 61" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M27 52 Q50 27 73 52" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M17 43 Q50 10 83 43" stroke="currentColor" stroke-width="9" fill="none" stroke-linecap="round"/></svg>',
}
HANDLE = {"smark": "@smark", "provider-max": "@providermax", "elever-ai": "@eleverai"}
BIO = {
 "smark": "Assessoria tecnológica para crescer com eficiência e escala — sem trocar o que já funciona. A gente entra com o método que faz a IA virar resultado.",
 "provider-max": "Um funcionário de IA que renova os contratos dos seus clientes — sozinho, dia e noite, sem você contratar mais gente. uma plataforma smark.",
 "elever-ai": "Um vendedor de IA no WhatsApp que atende seus clientes dia e noite — e nunca deixa ninguém sem resposta. Você só fecha. uma plataforma smark.",
}

# n, tipo, headline (| = quebra · *x* = acento), sub, cta, tema, formato, caption
LANC = {
 "smark": [
  (1, "manifesto", "UM NOVO JEITO|DE LEVAR IA PRA|*OPERAÇÃO.*", "Esse é o novo momento da smark.", "ARRASTA →", "escuro", "carrossel",
   "A gente sempre acreditou numa coisa: tecnologia boa não troca o que funciona — ela soma. Hoje a smark assume isso de vez. Bora?"),
  (2, "núcleo", "IA QUE PLUGA NO|QUE VOCÊ *JÁ TEM.*", "Sem trocar seu sistema, seu time ou seus processos.", "", "escuro", "post",
   "Seu ERP, seu CRM, o jeito que seu time já trabalha. A IA entra por aí — sem rebuild, sem parar a operação."),
  (3, "dor", "VOCÊ NÃO PRECISA|TROCAR O QUE|*FUNCIONA.*", "A IA entra em volta do que você já tem.", "", "claro", "post",
   "A maioria dos projetos de IA morre porque alguém tentou trocar tudo de uma vez. Tem caminho melhor."),
  (4, "provoca", "IA SEM MÉTODO|NÃO *ESCALA.*", "Sem processo, vira mais uma aba que ninguém abre.", "", "escuro", "post",
   "Ferramenta nova não é estratégia. Método é. É isso que a gente entrega."),
  (5, "educativo", "3 SINAIS DE QUE SUA|EMPRESA TÁ|*PRONTA PRA IA.*", "Arrasta e confere.", "ARRASTA →", "claro", "carrossel",
   "Antes de comprar ferramenta, veja se a casa está pronta. 3 sinais (e o que fazer em cada um)."),
  (6, "antihype", "A IA NÃO TE|SUBSTITUI. *TE LIBERA.*", "Tira o operacional repetitivo; sobra o que importa.", "", "escuro", "post",
   "O medo é virar dispensável. A real é o contrário: a IA tira de você o trabalho chato pra você fazer o que máquina nenhuma faz."),
  (7, "prova", "DA IDEIA AO AR|EM *SEMANAS.*", "Não em PowerPoint.", "", "claro", "post",
   "Projeto de IA não precisa ser eterno. Quando pluga no que já existe, o ganho aparece rápido."),
  (8, "autoridade", "QUATRO SÓCIOS QUE|ATENDEM O|*TELEFONE.*", "Conta a dor. A gente constrói junto.", "", "escuro", "post",
   "Sem camada de atendimento, sem release. Você fala com quem constrói. É parte da marca."),
  (9, "diferencial", "EM VOLTA DO QUE|VOCÊ *JÁ TEM.*", "ERP, CRM, time — a IA pluga, não troca.", "ARRASTA →", "escuro", "carrossel",
   "O nosso jeito: construir em volta do que você já tem. Sem quebrar o que está de pé."),
  (10, "cta", "ONDE A IA ENCAIXA|NA SUA *OPERAÇÃO?*", "Diagnóstico gratuito.", "DIAGNÓSTICO →", "claro", "post",
   "Em 30 minutos a gente acha onde a IA encaixa na sua operação — sem rebuild. Chama no direct."),
 ],
 "provider-max": [
  (1, "manifesto", "FUNCIONÁRIOS DE IA|PRO SEU *PROVEDOR.*", "Esse é o Provider Max.", "ARRASTA →", "escuro", "carrossel",
   "Sua base já vale mais do que você fatura. Apresentamos os funcionários de IA que vão buscar essa receita."),
  (2, "herói", "SEU TIME NÃO DÁ|CONTA. A IA *DÁ.*", "Renovar, recuperar e fazer upgrade de 10 mil contratos.", "QUERO VER →", "escuro", "post",
   "Ninguém liga, renova e oferta upgrade pra 10 mil contratos, um a um, na hora certa. A IA dá conta."),
  (3, "núcleo", "A RECEITA JÁ ESTÁ|NA BASE. FALTA|QUEM *EXECUTE.*", "A Provider Max é o braço que executa.", "", "claro", "post",
   "Não é falta de estratégia. É falta de braço pra executar a base inteira. A gente é esse braço."),
  (4, "recuperação", "RECUPERA A BASE|ANTES DO *CHURN.*", "Cliente em risco, reativado no automático.", "", "escuro", "post",
   "Contrato vencido hoje é cancelamento amanhã. A IA age antes — recupera quem ia sair."),
  (5, "renovação", "RENOVA ANTES DE O|CLIENTE PENSAR|EM *SAIR.*", "Renovação não é sorte. É processo.", "", "claro", "post",
   "O Gestor de Renovações antecipa o vencimento e renova proativo — no WhatsApp, registrado no IXC."),
  (6, "upgrade", "SOBE O TICKET COM|UPGRADE NA *BASE.*", "A receita que já existe, capturada.", "", "escuro", "post",
   "Quem pode subir de plano? A IA acha e oferta na hora certa. ROI medível em 60–90 dias."),
  (7, "prova", "5× MAIS CARO|BUSCAR CLIENTE|*NOVO.*", "Sua base já vale mais do que você fatura.", "ARRASTA →", "claro", "carrossel",
   "Enquanto uns correm atrás de cliente novo (5x mais caro), os eficientes extraem a receita que já está na base."),
  (8, "integração", "INTEGRA NO SEU|IXC. SEM *PLANILHA.*", "Funcionários de IA que registram sozinhos.", "", "escuro", "post",
   "Sem virar projeto de TI. Os agentes conversam no WhatsApp e registram direto no seu IXC."),
  (9, "provoca", "ENQUANTO VOCÊ NÃO|AGE, O DINHEIRO|*SOME.*", "A IA age por você.", "", "claro", "post",
   "Cada dia parado é renovação perdida e upgrade não ofertado. O Provider Max age no seu lugar."),
  (10, "cta", "QUER VER NA SUA|*BASE?*", "Diagnóstico gratuito.", "DIAGNÓSTICO →", "escuro", "post",
   "Mostramos quanto de receita está parada na sua base — sem compromisso. Comenta BASE ou chama no direct."),
 ],
 "elever-ai": [
  (1, "manifesto", "UM FUNCIONÁRIO DE IA|QUE NÃO *DORME.*", "Esse é o Elever AI.", "ARRASTA →", "escuro", "carrossel",
   "Você não perde por falta de lead. Perde por demora. Apresentamos o funcionário de IA que atende dia e noite."),
  (2, "núcleo", "ATENDE DE DIA.|ATENDE DE *NOITE.*", "Responde todo lead na hora — e não tira férias.", "QUERO VER →", "claro", "post",
   "Um funcionário de IA que atende cada lead na hora, qualifica e entrega pronto. Você só fecha."),
  (3, "dor", "ELE CHAMOU 22H.|VOCÊ RESPONDEU|*AMANHÃ.*", "Lead de noite também é venda.", "", "escuro", "post",
   "O cliente chama 22h, no domingo, na madrugada. De manhã ele já fechou com quem respondeu. A IA cobre esse turno."),
  (4, "dor", "LEAD DE DOMINGO|TAMBÉM É *VENDA.*", "O cliente não some — só foi atendido em outro lugar.", "", "claro", "post",
   "Quem responde primeiro leva. A IA responde na hora, todo dia, toda hora."),
  (5, "follow-up", "AQUELE ORÇAMENTO|QUE VIROU|*SILÊNCIO.*", "A IA puxa o papo de volta no tempo certo.", "", "escuro", "post",
   "O dinheiro está no follow-up. E ninguém tem tempo de lembrar de cada cliente, um por um. A IA tem."),
  (6, "divisão", "VOCÊ FECHA.|A IA *ATENDE.*", "A IA faz o trabalho chato; você faz a venda.", "", "claro", "post",
   "Não é robô que substitui o time. É quem atende, qualifica e lembra — pra seu vendedor focar em fechar."),
  (7, "velocidade", "QUEM RESPONDE|PRIMEIRO, *FECHA.*", "Lead quente esfria em minutos.", "", "escuro", "post",
   "Cada minuto de demora é conversão que escorre. A IA responde no segundo em que o lead chega."),
  (8, "nicho", "CLIENTE SUMIU DEPOIS|DO *ORÇAMENTO?*", "A IA atende na hora e não esquece ninguém.", "", "escuro", "post",
   "Móvel, plano, projeto — venda que demora pede follow-up. A IA faz por você, sem você correr atrás."),
  (9, "antimedo", "NÃO É ROBÔ. É UM|FUNCIONÁRIO DE *IA.*", "Atende como gente, na hora, 24h.", "", "claro", "post",
   "Esquece o chatbot travado. É um atendimento que conversa de verdade — e não dorme."),
  (10, "cta", "QUER UM FUNCIONÁRIO|QUE NÃO *FALTA?*", "Diagnóstico gratuito.", "DIAGNÓSTICO →", "escuro", "post",
   "Mostramos como a IA atende seus leads dia e noite. Comenta EU QUERO ou chama no direct."),
 ],
}


DATA = os.path.join(VAULT, "lancamento.json")


def seed():
    d = {"marcas": {}}
    for m, items in LANC.items():
        recs = [{"n": n, "tipo": t, "headline": hl, "sub": sub, "cta": cta, "tema": tema,
                 "formato": fmt, "caption": cap, "status": "rascunho", "thumb": ""}
                for (n, t, hl, sub, cta, tema, fmt, cap) in items]
        d["marcas"][m] = {"handle": HANDLE[m], "bio": BIO[m], "sym": SYM[m], "recs": recs}
    return d


def load():
    return json.load(open(DATA, encoding="utf-8")) if os.path.exists(DATA) else seed()


def save(d):
    json.dump(d, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def render_one(marca, rec):
    dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram", "arte", "_lancamento")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{rec['n']:02d}.png")
    args = ["python3", COMPO, "--placeholder", "--tema", rec["tema"], "--marca", marca,
            "--out", png, "--headline", rec["headline"].replace("|", "\\n"), "--sub", rec.get("sub", "")]
    if rec.get("cta"):
        args += ["--cta", rec["cta"]]
    subprocess.run(args, cwd=VAULT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["thumb"] = os.path.relpath(png, VAULT) if os.path.exists(png) else ""
    return rec["thumb"]


def render_all(d):
    for m, info in d["marcas"].items():
        for rec in info["recs"]:
            render_one(m, rec)
        print(f"  {m}: {len([r for r in info['recs'] if r['thumb']])}/10 artes")


def build_html(d):
    html = TEMPLATE.replace("/*DADOS*/", json.dumps(d, ensure_ascii=False))
    open(os.path.join(VAULT, "lancamento.html"), "w", encoding="utf-8").write(html)


TEMPLATE = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Lançamento · Grupo Smark</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{background:#0B0B0B;color:#EAEAF0}
.nav{position:sticky;top:0;z-index:10;background:linear-gradient(180deg,#15121f,#0d0b14);border-bottom:1px solid rgba(255,255,255,.1);padding:16px 28px;display:flex;align-items:center;gap:22px}
.nav h1{font-family:'Anton';font-size:24px;letter-spacing:1px;text-transform:uppercase;margin-right:auto}
.nav a{color:#9a93ad;text-decoration:none;font-weight:700;font-size:14px;padding:7px 14px;border-radius:9px}
.nav a.on{background:#8B3CF7;color:#fff}
.brands{display:flex;gap:8px;padding:18px 28px 4px}
.bt{background:#15151c;border:1px solid rgba(255,255,255,.12);color:#cfcad8;border-radius:999px;padding:9px 18px;font-weight:800;cursor:pointer}
.bt.on{background:#8B3CF7;border-color:#8B3CF7;color:#fff}
.wrap{max-width:860px;margin:0 auto;padding:18px 16px 60px}
.profile{display:flex;gap:30px;align-items:center;padding:20px 8px 26px}
.av{width:120px;height:120px;border-radius:50%;background:linear-gradient(155deg,#9A4DFF,#2A1CA8);display:flex;align-items:center;justify-content:center;flex:none}
.pinfo .h{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.pinfo .hn{font-size:24px;font-weight:500}
.pinfo .stats{display:flex;gap:30px;margin-bottom:14px;font-size:15px;color:#cfcad8}
.pinfo .stats b{color:#fff}
.pinfo .bio{font-size:14px;color:#d6d2e2;line-height:1.5;max-width:520px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.cell{position:relative;aspect-ratio:1/1;background:#16151d center/cover no-repeat;cursor:pointer}
.cell:hover::after{content:"";position:absolute;inset:0;background:rgba(139,60,247,.25)}
.cell .car{position:absolute;top:8px;right:8px;color:#fff;font-size:16px;filter:drop-shadow(0 1px 2px #000)}
.cell .badge{position:absolute;bottom:8px;left:8px;background:rgba(0,0,0,.6);color:#fff;font-size:10px;font-weight:700;border-radius:5px;padding:2px 7px}
.hint{text-align:center;color:#6a6478;font-size:13px;padding:14px}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.74);display:none;z-index:50;padding:24px;overflow:auto}
.ov.on{display:flex;align-items:center;justify-content:center}
.modal{background:#121119;border:1px solid rgba(255,255,255,.14);border-radius:18px;max-width:840px;width:100%;display:grid;grid-template-columns:360px 1fr;max-height:92vh;overflow:auto}
.modal img{width:100%;border-radius:18px 0 0 18px;display:block}
.modal .side{padding:24px 26px}
.modal .lab{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#8a83a0;font-weight:800;margin:14px 0 6px}
.modal .tipo{display:inline-block;background:#8B3CF7;color:#fff;font-weight:800;font-size:12px;border-radius:7px;padding:4px 10px}
.modal .cap{background:#0c0b12;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:12px 14px;white-space:pre-wrap;font-size:14px;line-height:1.55;color:#dcd7e8}
.x{position:fixed;top:24px;right:30px;font-size:30px;color:#fff;cursor:pointer;z-index:60}
@media(max-width:700px){.modal{grid-template-columns:1fr}.modal img{border-radius:18px 18px 0 0}.profile{flex-direction:column;text-align:center}}
</style></head><body>
<div class="nav"><h1>Grupo Smark</h1><a href="http://localhost:8765/painel">Conteúdo</a><a href="http://localhost:8765/vitrine" class="on">Vitrine</a><a href="http://localhost:8765/editor">✎ Editor</a></div>
<div class="brands" id="brands"></div>
<div class="wrap" id="wrap"></div>
<div class="ov" id="ov"><span class="x" onclick="fechar()">×</span><div class="modal" id="modal"></div></div>
<script>
const D = /*DADOS*/;
const NOME={"smark":"smark","provider-max":"providermax","elever-ai":"eleverai"};
let cur="smark";
function tabs(){const el=document.getElementById("brands");el.innerHTML="";
  Object.keys(D.marcas).forEach(m=>{const b=document.createElement("span");b.className="bt"+(m===cur?" on":"");
    b.textContent=({"smark":"smark","provider-max":"Provider Max","elever-ai":"Elever AI"})[m];
    b.onclick=()=>{cur=m;tabs();view();};el.appendChild(b);});}
function view(){const o=D.marcas[cur],w=document.getElementById("wrap");
  const cells=o.recs.map((r,i)=>`<div class="cell" style="background-image:url('${encodeURI(r.thumb)}')" onclick="abrir(${i})">
    ${r.formato==="carrossel"?'<span class="car">▦</span>':''}<span class="badge">${r.tipo}</span></div>`).join("");
  w.innerHTML=`<div class="profile"><div class="av">${o.sym}</div><div class="pinfo">
    <div class="h"><span class="hn">${o.handle.replace('@','')}</span></div>
    <div class="stats"><span><b>10</b> publicações</span><span><b>—</b> seguidores</span><span><b>—</b> seguindo</span></div>
    <div class="bio">${o.bio}</div></div></div>
    <div class="grid">${cells}</div>
    <div class="hint">Simulação (fundo placeholder, sem gastar API). Clique numa arte pra ver a copy e aprovar.</div>`;}
function abrir(i){const r=D.marcas[cur].recs[i],m=document.getElementById("modal");
  m.innerHTML=`<img src="${encodeURI(r.thumb)}"><div class="side">
    <span class="tipo">${r.tipo}</span> &nbsp;<span style="color:#8a83a0;font-size:12px">${r.formato} · ${r.tema}</span>
    <div class="lab">Legenda Instagram (rascunho)</div><div class="cap">${r.caption}</div>
    <div class="lab">Status</div><div class="cap">Aguardando sua aprovação. Diga "aprovo ${cur} ${r.n}" ou peça ajuste na copy.</div>
  </div>`;document.getElementById("ov").classList.add("on");}
function fechar(){document.getElementById("ov").classList.remove("on");}
document.getElementById("ov").onclick=e=>{if(e.target.id==="ov")fechar();};
tabs();view();
</script></body></html>"""


if __name__ == "__main__":
    print("Renderizando artes (placeholder, sem API)...")
    d = load()
    render_all(d)
    save(d)
    build_html(d)
    print(f"OK: lancamento.json + lancamento.html — abra no navegador (ou rode o editor).")
