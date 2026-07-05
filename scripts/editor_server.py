#!/usr/bin/env python3
"""SUPER EDITOR — servidor local do editor de arte por FRAME (localhost:8765).

Preview ao vivo (mesmo HTML/CSS do compositor) + export do PNG final + upload de fundo
+ regerar fundo de IA. Fonte de dados: editor.json (posts → frames).

Rodar:  python3 scripts/editor_server.py   →   http://localhost:8765
"""
import base64
import glob
import hashlib
import http.server
import json
import os
import re
import secrets
import threading
import socketserver
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compositor  # noqa: E402
import estudio  # noqa: E402  (cérebro do chat: copy + conceito visual)

PORT = 8765
PAINEL = os.path.join(VAULT, "painel.html")
VITRINE = os.path.join(VAULT, "lancamento.html")

HUB = """<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>smark · Sistema</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css">
<style>
body.sk{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px}
.wrap{max-width:820px;width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:30px}
a.tile{display:block;text-decoration:none;color:inherit}
a.tile .sk-card{transition:.15s;height:100%}
a.tile:hover .sk-card{border-color:var(--accent);transform:translateY(-2px)}
.ic{font-size:28px;margin-bottom:12px;display:block}
.tile b{font-size:16px;display:block;margin-bottom:5px}
.tile p{color:var(--muted);font-size:12.5px;line-height:1.45}
.foot{color:var(--muted);font-size:11px;margin-top:30px;text-align:center}
</style></head><body class="sk">
<div class=wrap>
<div class=sk-kicker>tudo local · localhost:8765</div>
<h1 class=sk-h1 style="font-size:52px;margin-top:8px">Grupo <span class=sk-accent>smark</span> · Sistema</h1>
<div class=grid>
  <a class=tile href="/editor"><div class=sk-card><span class=ic>✎</span><b>Super Editor</b><p>Edita arte frame a frame, preview ao vivo, troca de fundo, cor, upload e regenerar por IA.</p></div></a>
  <a class=tile href="/painel"><div class=sk-card><span class=ic>▦</span><b>Painel de Conteúdo</b><p>Todas as publicações com preview de Instagram/LinkedIn e download.</p></div></a>
  <a class=tile href="/vitrine"><div class=sk-card><span class=ic>▤</span><b>Vitrine</b><p>Galeria read-only por marca — feed pra aprovar copy e conceito.</p></div></a>
  <a class=tile href="/config"><div class=sk-card><span class=ic>⚙</span><b>Configurações</b><p>Como o sistema está se comportando: temas, cores, degradês, conceitos e estado.</p></div></a>
  <a class=tile href="/design-system/dist/smark-design-system.html"><div class="sk-card sk-card--brand"><span class=ic>◈</span><b style="color:#fff">Design System</b><p style="color:#ffffffcc">Catálogo vivo: tokens, botões, cards, badges e o toggle claro/escuro. Fonte visual do painel.</p></div></a>
</div>
<div class=foot>Editor, Painel, Vitrine e Design System servidos pelo mesmo servidor.</div>
</div>
</body></html>"""

SMARK_MARK = "M50 7 L86 90 L50 58 L14 90 Z M41 46 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0 Z"


def smark_logo(h=26, wordmark=True, word="smark", suffix=""):
    """Logo oficial da smark: brasão (seta A em quadrado roxo) + wordmark. Usado em todo o sistema."""
    r = round(h * 0.28)
    g = round(h * 0.62)
    mark = (f'<span style="display:inline-flex;align-items:center;justify-content:center;width:{h}px;height:{h}px;'
            f'border-radius:{r}px;background:linear-gradient(155deg,#9A4DFF,#2A1CA8);flex:0 0 auto">'
            f'<svg viewBox="0 0 100 100" width="{g}" height="{g}"><path fill-rule="evenodd" fill="#fff" d="{SMARK_MARK}"/></svg></span>')
    if not wordmark:
        return mark
    fs = round(h * 0.82)
    suf = (f'<span style="font-family:var(--font-text);font-weight:700;font-size:{round(h*0.5)}px;'
           f'color:var(--muted);margin-left:4px">{suffix}</span>') if suffix else ""
    return (f'<span style="display:inline-flex;align-items:center;gap:9px">{mark}'
            f'<span style="font-family:var(--font-text);font-weight:800;font-size:{fs}px;letter-spacing:-.01em;'
            f'color:var(--text)">{word}<span style="color:var(--accent)">.</span></span>{suf}</span>')


def claude_logo(h=14):
    """Brasão laranja do Claude (sunburst estilizado)."""
    return (f'<svg viewBox="0 0 24 24" width="{h}" height="{h}" style="flex:0 0 auto">'
            f'<g fill="#D97757"><path d="M12 2.5c.3 0 .5.2.6.5l.9 4.3 3.1-3.1c.3-.3.7-.2.8.2l.5 2.9 2.9.5c.4.1.5.5.2.8l-3.1 3.1 4.3.9c.5.1.5.9 0 1l-4.3.9 3.1 3.1c.3.3.2.7-.2.8l-2.9.5-.5 2.9c-.1.4-.5.5-.8.2l-3.1-3.1-.9 4.3c-.1.5-.9.5-1 0l-.9-4.3-3.1 3.1c-.3.3-.7.2-.8-.2l-.5-2.9-2.9-.5c-.4-.1-.5-.5-.2-.8l3.1-3.1-4.3-.9c-.5-.1-.5-.9 0-1l4.3-.9-3.1-3.1c-.3-.3-.2-.7.2-.8l2.9-.5.5-2.9c.1-.4.5-.5.8-.2l3.1 3.1.9-4.3c.1-.3.3-.5.6-.5z"/></g></svg>')


def fmt_tipo(n):
    """Tipagem do formato pela contagem de frames (item 6)."""
    return "post único" if n <= 1 else f"carrossel · {n}"


def topbar(active=""):
    """App shell topbar (.sk-topbar) — substitui o botão flutuante de menu em todas as telas."""
    def lk(href, label, key):
        cls = "sk-navlink is-active" if key == active else "sk-navlink"
        return f'<a class="{cls}" href="{href}">{label}</a>'
    return ('<div class="sk-topbar">'
            f'<a href="/" style="text-decoration:none;margin-right:6px">{smark_logo(26)}</a>'
            + lk("/painel", "Painel", "painel") + lk("/vitrine", "Vitrine", "vitrine")
            + lk("/config", "Config", "config") + lk("/editor", "Editor", "editor")
            + '<span class="sk-spacer"></span>'
            '<a class="sk-btn sk-btn--secondary sk-btn--sm" href="/editor">✎ Abrir editor</a>'
            '</div>')


