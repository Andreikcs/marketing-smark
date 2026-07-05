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
body.sk{{padding:20px 30px 60px}}
a.menu{{position:fixed;top:8px;left:8px;background:var(--accent);color:var(--accent-ink);padding:6px 12px;border-radius:8px;font:600 12px var(--font-text);text-decoration:none;z-index:9}}
h1{{font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:30px;margin:18px 0 4px}}h1 span{{color:var(--accent)}} .sub{{color:var(--muted);font-size:13px;margin-bottom:24px}}
.gh{{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:12px}}
.sk-card{{margin-bottom:16px;max-width:880px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.06em}}
tr:last-child td{{border-bottom:0}}
.kv{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}.kv .cell{{background:var(--inset);border:1px solid var(--line);border-radius:var(--radius-md);padding:8px 12px;font-size:13px}}.kv b{{color:var(--accent-2)}}
.ok{{color:var(--good);font-weight:600}}
.sk-input.mini,.sk-select.mini{{padding:7px 10px;font-size:13px;width:auto}}
</style></head><body class="sk">
<a class=menu href="/">☰ Menu</a>
<div class=sk-kicker>painel local · tokens.json</div>
<h1>Configurações do <span>Sistema</span></h1>
<div class=sub>Edite os padrões e os handles das marcas — salva no tokens.json.</div>

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
    """Painel de Conteúdo integrado — galeria de TODAS as publicações do editor.json."""
    return """<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Painel de Conteúdo · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{padding:16px 26px 60px}
a.menu{position:fixed;top:8px;left:8px;background:var(--accent);color:var(--accent-ink);padding:6px 12px;border-radius:8px;font:600 12px var(--font-text);text-decoration:none;z-index:9}
h1{font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:30px;margin:16px 0 4px}h1 span{color:var(--accent)}.sub{color:var(--muted);font-size:13px;margin-bottom:16px}
.bar{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
.bar button,.bar a{border:1px solid var(--field-line);background:var(--surface);color:var(--text);border-radius:var(--radius-md);padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;transition:.15s}
.bar button:hover,.bar a:hover{background:var(--surface-2)}
.bar .del:hover{border-color:var(--bad);color:var(--bad);background:var(--bad-soft)}
.bar .go{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);box-shadow:var(--shadow)}.bar .go:hover{filter:brightness(1.07);background:var(--accent)}
.filters{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}.filters button{padding:7px 14px;font-size:12px;font-weight:600;border-radius:var(--radius-pill);background:var(--inset);color:var(--sub);border:1px solid transparent}.filters button:hover{color:var(--text)}.filters button.on{background:var(--accent-soft);border-color:transparent;color:var(--accent);font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);overflow:hidden;position:relative;box-shadow:var(--shadow);transition:.15s}
.card:hover{transform:translateY(-2px);border-color:var(--line-strong)}
.card .cb{position:absolute;top:8px;left:8px;z-index:2;accent-color:var(--accent);width:18px;height:18px}
.card .chbadge{position:absolute;top:8px;right:8px;z-index:2;display:flex;gap:3px}
.card .acts button,.card .acts a{font-size:11px;padding:8px 3px}
.card .th{aspect-ratio:4/5;width:100%;object-fit:cover;display:block}
.card .thx{aspect-ratio:4/5;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px;background:var(--surface-2)}
.card .meta{padding:10px 11px}.card .meta b{font-size:13px;display:block;margin-bottom:2px}.card .meta small{color:var(--muted);font-size:11px}
.stt{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;margin-left:5px}.stt.r{background:var(--warn-soft);color:var(--warn)}.stt.s{background:var(--good-soft);color:var(--good)}
.card .acts{display:flex;border-top:1px solid var(--line)}
.card .acts a,.card .acts button{flex:1;border:0;background:transparent;color:var(--accent-2);padding:9px 4px;font-size:12px;cursor:pointer;border-right:1px solid var(--line)}
.card .acts button:last-child{border-right:0;color:var(--bad)}
.modal{display:none;position:fixed;inset:0;background:#000c;z-index:50;align-items:center;justify-content:center;padding:20px}
.modal .box{background:var(--surface);border-radius:12px;overflow:hidden}
.modal .mm{width:400px;max-width:90vw;height:500px;overflow:hidden;position:relative;background:#000}
.modal iframe{border:0;width:1080px;height:1350px;transform:scale(.37);transform-origin:top left}
.mnav{display:flex;justify-content:space-between;align-items:center;padding:8px 10px}.mnav button{background:var(--surface-2);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:6px 12px;cursor:pointer}
</style></head><body class="sk">
<a class=menu href="/">&#9776; Menu</a>
<h1>Painel de <span>Conteudo</span></h1>
<div class=sub>Todas as publicacoes, todas as marcas &mdash; integrado ao editor.</div>
<div class=bar><button class=del id=delsel>&#128465; Excluir selecionados</button>
<a class=go href="/editor">+ Novo / abrir editor</a>
<div class=filters id=sfilters></div><div class=filters id=filters></div></div>
<div class=grid id=grid></div>
<div class=modal id=modal><div class=box><div class=mm><iframe id=mif></iframe></div>
<div class=mnav><button id=mprev>&lsaquo;</button><span id=mpg></span><button id=mnext>&rsaquo;</button></div>
<div style="padding:0 10px 12px"><button class="sk-btn" onclick="document.getElementById('modal').style.display='none'" style="width:100%">Fechar</button></div></div></div>
<script>
const T="__EDITOR_TOKEN__";let D=null,FILT='',STATUSF='',MI=0,MP=0;
async function load(){D=await(await fetch('/dados')).json();render()}
function brands(){return [...new Set(D.posts.map(p=>p.marca||'smark'))]}
function chIcon(c){if(c==='linkedin')return '<span title=LinkedIn style="background:#0a66c2;color:#fff;font:700 9px sans-serif;padding:2px 4px;border-radius:3px">in</span>';
  return '<span title=Instagram style="background:linear-gradient(45deg,#f09433,#dc2743,#bc1888);color:#fff;font:700 9px sans-serif;padding:2px 5px;border-radius:4px">IG</span>'}
function render(){
  const sf=document.getElementById('sfilters');sf.innerHTML='';
  [['','status: todos'],['rascunho','rascunho'],['salvo','salvo']].forEach(([v,lb])=>{const b=document.createElement('button');b.textContent=lb;if(STATUSF===v)b.className='on';b.onclick=()=>{STATUSF=v;render()};sf.appendChild(b)});
  const fl=document.getElementById('filters');fl.innerHTML='';
  [''].concat(brands()).forEach(b=>{const btn=document.createElement('button');btn.textContent=b||'todas as marcas';if(FILT===b)btn.className='on';btn.onclick=()=>{FILT=b;render()};fl.appendChild(btn)});
  const g=document.getElementById('grid');g.innerHTML='';
  const items=D.posts.map((p,i)=>({p,i})).reverse();  // mais novos primeiro
  items.forEach(({p,i})=>{
    if(FILT&&(p.marca||'smark')!==FILT)return;
    if(STATUSF&&(p.status||'rascunho')!==STATUSF)return;
    const f0=p.frames&&p.frames[0];const cp=f0?((f0.bgmode==='imagem'&&f0.bg)?f0.bg:(f0.out||'')):'';
    const cov=cp?('/'+cp+'?t='+Date.now()):'';
    const st=p.status==='salvo'?'<span class="stt s">salvo</span>':'<span class="stt r">rascunho</span>';
    const ch=(p.canais||['instagram']).map(chIcon).join(' ');
    const c=document.createElement('div');c.className='card';
    c.innerHTML='<input type=checkbox class=cb data-i="'+i+'">'
      +'<div class=chbadge>'+ch+'</div>'
      +(cov?'<img class=th src="'+cov+'">':'<div class=thx>sem arte</div>')
      +'<div class=meta><b>'+(p.titulo||p.slug)+'</b><small>'+(p.marca||'smark')+' &middot; '+(p.frames?p.frames.length:0)+' frames'+st+'</small></div>'
      +'<div class=acts><button onclick="ver('+i+')">&#128065; Ver</button><a href="/editor?post='+i+'">&#9998; Editar</a><button onclick="dupPost('+i+')">&#10697; Dup</button><button onclick="del(['+i+'])">&#128465;</button></div>';
    g.appendChild(c)});
}
async function ver(i){MP=i;MI=0;document.getElementById('modal').style.display='flex';mframe()}
async function mframe(){const p=D.posts[MP],fr=p.frames[MI];
  const r=await fetch('/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({frame:fr,size:p.size,marca:p.marca||'smark'})});
  document.getElementById('mif').srcdoc=await r.text();document.getElementById('mpg').textContent=(MI+1)+'/'+p.frames.length}
document.getElementById('mprev').onclick=()=>{const n=D.posts[MP].frames.length;MI=(MI-1+n)%n;mframe()};
document.getElementById('mnext').onclick=()=>{const n=D.posts[MP].frames.length;MI=(MI+1)%n;mframe()};
async function del(idx){if(!idx.length){alert('Selecione ao menos um');return}
  if(!confirm('Excluir '+idx.length+' publicacao(oes)?'))return;
  await fetch('/excluir-posts',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:idx})});await load()}
async function dupPost(i){await fetch('/duplicar-post',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:i})});await load()}
document.getElementById('delsel').onclick=()=>del([...document.querySelectorAll('.cb:checked')].map(c=>+c.dataset.i));
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});  // sincroniza ao voltar pra aba
load();
</script></body></html>"""


