#!/usr/bin/env python3
"""PAINEL DE CONTEÚDO — dashboard local (painel.html) que abre no navegador, sem servidor.
Varre notas .md + artes de marcas/*/publicacoes/**, cruza dados e embute no HTML.
Preview em formato Instagram/LinkedIn, download por arquivo, filtros e busca.
Atualizar:  python3 scripts/painel.py
"""
import json
import os
import re
import glob
import datetime

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fm(txt):
    d = {}
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                d[k.strip()] = v.strip().strip('"')
    return d


def secao(txt, nome):
    m = re.search(rf"^##\s*{nome}\s*\n(.*?)(?=^##\s|\Z)", txt, re.S | re.M | re.I)
    return m.group(1).strip() if m else ""


def mtime(p):
    return datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()


def achar_thumb(note_path, fmd, body):
    notedir = os.path.dirname(note_path)
    cands = []
    arte = fmd.get("arte", "")
    if arte:
        ap = os.path.join(notedir, arte)
        if os.path.isdir(ap):
            cands += sorted(glob.glob(os.path.join(ap, "0*.png"))) or sorted(glob.glob(os.path.join(ap, "*.png")))
        elif ap.endswith(".png"):
            cands.append(ap)
    for m in re.findall(r"!\[\[([^\]]+\.png)\]\]", body):
        cands.append(os.path.join(notedir, m))
    for c in cands:
        if os.path.exists(c) and "bg" not in os.path.basename(c).lower():
            return os.path.relpath(c, VAULT)
    return ""


def marca_de(path):
    m = re.search(r"marcas/([^/]+)/", path)
    return m.group(1) if m else ""


def canal_de(path):
    if "/linkedin/" in path:
        return "linkedin"
    if "/instagram/" in path:
        return "instagram"
    if "/marketing/" in path:
        return "marketing"
    return "—"