def config_html():
    """Tela read-only das configurações do sistema (como ele está se comportando)."""
    try:
        tok = json.load(open(os.path.join(VAULT, "design-system", "tokens", "tokens.json"), encoding="utf-8"))
    except Exception:
        tok = {}
    try:
        import _direcao
        conceitos = list(getattr(_direcao, "CONCEITOS", {}).keys())
    except Exception:
        conceitos = []
    ed = load() if os.path.isfile(DATA) else {"posts": []}
    fund = tok.get("fundacao", {})
    marcas = tok.get("marcas", {})
    tp = tok.get("tema_padrao") or "claro"
    defsize = tok.get("editor_defaults", {}).get("size", "1080x1350")
    sw = lambda c: f"<span style='display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;margin-right:6px;background:{c};border:1px solid #333'></span>"
    rows_m = "".join(
        f"<tr><td><b>{m.get('nome', s)}</b></td><td>{sw(m.get('acento','#000'))}{m.get('acento','')}</td>"
        f"<td>{sw(m.get('acento_claro', m.get('acento','#000')))}{m.get('acento_claro','—')}</td>"
        f"<td style='font-size:11px;max-width:260px;word-break:break-all'>{m.get('gradiente','—')}</td>"
        f"<td><input class=\"sk-input\" style=\"padding:7px 10px;font-size:13px\" id='cf_h_{s}' value='{m.get('handle','')}'></td></tr>" for s, m in marcas.items())
    rows_p = "".join(
        f"<tr><td>{i+1}</td><td>{p.get('titulo','')}</td><td>{p.get('slug','')}</td>"
        f"<td>{len(p.get('frames',[]))}</td></tr>" for i, p in enumerate(ed.get("posts", [])))
    chips = " ".join(f"<span class='sk-pill'>{c}</span>" for c in conceitos)
    return f"""<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Configurações · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{{padding:0}}
.wrap{{padding:24px 30px 60px;max-width:1000px;margin:0 auto}}
.sk-pagehead h1{{font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:32px;margin:6px 0 4px}}h1 span{{color:var(--accent)}} .sub{{color:var(--muted);font-size:13px}}
.gh{{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:12px}}
.sk-card{{margin-bottom:16px;max-width:880px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.06em}}
tr:last-child td{{border-bottom:0}}
.kv{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}.kv .cell{{background:var(--inset);border:1px solid var(--line);border-radius:var(--radius-md);padding:8px 12px;font-size:13px}}.kv b{{color:var(--accent-2)}}
.ok{{color:var(--good);font-weight:600}}
.sk-input.mini,.sk-select.mini{{padding:7px 10px;font-size:13px;width:auto}}
</style></head><body class="sk">
{topbar("config")}
<div class=wrap>
<div class="sk-pagehead"><div>
<div class=sk-kicker>painel local · tokens.json</div>
<h1>Configurações do <span>Sistema</span></h1>
<div class=sub>Edite os padrões e os handles das marcas — salva no tokens.json.</div></div></div>

<div class="sk-card"><div class=gh>Padrões editáveis</div><div class=kv>
<div class=cell>Tema-padrão: <select class="sk-select mini" id=cf_tema><option value=claro>claro</option><option value=escuro>escuro</option></select></div>
<div class=cell>Template padrão (tamanho): <select class="sk-select mini" id=cf_size><option value=1080x1350>Feed 4:5</option><option value=1080x1080>Quadrado 1:1</option><option value=1080x1920>Story 9:16</option></select></div>
<div class=cell>Assinatura padrão (rodapé direito): <input class="sk-input mini" id=cf_rodape value="{fund.get('rodape','')}" style="width:180px"></div>
</div>
<div style="margin-top:12px;color:var(--muted);font-size:12px">Regra #9: imagens geradas saem <b style="color:var(--accent-2)">claras</b> por padrão · Base clara {tok.get('tema_claro',{}).get('base','#F4F2FB')} · Base escura {fund.get('base','#0B0B0B')} · Rodapé {fund.get('rodape','—')}</div>
<div style="margin-top:14px"><button class="sk-btn" id=cf_save>💾 Salvar configurações</button> <span id=cf_msg class=ok></span></div>
</div>

<div class="sk-card"><div class=gh>Marcas (cores / degradê / handle editável)</div>
<table><tr><th>Marca</th><th>Acento</th><th>Acento claro</th><th>Degradê</th><th>Handle</th></tr>{rows_m}</table></div>

<div class="sk-card"><div class=gh>Conceitos de direção de arte ({len(conceitos)})</div>{chips}</div>

<div class="sk-card"><div class=gh>Posts no editor ({len(ed.get('posts',[]))})</div>
<table><tr><th>#</th><th>Título</th><th>Slug</th><th>Frames</th></tr>{rows_p}</table></div>

<div class="sk-card"><div class=gh>Servidor & segurança</div><div class=kv>
<div class=cell>Porta: <b>{PORT}</b></div>
<div class=cell>Hosts permitidos: <b>localhost:8765 / 127.0.0.1:8765</b></div>
<div class=cell>Proteção CSRF/DNS: <b class=ok>ativa</b> (Host+Origin+token)</div>
<div class=cell>Dados do editor: <b>editor.json</b></div>
</div></div>
</div>
<script>
const T="__EDITOR_TOKEN__";
document.getElementById('cf_tema').value="{tp}";
document.getElementById('cf_size').value="{defsize}";
document.getElementById('cf_save').onclick=async()=>{{
  const handles={{}};document.querySelectorAll('[id^=\\"cf_h_\\"]').forEach(i=>handles[i.id.slice(5)]=i.value.trim());
  const r=await(await fetch('/config-save',{{method:'POST',headers:{{'Content-Type':'application/json','X-Editor-Token':T}},
    body:JSON.stringify({{tema_padrao:document.getElementById('cf_tema').value,size:document.getElementById('cf_size').value,rodape:document.getElementById('cf_rodape').value,handles:handles}})}})).json();
  document.getElementById('cf_msg').textContent=r.ok?'Salvo ✓':('Erro: '+(r.erro||''));
}};
</script>
</body></html>"""