def vitrine_html():
    """Vitrine estilo feed do Instagram — todas as publicações do editor.json."""
    return """<!doctype html><html lang=pt-BR data-theme="claro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Vitrine · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{padding-bottom:50px}
a.menu{position:fixed;top:8px;left:8px;background:var(--accent);color:var(--accent-ink);padding:6px 12px;border-radius:8px;font:600 12px var(--font-text);text-decoration:none;z-index:9}
.top{text-align:center;padding:16px;font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:18px;letter-spacing:.02em;border-bottom:1px solid var(--line);background:var(--surface);position:sticky;top:0;z-index:5}.top span{color:var(--accent)}
.feed{max-width:440px;margin:18px auto;display:flex;flex-direction:column;gap:22px;padding:0 8px}
.post{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow)}
.ph{display:flex;align-items:center;gap:9px;padding:11px 13px;font-size:14px;font-weight:600}
.av{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent-2))}
.media{position:relative;background:#000;aspect-ratio:4/5;cursor:pointer}
.media img{width:100%;height:100%;object-fit:cover;display:block}
.cbadge{position:absolute;top:10px;right:10px;background:#000a;color:#fff;font-size:12px;padding:2px 9px;border-radius:12px}
.dots{position:absolute;bottom:10px;left:0;right:0;display:flex;gap:5px;justify-content:center}
.dot{width:6px;height:6px;border-radius:50%;background:#ffffff88}.dot.on{background:#fff}
.icons{display:flex;gap:15px;padding:10px 13px;font-size:22px}
.cap{padding:0 13px 14px;font-size:14px;line-height:1.4;white-space:pre-wrap;color:var(--text)}.cap b{font-weight:600}
.empty{text-align:center;color:var(--muted);padding:40px;font-size:14px}
</style></head><body class="sk">
<a class=menu href="/">&#9776; Menu</a>
<div class=top><span>smark</span> &middot; vitrine</div>
<div class=feed id=feed></div>
<script>
async function load(){const D=await(await fetch('/dados')).json();const f=document.getElementById('feed');f.innerHTML='';let n=0;
  D.posts.forEach(p=>{
    const imgs=(p.frames||[]).map(fr=>((fr.bgmode==='imagem'&&fr.bg)?fr.bg:fr.out)).filter(Boolean);
    if(!imgs.length)return;n++;
    const el=document.createElement('div');el.className='post';
    el.innerHTML='<div class=ph><div class=av></div>'+(p.marca||'smark')+'<span style="flex:1"></span>&middot;&middot;&middot;</div>'
      +'<div class=media><img src="/'+imgs[0]+'"><div class=cbadge>1/'+imgs.length+'</div><div class=dots>'+imgs.map((_,i)=>'<span class="dot'+(i?'':' on')+'"></span>').join('')+'</div></div>'
      +'<div class=icons><span>&#9825;</span><span>&#128172;</span><span>&#10148;</span><span style="flex:1"></span><span>&#128278;</span></div>'
      +'<div class=cap><b>'+(p.marca||'smark')+'</b> '+((p.caption||'').replace(/</g,'&lt;'))+'</div>';
    let idx=0;const img=el.querySelector('img'),badge=el.querySelector('.cbadge'),dots=el.querySelectorAll('.dot');
    el.querySelector('.media').onclick=()=>{idx=(idx+1)%imgs.length;img.src='/'+imgs[idx]+'?t='+Date.now();badge.textContent=(idx+1)+'/'+imgs.length;dots.forEach((d,i)=>d.classList.toggle('on',i===idx))};
    f.appendChild(el);
  });
  if(!n)f.innerHTML='<div class=empty>Nenhuma arte exportada ainda. Exporte no editor pra ver aqui.</div>';
}
load();
</script></body></html>"""


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


def _run_estudio(job_id, pedido, marca, n, tipo):
    """Roda o cérebro do chat em background (chat é rápido, mas não trava a UI)."""
    with GEN_SEM:
        try:
            res, prov = estudio.gerar(pedido, marca, n, tipo)
            JOBS[job_id] = {"status": "done", "resultado": res, "provider": prov}
        except Exception as e:
            JOBS[job_id] = {"status": "erro", "erro": str(e)}


def hl(text):
    """headline do editor usa '|' como quebra; o compositor usa '\\n'."""
    return (text or "").replace("|", "\\n")


def frame_kwargs(fr, size, for_export, marca="smark"):
    """Traduz um frame do editor.json nos kwargs do compose_html.
    for_export=True embute a imagem (base64, render headless); False usa URL estática (preview leve)."""
    k = dict(marca=marca, headline=hl(fr.get("headline", "")), sub=fr.get("sub", ""),
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
            return self._send(200, vitrine_html(), MIME[".html"])
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
                job_id = secrets.token_hex(6)
                JOBS[job_id] = {"status": "running"}
                threading.Thread(target=_run_estudio,
                                 args=(job_id, pedido, marca, n, tipo), daemon=True).start()
                return self._send(200, {"ok": True, "job": job_id})
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
