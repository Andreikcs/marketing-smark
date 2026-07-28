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
import _acervo  # noqa: E402
import _perfil  # noqa: E402
import _roi  # noqa: E402
import _marcas  # noqa: E402

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


def cmdk():
    """Command palette global (⌘K / Ctrl+K) — busca publicações + comandos, pula pra qualquer tela.
    Autocontido (markup + estilo + script); funciona em qualquer página (usa /dados)."""
    return """
<style>
.cmdk-ov{position:fixed;inset:0;z-index:400;display:none;background:rgba(10,8,20,.55);backdrop-filter:blur(3px);align-items:flex-start;justify-content:center;padding-top:12vh}
.cmdk-ov.on{display:flex}
.cmdk-ov .sk-command{width:100%;max-width:560px;max-height:70vh;display:flex;flex-direction:column}
.cmdk-list{overflow:auto;padding:6px}
.cmdk-empty{padding:22px;text-align:center;color:var(--muted);font-size:13px}
.sk-command-item.is-active{background:var(--accent-soft)}
.cmdk-ic{width:22px;text-align:center;flex:0 0 auto;color:var(--muted)}
.cmdk-hint{position:fixed;right:26px;bottom:18px;z-index:30;display:inline-flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:7px 12px;font-size:12px;color:var(--muted);cursor:pointer;box-shadow:var(--shadow)}
.cmdk-hint:hover{border-color:var(--accent);color:var(--text)}
</style>
<div class=cmdk-ov id=cmdk>
  <div class="sk-command" onclick="event.stopPropagation()">
    <div class=sk-command-head>
      <svg viewBox="0 0 24 24" width=17 height=17 fill=none stroke=currentColor stroke-width=2 style="color:var(--muted);flex:0 0 auto"><circle cx=11 cy=11 r=7/><path d="M21 21l-4-4"/></svg>
      <input id=cmdkin placeholder="Buscar publicação ou comando…" autocomplete=off spellcheck=false style="flex:1;background:transparent;border:0;outline:none;color:var(--text);font-size:15px;font-family:var(--font-text)">
      <span class=sk-kbd>Esc</span>
    </div>
    <div class=cmdk-list id=cmdklist></div>
  </div>
</div>
<button class=cmdk-hint id=cmdkhint>Buscar <span class=sk-kbd>⌘K</span></button>
<script>
(function(){
  const ov=document.getElementById('cmdk'),inp=document.getElementById('cmdkin'),list=document.getElementById('cmdklist');
  const NAV=[['Painel','/painel','▦'],['Vitrine','/vitrine','▤'],['Config','/config','⚙'],['Editor','/editor','✎']];
  const ACTS=[['Novo projeto','/editor?novo=1','＋'],['Estúdio IA','/editor?estudio=1','✦']];
  let posts=[],items=[],idx=0,loaded=false;
  const esc=s=>(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  async function load(){if(loaded)return;try{const d=await(await fetch('/dados')).json();posts=d.posts||[]}catch(e){}loaded=true}
  function fmt(n){return n<=1?'post único':'carrossel · '+n}
  function row(ic,t,m){return '<div class=sk-command-item><span class=cmdk-ic>'+ic+'</span><div style="flex:1;min-width:0"><div style="font-size:14px;color:var(--text)">'+esc(t)+'</div>'+(m?'<div style="font-size:11px;color:var(--muted)">'+esc(m)+'</div>':'')+'</div></div>'}
  function build(){const q=(inp.value||'').toLowerCase().trim();items=[];let h='';
    const nav=NAV.filter(n=>!q||n[0].toLowerCase().includes(q));
    if(nav.length){h+='<div class=sk-command-group>Ir para</div>';nav.forEach(n=>{items.push({go:n[1]});h+=row(n[2],n[0],'')})}
    const act=ACTS.filter(a=>!q||a[0].toLowerCase().includes(q));
    if(act.length){h+='<div class=sk-command-group>Ações</div>';act.forEach(a=>{items.push({go:a[1]});h+=row(a[2],a[0],'')})}
    const ps=posts.map((p,i)=>({p,i})).reverse().filter(({p})=>!q||((p.titulo||p.slug||'')+' '+(p.marca||'')).toLowerCase().includes(q));
    if(ps.length){h+='<div class=sk-command-group>Publicações</div>';ps.slice(0,20).forEach(({p,i})=>{items.push({go:'/editor?post='+i});h+=row('▦',(p.titulo||p.slug),(p.marca||'smark')+' · '+fmt((p.frames||[]).length))})}
    list.innerHTML=h||'<div class=cmdk-empty>Nada encontrado</div>';idx=0;mark();
  }
  function mark(){const els=list.querySelectorAll('.sk-command-item');els.forEach((e,i)=>e.classList.toggle('is-active',i===idx));const a=els[idx];if(a)a.scrollIntoView({block:'nearest'});
    els.forEach((e,i)=>e.onclick=()=>{idx=i;pick()})}
  function pick(){const it=items[idx];if(it&&it.go)location.href=it.go}
  async function open(){await load();ov.classList.add('on');inp.value='';build();setTimeout(()=>inp.focus(),30)}
  function close(){ov.classList.remove('on')}
  inp.oninput=build;
  inp.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();idx=Math.min(idx+1,items.length-1);mark()}
    else if(e.key==='ArrowUp'){e.preventDefault();idx=Math.max(idx-1,0);mark()}
    else if(e.key==='Enter'){e.preventDefault();pick()}else if(e.key==='Escape'){close()}};
  ov.onclick=close;document.getElementById('cmdkhint').onclick=open;
  document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();ov.classList.contains('on')?close():open()}});
})();
</script>
"""


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
            '</div>' + cmdk())


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
    rows_p = "".join(
        f"<tr><td>{i+1}</td><td>{p.get('titulo','')}</td><td>{p.get('slug','')}</td>"
        f"<td>{p.get('marca','')}</td><td>{len(p.get('frames',[]))}</td></tr>"
        for i, p in enumerate(ed.get("posts", [])))
    chips = " ".join(f"<span class='sk-pill'>{c}</span>" for c in conceitos)
    return f"""<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Configurações · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{{padding:0}}
.wrap{{padding:24px 30px 60px;max-width:1080px;margin:0 auto}}
.sk-pagehead h1{{font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:32px;margin:6px 0 4px}}h1 span{{color:var(--accent)}} .sub{{color:var(--muted);font-size:13px}}
.gh{{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;gap:10px}}
.sk-card{{margin-bottom:16px;max-width:1000px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.06em}}
tr:last-child td{{border-bottom:0}}
.kv{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}.kv .cell{{background:var(--inset);border:1px solid var(--line);border-radius:var(--radius-md);padding:8px 12px;font-size:13px}}.kv b{{color:var(--accent-2)}}
.ok{{color:var(--good);font-weight:600}}.err{{color:#e07070;font-weight:600}}
.sk-input.mini,.sk-select.mini{{padding:7px 10px;font-size:13px;width:auto}}
.mgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
.mcard{{background:var(--inset);border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:10px}}
.mcard .top{{display:flex;gap:12px;align-items:center}}
.mlogo{{width:48px;height:48px;border-radius:12px;display:grid;place-items:center;font-weight:800;font-size:20px;color:#fff;flex:0 0 auto;overflow:hidden;background:var(--accent)}}
.mlogo img{{width:100%;height:100%;object-fit:cover}}
.mcard h3{{font-size:15px;margin:0}} .mcard .slug{{color:var(--muted);font-size:12px}}
.mmeta{{font-size:12px;color:var(--muted);line-height:1.45}}
.macts{{display:flex;gap:8px;flex-wrap:wrap;margin-top:auto}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:middle;margin-right:4px;border:1px solid #333}}
.pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;border:1px solid var(--line);color:var(--muted)}}
.pill.ok{{border-color:var(--good);color:var(--good)}}
.pill.warn{{border-color:#c90;color:#c90}}
.modal{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:80;padding:20px}}
.modal.on{{display:flex}}
.mbox{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;width:min(520px,100%);max-height:90vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,.45)}}
.mbox h2{{font-size:18px;margin:0 0 14px}}
.fld{{margin-bottom:12px}} .fld label{{display:block;font-size:11px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}}
.fld input,.fld textarea{{width:100%;background:var(--inset);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:10px 12px;font-size:14px;font-family:inherit}}
.fld textarea{{min-height:70px;resize:vertical}}
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.mbtns{{display:flex;gap:8px;justify-content:flex-end;margin-top:8px}}
.logoprev{{width:64px;height:64px;border-radius:14px;border:1px dashed var(--line);display:grid;place-items:center;overflow:hidden;background:var(--inset);font-size:11px;color:var(--muted)}}
.logoprev img{{width:100%;height:100%;object-fit:cover}}
</style></head><body class="sk">
{topbar("config")}
<div class=wrap>
<div class="sk-pagehead"><div>
<div class=sk-kicker>painel local · tokens.json</div>
<h1>Configurações do <span>Sistema</span></h1>
<div class=sub>Padrões do studio + gestão de marcas (criar, editar, logo) — tudo pela interface.</div></div></div>

<div class="sk-card"><div class=gh>Padrões editáveis</div><div class=kv>
<div class=cell>Tema-padrão: <select class="sk-select mini" id=cf_tema><option value=claro>claro</option><option value=escuro>escuro</option></select></div>
<div class=cell>Template padrão (tamanho): <select class="sk-select mini" id=cf_size><option value=1080x1350>Feed 4:5</option><option value=1080x1080>Quadrado 1:1</option><option value=1080x1920>Story 9:16</option></select></div>
<div class=cell>Assinatura padrão (rodapé direito): <input class="sk-input mini" id=cf_rodape value="{fund.get('rodape','')}" style="width:180px"></div>
</div>
<div style="margin-top:12px;color:var(--muted);font-size:12px">Regra #9: imagens geradas saem <b style="color:var(--accent-2)">claras</b> por padrão · Base clara {tok.get('tema_claro',{}).get('base','#F4F2FB')} · Base escura {fund.get('base','#0B0B0B')}</div>
<div style="margin-top:14px"><button class="sk-btn" id=cf_save>💾 Salvar padrões</button> <span id=cf_msg class=ok></span></div>
</div>

<div class="sk-card">
  <div class=gh><span>Marcas</span><button class="sk-btn sk-btn--sm" id=bm_new>+ Nova marca</button></div>
  <div id=mgrid class=mgrid><div style="color:var(--muted);font-size:13px">Carregando marcas…</div></div>
  <div style="margin-top:12px;color:var(--muted);font-size:12px;line-height:1.5">
    Cliente novo: crie a marca → revise cores/logo → no <a href="/editor">Editor</a> escolha a marca no post ou Estúdio.
    Entrega final = <code>tier=final</code> (Gemini) após 3 pilotos aprovados.
  </div>
</div>

<div class="sk-card"><div class=gh>Conceitos de direção de arte ({len(conceitos)})</div>{chips}</div>

<div class="sk-card">
  <div class=gh><span>Publicações &amp; tempo</span><span id=plog_count style="font-size:12px;font-weight:500;color:var(--muted)"></span></div>
  <div class=kv style="margin-bottom:12px">
    <div class=cell>Marca: <select class="sk-select mini" id=plog_marca><option value="">Todas</option></select></div>
    <div class=cell>Busca: <input class="sk-input mini" id=plog_q placeholder="título…" style="width:160px"></div>
  </div>
  <div id=plog_stats class=kv style="margin-bottom:12px"></div>
  <div id=plog_list style="display:flex;flex-direction:column;gap:6px"></div>
</div>

<div class="sk-card"><div class=gh>Servidor</div><div class=kv>
<div class=cell>Porta: <b>{PORT}</b></div>
<div class=cell>Acesso: <b>só neste computador</b></div>
<div class=cell>Proteção: <b class=ok>ativa</b></div>
</div></div>
</div>

<div class=modal id=mmodal>
  <div class=mbox>
    <h2 id=mtitle>Nova marca</h2>
    <div class=fld id=fld_slug><label>Slug (kebab-case, único)</label><input id=mf_slug placeholder="ex: netsul-fibra"></div>
    <div class=fld><label>Nome</label><input id=mf_nome placeholder="NetSul Fibra"></div>
    <div class=row2>
      <div class=fld><label>Acento</label><input id=mf_acento type=color value="#E0562D" style="height:42px;padding:4px"></div>
      <div class=fld><label>Acento claro</label><input id=mf_acento_claro type=color value="#FF7A4D" style="height:42px;padding:4px"></div>
    </div>
    <div class=row2>
      <div class=fld><label>Handle</label><input id=mf_handle placeholder="@marca"></div>
      <div class=fld><label>Glyph (1–2 letras)</label><input id=mf_glyph placeholder="N" maxlength=2></div>
    </div>
    <div class=fld><label>Wordmark (chip)</label><input id=mf_wordmark placeholder="NetSul"></div>
    <div class=fld><label>Mood (inglês, direção de arte)</label><textarea id=mf_mood placeholder="regional ISP fiber brand — warm, reliable, clean"></textarea></div>
    <div class=fld><label>Logo (PNG/SVG)</label>
      <div style="display:flex;gap:12px;align-items:center">
        <div class=logoprev id=mf_logoprev>sem logo</div>
        <input type=file id=mf_logo accept="image/*" style="font-size:12px;color:var(--muted)">
      </div>
    </div>
    <div class=fld><label>Referências da marca (prints do feed / peças aprovadas)</label>
      <input type=file id=mf_refs accept="image/*" multiple style="font-size:12px;color:var(--muted)">
      <div id=mf_refs_prev style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px"></div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">Entra no acervo da marca e guia as próximas gerações de fundo.</div>
    </div>
    <div class=fld><label>Site (opcional)</label><input id=mf_site placeholder="https://cliente.com.br"></div>
    <div id=mf_msg style="font-size:13px;min-height:18px;margin:4px 0"></div>
    <div class=mbtns>
      <button class="sk-btn sk-btn--secondary" id=mf_cancel>Cancelar</button>
      <button class="sk-btn" id=mf_save>Salvar marca</button>
    </div>
  </div>
</div>

<script>
const T="__EDITOR_TOKEN__";
const H={{'Content-Type':'application/json','X-Editor-Token':T}};
const esc=s=>(s==null?'':String(s)).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
document.getElementById('cf_tema').value="{tp}";
document.getElementById('cf_size').value="{defsize}";
document.getElementById('cf_save').onclick=async()=>{{
  const r=await(await fetch('/config-save',{{method:'POST',headers:H,
    body:JSON.stringify({{tema_padrao:document.getElementById('cf_tema').value,size:document.getElementById('cf_size').value,rodape:document.getElementById('cf_rodape').value}})}})).json();
  document.getElementById('cf_msg').textContent=r.ok?'Salvo ✓':('Erro: '+(r.erro||''));
}};

let MARCAS=[], EDIT=null, LOGO_DATA=null, REFS_DATA=[];
async function loadMarcas(){{
  const r=await(await fetch('/marcas')).json();
  MARCAS=(r.ok&&r.marcas)?r.marcas:[];
  const g=document.getElementById('mgrid');
  if(!MARCAS.length){{g.innerHTML='<div style="color:var(--muted)">Nenhuma marca.</div>';return}}
  g.innerHTML=MARCAS.map(m=>`
    <div class=mcard>
      <div class=top>
        <div class=mlogo style="background:${{m.gradiente||m.acento}}">${{
          m.logo_url?`<img src="${{esc(m.logo_url)}}?t=${{Date.now()}}" alt="">`:esc(m.glyph||'?')
        }}</div>
        <div>
          <h3>${{esc(m.nome)}}</h3>
          <div class=slug>${{esc(m.slug)}} · ${{esc(m.handle||'')}}</div>
        </div>
      </div>
      <div class=mmeta>
        <span class=sw style="background:${{esc(m.acento)}}"></span>${{esc(m.acento)}}
        · <span class=sw style="background:${{esc(m.acento_claro)}}"></span>${{esc(m.acento_claro)}}
        <br>
        <span class="pill ${{m.pronta?'ok':'warn'}}">${{m.pronta?'pronta':'setup'}}</span>
        ${{m.canonica?'<span class=pill>canônica</span>':''}}
        ${{m.mood?('<div style="margin-top:6px">'+esc(m.mood.slice(0,90))+(m.mood.length>90?'…':'')+'</div>'):''}}
      </div>
      <div class=macts>
        <button class="sk-btn sk-btn--secondary sk-btn--sm" data-edit="${{esc(m.slug)}}">Editar</button>
        <a class="sk-btn sk-btn--sm" href="/editor?novo=1&marca=${{encodeURIComponent(m.slug)}}">Novo post</a>
      </div>
    </div>`).join('');
  g.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>openEdit(b.dataset.edit));
}}

function clearRefsPrev(){{
  REFS_DATA=[];
  const el=document.getElementById('mf_refs_prev'); if(el) el.innerHTML='';
  const inp=document.getElementById('mf_refs'); if(inp) inp.value='';
}}
function openNew(){{
  EDIT=null; LOGO_DATA=null; clearRefsPrev();
  document.getElementById('mtitle').textContent='Nova marca';
  document.getElementById('fld_slug').style.display='';
  document.getElementById('mf_slug').value='';
  document.getElementById('mf_slug').disabled=false;
  document.getElementById('mf_nome').value='';
  document.getElementById('mf_acento').value='#1CA5B2';
  document.getElementById('mf_acento_claro').value='#3DC4D0';
  document.getElementById('mf_handle').value='';
  document.getElementById('mf_glyph').value='';
  document.getElementById('mf_wordmark').value='';
  document.getElementById('mf_mood').value='';
  document.getElementById('mf_site').value='';
  document.getElementById('mf_logoprev').innerHTML='sem logo';
  document.getElementById('mf_logo').value='';
  document.getElementById('mf_msg').textContent='';
  document.getElementById('mmodal').classList.add('on');
}}
function openEdit(slug){{
  const m=MARCAS.find(x=>x.slug===slug); if(!m)return;
  EDIT=slug; LOGO_DATA=null; clearRefsPrev();
  document.getElementById('mtitle').textContent='Editar · '+m.nome;
  document.getElementById('fld_slug').style.display='';
  document.getElementById('mf_slug').value=m.slug;
  document.getElementById('mf_slug').disabled=true;
  document.getElementById('mf_nome').value=m.nome||'';
  document.getElementById('mf_acento').value=m.acento||'#8B3CF7';
  document.getElementById('mf_acento_claro').value=m.acento_claro||m.acento||'#A472FF';
  document.getElementById('mf_handle').value=m.handle||'';
  document.getElementById('mf_glyph').value=m.glyph||'';
  document.getElementById('mf_wordmark').value=m.wordmark||'';
  document.getElementById('mf_mood').value=m.mood||'';
  document.getElementById('mf_site').value='';
  document.getElementById('mf_logoprev').innerHTML=m.logo_url?`<img src="${{esc(m.logo_url)}}?t=${{Date.now()}}">`:'sem logo';
  document.getElementById('mf_logo').value='';
  document.getElementById('mf_msg').textContent='';
  document.getElementById('mmodal').classList.add('on');
}}
document.getElementById('bm_new').onclick=openNew;
document.getElementById('mf_cancel').onclick=()=>document.getElementById('mmodal').classList.remove('on');
document.getElementById('mmodal').onclick=e=>{{if(e.target.id==='mmodal')e.currentTarget.classList.remove('on')}};
document.getElementById('mf_logo').onchange=e=>{{
  const f=e.target.files&&e.target.files[0]; if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{{LOGO_DATA=rd.result;document.getElementById('mf_logoprev').innerHTML=`<img src="${{rd.result}}">`}};
  rd.readAsDataURL(f);
}};
document.getElementById('mf_refs').onchange=async e=>{{
  const files=[...(e.target.files||[])].slice(0,12);
  REFS_DATA=[];
  const prev=document.getElementById('mf_refs_prev'); prev.innerHTML='';
  for(const f of files){{
    const dataurl=await new Promise(res=>{{const rd=new FileReader();rd.onload=()=>res(rd.result);rd.readAsDataURL(f)}});
    REFS_DATA.push({{nome:f.name.replace(/\\.[^.]+$/,''), dataurl}});
    const thumb=document.createElement('img');
    thumb.src=dataurl; thumb.style.cssText='width:48px;height:48px;object-fit:cover;border-radius:8px;border:1px solid var(--line)';
    prev.appendChild(thumb);
  }}
}};
document.getElementById('mf_save').onclick=async()=>{{
  const msg=document.getElementById('mf_msg');
  msg.className=''; msg.textContent='Salvando…';
  const body={{
    nome:document.getElementById('mf_nome').value.trim(),
    acento:document.getElementById('mf_acento').value,
    acento_claro:document.getElementById('mf_acento_claro').value,
    handle:document.getElementById('mf_handle').value.trim(),
    glyph:document.getElementById('mf_glyph').value.trim(),
    wordmark:document.getElementById('mf_wordmark').value.trim(),
    mood:document.getElementById('mf_mood').value.trim(),
    site:document.getElementById('mf_site').value.trim(),
  }};
  if(LOGO_DATA) body.logo_dataurl=LOGO_DATA;
  if(REFS_DATA.length) body.referencias=REFS_DATA;
  let r;
  if(EDIT){{
    body.slug=EDIT;
    r=await(await fetch('/editar-marca',{{method:'POST',headers:H,body:JSON.stringify(body)}})).json();
  }}else{{
    body.slug=document.getElementById('mf_slug').value.trim().toLowerCase();
    if(!body.slug||!body.nome){{msg.className='err';msg.textContent='Preencha slug e nome';return}}
    r=await(await fetch('/nova-marca',{{method:'POST',headers:H,body:JSON.stringify(body)}})).json();
  }}
  if(!r.ok){{msg.className='err';msg.textContent=r.erro||'erro';return}}
  const nref=(r.referencias||[]).filter(x=>x&&x.feed).length;
  msg.className='ok';
  msg.textContent='Salvo ✓'+(nref?(' · '+nref+' ref(s)'):'')+(r.avisos&&r.avisos.length?(' · '+r.avisos.join('; ')): '');
  await loadMarcas();
  setTimeout(()=>document.getElementById('mmodal').classList.remove('on'),700);
}};
loadMarcas();

function fmtMin(m){{if(m==null||m===undefined)return '—';m=Number(m);if(m<60)return m.toFixed(1)+' min';return (m/60).toFixed(1)+' h'}}
function relTime(iso){{if(!iso)return '—';const t=Date.parse(iso);if(!t)return '—';const min=Math.floor((Date.now()-t)/60000);
  if(min<1)return 'agora';if(min<60)return min+' min atrás';const h=Math.floor(min/60);if(h<48)return h+' h atrás';return Math.floor(h/24)+' d atrás'}}
async function loadPostLog(){{
  const list=document.getElementById('plog_list');
  const stats=document.getElementById('plog_stats');
  if(!list)return;
  list.innerHTML='<div style="color:var(--muted);font-size:13px">Carregando…</div>';
  try{{
    const r=await(await fetch('/roi-resumo',{{method:'POST',headers:H,body:JSON.stringify({{limit:80}})}})).json();
    if(!r.ok){{list.innerHTML='Não consegui carregar o histórico.';return}}
    const s=r.stats||{{}};
    const am=(s.avg_minutes_per_post||{{}}).mean;
    const cb=(s.cogs_brl||{{}}).sum;
    const cu=(s.cogs_usd||{{}}).sum;
    stats.innerHTML=
      '<div class=cell>Tempo médio / post: <b>'+(am!=null?fmtMin(am):'—')+'</b></div>'
      +'<div class=cell>Custo total (amostra): <b>'+(cb!=null?('R$ '+Number(cb).toFixed(2)): (cu!=null?('US$ '+Number(cu).toFixed(2)):'—'))+'</b></div>'
      +'<div class=cell>Posts no log: <b>'+(r.n||0)+'</b></div>';
    window._PLOG=r.posts||[];
    const sel=document.getElementById('plog_marca');
    const brands=[...new Set(window._PLOG.map(p=>p.marca).filter(Boolean))];
    const cur=sel.value;
    sel.innerHTML='<option value="">Todas</option>'+brands.map(b=>'<option value="'+esc(b)+'">'+esc(b)+'</option>').join('');
    if(cur)sel.value=cur;
    renderPostLog();
  }}catch(e){{list.innerHTML='Erro ao carregar';}}
}}
function renderPostLog(){{
  const list=document.getElementById('plog_list');
  if(!list)return;
  const marca=document.getElementById('plog_marca').value;
  const q=(document.getElementById('plog_q').value||'').toLowerCase();
  let rows=window._PLOG||[];
  if(marca)rows=rows.filter(p=>p.marca===marca);
  if(q)rows=rows.filter(p=>((p.titulo||'')+' '+(p.slug||'')).toLowerCase().includes(q));
  document.getElementById('plog_count').textContent=rows.length+' post(s)';
  if(!rows.length){{list.innerHTML='<div style="color:var(--muted);font-size:13px">Nenhum post neste filtro.</div>';return}}
  list.innerHTML=rows.map((p)=>{{
    const custo=p.total_brl!=null?('R$ '+Number(p.total_brl).toFixed(2)):(p.total_usd!=null?('US$ '+Number(p.total_usd).toFixed(3)):'—');
    const tempo=fmtMin(p.total_minutes);
    const ativo=p.active?(' · <span style="color:var(--accent)">em edição '+fmtMin(p.active_minutes)+'</span>'):'';
    return '<details style="border:1px solid var(--line);border-radius:12px;background:var(--inset);overflow:hidden">'
      +'<summary style="cursor:pointer;padding:12px 14px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;list-style:none">'
      +'<b style="flex:1;min-width:140px">'+esc(p.titulo)+'</b>'
      +'<span class=pill>'+esc(p.marca)+'</span>'
      +'<span style="font-size:12px;color:var(--muted)">⏱ '+tempo+ativo+'</span>'
      +'<span style="font-size:12px;color:var(--muted)">💰 '+custo+'</span>'
      +'<span style="font-size:12px;color:var(--muted)">'+relTime(p.updated_at||p.created_at)+'</span>'
      +'</summary>'
      +'<div style="padding:0 14px 14px;font-size:12px;color:var(--muted);line-height:1.55;border-top:1px solid var(--line)">'
      +'<div style="margin-top:10px">Criado: <b style="color:var(--text)">'+esc(p.created_at||'—')+'</b> · Atualizado: <b style="color:var(--text)">'+esc(p.updated_at||'—')+'</b></div>'
      +'<div>Peças: '+(p.n_frames||0)+' · Textos IA: '+(p.copy_calls_total||0)+' · Imagens: '+(p.image_gens_total||0)+' · Exports: '+(p.exports_total||0)+'</div>'
      +'<div>Ciclos: '+(p.cycles_n||0)+(p.avg_minutes!=null?(' · média '+fmtMin(p.avg_minutes)):'')+(p.last_minutes!=null?(' · último '+fmtMin(p.last_minutes)):'')+'</div>'
      +'<div style="margin-top:8px"><a class="sk-btn sk-btn--sm" href="/editor?post='+p.idx+'">Abrir no editor</a></div>'
      +'</div></details>';
  }}).join('');
}}
document.getElementById('plog_marca').onchange=renderPostLog;
document.getElementById('plog_q').oninput=()=>{{clearTimeout(window._plogT);window._plogT=setTimeout(renderPostLog,180)}};
loadPostLog();

// deep-link
const qs=new URLSearchParams(location.search);
if(qs.get('nova')) setTimeout(openNew,80);
else if(qs.get('editar')) setTimeout(()=>openEdit(qs.get('editar')),120);
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
.sk-post-actions.a5{grid-template-columns:repeat(5,1fr)}
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
.igmcap{margin:0 14px 12px;width:calc(100% - 28px);min-height:66px;max-height:150px;font-size:13px;line-height:1.45;color:var(--text);background:var(--field);border:1px solid var(--field-line);border-radius:10px;padding:9px 11px;font-family:var(--font-text);resize:vertical}
.igmcap:focus{outline:none;border-color:var(--accent)}
.msave{font-size:11px;color:var(--muted)}
.igmbtns{display:flex;gap:8px;padding:0 14px 14px}
.igmbtns .sk-btn{padding:9px 12px}
.dlmenu{position:fixed;z-index:600;background:var(--surface);border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow-lg);padding:6px;display:flex;flex-direction:column;gap:4px;min-width:190px}
.dlmenu button{border:0;background:transparent;color:var(--text);text-align:left;padding:9px 12px;border-radius:8px;cursor:pointer;font-size:13px}
.dlmenu button:hover{background:var(--surface-2)}
.ftbar{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:12px 14px;margin-bottom:18px}
.fttop{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.ftsearch{flex:1;min-width:180px;background:var(--inset);border:1px solid var(--field-line);border-radius:10px;color:var(--text);padding:9px 12px;font-size:13px}
.ftsel{background:var(--inset);border:1px solid var(--field-line);border-radius:10px;color:var(--text);padding:8px 10px;font-size:12px}
.ftbtn{border:1px solid var(--field-line);background:var(--surface-2);color:var(--text);border-radius:10px;padding:8px 12px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.ftbtn.on,.ftbtn[aria-expanded=true]{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 18%,transparent)}
.ftbadge{background:var(--accent);color:#fff;border-radius:999px;font-size:10px;padding:1px 6px;font-weight:700}
.ftpanel{display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--line);gap:16px}
.ftpanel.open{display:grid;grid-template-columns:1fr 1.4fr;gap:18px}
@media(max-width:720px){.ftpanel.open{grid-template-columns:1fr}}
.ftcol h5{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0 0 8px}
.ftcheck{display:flex;flex-direction:column;gap:6px}
.ftcheck label{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text);cursor:pointer;padding:4px 0}
.ftcheck input{accent-color:var(--accent);width:15px;height:15px}
.ftactive{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;min-height:0}
.fttag{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:4px 10px;color:var(--muted);background:var(--inset);cursor:pointer}
.fttag:hover{border-color:var(--accent);color:var(--text)}
.sk-cardgrid.mosaic{grid-template-columns:repeat(3,1fr);gap:10px}
@media(max-width:900px){.sk-cardgrid.mosaic{grid-template-columns:repeat(2,1fr)}}
.sk-cardgrid.mosaic .sk-post-body{padding:8px 10px}
.sk-cardgrid.mosaic .sk-post-title{font-size:13px}
.sk-cardgrid.mosaic .sk-post-actions{display:none}
.timetag{font-size:11px;color:var(--muted)}
</style></head><body class="sk">
__TOPBAR__
<div class=wrap>
<div class="sk-pagehead">
  <div style="display:flex;align-items:center;gap:10px">__LOGOSTORE__</div>
  <div class="sk-pagehead-actions">
    <button class="sk-btn sk-btn--danger sk-btn--sm" id=delsel>🗑 Excluir selecionados</button>
    <a class="sk-btn" href="/editor">＋ Novo post</a></div>
</div>
<div class=ftbar>
  <div class=fttop>
    <input class=ftsearch id=psearch placeholder="Buscar título ou marca…" />
    <select class=ftsel id=viewsel title="Layout">
      <option value=cards>Cards</option>
      <option value=mosaic>Mosaico · 3 colunas</option>
    </select>
    <select class=ftsel id=sortsel title="Ordem">
      <option value=recent>Mais recentes</option>
      <option value=old>Mais antigos</option>
      <option value=alpha>A–Z</option>
    </select>
    <button type=button class=ftbtn id=ftoggle aria-expanded=false>Filtros <span class=ftbadge id=fcount hidden>0</span></button>
    <span id=count style="font-size:12px;color:var(--muted);white-space:nowrap"></span>
  </div>
  <div class=ftpanel id=fpanel>
    <div class=ftcol>
      <h5>Status</h5>
      <div class=ftcheck id=sfilters></div>
    </div>
    <div class=ftcol>
      <h5>Marcas</h5>
      <div class=ftcheck id=filters></div>
    </div>
  </div>
  <div class=ftactive id=factive></div>
</div>
<div class="sk-cardgrid" id=grid></div>
</div>
<div class="sk-overlay" id=modal style="display:none">
  <div class="sk-modal igm">
    <div class=igmhead><div class=igmav></div><input id=mtitle class=igmtitle title="clique pra editar o nome do post" spellcheck=false><span id=mst></span></div>
    <div class=igmmedia><div class=igmhost id=mhost></div>
      <button class="igmnav l" id=mprev>‹</button><button class="igmnav r" id=mnext>›</button>
      <div class=igmpg id=mpg></div></div>
    <div class=igmicons><span>&#9825;</span><span>&#128172;</span><span>&#10148;</span><span style="flex:1"></span><span id=msave class=msave></span></div>
    <textarea class=igmcap id=mcap placeholder="escreva a legenda… (salva sozinho)" spellcheck=false></textarea>
    <div class=igmbtns>
      <button class="sk-btn" id=mopen style="flex:2">✎ Abrir no editor</button>
      <button class="sk-btn sk-btn--secondary" id=mcopy title="copiar legenda">⧉ Copiar</button>
      <button class="sk-btn sk-btn--secondary" id=mdl title="baixar imagem (um ou todos)">⬇</button>
      <button class="sk-btn sk-btn--secondary" id=mclose>Fechar</button>
    </div>
  </div>
</div>
<script>
const T="__EDITOR_TOKEN__";let D=null,VIEW='cards',SORT='recent',Q='',MI=0,MP=0;const SEL=new Set();
let STATUS_SET=new Set(), MARCA_SET=new Set();
let NOME_MARCA={};
async function load(){
  try{const r=await(await fetch('/marcas')).json();if(r.ok)(r.marcas||[]).forEach(m=>NOME_MARCA[m.slug]=m.nome||m.slug)}catch(e){}
  D=await(await fetch('/dados')).json();render()}
function brands(){return [...new Set(D.posts.map(p=>p.marca||'smark'))]}
function nomeMarca(s){return NOME_MARCA[s]||s}
function fmtTipo(n){return n<=1?'1 peça':n+' peças'}
function relTime(iso){
  if(!iso)return '';
  const t=Date.parse(iso);if(!t)return '';
  const m=Math.floor((Date.now()-t)/60000);
  if(m<1)return 'agora';if(m<60)return m+' min';
  const h=Math.floor(m/60);if(h<48)return h+' h';
  const d=Math.floor(h/24);return d+' d';
}
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
function buildChecks(host,opts,set,onChange){
  host.innerHTML='';
  opts.forEach(([v,lb])=>{
    const id='ck_'+host.id+'_'+v;
    const lab=document.createElement('label');
    lab.innerHTML='<input type=checkbox id="'+id+'" '+(set.has(v)?'checked':'')+'> <span>'+lb+'</span>';
    lab.querySelector('input').onchange=e=>{if(e.target.checked)set.add(v);else set.delete(v);onChange()};
    host.appendChild(lab);
  });
}
function nActiveFilters(){return STATUS_SET.size+MARCA_SET.size}
function renderActive(){
  const el=document.getElementById('factive');if(!el)return;
  const tags=[];
  STATUS_SET.forEach(s=>tags.push(['s',s,s==='salvo'?'Pronto':'Rascunho']));
  MARCA_SET.forEach(m=>tags.push(['m',m,nomeMarca(m)]));
  const badge=document.getElementById('fcount');
  if(badge){if(tags.length){badge.hidden=false;badge.textContent=tags.length}else badge.hidden=true}
  if(!tags.length){el.innerHTML='';return}
  el.innerHTML=tags.map(([t,v,lb])=>'<button type=button class=fttag data-t="'+t+'" data-v="'+v+'">'+lb+' ×</button>').join('')
    +'<button type=button class=fttag data-t=clear>Limpar filtros</button>';
  el.querySelectorAll('.fttag').forEach(b=>b.onclick=()=>{
    if(b.dataset.t==='clear'){STATUS_SET.clear();MARCA_SET.clear()}
    else if(b.dataset.t==='s')STATUS_SET.delete(b.dataset.v);
    else if(b.dataset.t==='m')MARCA_SET.delete(b.dataset.v);
    render();
  });
}
function filtered(){
  let items=D.posts.map((p,i)=>({p,i}));
  items=items.filter(({p})=>{
    if(MARCA_SET.size&&!MARCA_SET.has(p.marca||'smark'))return false;
    if(STATUS_SET.size&&!STATUS_SET.has(p.status||'rascunho'))return false;
    if(Q){const q=Q.toLowerCase();const t=((p.titulo||'')+' '+(p.slug||'')+' '+(p.marca||'')).toLowerCase();if(!t.includes(q))return false}
    return true;
  });
  items.sort((a,b)=>{
    if(SORT==='alpha')return (a.p.titulo||a.p.slug||'').localeCompare(b.p.titulo||b.p.slug||'','pt');
    if(SORT==='old'){
      const ta=Date.parse(a.p.created_at||'')||a.i;
      const tb=Date.parse(b.p.created_at||'')||b.i;
      return ta-tb;
    }
    const ta=Date.parse(a.p.updated_at||a.p.created_at||'')||a.i;
    const tb=Date.parse(b.p.updated_at||b.p.created_at||'')||b.i;
    return tb-ta || b.i-a.i;
  });
  return items;
}
function render(){
  VIEW=document.getElementById('viewsel').value||'cards';
  SORT=document.getElementById('sortsel').value||'recent';
  buildChecks(document.getElementById('sfilters'),[['rascunho','Rascunho'],['salvo','Pronto']],STATUS_SET,()=>render());
  buildChecks(document.getElementById('filters'),brands().map(b=>[b,nomeMarca(b)]),MARCA_SET,()=>render());
  renderActive();
  const g=document.getElementById('grid');g.innerHTML='';
  g.className='sk-cardgrid'+(VIEW==='mosaic'?' mosaic':'');
  const items=filtered();let n=0;
  items.forEach(({p,i})=>{
    n++;
    const salvo=p.status==='salvo';
    const badge='<span class="stdot '+(salvo?'st-s':'st-r')+'" title="'+(salvo?'pronto':'rascunho')+'"></span>';
    const ch=(p.canais||['instagram']).map(chIcon).join('');
    const on=SEL.has(i);
    const age=relTime(p.updated_at||p.created_at);
    const c=document.createElement('div');c.className='sk-post'+(on?' is-selected':'');
    c.dataset.pi=i;
    c.innerHTML='<div class="sk-post-thumb">'
      +'<div class="thumbhost"><div class="sk-skel" style="position:absolute;inset:0"></div></div>'
      +'<div class="sk-post-check'+(on?' is-on':'')+'" data-i="'+i+'">✓</div>'
      +'<div class="sk-post-channel">'+ch+'</div>'
      +'</div><div class="sk-post-body">'
      +'<div class="sk-post-title">'+(p.titulo||p.slug)+'</div>'
      +'<div class="sk-post-meta">'+badge+nomeMarca(p.marca||'smark')+'<span class=sk-dot></span>'+fmtTipo(p.frames?p.frames.length:0)
      +(age?('<span class=sk-dot></span><span class=timetag>'+age+'</span>'):'')
      +'</div>'
      +'<div class="sk-post-actions a5">'
      +'<button data-a=ver data-i="'+i+'" title=Ver>👁</button>'
      +'<button class=act-edit data-a=edit data-i="'+i+'" title=Editar>✎</button>'
      +'<button data-a=dl data-i="'+i+'" title="Baixar">⬇</button>'
      +'<button data-a=dup data-i="'+i+'" title=Duplicar>⧉</button>'
      +'<button class=act-del data-a=del data-i="'+i+'" title=Excluir>🗑</button>'
      +'</div></div>';
    g.appendChild(c)});
  document.getElementById('count').textContent=n+' publicação'+(n===1?'':'ões');
  if(n===0){g.innerHTML='<div class="sk-empty" style="grid-column:1/-1"><div class="sk-empty-icon sk-empty-icon--muted">▦</div>'
    +'<div class="sk-empty-title">'+((FILT||STATUSF||Q)?'Nada com esse filtro':'Nenhuma publicação ainda')+'</div>'
    +'<div class="sk-empty-text">'+((FILT||STATUSF||Q)?'Ajuste os filtros acima.':'Crie a primeira no editor.')+'</div>'
    +'<a class="sk-btn" href="/editor">＋ Novo post</a></div>';}
  const io=new IntersectionObserver((es)=>{es.forEach(en=>{if(en.isIntersecting){const card=en.target;io.unobserve(card);
    const host=card.querySelector('.thumbhost');const pi=+card.dataset.pi;if(host&&D.posts[pi])loadThumb(host,D.posts[pi])}})},{rootMargin:'200px'});
  g.querySelectorAll('.sk-post').forEach(card=>io.observe(card));
}
let _qT=null;
document.addEventListener('input',e=>{if(e.target&&e.target.id==='psearch'){clearTimeout(_qT);_qT=setTimeout(()=>{Q=e.target.value.trim();render()},200)}});
document.getElementById('viewsel').onchange=()=>render();
document.getElementById('sortsel').onchange=()=>render();
document.getElementById('ftoggle').onclick=()=>{
  const pan=document.getElementById('fpanel');
  const open=pan.classList.toggle('open');
  document.getElementById('ftoggle').setAttribute('aria-expanded',open?'true':'false');
};
document.getElementById('grid').addEventListener('click',e=>{
  const chk=e.target.closest('.sk-post-check');if(chk){const i=+chk.dataset.i;SEL.has(i)?SEL.delete(i):SEL.add(i);render();return}
  const b=e.target.closest('[data-a]');if(!b)return;const i=+b.dataset.i,a=b.dataset.a;
  if(a==='ver')ver(i);else if(a==='edit')location.href='/editor?post='+i;else if(a==='dup')dupPost(i);else if(a==='del')del([i]);
  else if(a==='dl'){MP=i;MI=0;dlMenu({currentTarget:b},i)}
});
async function ver(i){MP=i;MI=0;const p=D.posts[i];
  document.getElementById('modal').style.display='flex';
  document.getElementById('mtitle').value=p.titulo||p.slug||'';
  document.getElementById('mst').innerHTML=(p.status==='salvo'?'<span class="stdot st-s"></span> salvo':'<span class="stdot st-r"></span> rascunho');
  document.getElementById('mcap').value=p.caption||'';document.getElementById('msave').textContent='';mframe()}
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
// legenda editável — salva sozinho (auto-save)
let mcapT=null;
document.getElementById('mcap').oninput=e=>{const v=e.target.value;document.getElementById('msave').textContent='salvando…';
  clearTimeout(mcapT);mcapT=setTimeout(async()=>{
    await fetch('/legenda',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:MP,caption:v})});
    if(D.posts[MP])D.posts[MP].caption=v;document.getElementById('msave').textContent='salvo ✓';},700)};
document.getElementById('mcopy').onclick=async()=>{try{await navigator.clipboard.writeText(document.getElementById('mcap').value||'');document.getElementById('mcopy').textContent='✓ Copiado';setTimeout(()=>document.getElementById('mcopy').textContent='⧉ Copiar',1400)}catch(e){alert('Não consegui copiar')}};
document.getElementById('mdl').onclick=(e)=>dlMenu(e,MP);
// baixa a arte compilada (renderiza no servidor e faz download)
async function baixarPost(pi,scope){
  const p=D.posts[pi];toast('Renderizando PNG…');
  const r=await(await fetch('/exportar',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({post:pi,frame:scope==='all'?'all':MI})})).json();
  if(!r.ok||!r.feitas||!r.feitas.length){toast('Erro ao renderizar');return}
  r.feitas.forEach((path,k)=>{setTimeout(()=>{const a=document.createElement('a');a.href='/'+path+'?t='+Date.now();a.download=(p.slug||'post')+'-'+String(k+1).padStart(2,'0')+'.png';document.body.appendChild(a);a.click();a.remove()},k*400)});
  toast('⬇ Baixando '+r.feitas.length+' PNG');
}
function dlMenu(e,pi){document.querySelectorAll('.dlmenu').forEach(m=>m.remove());
  const p=D.posts[pi],n=(p.frames||[]).length;
  const m=document.createElement('div');m.className='dlmenu';
  m.innerHTML='<button data-s=one>⬇ Baixar este frame</button>'+(n>1?'<button data-s=all>⬇ Baixar o carrossel todo ('+n+')</button>':'');
  document.body.appendChild(m);const r=e.currentTarget.getBoundingClientRect();
  m.style.top=(r.bottom+6)+'px';m.style.left=Math.min(r.left,window.innerWidth-210)+'px';
  m.onclick=ev=>{const b=ev.target.closest('button');if(!b)return;baixarPost(pi,b.dataset.s);m.remove()};
  setTimeout(()=>document.addEventListener('mousedown',function h(ev){if(!m.contains(ev.target)){m.remove();document.removeEventListener('mousedown',h)}}),40);
}
async function del(idx){if(!idx.length){alert('Selecione ao menos um');return}
  if(!confirm('Excluir '+idx.length+' publicação(ões)?'))return;
  await fetch('/excluir-posts',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:idx})});SEL.clear();await load()}
async function dupPost(i){await fetch('/duplicar-post',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({idx:i})});await load()}
document.getElementById('delsel').onclick=()=>del([...SEL]);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
load();
</script></body></html>""").replace("__TOPBAR__", topbar("painel")).replace("__LOGOSTORE__", smark_logo(34, suffix="STORE"))