def painel_html():
    """Painel de Conteúdo — novo layout: topbar + toolbar segmentada + cards .sk-post."""
    return ("""<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Painel de Conteúdo · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
.wrap{padding:26px 30px 60px;max-width:1240px;margin:0 auto}
.sk-pagehead h1{font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:34px;line-height:.96;margin:6px 0 4px}
.sk-pagehead .sub{color:var(--muted);font-size:13px}
.thumbimg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.thumbhost{position:absolute;inset:0;overflow:hidden;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px}
.thumbfr{position:absolute;top:0;left:0;border:0;transform-origin:top left;pointer-events:none;background:#000}
.chpill{display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.4)}
.chIG{background:linear-gradient(45deg,#f09433,#dc2743,#bc1888)}.chIN{background:#0a66c2}
.stdot{display:inline-block;width:9px;height:9px;border-radius:50%;flex:0 0 auto}.st-s{background:var(--good)}.st-r{background:var(--warn)}
.sk-post-meta{gap:7px}
/* modal estilo Instagram (item 9) */
.igm{max-width:420px;padding:0;overflow:hidden}
.igmhead{display:flex;align-items:center;gap:10px;padding:11px 13px}
.igmav{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent-2));flex:0 0 auto}
.igmtitle{flex:1;background:transparent;border:1px solid transparent;border-radius:8px;color:var(--text);font-weight:700;font-size:14px;padding:6px 8px;font-family:var(--font-text)}
.igmtitle:hover{border-color:var(--field-line)}.igmtitle:focus{outline:none;border-color:var(--accent);background:var(--field)}
.igmhead #mst{font-size:11px;color:var(--muted)}
.igmmedia{position:relative;background:#000;aspect-ratio:4/5;overflow:hidden}
.igmhost{position:absolute;inset:0;overflow:hidden}
.igmnav{position:absolute;top:50%;transform:translateY(-50%);z-index:2;background:#000a;color:#fff;border:0;width:32px;height:32px;border-radius:50%;font-size:18px;cursor:pointer}
.igmnav.l{left:8px}.igmnav.r{right:8px}
.igmpg{position:absolute;bottom:10px;left:0;right:0;text-align:center;color:#fff;font-size:12px;text-shadow:0 1px 3px #000}
.igmicons{display:flex;gap:15px;padding:10px 14px;font-size:21px}
.igmcap{padding:0 14px 12px;font-size:13px;line-height:1.4;color:var(--text);max-height:120px;overflow:auto;white-space:pre-wrap}
.igmbtns{display:flex;gap:8px;padding:0 14px 14px}
</style></head><body class="sk">
__TOPBAR__
<div class=wrap>
<div class="sk-pagehead">
  <div style="display:flex;align-items:center;gap:10px">__LOGOSTORE__</div>
  <div class="sk-pagehead-actions">
    <button class="sk-btn sk-btn--danger sk-btn--sm" id=delsel>🗑 Excluir selecionados</button>
    <a class="sk-btn" href="/editor">＋ Novo post</a></div>
</div>
<div class="sk-toolbar">
  <div class="sk-filter-group"><span class="sk-filter-label">Status</span><div class="sk-segmented" id=sfilters></div></div>
  <div class="sk-toolbar-sep"></div>
  <div class="sk-filter-group"><span class="sk-filter-label">Marca</span><div class="sk-segmented" id=filters></div></div>
  <span class="sk-spacer"></span>
  <span id=count style="font-size:12px;color:var(--muted)"></span>
</div>
<div class="sk-cardgrid" id=grid></div>
</div>
<div class="sk-overlay" id=modal style="display:none">
  <div class="sk-modal igm">
    <div class=igmhead><div class=igmav></div><input id=mtitle class=igmtitle title="clique pra editar o nome do post" spellcheck=false><span id=mst></span></div>
    <div class=igmmedia><div class=igmhost id=mhost></div>
      <button class="igmnav l" id=mprev>‹</button><button class="igmnav r" id=mnext>›</button>
      <div class=igmpg id=mpg></div></div>
    <div class=igmicons><span>&#9825;</span><span>&#128172;</span><span>&#10148;</span><span style="flex:1"></span><span>&#128278;</span></div>
    <div class=igmcap id=mcap></div>
    <div class=igmbtns><button class="sk-btn" id=mopen style="flex:2">✎ Abrir no editor</button><button class="sk-btn sk-btn--secondary" id=mclose style="flex:1">Fechar</button></div>
  </div>
</div>
<script>
const T="__EDITOR_TOKEN__";let D=null,FILT='',STATUSF='',MI=0,MP=0;const SEL=new Set();
async function load(){D=await(await fetch('/dados')).json();render()}
function brands(){return [...new Set(D.posts.map(p=>p.marca||'smark'))]}
function fmtTipo(n){return n<=1?'post único':'carrossel · '+n}
function chIcon(c){
  if(c==='linkedin')return '<span class="chpill chIN" title=LinkedIn><svg viewBox="0 0 24 24" width=13 height=13 fill="#fff"><path d="M4.98 3.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.4 8.65 21 11 21 14v7h-4v-6.2c0-1.48-.03-3.4-2.07-3.4-2.07 0-2.39 1.62-2.39 3.29V21H9z"/></svg></span>';
  return '<span class="chpill chIG" title=Instagram><svg viewBox="0 0 24 24" width=13 height=13 fill="none" stroke="#fff" stroke-width="2.1"><rect x="2" y="2" width="20" height="20" rx="5.5"/><circle cx="12" cy="12" r="4.3"/><circle cx="17.6" cy="6.4" r="1.2" fill="#fff" stroke="none"/></svg></span>';}
async function loadThumb(host,p){
  try{
    const fr=(p.frames||[])[0];if(!fr){host.innerHTML='sem arte';return}
    const r=await fetch('/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({frame:fr,size:p.size,marca:p.marca||'smark'})});
    const html=await r.text();
    const w=host.clientWidth||228,s=w/1080;
    const ifr=document.createElement('iframe');ifr.className='thumbfr';
    ifr.style.width='1080px';ifr.style.height='1350px';ifr.style.transform='scale('+s+')';
    host.innerHTML='';host.appendChild(ifr);ifr.srcdoc=html;
  }catch(e){host.textContent='sem arte'}
}
function seg(host,opts,cur,cb){host.innerHTML='';opts.forEach(([v,lb])=>{const b=document.createElement('button');b.textContent=lb;if(cur===v)b.className='is-active';b.onclick=()=>cb(v);host.appendChild(b)})}
function render(){
  seg(document.getElementById('sfilters'),[['','Todos'],['rascunho','Rascunho'],['salvo','Salvo']],STATUSF,v=>{STATUSF=v;render()});
  seg(document.getElementById('filters'),[['','Todas']].concat(brands().map(b=>[b,b])),FILT,v=>{FILT=v;render()});
  const g=document.getElementById('grid');g.innerHTML='';let n=0;
  const items=D.posts.map((p,i)=>({p,i})).reverse();
  items.forEach(({p,i})=>{
    if(FILT&&(p.marca||'smark')!==FILT)return;
    if(STATUSF&&(p.status||'rascunho')!==STATUSF)return;
    n++;
    const salvo=p.status==='salvo';
    const badge='<span class="stdot '+(salvo?'st-s':'st-r')+'" title="'+(salvo?'salvo':'rascunho')+'"></span>';
    const ch=(p.canais||['instagram']).map(chIcon).join('');
    const on=SEL.has(i);
    const c=document.createElement('div');c.className='sk-post'+(on?' is-selected':'');
    c.dataset.pi=i;
    c.innerHTML='<div class="sk-post-thumb">'
      +'<div class="thumbhost">carregando…</div>'
      +'<div class="sk-post-check'+(on?' is-on':'')+'" data-i="'+i+'">✓</div>'
      +'<div class="sk-post-channel">'+ch+'</div>'
      +'</div><div class="sk-post-body">'
      +'<div class="sk-post-title">'+(p.titulo||p.slug)+'</div>'
      +'<div class="sk-post-meta">'+badge+(p.marca||'smark')+'<span class=sk-dot></span>'+fmtTipo(p.frames?p.frames.length:0)+'</div>'
      +'<div class="sk-post-actions">'
      +'<button data-a=ver data-i="'+i+'" title=Ver>👁</button>'
      +'<button class=act-edit data-a=edit data-i="'+i+'" title=Editar>✎</button>'
      +'<button data-a=dup data-i="'+i+'" title=Duplicar>⧉</button>'
      +'<button class=act-del data-a=del data-i="'+i+'" title=Excluir>🗑</button>'
      +'</div></div>';
    g.appendChild(c)});
  document.getElementById('count').textContent=n+' publicação'+(n===1?'':'ões');
  // lazy-load das miniaturas compiladas (mostra a headline, nunca quebra)
  const io=new IntersectionObserver((es)=>{es.forEach(en=>{if(en.isIntersecting){const card=en.target;io.unobserve(card);
    const host=card.querySelector('.thumbhost');const pi=+card.dataset.pi;if(host&&D.posts[pi])loadThumb(host,D.posts[pi])}})},{rootMargin:'200px'});
  g.querySelectorAll('.sk-post').forEach(card=>io.observe(card));
}
document.getElementById('grid').addEventListener('click',e=>{
  const chk=e.target.closest('.sk-post-check');if(chk){const i=+chk.dataset.i;SEL.has(i)?SEL.delete(i):SEL.add(i);render();return}
  const b=e.target.closest('[data-a]');if(!b)return;const i=+b.dataset.i,a=b.dataset.a;
  if(a==='ver')ver(i);else if(a==='edit')location.href='/editor?post='+i;else if(a==='dup')dupPost(i);else if(a==='del')del([i]);
});
async function ver(i){MP=i;MI=0;const p=D.posts[i];
  document.getElementById('modal').style.display='flex';
  document.getElementById('mtitle').value=p.titulo||p.slug||'';
  document.getElementById('mst').innerHTML=(p.status==='salvo'?'<span class="stdot st-s"></span> salvo':'<span class="stdot st-r"></span> rascunho');
  document.getElementById('mcap').textContent=p.caption||'';mframe()}
async function mframe(){const p=D.posts[MP],fr=p.frames[MI],host=document.getElementById('mhost');
  const r=await fetch('/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({frame:fr,size:p.size,marca:p.marca||'smark'})});
  const html=await r.text();const s=(host.clientWidth||420)/1080;
  host.innerHTML='';const ifr=document.createElement('iframe');ifr.style.cssText='position:absolute;top:0;left:0;border:0;width:1080px;height:1350px;transform-origin:top left;pointer-events:none;transform:scale('+s+')';host.appendChild(ifr);ifr.srcdoc=html;
  document.getElementById('mpg').textContent=(MI+1)+'/'+p.frames.length;
  const one=p.frames.length<2;['mprev','mnext','mpg'].forEach(id=>document.getElementById(id).style.display=one?'none':'')}
document.getElementById('mprev').onclick=()=>{const n=D.posts[MP].frames.length;MI=(MI-1+n)%n;mframe()};
document.getElementById('mnext').onclick=()=>{const n=D.posts[MP].frames.length;MI=(MI+1)%n;mframe()};
document.getElementById('mopen').onclick=()=>location.href='/editor?post='+MP;
document.getElementById('mclose').onclick=()=>document.getElementById('modal').style.display='none';
document.getElementById('mtitle').onchange=async e=>{const t=e.target.value.trim();if(!t)return;
  await fetch('/renomear',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:MP,titulo:t})});D.posts[MP].titulo=t;render()};
async function del(idx){if(!idx.length){alert('Selecione ao menos um');return}
  if(!confirm('Excluir '+idx.length+' publicação(ões)?'))return;
  await fetch('/excluir-posts',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:idx})});SEL.clear();await load()}
async function dupPost(i){await fetch('/duplicar-post',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:i})});await load()}
document.getElementById('delsel').onclick=()=>del([...SEL]);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
load();
</script></body></html>""").replace("__TOPBAR__", topbar("painel")).replace("__LOGOSTORE__", smark_logo(34, suffix="STORE"))