def main():
    registros, usados = [], set()

    for nota in glob.glob(os.path.join(VAULT, "marcas", "*", "publicacoes", "**", "*.md"), recursive=True):
        if "/arte/" in nota:
            continue
        txt = open(nota, encoding="utf-8").read()
        d = fm(txt)
        marca = d.get("marca") or marca_de(nota)
        h1 = re.search(r"^#\s+(.+)", txt, re.M)
        titulo = d.get("tema") or (h1.group(1).strip() if h1 else os.path.basename(nota)[:-3])
        thumb = achar_thumb(nota, d, txt)
        if thumb:
            usados.add(os.path.join(VAULT, thumb))
        registros.append({
            "tipo": "post", "marca": marca, "canal": d.get("canal") or canal_de(nota),
            "formato": d.get("formato", ""), "status": d.get("status", "draft"),
            "data": d.get("data", "") or mtime(nota), "gerada": d.get("arte-gerada-em", "") or d.get("data", ""),
            "tema": titulo, "thumb": thumb,
            "legenda_ig": secao(txt, "Legenda Instagram") or secao(txt, "Legenda"),
            "legenda_li": secao(txt, "Legenda LinkedIn"),
            "hashtags": secao(txt, "Hashtags"),
            "drive": d.get("drive", ""), "alt": d.get("alt", ""),
            "arquivo": os.path.relpath(nota, VAULT),
        })

    for png in glob.glob(os.path.join(VAULT, "marcas", "*", "publicacoes", "**", "arte", "**", "*.png"), recursive=True):
        if png in usados or "bg" in os.path.basename(png).lower() or "_demo" in png:
            continue
        registros.append({
            "tipo": "arte", "marca": marca_de(png), "canal": canal_de(png), "formato": "",
            "status": "arte", "data": mtime(png), "gerada": mtime(png),
            "tema": os.path.basename(os.path.dirname(png)).lstrip("_").replace("-", " "),
            "thumb": os.path.relpath(png, VAULT),
            "legenda_ig": "", "legenda_li": "", "hashtags": "", "drive": "", "alt": "",
            "arquivo": os.path.relpath(png, VAULT),
        })

    registros.sort(key=lambda r: r["data"], reverse=True)
    html = (TEMPLATE.replace("/*DADOS*/", json.dumps(registros, ensure_ascii=False))
            .replace("{{GERADO}}", datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
            .replace("{{TOTAL}}", str(len(registros))))
    out = os.path.join(VAULT, "painel.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"OK: {out}  ({len(registros)} itens) — abra no navegador (duplo clique).")


TEMPLATE = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Painel de Conteúdo · Grupo Smark</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Archivo',sans-serif}
body{background:#0B0B0B;color:#EAEAF0}
.top{position:sticky;top:0;z-index:10;background:linear-gradient(180deg,#15121f,#0d0b14);border-bottom:1px solid rgba(255,255,255,.1);padding:20px 28px}
.top h1{font-family:'Anton';font-size:30px;letter-spacing:1px;text-transform:uppercase}
.top .meta{color:#9a93ad;font-size:13px;margin-top:4px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:16px 28px;border-bottom:1px solid rgba(255,255,255,.08)}
.bar input{flex:1;min-width:200px;background:#15151c;border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:10px 14px;color:#fff;font-size:14px}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{background:#15151c;border:1px solid rgba(255,255,255,.12);color:#cfcad8;border-radius:999px;padding:7px 14px;font-size:13px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.chip.on{background:#8B3CF7;border-color:#8B3CF7;color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px;padding:24px 28px}
.card{background:#121119;border:1px solid rgba(255,255,255,.1);border-radius:16px;overflow:hidden;cursor:pointer;transition:.15s}
.card:hover{border-color:#8B3CF7;transform:translateY(-2px)}
.card .thumb{width:100%;aspect-ratio:4/5;background:#1c1a26 center/cover no-repeat;display:flex;align-items:center;justify-content:center;color:#544f63;font-size:12px}
.card .b{padding:12px 14px}
.card .tt{font-weight:800;font-size:15px;line-height:1.25;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tags{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.t{font-size:11px;font-weight:700;border-radius:6px;padding:3px 8px;display:inline-flex;align-items:center;gap:4px}
.t.marca{background:#8B3CF7;color:#fff}
.t.canal{background:#23202e;color:#c9c2da}
.t.st{border:1px solid}.st-draft{color:#f0b95c;border-color:#f0b95c66}.st-arte{color:#8a8a96;border-color:#8a8a9666}
.st-aprovado{color:#46E89A;border-color:#46E89A66}.st-publicado{color:#6BA5FF;border-color:#6BA5FF66}
.card .dt{color:#7a7486;font-size:11px;margin-top:8px}
.empty{padding:60px;text-align:center;color:#6a6478}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.72);display:none;z-index:50;padding:24px;overflow:auto}
.ov.on{display:flex;align-items:center;justify-content:center}
.modal{background:#121119;border:1px solid rgba(255,255,255,.14);border-radius:18px;max-width:900px;width:100%;max-height:92vh;overflow:auto;display:grid;grid-template-columns:380px 1fr}
.modal .preview{padding:22px;background:#0c0b12;border-radius:18px 0 0 18px;display:flex;align-items:center;justify-content:center}
.modal .side{padding:24px 26px}
.modal h2{font-size:21px;font-weight:800;margin-bottom:8px}
.modal .row{margin:14px 0}
.modal .lab{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#8a83a0;font-weight:800;margin-bottom:6px}
.modal .cap{background:#0c0b12;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:12px 14px;white-space:pre-wrap;font-size:14px;line-height:1.5;color:#dcd7e8}
.dl{display:inline-flex;align-items:center;gap:8px;background:#8B3CF7;color:#fff;font-weight:800;text-decoration:none;border-radius:10px;padding:11px 18px;font-size:14px;margin-top:6px}
.x{position:fixed;top:24px;right:30px;font-size:30px;color:#fff;cursor:pointer;z-index:60}
/* mockup Instagram */
.mock{width:340px;max-width:100%;border-radius:14px;overflow:hidden;background:#fff;color:#111;font-size:13px}
.mock.ig .hd{display:flex;align-items:center;gap:9px;padding:10px 12px}
.mock.ig .av{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#9A4DFF,#2A1CA8);display:flex;align-items:center;justify-content:center;color:#fff;font-size:14px}
.mock.ig .nm{font-weight:700;font-size:13px;flex:1}
.mock .img{width:100%;aspect-ratio:4/5;background:#eee center/cover no-repeat}
.mock.ig .acts{display:flex;gap:14px;padding:10px 12px 4px;font-size:18px}
.mock.ig .acts .save{margin-left:auto}
.mock.ig .likes{font-weight:700;padding:0 12px}
.mock.ig .cap{padding:6px 12px 14px;line-height:1.4;color:#222}
.mock.ig .cap b{font-weight:700}
.mock .more{color:#8a8a8a}
/* mockup LinkedIn */
.mock.li{background:#fff}
.mock.li .hd{display:flex;align-items:center;gap:10px;padding:12px}
.mock.li .av{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#9A4DFF,#2A1CA8);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:15px}
.mock.li .nm{font-weight:700;font-size:14px}
.mock.li .sub{color:#666;font-size:12px}
.mock.li .txt{padding:0 12px 10px;line-height:1.45;color:#222}
.mock.li .react{display:flex;gap:8px;padding:10px 12px;border-top:1px solid #eee;color:#666;font-size:12px}
@media(max-width:700px){.modal{grid-template-columns:1fr}.modal .preview{border-radius:18px 18px 0 0}}
</style></head><body>
<div class="top"><div style="display:flex;align-items:center;gap:18px;margin-bottom:6px">
  <h1 style="margin:0">Grupo Smark</h1>
  <a href="http://localhost:8765/painel" style="color:#fff;background:#8B3CF7;text-decoration:none;font-weight:700;font-size:13px;padding:7px 14px;border-radius:9px">Conteúdo</a>
  <a href="http://localhost:8765/vitrine" style="color:#9a93ad;text-decoration:none;font-weight:700;font-size:13px;padding:7px 14px;border-radius:9px">Vitrine</a>
  <a href="http://localhost:8765/editor" style="color:#9a93ad;text-decoration:none;font-weight:700;font-size:13px;padding:7px 14px;border-radius:9px">✎ Editor</a></div>
  <div class="meta">{{TOTAL}} itens · atualizado {{GERADO}} · rode <b>python3 scripts/painel.py</b> pra atualizar</div></div>
<div class="bar"><input id="q" placeholder="Buscar por tema, copy, arquivo…">
  <div class="chips" id="fmarca"></div><div class="chips" id="fcanal"></div><div class="chips" id="fstatus"></div></div>
<div class="grid" id="grid"></div>
<div class="ov" id="ov"><span class="x" onclick="fechar()">×</span><div class="modal" id="modal"></div></div>
<script>
const DADOS = /*DADOS*/;
const NOME={"smark":"smark","provider-max":"Provider Max","elever-ai":"Elever AI"};
const HANDLE={"smark":"@smark","provider-max":"@providermax","elever-ai":"@eleverai"};
let fMarca="",fCanal="",fStatus="",q="";
const IG='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none"/></svg>';
const LI='<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM10 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.4c0-1.3 0-2.95-1.8-2.95-1.8 0-2.08 1.4-2.08 2.85V21h-4z"/></svg>';
function canalIcon(c){if(c==="instagram")return IG+' Instagram';if(c==="linkedin")return LI+' LinkedIn';return c;}
function uniq(k){return [...new Set(DADOS.map(d=>d[k]).filter(Boolean))];}
function mkChips(id,vals,cur,set){const el=document.getElementById(id);el.innerHTML="";
  [["","todos"]].concat(vals.map(v=>[v,NOME[v]||v])).forEach(([v,label])=>{
    const c=document.createElement("span");c.className="chip"+(cur()===v?" on":"");
    c.innerHTML=(id==="fcanal"?canalIcon(v)||label:label);if(!v)c.textContent=label;
    c.onclick=()=>{set(v);renderChips();render();};el.appendChild(c);});}
function renderChips(){mkChips("fmarca",uniq("marca"),()=>fMarca,v=>fMarca=v);
  mkChips("fcanal",uniq("canal"),()=>fCanal,v=>fCanal=v);mkChips("fstatus",uniq("status"),()=>fStatus,v=>fStatus=v);}
function stCls(s){return "st-"+(s||"draft");}
function trunc(t,n){t=(t||"").trim();return t.length>n?t.slice(0,n)+"… ":t+" ";}
function render(){const g=document.getElementById("grid");g.innerHTML="";
  const list=DADOS.filter(d=>(!fMarca||d.marca===fMarca)&&(!fCanal||d.canal===fCanal)&&(!fStatus||d.status===fStatus)&&(!q||JSON.stringify(d).toLowerCase().includes(q)));
  if(!list.length){g.innerHTML='<div class="empty">Nada encontrado.</div>';return;}
  list.forEach(d=>{const c=document.createElement("div");c.className="card";c.onclick=()=>abrir(d);
    const th=d.thumb?`<div class="thumb" style="background-image:url('${encodeURI(d.thumb)}')"></div>`:`<div class="thumb">sem imagem</div>`;
    c.innerHTML=th+`<div class="b"><div class="tt">${d.tema||"(sem título)"}</div><div class="tags">
      <span class="t marca">${NOME[d.marca]||d.marca}</span>
      <span class="t canal" title="${d.canal}">${canalIcon(d.canal)}</span>
      <span class="t st ${stCls(d.status)}">${d.status}</span></div>
      <div class="dt">${d.tipo==="post"?"📝 post":"🖼️ arte"} · ${d.data}</div></div>`;
    g.appendChild(c);});}
function mockup(d){
  const h=HANDLE[d.marca]||"@marca", img=d.thumb?`style="background-image:url('${encodeURI(d.thumb)}')"`:"";
  if(d.canal==="linkedin"){
    const cap=d.legenda_li||d.legenda_ig||"(sem legenda — gere a copy)";
    return `<div class="mock li"><div class="hd"><div class="av">in</div><div><div class="nm">${NOME[d.marca]||d.marca}</div><div class="sub">uma plataforma smark · 2h · 🌐</div></div></div>
      <div class="txt">${trunc(cap,160)}<span class="more">…ver mais</span></div><div class="img" ${img}></div>
      <div class="react">👍❤️ 84 · 12 comentários · 5 compart.</div></div>`;}
  const cap=d.legenda_ig||"(sem legenda — gere a copy)";
  return `<div class="mock ig"><div class="hd"><div class="av">✦</div><div class="nm">${h.replace('@','')}</div><div>•••</div></div>
    <div class="img" ${img}></div><div class="acts"><span>♡</span><span>💬</span><span>✈</span><span class="save">🔖</span></div>
    <div class="likes">128 curtidas</div><div class="cap"><b>${h.replace('@','')}</b> ${trunc(cap,120)}<span class="more">mais</span></div></div>`;}
function abrir(d){const m=document.getElementById("modal");
  const cap=(lab,v)=>v?`<div class="row"><div class="lab">${lab}</div><div class="cap">${v}</div></div>`:"";
  const dl=d.thumb?`<a class="dl" href="${encodeURI(d.thumb)}" download>⬇ Baixar imagem</a>`:"";
  m.innerHTML=`<div class="preview">${mockup(d)}</div><div class="side">
    <h2>${d.tema||"(sem título)"}</h2>
    <div class="tags"><span class="t marca">${NOME[d.marca]||d.marca}</span>
      <span class="t canal" title="${d.canal}">${canalIcon(d.canal)}</span>
      <span class="t st ${stCls(d.status)}">${d.status}</span></div>
    <div class="row"><div class="lab">Dados</div><div class="cap">canal: ${d.canal}
formato: ${d.formato||"—"}
data: ${d.data}   ·   gerada: ${d.gerada||"—"}
arquivo: ${d.arquivo}${d.alt?"\nalt: "+d.alt:""}</div></div>
    ${cap("Legenda · Instagram",d.legenda_ig)}${cap("Legenda · LinkedIn",d.legenda_li)}${cap("Hashtags",d.hashtags)}
    <div class="row">${dl}</div>${d.drive?`<div class="row"><div class="lab">Drive</div><div class="cap">${d.drive}</div></div>`:""}
  </div>`;document.getElementById("ov").classList.add("on");}
function fechar(){document.getElementById("ov").classList.remove("on");}
document.getElementById("ov").onclick=e=>{if(e.target.id==="ov")fechar();};
document.getElementById("q").oninput=e=>{q=e.target.value.toLowerCase();render();};
renderChips();render();
const op=new URLSearchParams(location.search).get("open");if(op!==null&&DADOS[op])abrir(DADOS[op]);
</script></body></html>"""


if __name__ == "__main__":
    main()