def vitrine_html():
    """Vitrine — feed Instagram, mosaico 3 colunas, ordenação e filtro de marca."""
    return ("""<!doctype html><html lang=pt-BR data-theme="claro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Vitrine · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css"><style>
body.sk{padding-bottom:50px;background:var(--bg)}
.top{text-align:center;padding:14px;font-family:var(--font-display);text-transform:uppercase;font-weight:400;font-size:16px;letter-spacing:.02em;border-bottom:1px solid var(--line);background:var(--surface)}.top span{color:var(--accent)}
.toolbar{max-width:980px;margin:14px auto 10px;padding:12px 14px;display:flex;flex-direction:column;gap:0;background:var(--surface);border:1px solid var(--line);border-radius:16px}
.ttop{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.tsel{background:var(--inset);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:8px 10px;font-size:12px}
.tbtn{border:1px solid var(--line);background:var(--surface-2);color:var(--text);border-radius:10px;padding:8px 12px;font-size:12px;cursor:pointer}
.tbtn[aria-expanded=true]{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 14%,transparent)}
.tbadge{background:var(--accent);color:#fff;border-radius:999px;font-size:10px;padding:1px 6px;font-weight:700;margin-left:4px}
.tpanel{display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
.tpanel.open{display:block}
.tcheck{display:flex;flex-wrap:wrap;gap:10px 16px}
.tcheck label{display:flex;align-items:center;gap:7px;font-size:13px;cursor:pointer}
.tcheck input{accent-color:var(--accent)}
.count{margin-left:auto;font-size:12px;color:var(--muted)}
/* feed */
.feed{max-width:440px;margin:12px auto 30px;display:flex;flex-direction:column;gap:22px;padding:0 8px}
.feed.mosaic{max-width:980px;display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:0 12px}
@media(max-width:700px){.feed.mosaic{grid-template-columns:repeat(2,1fr)}}
.post{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow)}
.feed.mosaic .post{border-radius:0;border:0;box-shadow:none;background:#000}
.feed.mosaic .ph,.feed.mosaic .icons,.feed.mosaic .cap,.feed.mosaic .dots{display:none}
.feed.mosaic .media{aspect-ratio:1/1;cursor:pointer}
.ph{display:flex;align-items:center;gap:9px;padding:11px 13px;font-size:14px;font-weight:600}
.av{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent-2));flex:0 0 auto}
.media{position:relative;background:#000;aspect-ratio:4/5;cursor:pointer;overflow:hidden}
.vhost{position:absolute;inset:0;overflow:hidden;background:#000}
.cbadge{position:absolute;top:10px;right:10px;background:#000a;color:#fff;font-size:12px;padding:2px 9px;border-radius:12px}
.dots{position:absolute;bottom:10px;left:0;right:0;display:flex;gap:5px;justify-content:center}
.dot{width:6px;height:6px;border-radius:50%;background:#ffffff88}.dot.on{background:#fff}
.icons{display:flex;gap:15px;padding:10px 13px;font-size:22px}
.cap{padding:0 13px 14px;font-size:14px;line-height:1.4;white-space:pre-wrap;color:var(--text)}.cap b{font-weight:600}
.empty{text-align:center;color:var(--muted);padding:40px;font-size:14px;grid-column:1/-1}
.age{font-size:11px;color:var(--muted);font-weight:400}
</style></head><body class="sk">
__TOPBAR__
<div class=top><span id=vtbrand>todas as marcas</span> &middot; vitrine · feed pra aprovar</div>
<div class=toolbar>
  <div class=ttop>
    <select class=tsel id=viewsel>
      <option value=feed>Feed</option>
      <option value=mosaic>Mosaico · 3 colunas</option>
    </select>
    <select class=tsel id=sortsel>
      <option value=recent>Mais recentes</option>
      <option value=old>Mais antigos</option>
    </select>
    <button type=button class=tbtn id=ftoggle aria-expanded=false>Marcas <span class=tbadge id=fcount hidden>0</span></button>
    <span class=count id=vcount></span>
  </div>
  <div class=tpanel id=fpanel>
    <div class=tcheck id=vbrands></div>
  </div>
</div>
<div class=feed id=feed></div>
<script>
const T="__EDITOR_TOKEN__";
let D=null, VIEW='feed', SORT='recent', NOMES={};
const MARCA_SET=new Set();
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function relTime(iso){if(!iso)return '';const t=Date.parse(iso);if(!t)return '';const m=Math.floor((Date.now()-t)/60000);
  if(m<1)return 'agora';if(m<60)return m+' min';const h=Math.floor(m/60);if(h<48)return h+' h';return Math.floor(h/24)+' d'}
async function compose(host,fr,p){
  try{
    const r=await fetch('/preview',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':T},body:JSON.stringify({frame:fr,size:p.size,marca:p.marca||'smark'})});
    const html=await r.text();const s=(host.clientWidth||200)/1080;
    host.innerHTML='';const ifr=document.createElement('iframe');
    ifr.style.cssText='position:absolute;top:0;left:0;border:0;width:1080px;height:1350px;transform-origin:top left;pointer-events:none;transform:scale('+s+')';
    host.appendChild(ifr);ifr.srcdoc=html;
  }catch(e){host.textContent=''}
}
function listPosts(){
  let items=(D.posts||[]).map((p,i)=>({p,i})).filter(({p})=>(p.frames||[]).length);
  if(MARCA_SET.size)items=items.filter(({p})=>MARCA_SET.has(p.marca||'smark'));
  items.sort((a,b)=>{
    const ta=Date.parse(a.p.updated_at||a.p.created_at||'')||a.i;
    const tb=Date.parse(b.p.updated_at||b.p.created_at||'')||b.i;
    return SORT==='old'?(ta-tb):(tb-ta||b.i-a.i);
  });
  return items;
}
function render(){
  VIEW=document.getElementById('viewsel').value;
  SORT=document.getElementById('sortsel').value;
  const badge=document.getElementById('fcount');
  if(MARCA_SET.size){badge.hidden=false;badge.textContent=MARCA_SET.size}else badge.hidden=true;
  const f=document.getElementById('feed');f.className='feed'+(VIEW==='mosaic'?' mosaic':'');f.innerHTML='';
  const items=listPosts();
  document.getElementById('vcount').textContent=items.length+' peça'+(items.length===1?'':'s');
  if(MARCA_SET.size===1)document.getElementById('vtbrand').textContent=NOMES[[...MARCA_SET][0]]||[...MARCA_SET][0];
  else if(MARCA_SET.size>1)document.getElementById('vtbrand').textContent=MARCA_SET.size+' marcas';
  else document.getElementById('vtbrand').textContent='todas as marcas';
  if(!items.length){f.innerHTML='<div class=empty>Nenhum post com esses filtros.</div>';return}
  items.forEach(({p})=>{
    const frames=p.frames||[];
    const nome=NOMES[p.marca||'smark']||p.marca||'smark';
    const age=relTime(p.updated_at||p.created_at);
    const el=document.createElement('div');el.className='post';
    el.innerHTML='<div class=ph><div class=av></div><span>'+esc(nome)+'</span>'
      +(age?('<span class=age style="margin-left:8px">'+age+'</span>'):'')
      +'<span style="flex:1"></span>&middot;&middot;&middot;</div>'
      +'<div class=media><div class=vhost><div class="sk-skel" style="position:absolute;inset:0"></div></div>'
      +(VIEW==='feed'?('<div class=cbadge>1/'+frames.length+'</div><div class=dots>'+frames.map((_,i)=>'<span class="dot'+(i?'':' on')+'"></span>').join('')+'</div>'):'')
      +'</div>'
      +(VIEW==='feed'?('<div class=icons><span>&#9825;</span><span>&#128172;</span><span>&#10148;</span><span style="flex:1"></span><span>&#128278;</span></div>'
        +'<div class=cap><b>'+esc(nome)+'</b> '+esc(p.caption||p.titulo||'')+'</div>'):'');
    const host=el.querySelector('.vhost');
    let idx=0;
    el.querySelector('.media').onclick=()=>{
      if(VIEW==='mosaic'){location.href='/editor';return}
      idx=(idx+1)%frames.length;compose(host,frames[idx],p);
      const badge=el.querySelector('.cbadge');if(badge)badge.textContent=(idx+1)+'/'+frames.length;
      el.querySelectorAll('.dot').forEach((d,i)=>d.classList.toggle('on',i===idx));
    };
    f.appendChild(el);compose(host,frames[0],p);
  });
}
async function load(){
  try{const r=await(await fetch('/marcas')).json();if(r.ok)(r.marcas||[]).forEach(m=>NOMES[m.slug]=m.nome||m.slug)}catch(e){}
  D=await(await fetch('/dados')).json();
  const brands=[...new Set((D.posts||[]).map(p=>p.marca||'smark'))];
  const hb=document.getElementById('vbrands');
  hb.innerHTML=brands.map(b=>'<label><input type=checkbox data-m="'+b+'"> '+(NOMES[b]||b)+'</label>').join('');
  hb.querySelectorAll('input').forEach(inp=>inp.onchange=()=>{
    if(inp.checked)MARCA_SET.add(inp.dataset.m);else MARCA_SET.delete(inp.dataset.m);
    render();
  });
  document.getElementById('viewsel').onchange=()=>render();
  document.getElementById('sortsel').onchange=()=>render();
  document.getElementById('ftoggle').onclick=()=>{
    const open=document.getElementById('fpanel').classList.toggle('open');
    document.getElementById('ftoggle').setAttribute('aria-expanded',open?'true':'false');
  };
  render();
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


def _parse_arte_meta(stdout):
    """Extrai custo/modelo/provider/seed do stdout de openai_image / openai_edit.

    Lê as linhas `arte-*` do meta_block e a linha OK: como fallback.
    """
    meta = {}
    text = stdout or ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("arte-modelo:"):
            meta["modelo"] = s.split(":", 1)[1].strip()
        elif s.startswith("arte-provider:"):
            meta["provider"] = s.split(":", 1)[1].strip()
        elif s.startswith("arte-seed:"):
            seed = s.split(":", 1)[1].strip()
            if seed:
                try:
                    meta["seed"] = int(seed)
                except ValueError:
                    meta["seed"] = seed
        elif s.startswith("arte-custo-usd:"):
            raw = s.split(":", 1)[1].strip()
            if raw:
                try:
                    meta["custo_usd"] = float(raw)
                except ValueError:
                    meta["custo_usd"] = raw
        elif s.startswith("arte-suplente:"):
            meta["suplente"] = s.split(":", 1)[1].strip().lower() in ("true", "1", "sim")
        elif s.startswith("OK:") and "custo=$" in s:
            # OK: path  (modelo via provider, seed=N, custo=$0.24)
            m = re.search(r"custo=\$([0-9.]+|\?)", s)
            if m and m.group(1) != "?" and "custo_usd" not in meta:
                try:
                    meta["custo_usd"] = float(m.group(1))
                except ValueError:
                    pass
            m = re.search(r"\(([^,\s]+)\s+via\s+([^,\s]+)", s)
            if m:
                meta.setdefault("modelo", m.group(1))
                meta.setdefault("provider", m.group(2))
            m = re.search(r"seed=(\d+)", s)
            if m:
                meta.setdefault("seed", int(m.group(1)))
    return meta


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
            meta = _parse_arte_meta(r.stdout or "")
            try:  # persiste pra não perder ao sair da tela
                with IO_LOCK:
                    d = load()
                    if pi < len(d["posts"]) and fi < len(d["posts"][pi].get("frames", [])):
                        f = d["posts"][pi]["frames"][fi]
                        f["bg"] = rel
                        f["bgmode"] = "imagem"
                        if meta.get("custo_usd") is not None:
                            f["bg_custo_usd"] = meta["custo_usd"]
                        if meta.get("modelo"):
                            f["bg_modelo"] = meta["modelo"]
                        if meta.get("provider"):
                            f["bg_provider"] = meta["provider"]
                        if meta.get("seed") is not None:
                            f["bg_seed"] = meta["seed"]
                        if "suplente" in meta:
                            f["bg_suplente"] = meta["suplente"]
                        # ROI humano: +1 imagem no ciclo ativo
                        try:
                            _roi.touch_image(d["posts"][pi])
                        except Exception:
                            pass
                        save(d)
            except Exception:
                pass
            job = {"status": "done", "path": rel}
            job.update({k: meta[k] for k in ("custo_usd", "modelo", "provider", "seed", "suplente")
                        if k in meta})
            # BRL ao vivo (mesmo se o stdout da CLI não trouxe)
            try:
                from _cambio import enriquecer  # noqa: E402
                if job.get("custo_usd") is not None:
                    pack = enriquecer(job["custo_usd"])
                    job["custo_brl"] = pack["custo_brl"]
                    job["usd_brl"] = pack["usd_brl"]
                    job["cambio_fonte"] = pack["cambio_fonte"]
            except Exception:
                pass
            # exit 3 = gate de texto falhou (rascunho poluído); arquivo existe
            if r.returncode == 3 or "GATE_FALHOU" in (r.stdout or ""):
                job["gate_falhou"] = True
                job["publicavel"] = False
            JOBS[job_id] = job
        else:
            JOBS[job_id] = {"status": "erro", "erro": (r.stderr or r.stdout or "falhou")[-400:]}


def _run_estudio(job_id, pedido, marca, n, tipo, contexto="", historico=None,
                 imagem_b64=None, imagem_mime="image/jpeg", slug="", post_idx=None):
    """Roda o cérebro do chat em background (chat é rápido, mas não trava a UI)."""
    with GEN_SEM:
        try:
            out = estudio.gerar(pedido, marca, n, tipo, contexto, historico,
                                imagem_b64, imagem_mime, slug=slug or "")
            # compat: gerar devolve 2 ou 3 valores
            if len(out) == 3:
                res, prov, meta = out
            else:
                res, prov = out[0], out[1]
                meta = {}
            # ROI humano: +1 copy no post ativo
            if post_idx is not None:
                try:
                    with IO_LOCK:
                        d = load()
                        if 0 <= int(post_idx) < len(d["posts"]):
                            _roi.touch_copy(d["posts"][int(post_idx)])
                            save(d)
                except Exception:
                    pass
            JOBS[job_id] = {
                "status": "done", "resultado": res, "provider": prov,
                "custo": res.get("_custo") or {
                    "tipo": "copy",
                    "custo_usd": meta.get("custo_usd"),
                    "custo_brl": meta.get("custo_brl"),
                    "usd_brl": meta.get("usd_brl"),
                    "modelo": meta.get("modelo"),
                    "provider": meta.get("provider") or prov,
                    "input_tokens": meta.get("input_tokens"),
                    "output_tokens": meta.get("output_tokens"),
                },
            }
        except Exception as e:
            JOBS[job_id] = {"status": "erro", "erro": str(e)}


def hl(text):
    """quebra de linha: '|' (legado) e Enter (newline real) → '\\n' que o compositor entende."""
    return (text or "").replace("\r", "").replace("|", "\\n").replace("\n", "\\n")


def frame_kwargs(fr, size, for_export, marca="smark"):
    """Traduz um frame do editor.json nos kwargs do compose_html.
    for_export=True embute a imagem (base64, render headless); False usa URL estática (preview leve).

    Cores vêm SEMPRE da marca ativa (tokens) — nunca roxo smark em cliente.
    """
    meta = _marcas.get(marca) or {}
    acc = meta.get("acento") or "#8B3CF7"
    acc2 = meta.get("acento_claro") or acc
    grad = meta.get("gradiente") or f"linear-gradient(155deg,{acc} 0%,{_marcas._base_escura_de(acc)} 100%)"
    alt = meta.get("acento_alternativo") or ""

    k = dict(marca=marca, headline=hl(fr.get("headline", "")), sub=hl(fr.get("sub", "")),
             cta=fr.get("cta", ""), page=fr.get("page", ""), no_chip=not fr.get("chip", False),
             tema=fr.get("tema", "escuro"), size=size, hsize=int(fr.get("hsize", 0) or 0),
             accent=fr.get("accent") or acc, bright=fr.get("bright") or acc2,
             square=fr.get("square") or grad,
             no_grade=not fr.get("grade", True),
             zoom=float(fr.get("zoom", 1.0) or 1.0), posx=int(fr.get("posx", 50)),
             posy=int(fr.get("posy", 50)), overlay=fr.get("overlay", "none"),
             overlay_op=float(fr.get("overlay_op", 0.85)),
             ov_ang=int(fr.get("ov_ang", 180)), ov_pos=int(fr.get("ov_pos", 20)),
             brilho=float(fr.get("brilho", 1.0)), contraste=float(fr.get("contraste", 1.0)),
             satur=float(fr.get("satur", 1.0)),
             handle_over=fr.get("handle", "") or meta.get("handle", ""),
             rodape_over=fr.get("rodape", ""),
             raw=bool(fr.get("raw", False)))

    # paleta: "marca" (default) | "secundario" | legado "lima"/"roxo"
    pal = (fr.get("paleta") or "marca").lower()
    if pal in ("lima", "secundario", "alt"):
        sec = alt or acc2 or "#C6F24E"
        k["accent"] = sec
        k["bright"] = sec
        k["square"] = sec
    elif pal in ("marca", "roxo", "", "primario"):
        k["accent"] = acc
        k["bright"] = acc2
        k["square"] = grad
    # se o frame forçou accent manual, respeita
    if fr.get("accent"):
        k["accent"] = fr["accent"]
        k["bright"] = fr.get("bright") or fr["accent"]

    mode = fr.get("bgmode", "imagem")
    if mode == "imagem" and fr.get("bg"):
        if for_export:
            k["bg"] = fr["bg"]
        else:
            k["bg_url"] = "/" + urllib.parse.quote(fr["bg"])
    elif mode == "cor":
        k["base"] = fr.get("cor") or ""
    elif mode == "degrade":  # degradê claro TINGIDO pela marca
        k["base"] = compositor.degrade_claro_da_marca(acc, acc2)
        k["tema"] = "claro"
    else:  # escuro | claro (preset com mesh on-brand)
        k["placeholder"] = True
        k["tema"] = "claro" if mode == "claro" else "escuro"
    return k


def safe_marca(m):
    """Marca path-safe e registrada; desconhecida → smark (só paths/UI legada)."""
    return _marcas.safe_marca(m, fallback="smark")


def require_marca(m):
    """Marca registrada ou ValueError — usar em geração/copy (sem fallback silencioso)."""
    m = (m or "").strip()
    if not m:
        return "smark"
    return _marcas.require(m)


def _decode_dataurl(dataurl):
    """Devolve (raw_bytes, ext) a partir de data URL ou base64 puro."""
    dataurl = (dataurl or "").strip()
    if not dataurl:
        raise ValueError("dataurl vazio")
    if "," in dataurl:
        head, b64 = dataurl.split(",", 1)
    else:
        head, b64 = "data:image/png;base64", dataurl
    ext = ".png"
    if "image/jpeg" in head or "image/jpg" in head:
        ext = ".jpg"
    elif "image/webp" in head:
        ext = ".webp"
    elif "image/svg" in head:
        ext = ".svg"
    return base64.b64decode(b64), ext


def _logo_from_dataurl(slug, dataurl):
    """Decodifica data:image/...;base64,... e grava via _marcas.salvar_logo_bytes."""
    raw, ext = _decode_dataurl(dataurl)
    return _marcas.salvar_logo_bytes(slug, raw, ext=ext)


def _refs_from_dataurls(slug, lista):
    """Salva lista de dataurls como referências/acervo da marca."""
    out = []
    for i, item in enumerate(lista or []):
        if not item:
            continue
        if isinstance(item, dict):
            du = item.get("dataurl") or item.get("data") or ""
            nome = item.get("nome") or f"ref-{i+1:02d}"
        else:
            du, nome = item, f"ref-{i+1:02d}"
        try:
            raw, ext = _decode_dataurl(du)
            out.append(_marcas.salvar_referencia_bytes(slug, raw, nome=nome, ext=ext))
        except Exception as e:
            out.append({"erro": str(e), "nome": nome})
    return out


def safe_slug(s):
    """Bloqueia path traversal via slug — só kebab-case [a-z0-9-]."""
    s = re.sub(r"[^a-z0-9-]+", "-", (s or "").lower()).strip("-")
    return s or "post"


def _agora_iso():
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


def normaliza(d):
    """Garante n sequencial, marca/slug seguros, datas e caminho 'out' pra todo frame."""
    now = _agora_iso()
    for p in d.get("posts", []):
        p["marca"] = safe_marca(p.get("marca", "smark"))
        p["slug"] = safe_slug(p.get("slug", ""))
        if not p.get("canais"):
            p["canais"] = ["instagram"]
        if not p.get("created_at"):
            p["created_at"] = now
        p["updated_at"] = now
        _roi.ensure(p)
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
            html = html.replace("</body>", cmdk() + "</body>", 1)
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
        if path == "/marcas":
            try:
                return self._send(200, {"ok": True, "marcas": _marcas.listar_detalhes()})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
        if path == "/historico":
            # versões de UM post ao longo dos autosaves do git (dedupe: só quando o post mudou)
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                pi = int(qs.get("post", ["-1"])[0])
                d = load()
                if not (0 <= pi < len(d["posts"])):
                    return self._send(400, {"ok": False, "erro": "post inválido"})
                slug = d["posts"][pi].get("slug", "")
                try:
                    log = subprocess.check_output(
                        ["git", "-C", VAULT, "log", "--format=%h %ct", "-60", "--", "editor.json"],
                        stderr=subprocess.DEVNULL).decode().splitlines()
                except Exception:
                    log = []
                versoes, last_fp = [], None
                for line in log:
                    parts = line.split()
                    if len(parts) != 2:
                        continue
                    commit, ts = parts
                    try:
                        cd = json.loads(subprocess.check_output(
                            ["git", "-C", VAULT, "show", f"{commit}:editor.json"],
                            stderr=subprocess.DEVNULL).decode())
                    except Exception:
                        continue
                    p = next((x for x in cd.get("posts", []) if x.get("slug") == slug), None)
                    if not p:
                        continue
                    fp = json.dumps(p, sort_keys=True, ensure_ascii=False)
                    if fp == last_fp:  # mesma versão do post → não repete
                        continue
                    last_fp = fp
                    versoes.append({"commit": commit, "ts": int(ts),
                                    "frames": len(p.get("frames", [])),
                                    "titulo": p.get("titulo", "")})
                return self._send(200, {"ok": True, "slug": slug, "versoes": versoes})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
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

        if path == "/restaurar":
            # troca UM post pela sua versão de um commit — só esse post, o resto do editor.json fica igual
            try:
                with IO_LOCK:
                    d = load()
                    pi = int(req.get("post", -1))
                    commit = str(req.get("commit", ""))
                    if not (0 <= pi < len(d["posts"])):
                        return self._send(400, {"ok": False, "erro": "post inválido"})
                    if not re.fullmatch(r"[0-9a-f]{4,40}", commit):
                        return self._send(400, {"ok": False, "erro": "commit inválido"})
                    slug = d["posts"][pi].get("slug", "")
                    try:
                        cd = json.loads(subprocess.check_output(
                            ["git", "-C", VAULT, "show", f"{commit}:editor.json"],
                            stderr=subprocess.DEVNULL).decode())
                    except Exception:
                        return self._send(404, {"ok": False, "erro": "commit não encontrado"})
                    old = next((x for x in cd.get("posts", []) if x.get("slug") == slug), None)
                    if not old:
                        return self._send(404, {"ok": False, "erro": "essa versão não tem este post"})
                    d["posts"][pi] = old
                    save(d)
                return self._send(200, {"ok": True, "frames": len(old.get("frames", []))})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

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
            try:
                marca = require_marca(req.get("marca", "smark"))
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
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
                feitas, faltaram = [], []
                for i in idxs:
                    fr = post["frames"][i]
                    kw = frame_kwargs(fr, post.get("size", "1080x1350"), for_export=True,
                                      marca=post.get("marca", "smark"))
                    html, w, h = compositor.compose_html(**kw)
                    base_out = fr.get("out") or post["frames"][0].get("out", "")
                    if base_out:
                        out = fr.get("out") or f"{os.path.dirname(base_out)}/{i+1:02d}.png"
                    else:  # post novo sem arte ainda → caminho seguro no vault (nunca escreve em '/')
                        marca = safe_marca(post.get("marca", "smark"))
                        slug = safe_slug(post.get("slug", "avulso"))
                        dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social",
                                          "instagram", "arte", slug)
                        os.makedirs(dd, exist_ok=True)
                        out = os.path.join(dd, f"{i+1:02d}.png")
                    if compositor.render_html_to_png(html, out, w, h):
                        feitas.append(os.path.relpath(out, VAULT) if os.path.isabs(out) else out)
                    else:
                        faltaram.append(i + 1)
                # ROI humano: fecha ciclo ativo no export bem-sucedido
                cycle = None
                if feitas:
                    try:
                        with IO_LOCK:
                            d2 = load()
                            pi = int(req["post"])
                            if 0 <= pi < len(d2["posts"]):
                                cycle = _roi.close_export(d2["posts"][pi])
                                save(d2)
                    except Exception:
                        cycle = None
                return self._send(200, {"ok": True, "feitas": feitas,
                                        "faltaram": faltaram, "esperado": len(idxs),
                                        "roi_cycle": cycle})
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

        if path == "/acervo-add":
            try:
                marca = safe_marca(req.get("marca", "smark"))
                rel = str(req.get("path", "")).lstrip("/")
                origem = os.path.join(VAULT, rel)
                if not os.path.isfile(origem):
                    return self._send(400, {"ok": False, "erro": "arquivo não encontrado"})
                perfil = _perfil.resolver(marca)
                if not perfil["acervo_dir"]:
                    return self._send(400, {"ok": False, "erro": "família sem acervo no contrato"})
                _acervo.adicionar(origem, perfil["acervo_dir"])
                total = len(_acervo.listar(perfil["acervo_dir"], 10 ** 6))
                return self._send(200, {"ok": True, "total": total,
                                        "teto": perfil["acervo_max"],
                                        "familia": perfil["familia"]})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/regerar-fundo":
            try:
                d = load()
                post = d["posts"][req["post"]]
                fr = post["frames"][req["frame"]]
                slug = safe_slug(post.get("slug", ""))
                try:
                    marca = require_marca(post.get("marca", "smark"))
                except ValueError as e:
                    return self._send(400, {"ok": False, "erro": str(e)})
                dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram",
                                  "arte", slug, "_regen")
                os.makedirs(dd, exist_ok=True)
                out = os.path.join(dd, f"{req['frame']+1:02d}-{secrets.token_hex(3)}.png")
                # ref: anexo do Estúdio OU fundo atual do card. Com ref = EDIÇÃO (gpt-image).
                # Sem ref = geração do zero (Gemini + direção de arte).
                ref = (req.get("ref") or "").strip().lstrip("/")
                if ref and not os.path.isfile(os.path.join(VAULT, ref)):
                    # path inválido → cai pro caminho sem ref (não quebra o job)
                    ref = ""
                if ref:
                    # Pedido do usuário manda; conceito_visual do Claude é só reforço.
                    pedido = (req.get("pedido") or req.get("prompt") or "").strip()
                    conceito = (req.get("conceito") or "").strip()
                    partes = []
                    if pedido:
                        partes.append("USER REQUEST (follow closely):\n" + pedido[:1200])
                    if conceito and conceito.lower() not in pedido.lower():
                        partes.append("Visual hint: " + conceito[:400])
                    partes.append(
                        "This is an IMAGE EDIT of the provided reference photo — NOT a new scene. "
                        "Preserve the same person(s), face(s), body, pose, camera angle, framing, "
                        "lighting, time of day, environment and photographic realism unless the user "
                        "explicitly asks to change them. Apply ONLY the changes in the USER REQUEST. "
                        "Do not invent a studio, mannequins, abstract glass, or a different location. "
                        "Keep the lower third relatively clean for headline overlay when possible. "
                        "No text, letters, logos or watermarks in the image. Photorealistic, high detail, 4k."
                    )
                    full = "\n\n".join(partes)
                    cmd = ["python3", os.path.join(HERE, "openai_edit.py"),
                           "--image", os.path.join(VAULT, ref), "--out", out,
                           "--prompt", full, "--size", "1024x1536", "--quality", "high",
                           "--input-fidelity", "high"]
                else:  # direção de arte (padrão claro, rule #9)
                    # padrão do sistema: Seedream (rascunho). UI não expõe escolha.
                    # edição com ref nunca cai aqui (ramo openai_edit acima).
                    tier = (req.get("tier") or "rascunho").strip().lower()
                    if tier not in ("final", "rascunho"):
                        tier = "rascunho"
                    cmd = ["python3", os.path.join(HERE, "openai_image.py"), "--out", out, "--direcao",
                           "--marca", marca, "--tipo", req.get("tipo", "manifesto"),
                           "--tema", req.get("tema", "claro"),
                           "--headline", (fr.get("headline", "") or "").replace("|", " "),
                           "--size", "1024x1536", "--quality", "high",
                           "--tier", tier]
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
                try:
                    marca = require_marca(req.get("marca", "smark"))
                except ValueError as e:
                    return self._send(400, {"ok": False, "erro": str(e)})
                n = max(1, min(10, int(req.get("n", 3) or 3)))
                tipo = req.get("tipo", "")
                contexto = str(req.get("contexto", ""))[:1500]
                historico = req.get("historico") if isinstance(req.get("historico"), list) else None
                img_b64 = req.get("imagem") or None
                img_mime = req.get("imagem_mime", "image/jpeg")
                slug = safe_slug(req.get("slug", "") or "")
                post_idx = req.get("post")
                try:
                    post_idx = int(post_idx) if post_idx is not None and post_idx != "" else None
                except (TypeError, ValueError):
                    post_idx = None
                job_id = secrets.token_hex(6)
                JOBS[job_id] = {"status": "running"}
                threading.Thread(target=_run_estudio,
                                 args=(job_id, pedido, marca, n, tipo, contexto, historico,
                                       img_b64, img_mime, slug, post_idx), daemon=True).start()
                return self._send(200, {"ok": True, "job": job_id})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/roi-start":
            # Abre ciclo de tempo no post (manual ou ao focar o post)
            try:
                with IO_LOCK:
                    d = load()
                    pi = int(req.get("post", -1))
                    if not (0 <= pi < len(d["posts"])):
                        return self._send(400, {"ok": False, "erro": "post inválido"})
                    force = bool(req.get("force"))
                    act = _roi.start(d["posts"][pi], force=force)
                    save(d)
                return self._send(200, {"ok": True, "active": act, "roi": d["posts"][pi].get("roi")})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/roi-resumo":
            try:
                import _ledger  # noqa: E402
                limit = max(1, min(50, int(req.get("limit", 20) or 20)))
                d = load()
                resumo = _roi.resumo_posts(
                    d.get("posts") or [],
                    limit=limit,
                    totais_fn=_ledger.totais_por_post,
                )
                return self._send(200, {"ok": True, **resumo})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/nova-marca":
            # cria marca de cliente (Sprint multi-marca) + refs opcionais
            try:
                slug = str(req.get("slug", "")).strip().lower()
                nome = str(req.get("nome", "")).strip()
                acento = str(req.get("acento", "")).strip()
                r = _marcas.criar(
                    slug, nome, acento,
                    acento_claro=str(req.get("acento_claro") or "") or None,
                    handle=str(req.get("handle") or "") or None,
                    glyph=str(req.get("glyph") or "") or None,
                    wordmark=str(req.get("wordmark") or "") or None,
                    mood=str(req.get("mood") or ""),
                )
                avisos = []
                if req.get("logo_dataurl"):
                    try:
                        _logo_from_dataurl(r["slug"], req["logo_dataurl"])
                    except Exception as le:
                        avisos.append(f"logo: {le}")
                refs_in = req.get("referencias") or req.get("refs") or []
                refs_out = []
                if refs_in:
                    try:
                        refs_out = _refs_from_dataurls(r["slug"], refs_in)
                    except Exception as re_:
                        avisos.append(f"refs: {re_}")
                # site / nota opcional no tokens
                if req.get("site"):
                    t = _marcas._load_tokens()
                    t["marcas"][r["slug"]]["site"] = str(req["site"])[:200]
                    _marcas._save_tokens(t)
                return self._send(200, {
                    "ok": True,
                    "slug": r["slug"],
                    "pronta": _marcas.pronta(r["slug"]),
                    "dir": r["dir"],
                    "meta": _marcas.get(r["slug"]),
                    "referencias": refs_out,
                    "avisos": avisos,
                    "detalhe": next((d for d in _marcas.listar_detalhes()
                                     if d["slug"] == r["slug"]), None),
                })
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/editar-marca":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                campos = {}
                for k in ("nome", "acento", "acento_claro", "handle", "glyph",
                          "wordmark", "mood", "gradiente"):
                    if k in req and req[k] is not None:
                        campos[k] = req[k]
                if "endossa" in req:
                    campos["endossa"] = bool(req["endossa"])
                r = _marcas.atualizar(slug, **campos)
                if req.get("logo_dataurl"):
                    try:
                        _logo_from_dataurl(slug, req["logo_dataurl"])
                        r["meta"] = _marcas.get(slug)
                        r["pronta"] = _marcas.pronta(slug)
                    except Exception as le:
                        return self._send(200, {"ok": True, **r, "aviso_logo": str(le),
                                                "detalhe": next((d for d in _marcas.listar_detalhes()
                                                                 if d["slug"] == slug), None)})
                refs_out = []
                if req.get("referencias") or req.get("refs"):
                    refs_out = _refs_from_dataurls(slug, req.get("referencias") or req.get("refs"))
                return self._send(200, {"ok": True, **r, "referencias": refs_out,
                                        "detalhe": next((d for d in _marcas.listar_detalhes()
                                                         if d["slug"] == slug), None)})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-logo":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                dest = _logo_from_dataurl(slug, req.get("logo_dataurl") or req.get("dataurl") or "")
                return self._send(200, {"ok": True, "slug": slug,
                                        "path": os.path.relpath(dest, VAULT).replace("\\", "/"),
                                        "detalhe": next((d for d in _marcas.listar_detalhes()
                                                         if d["slug"] == slug), None)})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/custos-post":
            # GET-like via POST body: {slug, marca} → totais copy+imagem em USD/BRL
            try:
                import _ledger  # noqa: E402
                slug = safe_slug(req.get("slug", ""))
                marca = safe_marca(req.get("marca", "smark"))
                t = _ledger.totais_por_post(slug, marca)
                # não devolve listas enormes na UI
                t.pop("imagens", None)
                t.pop("copys", None)
                return self._send(200, {"ok": True, **t})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/custos-resumo":
            try:
                import _ledger  # noqa: E402
                periodo = str(req.get("periodo", "") or "")
                return self._send(200, {"ok": True, **_ledger.resumo_periodo(periodo)})
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

        if path == "/legenda":
            try:
                with IO_LOCK:
                    d = load()
                    i = int(req.get("idx", -1))
                    if 0 <= i < len(d["posts"]):
                        d["posts"][i]["caption"] = str(req.get("caption", ""))[:4000]
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