def vitrine_html():
    """Vitrine estilo feed do Instagram — todas as publicações do editor.json."""
    return ("""<!doctype html><html lang=pt-BR data-theme="claro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Vitrine · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{padding-bottom:50px}
.top{text-align:center;padding:14px;font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:16px;letter-spacing:.02em;border-bottom:1px solid var(--line);background:var(--surface)}.top span{color:var(--accent)}
.feed{max-width:440px;margin:18px auto;display:flex;flex-direction:column;gap:22px;padding:0 8px}
.post{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow)}
.ph{display:flex;align-items:center;gap:9px;padding:11px 13px;font-size:14px;font-weight:600}
.av{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent-2))}
.media{position:relative;background:#000;aspect-ratio:4/5;cursor:pointer;overflow:hidden}
.vhost{position:absolute;inset:0;overflow:hidden;background:#000}
.cbadge{position:absolute;top:10px;right:10px;background:#000a;color:#fff;font-size:12px;padding:2px 9px;border-radius:12px}
.dots{position:absolute;bottom:10px;left:0;right:0;display:flex;gap:5px;justify-content:center}
.dot{width:6px;height:6px;border-radius:50%;background:#ffffff88}.dot.on{background:#fff}
.icons{display:flex;gap:15px;padding:10px 13px;font-size:22px}
.cap{padding:0 13px 14px;font-size:14px;line-height:1.4;white-space:pre-wrap;color:var(--text)}.cap b{font-weight:600}
.empty{text-align:center;color:var(--muted);padding:40px;font-size:14px}
</style></head><body class="sk">
__TOPBAR__
<div class=top><span>smark</span> &middot; vitrine · feed pra aprovar</div>
<div class=feed id=feed></div>
<script>
const T="__EDITOR_TOKEN__";
async function compose(host,fr,p){
  try{
    const r=await fetch('/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({frame:fr,size:p.size,marca:p.marca||'smark'})});
    const html=await r.text();const s=(host.clientWidth||424)/1080;
    host.innerHTML='';const ifr=document.createElement('iframe');
    ifr.style.cssText='position:absolute;top:0;left:0;border:0;width:1080px;height:1350px;transform-origin:top left;pointer-events:none;transform:scale('+s+')';
    host.appendChild(ifr);ifr.srcdoc=html;
  }catch(e){host.textContent=''}
}
async function load(){const D=await(await fetch('/dados')).json();const f=document.getElementById('feed');f.innerHTML='';let n=0;
  D.posts.forEach(p=>{
    const frames=(p.frames||[]);if(!frames.length)return;n++;
    const el=document.createElement('div');el.className='post';
    el.innerHTML='<div class=ph><div class=av></div>'+(p.marca||'smark')+'<span style="flex:1"></span>&middot;&middot;&middot;</div>'
      +'<div class=media><div class=vhost></div><div class=cbadge>1/'+frames.length+'</div><div class=dots>'+frames.map((_,i)=>'<span class="dot'+(i?'':' on')+'"></span>').join('')+'</div></div>'
      +'<div class=icons><span>&#9825;</span><span>&#128172;</span><span>&#10148;</span><span style="flex:1"></span><span>&#128278;</span></div>'
      +'<div class=cap><b>'+(p.marca||'smark')+'</b> '+((p.caption||'').replace(/</g,'&lt;'))+'</div>';
    const host=el.querySelector('.vhost'),badge=el.querySelector('.cbadge'),dots=el.querySelectorAll('.dot');
    let idx=0;
    el.querySelector('.media').onclick=()=>{idx=(idx+1)%frames.length;compose(host,frames[idx],p);badge.textContent=(idx+1)+'/'+frames.length;dots.forEach((d,i)=>d.classList.toggle('on',i===idx))};
    f.appendChild(el);compose(host,frames[0],p);
  });
  if(!n)f.innerHTML='<div class=empty>Nenhum post ainda. Crie no editor pra ver aqui.</div>';
}
load();
</script></body></html>""").replace("__TOPBAR__", topbar("vitrine"))


# Segurança (CSRF / DNS rebinding): o servidor é local, mas tem rotas que gastam
# dinheiro (regerar-fundo→OpenAI) e escrevem em disco. Um site malicioso aberto no
# navegador poderia dar POST em localhost. Defesa: Host + Origin + token de sessão.
ALLOWED_HOSTS = {"127.0.0.1:8765", "localhost:8765"}
TOKEN = secrets.token_hex(16)  # novo a cada boot; injetado no HTML servido
DATA = os.path.join(VAULT, "editor.json")
UI = os.path.join(HERE, "_editor2.html")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".svg": "image/svg+xml", ".css": "text/css",
        ".js": "application/javascript", ".html": "text/html; charset=utf-8"}


IO_LOCK = threading.RLock()      # protege leitura/escrita do editor.json (servidor multi-thread)
GEN_SEM = threading.Semaphore(2)  # no máx. 2 gerações de IA simultâneas
JOBS = {}                         # id -> {"status": running|done|erro, "path":..., "erro":...}


def load():
    with IO_LOCK:
        return json.load(open(DATA, encoding="utf-8"))


def save(d):
    with IO_LOCK:
        json.dump(d, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _run_gen(job_id, cmd, out, pi, fi):
    """Roda a geração de IA em background (cap de 2 simultâneas). Persiste o fundo no editor.json."""
    with GEN_SEM:
        try:
            r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True)
        except Exception as e:
            JOBS[job_id] = {"status": "erro", "erro": str(e)}
            return
        if os.path.exists(out):
            rel = os.path.relpath(out, VAULT)
            try:  # persiste pra não perder ao sair da tela
                with IO_LOCK:
                    d = load()
                    if pi < len(d["posts"]) and fi < len(d["posts"][pi].get("frames", [])):
                        f = d["posts"][pi]["frames"][fi]
                        f["bg"] = rel
                        f["bgmode"] = "imagem"
                        save(d)
            except Exception:
                pass
            JOBS[job_id] = {"status": "done", "path": rel}
        else:
            JOBS[job_id] = {"status": "erro", "erro": (r.stderr or r.stdout or "falhou")[-400:]}


def _run_estudio(job_id, pedido, marca, n, tipo, contexto="", historico=None,
                 imagem_b64=None, imagem_mime="image/jpeg"):
    """Roda o cérebro do chat em background (chat é rápido, mas não trava a UI)."""
    with GEN_SEM:
        try:
            res, prov = estudio.gerar(pedido, marca, n, tipo, contexto, historico,
                                      imagem_b64, imagem_mime)
            JOBS[job_id] = {"status": "done", "resultado": res, "provider": prov}
        except Exception as e:
            JOBS[job_id] = {"status": "erro", "erro": str(e)}


def hl(text):
    """quebra de linha: '|' (legado) e Enter (newline real) → '\\n' que o compositor entende."""
    return (text or "").replace("\r", "").replace("|", "\\n").replace("\n", "\\n")


def frame_kwargs(fr, size, for_export, marca="smark"):
    """Traduz um frame do editor.json nos kwargs do compose_html.
    for_export=True embute a imagem (base64, render headless); False usa URL estática (preview leve)."""
    k = dict(marca=marca, headline=hl(fr.get("headline", "")), sub=hl(fr.get("sub", "")),
             cta=fr.get("cta", ""), page=fr.get("page", ""), no_chip=not fr.get("chip", False),
             tema=fr.get("tema", "escuro"), size=size, hsize=int(fr.get("hsize", 0) or 0),
             accent=fr.get("accent", ""), no_grade=not fr.get("grade", True),
             zoom=float(fr.get("zoom", 1.0) or 1.0), posx=int(fr.get("posx", 50)),
             posy=int(fr.get("posy", 50)), overlay=fr.get("overlay", "none"),
             overlay_op=float(fr.get("overlay_op", 0.85)),
             ov_ang=int(fr.get("ov_ang", 180)), ov_pos=int(fr.get("ov_pos", 20)),
             brilho=float(fr.get("brilho", 1.0)), contraste=float(fr.get("contraste", 1.0)),
             satur=float(fr.get("satur", 1.0)),
             handle_over=fr.get("handle", ""), rodape_over=fr.get("rodape", ""),
             raw=bool(fr.get("raw", False)))
    mode = fr.get("bgmode", "imagem")
    if mode == "imagem" and fr.get("bg"):
        if for_export:
            k["bg"] = fr["bg"]
        else:
            k["bg_url"] = "/" + urllib.parse.quote(fr["bg"])
    elif mode == "cor":
        k["base"] = fr.get("cor") or ""
    elif mode == "degrade":  # degradê claro da marca (instantâneo, sem IA)
        k["base"] = compositor.DEGRADE_CLARO
        k["tema"] = "claro"
    else:  # escuro | claro (preset com mesh)
        k["placeholder"] = True
        k["tema"] = "claro" if mode == "claro" else "escuro"
    return k


BRANDS = ("smark", "provider-max", "elever-ai")


def safe_marca(m):
    """Bloqueia path traversal via marca — só marcas conhecidas."""
    return m if m in BRANDS else "smark"


def safe_slug(s):
    """Bloqueia path traversal via slug — só kebab-case [a-z0-9-]."""
    s = re.sub(r"[^a-z0-9-]+", "-", (s or "").lower()).strip("-")
    return s or "post"


def normaliza(d):
    """Garante n sequencial, marca/slug seguros e caminho 'out' pra todo frame."""
    for p in d.get("posts", []):
        p["marca"] = safe_marca(p.get("marca", "smark"))
        p["slug"] = safe_slug(p.get("slug", ""))
        if not p.get("canais"):
            p["canais"] = ["instagram"]
        A = f"marcas/{p['marca']}/publicacoes/social/instagram/arte"
        for i, fr in enumerate(p.get("frames", []), 1):
            fr["n"] = i
            fr["out"] = f"{A}/{p['slug']}/{i:02d}.png"
    return d


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def _host_ok(self):
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def _post_allowed(self):
        """POST muda estado / gasta dinheiro → exige Host + Origin próprios + token."""
        if not self._host_ok():
            return False
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlparse(origin).netloc not in ALLOWED_HOSTS:
            return False
        return self.headers.get("X-Editor-Token", "") == TOKEN

    def _serve_module(self, fp, nome):
        if not os.path.isfile(fp):
            return self._send(200, f"<!doctype html><html data-theme='escuro'><head>"
                              f"<link rel='stylesheet' href='/design-system/dist/smark-ds.css'></head>"
                              f"<body class='sk' style='padding:40px'>"
                              f"<a class='sk-btn sk-btn--ghost' href='/'>← Menu</a><h2 class='sk-h2' style='margin-top:16px'>{nome} ainda não foi gerado.</h2></body></html>",
                              MIME[".html"])
        bar = ('<a href="/" style="position:fixed;top:8px;left:8px;z-index:99999;background:#8b3cf7;color:#fff;'
               'padding:6px 12px;border-radius:8px;font:600 12px sans-serif;text-decoration:none">☰ Menu</a>')
        html = open(fp, encoding="utf-8").read().replace("</body>", bar + "</body>", 1)
        return self._send(200, html, MIME[".html"])

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._host_ok():  # bloqueia DNS rebinding
            return self._send(403, {"erro": "host não permitido"})
        if path in ("/", "/menu"):
            return self._send(200, HUB, MIME[".html"])
        if path == "/editor":
            html = open(UI, encoding="utf-8").read().replace("__EDITOR_TOKEN__", TOKEN)
            return self._send(200, html, MIME[".html"])
        if path == "/painel":
            return self._send(200, painel_html().replace("__EDITOR_TOKEN__", TOKEN), MIME[".html"])
        if path == "/painel-notas":
            return self._serve_module(PAINEL, "Painel (notas)")
        if path == "/vitrine":
            return self._send(200, vitrine_html().replace("__EDITOR_TOKEN__", TOKEN), MIME[".html"])
        if path == "/vitrine-notas":
            return self._serve_module(VITRINE, "Vitrine (notas)")
        if path == "/config":
            return self._send(200, config_html().replace("__EDITOR_TOKEN__", TOKEN), MIME[".html"])
        if path == "/job":
            jid = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("id", [""])[0]
            return self._send(200, JOBS.get(jid, {"status": "unknown"}))
        if path == "/dados":
            return self._send(200, load())
        # arquivo estático dentro do vault (imagens)
        rel = urllib.parse.unquote(path.lstrip("/"))
        full = os.path.realpath(os.path.join(VAULT, rel))
        if full.startswith(VAULT) and os.path.isfile(full):
            ext = os.path.splitext(full)[1].lower()
            with open(full, "rb") as f:
                return self._send(200, f.read(), MIME.get(ext, "application/octet-stream"))
        return self._send(404, {"erro": "não encontrado"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if not self._post_allowed():
            return self._send(403, {"ok": False, "erro": "bloqueado (host/origin/token) — recarregue o editor"})
        try:
            req = self._body()
        except Exception as e:
            return self._send(400, {"ok": False, "erro": f"body inválido: {e}"})

        if path == "/preview":
            try:
                html, _, _ = compositor.compose_html(**frame_kwargs(req.get("frame", {}),
                                                     req.get("size", "1080x1350"), for_export=False,
                                                     marca=req.get("marca", "smark")))
                return self._send(200, html, MIME[".html"])
            except Exception as e:
                return self._send(200, f"<pre style='color:#f66;font-family:monospace;padding:20px'>preview erro: {e}</pre>", MIME[".html"])

        if path == "/salvar":
            save(normaliza(req.get("dados", load())))
            return self._send(200, {"ok": True})

        if path == "/excluir-posts":
            d = load()
            idx = sorted([i for i in req.get("idx", []) if isinstance(i, int) and 0 <= i < len(d["posts"])], reverse=True)
            for i in idx:
                d["posts"].pop(i)
            save(normaliza(d))
            return self._send(200, {"ok": True, "restantes": len(d["posts"])})

        if path == "/duplicar-post":
            d = load()
            i = req.get("idx")
            if not isinstance(i, int) or not (0 <= i < len(d["posts"])):
                return self._send(400, {"ok": False, "erro": "índice inválido"})
            import copy
            novo = copy.deepcopy(d["posts"][i])
            novo["titulo"] = (novo.get("titulo", "") + " (cópia)")[:80]
            novo["slug"] = safe_slug(novo.get("slug", "post")) + "-c" + secrets.token_hex(2)
            novo["status"] = "rascunho"
            d["posts"].append(novo)  # cópia vai pro fim (= mais nova)
            save(normaliza(d))
            return self._send(200, {"ok": True, "index": len(d["posts"]) - 1})

        if path == "/importar-notas":
            d = load()
            existing = {(p.get("marca"), p.get("slug")) for p in d["posts"]}
            novos = 0
            for note in sorted(glob.glob(os.path.join(VAULT, "marcas", "*", "publicacoes", "social", "instagram", "*.md"))):
                parts = os.path.relpath(note, VAULT).split(os.sep)
                marca = safe_marca(parts[1])
                slug = safe_slug(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(note)[:-3]))
                if (marca, slug) in existing:
                    continue
                txt = open(note, encoding="utf-8").read()
                mt = re.search(r"^tema:\s*(.+)$", txt, re.M) or re.search(r"^#\s+(.+)$", txt, re.M)
                titulo = (mt.group(1).strip() if mt else slug)[:80]
                ml = re.search(r"##\s*Legenda\s*\n(.*?)(?:\n##\s|\Z)", txt, re.S)
                mh = re.search(r"##\s*Hashtags\s*\n(.*?)(?:\n##\s|\Z)", txt, re.S)
                caption = (ml.group(1).strip() if ml else "") + (("\n\n" + mh.group(1).strip()) if mh else "")
                adir = os.path.join(os.path.dirname(note), "arte", slug)
                pngs = sorted(glob.glob(os.path.join(adir, "*.png"))) if os.path.isdir(adir) else []
                single = os.path.join(os.path.dirname(note), "arte", slug + ".png")
                if not pngs and os.path.exists(single):
                    pngs = [single]
                frames = [{"headline": "", "sub": "", "cta": "", "page": "", "chip": False,
                           "tema": "escuro", "bgmode": "imagem", "bg": os.path.relpath(pg, VAULT),
                           "raw": True, "grade": False} for pg in pngs]
                if not frames:
                    frames = [{"headline": titulo.upper(), "sub": "", "cta": "", "page": "",
                               "chip": True, "tema": "claro", "bgmode": "claro", "grade": True}]
                d["posts"].append({"slug": slug, "marca": marca, "titulo": titulo,
                                   "status": "rascunho", "size": "1080x1350",
                                   "caption": caption, "frames": frames, "importado": True})
                existing.add((marca, slug))
                novos += 1
            save(normaliza(d))
            return self._send(200, {"ok": True, "novos": novos, "total": len(d["posts"])})

        if path == "/config-save":
            try:
                tokp = os.path.join(VAULT, "design-system", "tokens", "tokens.json")
                tok = json.load(open(tokp, encoding="utf-8"))
                if req.get("tema_padrao") in ("claro", "escuro"):
                    tok["tema_padrao"] = req["tema_padrao"]
                if re.match(r"^\d{3,4}x\d{3,4}$", req.get("size", "")):
                    tok.setdefault("editor_defaults", {})["size"] = req["size"]
                rod = re.sub(r"[^@A-Za-z0-9_. ]", "", str(req.get("rodape", "")))[:40].strip()
                if rod:
                    tok.setdefault("fundacao", {})["rodape"] = rod
                for slug, h in (req.get("handles") or {}).items():
                    if slug in tok.get("marcas", {}):
                        h = re.sub(r"[^@A-Za-z0-9_.]", "", str(h))[:40]
                        if h:
                            tok["marcas"][slug]["handle"] = h if h.startswith("@") else "@" + h
                json.dump(tok, open(tokp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                return self._send(200, {"ok": True})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/novo-post":
            d = load()
            slug = safe_slug(req.get("slug", "")) if req.get("slug") else ("novo-" + secrets.token_hex(3))
            if any(p["slug"] == slug for p in d["posts"]):
                slug = slug + "-" + secrets.token_hex(2)
            marca = safe_marca(req.get("marca", "smark"))
            try:
                defs = json.load(open(os.path.join(VAULT, "design-system", "tokens", "tokens.json"), encoding="utf-8"))
            except Exception:
                defs = {}
            tema = defs.get("tema_padrao", "claro")
            size = defs.get("editor_defaults", {}).get("size", "1080x1350")
            fr = {"headline": "SEU TÍTULO|*AQUI.*", "sub": "", "cta": "", "page": "01/01",
                  "chip": True, "tema": tema, "bgmode": tema, "bg": "", "cor": "#F4F2FB",
                  "accent": "", "hsize": 0, "grade": True}
            d["posts"].append({"slug": slug, "marca": marca, "status": "rascunho",
                               "titulo": req.get("titulo") or "Novo post", "size": size,
                               "frames": [fr], "caption": "", "canais": ["instagram"]})
            save(normaliza(d))
            return self._send(200, {"ok": True, "index": len(d["posts"]) - 1, "slug": slug})

        if path == "/exportar":
            d = load()
            try:
                post = d["posts"][req["post"]]
                idxs = [req["frame"]] if req.get("frame") is not None and req.get("frame") != "all" \
                    else list(range(len(post["frames"])))
                feitas = []
                for i in idxs:
                    fr = post["frames"][i]
                    kw = frame_kwargs(fr, post.get("size", "1080x1350"), for_export=True,
                                      marca=post.get("marca", "smark"))
                    html, w, h = compositor.compose_html(**kw)
                    out = fr.get("out") or f"{os.path.dirname(post['frames'][0].get('out',''))}/{i+1:02d}.png"
                    if compositor.render_html_to_png(html, out, w, h):
                        feitas.append(out)
                return self._send(200, {"ok": True, "feitas": feitas})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/upload":
            try:
                data = req["dataurl"].split(",", 1)[1]
                raw = base64.b64decode(data)
                slug = safe_slug(req.get("slug", "avulso"))
                marca = safe_marca(req.get("marca", "smark"))
                dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram",
                                  "arte", slug, "_uploads")
                os.makedirs(dd, exist_ok=True)
                name = hashlib.sha1(raw).hexdigest()[:10] + ".png"
                full = os.path.join(dd, name)
                open(full, "wb").write(raw)
                return self._send(200, {"ok": True, "path": os.path.relpath(full, VAULT)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/regerar-fundo":
            try:
                d = load()
                post = d["posts"][req["post"]]
                fr = post["frames"][req["frame"]]
                slug = safe_slug(post.get("slug", ""))
                marca = safe_marca(post.get("marca", "smark"))
                dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram",
                                  "arte", slug, "_regen")
                os.makedirs(dd, exist_ok=True)
                out = os.path.join(dd, f"{req['frame']+1:02d}-{secrets.token_hex(3)}.png")
                ref = req.get("ref", "")
                if ref:  # referência → openai_edit (contexto do usuário como prompt)
                    ctx = (req.get("prompt", "") or "").strip()
                    full = ((ctx + ". ") if ctx else "") + (
                        "Keep the SAME lighting, color palette, mood, materials and overall composition "
                        "style as the reference image, so it matches the other slides of the carousel. "
                        "Brand key visual, abstract, premium, violet/roxo palette, editorial, "
                        "lower third kept clean for headline text, 4k, no text, no logos.")
                    cmd = ["python3", os.path.join(HERE, "openai_edit.py"),
                           "--image", os.path.join(VAULT, ref), "--out", out,
                           "--prompt", full, "--size", "1024x1536", "--quality", "high"]
                else:  # direção de arte (padrão claro, rule #9)
                    cmd = ["python3", os.path.join(HERE, "openai_image.py"), "--out", out, "--direcao",
                           "--marca", marca, "--tipo", req.get("tipo", "manifesto"),
                           "--tema", req.get("tema", "claro"),
                           "--headline", (fr.get("headline", "") or "").replace("|", " "),
                           "--size", "1024x1536", "--quality", "high"]
                    if req.get("conceito"):  # metáfora visual vinda do Estúdio IA
                        cmd += ["--conceito", str(req["conceito"])[:400]]
                job_id = secrets.token_hex(6)
                JOBS[job_id] = {"status": "running"}
                threading.Thread(target=_run_gen, args=(job_id, cmd, out, req["post"], req["frame"]),
                                 daemon=True).start()
                return self._send(200, {"ok": True, "job": job_id})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/estudio":
            try:
                pedido = (req.get("prompt", "") or "").strip()
                if not pedido:
                    return self._send(400, {"ok": False, "erro": "pedido vazio"})
                marca = safe_marca(req.get("marca", "smark"))
                n = max(1, min(10, int(req.get("n", 3) or 3)))
                tipo = req.get("tipo", "")
                contexto = str(req.get("contexto", ""))[:1500]
                historico = req.get("historico") if isinstance(req.get("historico"), list) else None
                img_b64 = req.get("imagem") or None
                img_mime = req.get("imagem_mime", "image/jpeg")
                job_id = secrets.token_hex(6)
                JOBS[job_id] = {"status": "running"}
                threading.Thread(target=_run_estudio,
                                 args=(job_id, pedido, marca, n, tipo, contexto, historico,
                                       img_b64, img_mime), daemon=True).start()
                return self._send(200, {"ok": True, "job": job_id})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/renomear":
            try:
                with IO_LOCK:
                    d = load()
                    i = int(req.get("idx", -1))
                    if 0 <= i < len(d["posts"]):
                        d["posts"][i]["titulo"] = str(req.get("titulo", "")).strip()[:120]
                        save(d)
                return self._send(200, {"ok": True})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/estudio-upload":
            # salva a imagem de exemplo do Estúdio pra usar como REFERÊNCIA do fundo (openai_edit)
            try:
                data = req.get("data", "")
                if "," in data:
                    data = data.split(",", 1)[1]
                raw = base64.b64decode(data)
                marca = safe_marca(req.get("marca", "smark"))
                dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social",
                                  "instagram", "arte", "_estudio")
                os.makedirs(dd, exist_ok=True)
                ext = ".png" if "png" in req.get("mime", "") else ".jpg"
                out = os.path.join(dd, f"ref-{secrets.token_hex(4)}{ext}")
                with open(out, "wb") as f:
                    f.write(raw)
                return self._send(200, {"ok": True, "path": os.path.relpath(out, VAULT)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        return self._send(404, {"erro": "rota desconhecida"})


def main():
    if not os.path.isfile(DATA):
        sys.exit(f"ERRO: {DATA} não existe. Gere o editor.json primeiro.")
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
    httpd.daemon_threads = True
    with httpd:
        print(f"\n  ✎ SUPER EDITOR (multi-thread) em  http://localhost:{PORT}   (Ctrl+C pra parar)\n")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
