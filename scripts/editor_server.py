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
import _dna_marca  # noqa: E402
import _canais  # noqa: E402

PORT = 8765
PAINEL = os.path.join(VAULT, "painel.html")
VITRINE = os.path.join(VAULT, "lancamento.html")

HUB = """<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>smark · Sistema</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css">
<script>(function(){try{var t=localStorage.getItem('smark-ui-theme');if(t==='claro'||t==='escuro')document.documentElement.setAttribute('data-theme',t)}catch(e){}})()</script>
<style>
body.sk{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px}
.wrap{max-width:820px;width:100%}
.hub-brand{display:flex;flex-direction:column;align-items:flex-start;gap:10px;margin-bottom:8px}
.hub-brand .hub-logo{transform-origin:left center}
.hub-sub{color:var(--muted);font-size:14px;line-height:1.45;max-width:520px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:28px}
a.tile{display:block;text-decoration:none;color:inherit}
a.tile .sk-card{transition:.15s;height:100%}
a.tile:hover .sk-card{border-color:var(--accent);transform:translateY(-2px)}
.ic{font-size:28px;margin-bottom:12px;display:block}
.tile b{font-size:16px;display:block;margin-bottom:5px;color:var(--text)}
.tile p{color:var(--muted);font-size:12.5px;line-height:1.45}
.foot{color:var(--muted);font-size:11px;margin-top:30px;text-align:center}
</style></head><body class="sk">
<div class=wrap>
<div class=hub-brand>
  __HUB_LOGO__
  <div class=hub-sub>Painel local · editor, marcas e produção de conteúdo</div>
</div>
<div class=grid>
  <a class=tile href="/editor"><div class=sk-card><span class=ic>✎</span><b>Super Editor</b><p>Edita arte frame a frame, preview ao vivo, troca de fundo, cor, upload e regenerar por IA.</p></div></a>
  <a class=tile href="/painel"><div class=sk-card><span class=ic>▦</span><b>Painel de Conteúdo</b><p>Todas as publicações com preview de Instagram/LinkedIn e download.</p></div></a>
  <a class=tile href="/vitrine"><div class=sk-card><span class=ic>▤</span><b>Vitrine</b><p>Galeria read-only por marca — feed pra aprovar copy e conceito.</p></div></a>
  <a class=tile href="/config"><div class=sk-card><span class=ic>⚙</span><b>Configurações</b><p>Como o sistema está se comportando: temas, cores, degradês, conceitos e estado.</p></div></a>
  <a class=tile href="/design-system/dist/smark-design-system.html"><div class="sk-card sk-card--brand"><span class=ic>◈</span><b style="color:#fff">Design System</b><p style="color:#ffffffcc">Catálogo vivo: tokens, botões, cards, badges e o toggle claro/escuro. Fonte visual do painel.</p></div></a>
</div>
<div class=foot style="display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap">
  <button type="button" id="btheme" title="Alternar claro/escuro">◐</button>
  <span>Editor, Painel, Vitrine e Config · tema do sistema inteiro</span>
</div>
</div>
__THEME_BOOT__
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
  const ACTS=[['Novo projeto','/editor?novo=1','＋'],['Estúdio IA','/editor?estudio=1','★']];
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


# Tema UI compartilhado (claro/escuro) — localStorage + data-theme em TODAS as telas
HEAD_THEME = (
    '<script>(function(){try{var t=localStorage.getItem("smark-ui-theme");'
    'if(t==="claro"||t==="escuro")document.documentElement.setAttribute("data-theme",t)}catch(e){}})()</script>'
)
THEME_BOOT = r"""
<style>
#btheme{width:36px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--surface);
  color:var(--text);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
  font-size:15px;flex:0 0 auto;margin-right:6px}
#btheme:hover{border-color:var(--accent);color:var(--accent)}
</style>
<script>
(function(){
  var KEY='smark-ui-theme';
  function apply(t){
    t=(t==='claro'||t==='light')?'claro':'escuro';
    document.documentElement.setAttribute('data-theme',t);
    try{localStorage.setItem(KEY,t)}catch(e){}
    var b=document.getElementById('btheme');
    if(b){b.title=t==='claro'?'Mudar para tema escuro':'Mudar para tema claro';
      b.setAttribute('aria-label',b.title);
      b.textContent=t==='claro'?'◐':'◑';}
  }
  try{apply(localStorage.getItem(KEY)||document.documentElement.getAttribute('data-theme')||'escuro')}catch(e){apply('escuro')}
  function bind(){
    var b=document.getElementById('btheme');
    if(b&&!b._bound){b._bound=1;b.onclick=function(){
      var cur=document.documentElement.getAttribute('data-theme')||'escuro';
      apply(cur==='claro'?'escuro':'claro');
    }}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
  window.smarkApplyTheme=apply;
})();
</script>
"""

# HUB: logo oficial + tema (smark_logo / THEME_BOOT já existem neste ponto)
if "__HUB_LOGO__" in HUB:
    HUB = HUB.replace(
        "__HUB_LOGO__",
        f'<div class="hub-logo">{smark_logo(52, wordmark=True, word="smark")}</div>',
    )
if "__THEME_BOOT__" in HUB:
    HUB = HUB.replace("__THEME_BOOT__", THEME_BOOT)
elif THEME_BOOT not in HUB:
    HUB = HUB.replace("</body></html>", THEME_BOOT + "</body></html>")


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
            '<button type="button" id="btheme" title="Alternar claro/escuro" aria-label="Tema">◐</button>'
            '<a class="sk-btn sk-btn--secondary sk-btn--sm" href="/editor">✎ Abrir editor</a>'
            '</div>' + THEME_BOOT + cmdk())


def config_html():
    """Tela de configurações: padrões + marcas + log de publicações.

    Conceitos de direção de arte ficam só no motor (_direcao.CONCEITOS) —
    não são expostos na UI; mudança exige confirmação em fluxo admin.
    """
    try:
        tok = json.load(open(os.path.join(VAULT, "design-system", "tokens", "tokens.json"), encoding="utf-8"))
    except Exception:
        tok = {}
    fund = tok.get("fundacao", {})
    tp = tok.get("tema_padrao") or "claro"
    defsize = tok.get("editor_defaults", {}).get("size", "1080x1350")
    return f"""<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Configurações · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css">
{HEAD_THEME}<style>
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
/* ── Galeria de marcas — visual clean ───────────────────────────────── */
.mgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px}}
.mcard{{
  background:var(--surface);border:1px solid var(--line);border-radius:20px;overflow:hidden;
  display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.06);
  transition:border-color .18s,transform .18s,box-shadow .18s;position:relative;
}}
.mcard:hover{{border-color:color-mix(in srgb,var(--accent) 45%,var(--line));transform:translateY(-2px);
  box-shadow:0 4px 8px rgba(0,0,0,.06),0 16px 36px rgba(0,0,0,.1)}}
.mcard .mhero{{height:92px;position:relative;flex:0 0 auto;display:flex;align-items:flex-end;justify-content:center}}
.mcard .mhero::after{{content:'';position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,.12) 100%);pointer-events:none}}
.mlogo{{
  width:64px;height:64px;border-radius:18px;display:grid;place-items:center;font-weight:800;font-size:22px;color:#fff;
  overflow:hidden;background:#fff;border:3px solid var(--surface);box-shadow:0 6px 18px rgba(0,0,0,.18);
  position:relative;z-index:2;margin-bottom:-32px;flex:0 0 64px;
}}
.mlogo img{{width:100%;height:100%;object-fit:contain;padding:7px;background:#fff;box-sizing:border-box}}
.mlogo .glyph{{color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.25)}}
/* canais: ícones oficiais discretos + bolinha de status */
.msocial{{
  position:absolute;top:10px;right:10px;z-index:3;display:flex;gap:6px;
  padding:5px 7px;border-radius:999px;background:rgba(0,0,0,.28);backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.12);
}}
.soc{{
  position:relative;width:28px;height:28px;border-radius:9px;border:0;padding:0;cursor:pointer;
  display:grid;place-items:center;background:rgba(255,255,255,.12);transition:transform .12s,background .12s;
}}
.soc:hover{{transform:scale(1.08);background:rgba(255,255,255,.22)}}
.soc:disabled{{cursor:default;opacity:.85}}
.soc:disabled:hover{{transform:none;background:rgba(255,255,255,.12)}}
.soc svg{{width:16px;height:16px;display:block}}
.soc .dot{{
  position:absolute;right:-2px;bottom:-2px;width:9px;height:9px;border-radius:50%;
  border:2px solid rgba(20,16,30,.85);box-sizing:border-box;
}}
.soc .dot.on{{background:#34c759}}
.soc .dot.off{{background:#8e8e93}}
.soc .dot.wait{{background:#ffcc00}}
/* corpo: nome SEMPRE em superfície clara legível — nunca sobre o degradê */
.mbody{{
  padding:40px 16px 14px;display:flex;flex-direction:column;gap:10px;flex:1;min-width:0;
  background:var(--surface);text-align:center;
}}
.mcard h3{{
  font-size:15.5px;margin:0;letter-spacing:-.02em;line-height:1.25;font-weight:700;
  color:var(--text) !important;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;word-break:break-word;
}}
.mcard .slug{{
  color:var(--muted);font-size:12.5px;line-height:1.3;margin-top:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.mmeta{{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;min-height:18px}}
.mswatches{{display:flex;gap:5px;align-items:center;justify-content:center}}
.msw{{width:14px;height:14px;border-radius:50%;border:1px solid rgba(0,0,0,.08);box-shadow:inset 0 0 0 1px rgba(255,255,255,.15)}}
.mtag{{font-size:10px;font-weight:600;letter-spacing:.02em;color:var(--muted);padding:2px 8px;border-radius:999px;background:var(--inset);border:1px solid var(--line)}}
.macts{{display:flex;gap:8px;align-items:center;margin-top:auto;padding-top:6px}}
.macts .sk-btn{{flex:1;justify-content:center;text-align:center;min-width:0;border-radius:12px}}
.macts .sk-btn--primary{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.macts .iconbtn{{
  flex:0 0 38px;width:38px;height:38px;border-radius:12px;border:1px solid var(--line);
  background:var(--inset);color:var(--muted);cursor:pointer;display:grid;place-items:center;padding:0;
  transition:border-color .12s,color .12s,background .12s;
}}
.macts .iconbtn:hover{{border-color:var(--accent);color:var(--text);background:var(--surface)}}
.macts .iconbtn.del:hover{{border-color:var(--bad);color:var(--bad);background:var(--bad-soft)}}
.macts .iconbtn svg{{width:16px;height:16px}}
.chbanner{{
  font-size:12px;color:var(--muted);padding:10px 14px;border-radius:12px;
  background:var(--inset);border:1px solid var(--line);margin-bottom:14px;line-height:1.45;
}}
.chbanner code{{font-size:11px;background:var(--surface);padding:1px 5px;border-radius:4px;border:1px solid var(--line)}}
/* log de posts — sanfona + tabela */
.plog-acc{{border:1px solid var(--line);border-radius:14px;background:var(--inset);overflow:hidden}}
.plog-acc>summary{{cursor:pointer;padding:14px 16px;font-weight:600;font-size:14px;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;user-select:none}}
.plog-acc>summary::-webkit-details-marker{{display:none}}
.plog-acc>summary::after{{content:'▸';color:var(--muted);font-size:12px;transition:transform .15s}}
.plog-acc[open]>summary::after{{transform:rotate(90deg)}}
.plog-acc .plog-body{{padding:0 12px 14px;border-top:1px solid var(--line)}}
.plog-table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}}
.plog-table th{{text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:8px 8px;border-bottom:1px solid var(--line)}}
.plog-table td{{padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:middle}}
.plog-table tr:last-child td{{border-bottom:0}}
.plog-table .t{{font-weight:600;color:var(--text);max-width:240px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.plog-pager{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:12px;flex-wrap:wrap}}
.plog-pager .pginfo{{font-size:12px;color:var(--muted)}}
.plog-pager .pgbtns{{display:flex;gap:6px;align-items:center}}
.modal{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:80;padding:20px}}
.modal.on{{display:flex}}
.mbox{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;width:min(640px,100%);max-height:92vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,.45)}}
.mbox h2{{font-size:18px;margin:0 0 6px;color:var(--text)}}
.mbox .msub{{font-size:13px;color:var(--muted);margin:0 0 16px;line-height:1.4}}
.fld{{margin-bottom:14px}} .fld label{{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;font-weight:600}}
.fld input,.fld textarea,.fld select{{width:100%;background:var(--field);border:1px solid var(--field-line);border-radius:12px;color:var(--text);padding:11px 13px;font-size:14px;font-family:inherit}}
.fld input:focus,.fld textarea:focus,.fld select:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}}
.fld textarea{{min-height:70px;resize:vertical}}
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.msec{{border:1px solid var(--line);border-radius:14px;margin:0 0 14px;overflow:hidden;background:var(--inset)}}
.msec>summary{{cursor:pointer;padding:12px 14px;font-weight:600;font-size:13px;color:var(--text);list-style:none;display:flex;justify-content:space-between;align-items:center;user-select:none}}
.msec>summary::-webkit-details-marker{{display:none}}
.msec>summary::after{{content:'▸';color:var(--muted);font-size:11px}}
.msec[open]>summary::after{{transform:rotate(90deg)}}
.msec .msec-body{{padding:4px 14px 14px;border-top:1px solid var(--line)}}
.mbtns{{display:flex;gap:8px;justify-content:flex-end;margin-top:8px;flex-wrap:wrap;align-items:center}}
.mbtns .del-left{{margin-right:auto}}
.logoprev{{width:64px;height:64px;border-radius:14px;border:1px dashed var(--line);display:grid;place-items:center;overflow:hidden;background:var(--inset);font-size:11px;color:var(--muted)}}
.logoprev img{{width:100%;height:100%;object-fit:contain;padding:4px;box-sizing:border-box;background:#fff}}
/* wizard */
.wiz-steps{{display:flex;gap:6px;margin:0 0 18px;flex-wrap:wrap}}
.wiz-step{{flex:1;min-width:72px;text-align:center;padding:8px 6px;border-radius:12px;border:1px solid var(--line);background:var(--inset);font-size:11px;font-weight:600;color:var(--muted);cursor:pointer;transition:.15s}}
.wiz-step.on{{border-color:var(--accent);background:var(--accent-soft);color:var(--text)}}
.wiz-step.done{{border-color:color-mix(in srgb,var(--good) 40%,var(--line));color:var(--good)}}
.wiz-step .n{{display:block;font-size:14px;margin-bottom:2px}}
.wiz-pane{{display:none}}
.wiz-pane.on{{display:block}}
.wiz-tip{{font-size:13px;color:var(--muted);line-height:1.45;margin:0 0 14px;padding:10px 12px;border-radius:12px;background:var(--inset);border:1px solid var(--line)}}
.logo-vars{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}}
.logo-var{{border:2px solid var(--line);border-radius:14px;padding:12px 8px;text-align:center;cursor:pointer;background:var(--surface);transition:.15s}}
.logo-var:hover{{border-color:var(--accent)}}
.logo-var.on{{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}}
.logo-var .lv-prev{{width:56px;height:56px;margin:0 auto 8px;border-radius:12px;background:#1a1a22;display:grid;place-items:center;overflow:hidden;color:#fff;font-weight:800;font-size:22px}}
.logo-var .lv-prev img{{width:100%;height:100%;object-fit:contain;padding:6px;box-sizing:border-box}}
.logo-var .lv-lb{{font-size:12px;font-weight:600;color:var(--text)}}
.logo-var .lv-ds{{font-size:10px;color:var(--muted);margin-top:2px}}
.bb-preview{{margin-top:10px;max-height:220px;overflow:auto;padding:12px;border-radius:12px;border:1px solid var(--line);background:var(--inset);font-size:12px;line-height:1.5;color:var(--text);white-space:pre-wrap;font-family:var(--font-mono,ui-monospace,monospace)}}
.bb-assets{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}}
.bb-assets img{{width:64px;height:64px;object-fit:cover;border-radius:10px;border:1px solid var(--line)}}
/* galeria de refs — estilo Claude Projects */
.refdrop{{border:1.5px dashed var(--line);border-radius:16px;padding:18px 14px;text-align:center;background:var(--inset);cursor:pointer;transition:border-color .15s,background .15s}}
.refdrop:hover,.refdrop.drag{{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 8%,var(--inset))}}
.refdrop b{{display:block;font-size:14px;color:var(--text);margin-bottom:4px}}
.refdrop span{{font-size:12px;color:var(--muted);line-height:1.4}}
.refgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px;margin-top:12px}}
.refcard{{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 2px 10px rgba(0,0,0,.06);position:relative;transition:border-color .15s,transform .15s}}
.refcard:hover{{border-color:color-mix(in srgb,var(--accent) 40%,var(--line));transform:translateY(-1px)}}
.refcard .thumb{{aspect-ratio:4/3;background:#1a1a1e;display:grid;place-items:center;overflow:hidden}}
.refcard .thumb img{{width:100%;height:100%;object-fit:cover;display:block}}
.refcard .meta{{padding:8px 10px 10px}}
.refcard .meta .t{{font-size:12px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.refcard .meta .s{{font-size:10px;color:var(--muted);margin-top:2px}}
.refcard .x{{position:absolute;top:6px;right:6px;width:24px;height:24px;border-radius:50%;border:0;background:rgba(0,0,0,.55);color:#fff;font-size:14px;cursor:pointer;line-height:24px;padding:0;opacity:0;transition:opacity .12s}}
.refcard:hover .x{{opacity:1}}
.refcard.pending{{opacity:.75}}
.refcount{{font-size:12px;color:var(--muted);margin-top:8px}}
.glyphrow{{display:flex;gap:8px;align-items:center}}
.glyphrow select{{flex:1}}
.glyphrow input{{width:72px;flex:0 0 72px;text-align:center}}
.mbox{{width:min(680px,100%)}}
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
  <div class=gh><span>Marcas &amp; canais</span><button class="sk-btn sk-btn--sm" id=bm_new>+ Nova marca</button></div>
  <div class=chbanner id=canais_banner>Cada cliente conecta o <b>próprio Instagram</b> (Business/Creator) para postagens automáticas. LinkedIn em breve.</div>
  <div id=mgrid class=mgrid><div style="color:var(--muted);font-size:13px">Carregando marcas…</div></div>
  <div style="margin-top:12px;color:var(--muted);font-size:12px;line-height:1.5">
    Novo cliente: crie a marca, conecte o Instagram, confira cores e logo, depois abra o <a href="/editor">Editor</a> e gere 3 peças-piloto.
  </div>
</div>

<div class="sk-card">
  <details class=plog-acc id=plog_acc>
    <summary>
      <span>Publicações &amp; tempo <span id=plog_count style="font-weight:500;color:var(--muted);font-size:12px;margin-left:6px"></span></span>
    </summary>
    <div class=plog-body>
      <div class=kv style="margin:12px 0">
        <div class=cell>Marca: <select class="sk-select mini" id=plog_marca><option value="">Todas</option></select></div>
        <div class=cell>Busca: <input class="sk-input mini" id=plog_q placeholder="título…" style="width:160px"></div>
      </div>
      <div id=plog_stats class=kv style="margin-bottom:8px"></div>
      <div id=plog_list></div>
      <div class=plog-pager id=plog_pager style="display:none">
        <span class=pginfo id=plog_pginfo></span>
        <div class=pgbtns>
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=plog_prev>← Anterior</button>
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=plog_next>Próxima →</button>
        </div>
      </div>
    </div>
  </details>
</div>
<!-- Conceitos de direção de arte: config interna do motor (_direcao.CONCEITOS).
     Não expostos na UI — alteração só com confirmação explícita (API/admin). -->

</div>

<div class=modal id=mmodal>
  <div class=mbox>
    <h2 id=mtitle>Nova marca</h2>
    <p class=msub id=msub>Assistente em 4 passos: o site e as fotos preenchem o resto.</p>
    <div class=wiz-steps id=wiz_steps>
      <div class="wiz-step on" data-step=1><span class=n>1</span>Fontes</div>
      <div class=wiz-step data-step=2><span class=n>2</span>Identidade</div>
      <div class=wiz-step data-step=3><span class=n>3</span>Logo</div>
      <div class=wiz-step data-step=4><span class=n>4</span>Revisão</div>
    </div>
    <div class=fld id=fld_slug style="display:none"><label>Slug</label><input id=mf_slug readonly disabled></div>

    <!-- PASSO 1: fontes primeiro (puxam o resto) -->
    <div class="wiz-pane on" id=wiz1>
      <div class=wiz-tip>Comece pelo <b>site</b> e pelas <b>fotos</b> do cliente. O sistema sugere nome, cores e clima — você só revisa.</div>
      <div class=fld><label>Site do cliente</label>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <input id=mf_site placeholder="https://cliente.com.br" style="flex:1;min-width:180px">
          <button type=button class="sk-btn sk-btn--sm" id=mf_ler_site>Ler site</button>
        </div>
        <div id=mf_dna_msg style="font-size:12px;color:var(--muted);margin-top:6px;line-height:1.4"></div>
        <details class=msec id=mf_dna_box style="display:none;margin-top:10px">
          <summary>Resumo da marca (do site)</summary>
          <div class=msec-body>
            <div id=mf_dna_resumo style="font-size:13px;line-height:1.5;color:var(--text);margin-bottom:10px"></div>
            <div id=mf_dna_meta style="font-size:12px;color:var(--muted);line-height:1.45"></div>
          </div>
        </details>
      </div>
      <div class=fld><label>Referências visuais (feed, site, impressos)</label>
        <div class=refdrop id=mf_refdrop tabindex=0 role=button>
          <b>Arraste imagens ou clique</b>
          <span>JPG/PNG · após salvar a marca, envio é imediato</span>
          <input type=file id=mf_refs accept="image/png,image/jpeg,image/webp,image/jpg" multiple style="display:none">
        </div>
        <div id=mf_refgrid class=refgrid></div>
        <div class=refcount id=mf_refcount></div>
      </div>
      <div class=fld><label>Cores (sugeridas pelas fotos ou pelo site)</label>
        <div class=row2>
          <div class=fld style="margin:0"><label style="font-size:11px;font-weight:500">Principal</label>
            <div style="display:flex;gap:6px;align-items:center">
              <input id=mf_acento type=color value="#1CA5B2" style="height:42px;padding:4px;flex:1">
              <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_pick_acc>🖌</button>
            </div>
          </div>
          <div class=fld style="margin:0"><label style="font-size:11px;font-weight:500">Clara</label>
            <div style="display:flex;gap:6px;align-items:center">
              <input id=mf_acento_claro type=color value="#3DC4D0" style="height:42px;padding:4px;flex:1">
              <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_pick_acc2>🖌</button>
            </div>
          </div>
        </div>
        <div id=mf_swatches style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px"></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center">
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_extract_colors>Sugerir cores das fotos</button>
          <span id=mf_colors_msg style="font-size:12px;color:var(--muted)"></span>
        </div>
      </div>
    </div>

    <!-- PASSO 2: identidade (pré-preenchida) -->
    <div class=wiz-pane id=wiz2>
      <div class=wiz-tip>Revise o que o site sugeriu. Ajuste só o que estiver errado.</div>
      <div class=fld><label>Nome da empresa</label><input id=mf_nome placeholder="Ex.: NetSul Fibra" autocomplete=organization></div>
      <div class=row2>
        <div class=fld><label>@ Instagram / handle</label><input id=mf_handle placeholder="@marca"></div>
        <div class=fld><label>Nome no chip</label><input id=mf_wordmark placeholder="NetSul"></div>
      </div>
      <div class=fld><label>Segmento</label>
        <select id=mf_segmento>
          <option value="">Selecione…</option>
          <option value="contabilidade">Contabilidade / fiscal</option>
          <option value="telecom">Telecom / ISP</option>
          <option value="varejo">Varejo / e-commerce</option>
          <option value="imobiliaria">Imobiliário</option>
          <option value="saude">Saúde / clínicas</option>
          <option value="servicos">Serviços B2B</option>
          <option value="educacao">Educação</option>
          <option value="industria">Indústria</option>
          <option value="outro">Outro</option>
        </select>
      </div>
      <div class=fld><label>Clima visual (mood)</label>
        <textarea id=mf_mood placeholder="Como a marca deve parecer nas artes…"></textarea>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_ia_mood style="display:inline-flex;align-items:center">{ICON_IA_SM}Gerar mood</button>
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_ia_all style="display:inline-flex;align-items:center">{ICON_IA_SM}Sugerir handle</button>
        </div>
        <div id=mf_ia_dica style="font-size:11px;color:var(--muted);margin-top:6px"></div>
      </div>
      <div class=fld style="display:none"><label>Símbolo</label>
        <div class=glyphrow>
          <select id=mf_glyph_mode>
            <option value="auto">Automático</option>
            <option value="custom">Personalizado</option>
            <option value="none">Nenhum</option>
          </select>
          <input id=mf_glyph placeholder="N" maxlength=2>
        </div>
      </div>
    </div>

    <!-- PASSO 3: logo + 3 estilos -->
    <div class=wiz-pane id=wiz3>
      <div class=wiz-tip>A logo é a <b>assinatura</b> na tab e no chip. Envie o arquivo e escolha como aplicar (ícone mono, colorido ou letra).</div>
      <div class=fld><label>Arquivo da logo (PNG transparente preferível)</label>
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
          <div class=logoprev id=mf_logoprev>sem logo</div>
          <input type=file id=mf_logo accept="image/png,image/svg+xml,image/webp,image/jpeg" style="font-size:12px;color:var(--muted)">
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_logo_rm>Remover</button>
        </div>
      </div>
      <div class=fld><label>Como aplicar na arte</label>
        <div class=logo-vars id=mf_logo_vars>
          <div class="logo-var on" data-estilo=mono>
            <div class=lv-prev id=lv_mono>—</div>
            <div class=lv-lb>Mono</div>
            <div class=lv-ds>Ícone na cor do acento</div>
          </div>
          <div class=logo-var data-estilo=color>
            <div class=lv-prev id=lv_color>—</div>
            <div class=lv-lb>Colorido</div>
            <div class=lv-ds>Cores originais</div>
          </div>
          <div class=logo-var data-estilo=glyph>
            <div class=lv-prev id=lv_glyph>A</div>
            <div class=lv-lb>Letra</div>
            <div class=lv-ds>Monograma limpo</div>
          </div>
        </div>
        <input type=hidden id=mf_logo_estilo value=mono>
        <div id=mf_logo_msg style="font-size:12px;color:var(--muted);margin-top:8px"></div>
      </div>
    </div>

    <!-- PASSO 4: moldura + book + salvar -->
    <div class=wiz-pane id=wiz4>
      <div class=wiz-tip>Defina o que entra na arte por padrão e gere o branding book (resumo da marca no vault).</div>
      <div class=fld><label>Template padrão da arte</label>
        <div id=mf_moldura style="display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin-top:4px">
          <label class=chk><input type=checkbox id=mf_m_chip checked> Selo (chip)</label>
          <label class=chk><input type=checkbox id=mf_m_tab checked> Aba lateral</label>
          <label class=chk><input type=checkbox id=mf_m_logo checked> Logo no selo/aba</label>
          <label class=chk><input type=checkbox id=mf_m_footer checked> Rodapé</label>
          <label class=chk><input type=checkbox id=mf_m_page checked> Paginação</label>
          <label class=chk><input type=checkbox id=mf_m_grade checked> Acabamento</label>
        </div>
      </div>
      <div class=fld><label>Branding book</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <button type=button class="sk-btn sk-btn--secondary sk-btn--sm" id=mf_bb_gen>Gerar book</button>
          <label class="sk-btn sk-btn--secondary sk-btn--sm" style="cursor:pointer;margin:0">
            + Anexar páginas
            <input type=file id=mf_bb_files accept="image/*,.pdf" multiple style="display:none">
          </label>
          <span id=mf_bb_status style="font-size:12px;color:var(--muted)"></span>
        </div>
        <div id=mf_bb_preview class=bb-preview style="display:none"></div>
        <div id=mf_bb_assets class=bb-assets></div>
      </div>
      <div class=fld><label>Conferência rápida</label>
        <div id=mf_review style="font-size:13px;line-height:1.55;color:var(--muted);padding:10px 12px;border-radius:12px;background:var(--inset);border:1px solid var(--line)"></div>
      </div>
    </div>

    <div id=mf_msg style="font-size:13px;min-height:18px;margin:4px 0"></div>
    <div class=mbtns>
      <button type=button class="sk-btn sk-btn--secondary sk-btn--sm del-left" id=mf_del style="display:none">Excluir</button>
      <button class="sk-btn sk-btn--secondary" id=mf_cancel>Cancelar</button>
      <button type=button class="sk-btn sk-btn--secondary" id=mf_prev style="display:none">← Voltar</button>
      <button type=button class="sk-btn" id=mf_next>Continuar →</button>
      <button class="sk-btn" id=mf_save style="display:none">Salvar marca</button>
    </div>
  </div>
</div>

<script>
const T="__EDITOR_TOKEN__";
const H={{'Content-Type':'application/json','X-Editor-Token':T}};
const esc=s=>(s==null?'':String(s)).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
async function api(url, body){{
  try{{
    const r=await fetch(url,{{method:'POST',headers:H,body:JSON.stringify(body||{{}})}});
    let j={{}};
    try{{j=await r.json()}}catch(e){{j={{ok:false,erro:'resposta inválida ('+r.status+')'}}}}
    if(r.status===403||j.reload){{
      j.ok=false;
      j.erro=(j.erro||'sessão expirada')+' — recarregue (F5)';
    }}
    return j;
  }}catch(e){{
    return {{ok:false,erro:'rede: '+(e.message||e)}};
  }}
}}
document.getElementById('cf_tema').value="{tp}";
document.getElementById('cf_size').value="{defsize}";
document.getElementById('cf_save').onclick=async()=>{{
  if(!confirm('Salvar os padrões do sistema?\\n\\nIsso altera tema-padrão, tamanho e rodapé para novas artes.'))return;
  const r=await api('/config-save',{{tema_padrao:document.getElementById('cf_tema').value,size:document.getElementById('cf_size').value,rodape:document.getElementById('cf_rodape').value}});
  document.getElementById('cf_msg').textContent=r.ok?'Salvo ✓':('Erro: '+(r.erro||''));
}};

let MARCAS=[], EDIT=null, LOGO_DATA=null, REFS_DATA=[], REFS_SAVED=[];
let WIZ_STEP=1, LOGO_ESTILO='mono';
function goWiz(n){{
  WIZ_STEP=Math.max(1,Math.min(4,n|0));
  document.querySelectorAll('.wiz-pane').forEach((p,i)=>p.classList.toggle('on',i+1===WIZ_STEP));
  document.querySelectorAll('.wiz-step').forEach(s=>{{
    const sn=+s.dataset.step;
    s.classList.toggle('on',sn===WIZ_STEP);
    s.classList.toggle('done',sn<WIZ_STEP);
  }});
  const prev=document.getElementById('mf_prev');
  const next=document.getElementById('mf_next');
  const save=document.getElementById('mf_save');
  if(prev)prev.style.display=WIZ_STEP>1?'':'none';
  if(next)next.style.display=WIZ_STEP<4?'':'none';
  if(save)save.style.display=WIZ_STEP===4?'':'none';
  if(WIZ_STEP===3) refreshLogoVars();
  if(WIZ_STEP===4){{updateReview();if(EDIT)refreshBbStatus(EDIT)}}
}}
function updateReview(){{
  const el=document.getElementById('mf_review'); if(!el)return;
  const nome=document.getElementById('mf_nome').value.trim()||'—';
  const handle=document.getElementById('mf_handle').value.trim()||'—';
  const seg=document.getElementById('mf_segmento').value||'—';
  const site=document.getElementById('mf_site').value.trim()||'—';
  const acc=document.getElementById('mf_acento').value;
  const nref=(REFS_SAVED||[]).length+(REFS_DATA||[]).length;
  const estilo=document.getElementById('mf_logo_estilo').value||'mono';
  el.innerHTML=
    '<div><b style="color:var(--text)">'+esc(nome)+'</b> · '+esc(handle)+'</div>'
    +'<div>Segmento: '+esc(seg)+' · Site: '+esc(site)+'</div>'
    +'<div>Cor: <span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:'+esc(acc)+';vertical-align:middle"></span> '
    +esc(acc)+' · Logo: '+esc(estilo)+' · Refs: '+nref+'</div>';
}}
document.getElementById('mf_prev').onclick=()=>goWiz(WIZ_STEP-1);
document.getElementById('mf_next').onclick=()=>{{
  if(WIZ_STEP===1){{
    // se tem site e ainda não leu, avisa mas deixa seguir
  }}
  if(WIZ_STEP===2){{
    const nome=document.getElementById('mf_nome').value.trim();
    if(!nome){{document.getElementById('mf_msg').className='err';document.getElementById('mf_msg').textContent='Informe o nome da empresa';return}}
  }}
  goWiz(WIZ_STEP+1);
}};
document.querySelectorAll('.wiz-step').forEach(s=>s.onclick=()=>goWiz(+s.dataset.step));

function glyphFromForm(){{
  const mode=(document.getElementById('mf_glyph_mode')||{{}}).value||'auto';
  if(mode==='none') return '';
  if(mode==='custom') return (document.getElementById('mf_glyph').value||'').trim().slice(0,2);
  // auto
  const nome=(document.getElementById('mf_nome').value||'').trim();
  return (nome[0]||'M').toUpperCase();
}}
function molduraFromForm(){{
  return {{
    chip:!!document.getElementById('mf_m_chip').checked,
    tab:!!document.getElementById('mf_m_tab').checked,
    logo:!!document.getElementById('mf_m_logo').checked,
    footer:!!document.getElementById('mf_m_footer').checked,
    page:!!document.getElementById('mf_m_page').checked,
    grade:!!document.getElementById('mf_m_grade').checked,
  }};
}}
function setMolduraUI(m){{
  m=m||{{}};
  const set=(id,def)=>{{const el=document.getElementById(id);if(el)el.checked=m[id.replace('mf_m_','')]!==undefined?!!m[id.replace('mf_m_','')]:def}};
  // map explícito
  const map={{mf_m_chip:'chip',mf_m_tab:'tab',mf_m_logo:'logo',mf_m_footer:'footer',mf_m_page:'page',mf_m_grade:'grade'}};
  Object.keys(map).forEach(id=>{{
    const el=document.getElementById(id); if(!el)return;
    const k=map[id];
    el.checked=m[k]!==undefined?!!m[k]:true;
  }});
}}
function setGlyphUI(glyph){{
  const modeEl=document.getElementById('mf_glyph_mode');
  const inp=document.getElementById('mf_glyph');
  if(!modeEl||!inp)return;
  if(glyph===''||glyph===null||glyph===undefined){{
    modeEl.value='none'; inp.value=''; inp.disabled=true;
  }}else if(glyph.length<=2){{
    // se é só 1ª letra do nome → auto
    const nome=(document.getElementById('mf_nome').value||'').trim();
    if(glyph.toUpperCase()===(nome[0]||'').toUpperCase() && glyph.length===1){{
      modeEl.value='auto'; inp.value=glyph; inp.disabled=true;
    }}else{{
      modeEl.value='custom'; inp.value=glyph; inp.disabled=false;
    }}
  }}else{{
    modeEl.value='custom'; inp.value=String(glyph).slice(0,2); inp.disabled=false;
  }}
}}
function syncGlyphMode(){{
  const mode=document.getElementById('mf_glyph_mode').value;
  const inp=document.getElementById('mf_glyph');
  if(mode==='none'){{inp.value='';inp.disabled=true}}
  else if(mode==='auto'){{
    const nome=(document.getElementById('mf_nome').value||'').trim();
    inp.value=(nome[0]||'M').toUpperCase(); inp.disabled=true;
  }}else{{inp.disabled=false; if(!inp.value) inp.focus()}}
}}
document.getElementById('mf_glyph_mode').onchange=syncGlyphMode;
document.getElementById('mf_nome').addEventListener('input',()=>{{
  if(document.getElementById('mf_glyph_mode').value==='auto') syncGlyphMode();
}});

/* Ícones oficiais do sistema (IG / LI) */
function svgIg(id){{
  return `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><defs><linearGradient id="${{id}}" x1="0" y1="24" x2="24" y2="0"><stop stop-color="#f58529"/><stop offset=".5" stop-color="#dd2a7b"/><stop offset="1" stop-color="#515bd4"/></linearGradient></defs><rect x="2" y="2" width="20" height="20" rx="5.5" fill="url(#${{id}})"/><circle cx="12" cy="12" r="4.2" stroke="#fff" stroke-width="1.7"/><circle cx="17.4" cy="6.6" r="1.25" fill="#fff"/></svg>`;
}}
const SVG_LI=`<svg viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="5" fill="#0A66C2"/><path fill="#fff" d="M7.1 9.4H4.7V19h2.4V9.4zM5.9 5A1.4 1.4 0 105.9 7.8 1.4 1.4 0 005.9 5zM19.3 13.2c0-2.5-1.3-3.7-3.1-3.7a2.7 2.7 0 00-2.4 1.3h-.05V9.4h-2.3c.03.7 0 9.6 0 9.6h2.3v-5.4c0-.3 0-.5.1-.7.2-.5.7-1 1.5-1 1.1 0 1.5.8 1.5 2v5.1h2.4v-5.8z"/></svg>`;
const SVG_EDIT=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>`;
const SVG_TRASH=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>`;

function socialBar(m){{
  const ig=(m.canais&&m.canais.instagram)||{{}};
  const li=(m.canais&&m.canais.linkedin)||{{}};
  const igOk=!!ig.conectado;
  const igSvg=svgIg('ig_'+String(m.slug||'x').replace(/[^a-z0-9]/gi,''));
  const igTitle=igOk
    ?('Instagram @'+(ig.username||'')+(ig.modo==='fake'?' (simulado)':'')+' — clique p/ desconectar')
    :'Conectar Instagram';
  const liTitle=li.conectado?('LinkedIn @'+(li.username||'')):'LinkedIn em breve';
  const igBtn=igOk
    ?`<button type=button class=soc data-ig-off="${{esc(m.slug)}}" title="${{esc(igTitle)}}">${{igSvg}}<i class="dot on"></i></button>`
    :`<button type=button class=soc data-ig-on="${{esc(m.slug)}}" title="${{esc(igTitle)}}">${{igSvg}}<i class="dot off"></i></button>`;
  const liBtn=`<button type=button class=soc disabled title="${{esc(liTitle)}}">${{SVG_LI}}<i class="dot ${{li.conectado?'on':'wait'}}"></i></button>`;
  return `<div class=msocial>${{igBtn}}${{liBtn}}</div>`;
}}
async function conectarIg(slug){{
  const r=await api('/canais/conectar',{{marca:slug,canal:'instagram',return_to:'/config?editar='+encodeURIComponent(slug)}});
  if(!r.ok){{alert(r.erro||'não foi possível iniciar a conexão');return}}
  location.href=r.url;
}}
async function desconectarIg(slug){{
  const m=MARCAS.find(x=>x.slug===slug);
  const u=(m&&m.canais&&m.canais.instagram&&m.canais.instagram.username)||'';
  if(!confirm('Desconectar Instagram'+(u?(' @'+u):'')+' da marca '+((m&&m.nome)||slug)+'?'))return;
  const r=await api('/canais/desconectar',{{marca:slug,canal:'instagram'}});
  if(!r.ok){{alert(r.erro||'falhou');return}}
  await loadMarcas();
}}
async function loadMarcas(){{
  const r=await(await fetch('/marcas')).json();
  MARCAS=(r.ok&&r.marcas)?r.marcas:[];
  const ban=document.getElementById('canais_banner');
  if(ban){{
    const modo=r.canais_modo||'fake';
    ban.innerHTML=modo==='real'
      ?'App Meta <b>real</b> · toque no ícone do Instagram no card para conectar a conta do cliente.'
      :'Toque no <b>ícone do Instagram</b> no card para conectar · modo simulado até configurar o App Meta no <code>.env</code>.';
  }}
  const g=document.getElementById('mgrid');
  if(!MARCAS.length){{g.innerHTML='<div style="color:var(--muted)">Nenhuma marca.</div>';return}}
  g.innerHTML=MARCAS.map(m=>{{
    const hero=esc(m.gradiente||m.acento||'#5b3fd4');
    const logo=m.logo_url
      ?`<img src="${{esc(m.logo_url)}}?t=${{Date.now()}}" alt="">`
      :`<span class=glyph style="background:${{hero}};width:100%;height:100%;display:grid;place-items:center;border-radius:15px">${{esc((m.glyph||m.nome||'?')[0]||'?')}}</span>`;
    const tag=m.canonica?'Grupo':'Cliente';
    return `<article class=mcard data-slug="${{esc(m.slug)}}">
      <div class=mhero style="background:${{hero}}">
        ${{socialBar(m)}}
        <div class=mlogo title="${{esc(m.nome)}}">${{logo}}</div>
      </div>
      <div class=mbody>
        <div>
          <h3 title="${{esc(m.nome)}}">${{esc(m.nome)}}</h3>
          <div class=slug title="${{esc(m.handle||('@'+m.slug))}}">${{esc(m.handle||('@'+m.slug))}}</div>
        </div>
        <div class=mmeta>
          <div class=mswatches title="Paleta">
            <span class=msw style="background:${{esc(m.acento)}}"></span>
            <span class=msw style="background:${{esc(m.acento_claro||m.acento)}}"></span>
            ${{m.base_escura?`<span class=msw style="background:${{esc(m.base_escura)}}"></span>`:''}}
          </div>
          <span class=mtag>${{tag}}</span>
        </div>
        <div class=macts>
          <button type=button class="iconbtn" data-edit="${{esc(m.slug)}}" title="Editar marca">${{SVG_EDIT}}</button>
          <a class="sk-btn sk-btn--sm sk-btn--primary" href="/editor?novo=1&marca=${{encodeURIComponent(m.slug)}}">Novo post</a>
          ${{m.canonica?'':`<button type=button class="iconbtn del" data-del="${{esc(m.slug)}}" title="Excluir marca">${{SVG_TRASH}}</button>`}}
        </div>
      </div>
    </article>`;
  }}).join('');
  g.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>openEdit(b.dataset.edit));
  g.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>excluirMarca(b.dataset.del));
  g.querySelectorAll('[data-ig-on]').forEach(b=>b.onclick=()=>conectarIg(b.dataset.igOn));
  g.querySelectorAll('[data-ig-off]').forEach(b=>b.onclick=()=>desconectarIg(b.dataset.igOff));
}}
function slugifyNome(s){{
  return (s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')
    .replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40)||'marca';
}}
async function excluirMarca(slug){{
  const m=MARCAS.find(x=>x.slug===slug);
  if(!m)return;
  if(m.canonica){{alert('Marcas do grupo smark não podem ser excluídas.');return}}
  const ok=confirm('Excluir a marca "'+m.nome+'"?\\n\\nIsso remove o cadastro e a pasta de branding/refs. Posts já criados no editor não são apagados automaticamente.');
  if(!ok)return;
  const conf=prompt('Para confirmar, digite o nome da marca:\\n'+m.nome);
  if(conf!==m.nome){{if(conf!=null)alert('Nome não confere — nada foi apagado.');return}}
  const r=await api('/excluir-marca',{{slug,apagar_pasta:true}});
  if(!r.ok){{alert(r.erro||'falhou');return}}
  if(EDIT===slug){{document.getElementById('mmodal').classList.remove('on');EDIT=null}}
  await loadMarcas();
}}

function clearRefsPrev(){{
  REFS_DATA=[];
  REFS_SAVED=[];
  const grid=document.getElementById('mf_refgrid'); if(grid) grid.innerHTML='';
  const rc=document.getElementById('mf_refcount'); if(rc) rc.textContent='';
  const inp=document.getElementById('mf_refs'); if(inp) inp.value='';
  const sw=document.getElementById('mf_swatches'); if(sw) sw.innerHTML='';
  const cm=document.getElementById('mf_colors_msg'); if(cm) cm.textContent='';
}}
function showSwatches(cores){{
  const box=document.getElementById('mf_swatches');
  if(!box)return;
  if(!cores||!cores.length){{box.innerHTML='';return}}
  box.innerHTML=cores.map(c=>`<button type=button title="${{esc(c)}}" data-hex="${{esc(c)}}"
    style="width:28px;height:28px;border-radius:8px;border:2px solid var(--line);background:${{esc(c)}};cursor:pointer"></button>`).join('');
  box.querySelectorAll('[data-hex]').forEach(b=>b.onclick=()=>{{
    document.getElementById('mf_acento').value=b.dataset.hex;
    document.getElementById('mf_colors_msg').textContent='Acento → '+b.dataset.hex;
  }});
}}
function renderRefGrid(){{
  const grid=document.getElementById('mf_refgrid');
  const rc=document.getElementById('mf_refcount');
  if(!grid)return;
  // dedupe salvas por base
  const seen=new Set();
  const saved=[];
  (REFS_SAVED||[]).forEach(x=>{{
    const k=x.base||x.nome; if(seen.has(k))return; seen.add(k); saved.push(x);
  }});
  const pending=REFS_DATA||[];
  if(!saved.length&&!pending.length){{
    grid.innerHTML='';
    if(rc)rc.textContent='Nenhuma referência ainda — envie fotos do feed/site do cliente.';
    return;
  }}
  const cards=[];
  saved.forEach(x=>{{
    cards.push(`<div class=refcard data-nome="${{esc(x.nome)}}">
      <button type=button class=x title="Excluir" data-del-ref="${{esc(x.nome)}}">×</button>
      <div class=thumb><img src="${{esc(x.url)}}?t=${{Date.now()}}" alt="" loading=lazy></div>
      <div class=meta><div class=t title="${{esc(x.nome)}}">${{esc((x.base||x.nome||'').slice(0,28))}}</div>
      <div class=s>${{esc(x.kind||'ref')}} · salva</div></div></div>`);
  }});
  pending.forEach((x,i)=>{{
    cards.push(`<div class="refcard pending" data-pend="${{i}}">
      <button type=button class=x title="Tirar da fila" data-del-pend="${{i}}">×</button>
      <div class=thumb><img src="${{esc(x.dataurl)}}" alt=""></div>
      <div class=meta><div class=t>${{esc((x.nome||'ref').slice(0,28))}}</div>
      <div class=s>enviando…</div></div></div>`);
  }});
  grid.innerHTML=cards.join('');
  if(rc)rc.textContent=saved.length+' salva(s)'+(pending.length?(' · '+pending.length+' na fila'):'');
  grid.querySelectorAll('[data-del-ref]').forEach(b=>b.onclick=async(e)=>{{
    e.preventDefault(); e.stopPropagation();
    if(!EDIT){{alert('Salve a marca antes de excluir refs');return}}
    if(!confirm('Remover esta referência?'))return;
    const rr=await api('/marca-ref-del',{{slug:EDIT,nome:b.dataset.delRef}});
    if(!rr.ok){{alert(rr.erro||'falhou');return}}
    await loadSavedRefs(EDIT);
  }});
  grid.querySelectorAll('[data-del-pend]').forEach(b=>b.onclick=()=>{{
    const i=+b.dataset.delPend;
    REFS_DATA=REFS_DATA.filter((_,idx)=>idx!==i);
    renderRefGrid();
  }});
}}
async function pickColor(inputId){{
  const msg=document.getElementById('mf_colors_msg');
  if(!window.EyeDropper){{
    if(msg)msg.textContent='Pincel nativo do seletor de cor (clique no quadrado colorido)';
    try{{document.getElementById(inputId).click()}}catch(e){{}}
    return;
  }}
  try{{
    const ed=new EyeDropper();
    const res=await ed.open();
    if(res&&res.sRGBHex){{
      document.getElementById(inputId).value=res.sRGBHex;
      if(msg)msg.textContent='Cor copiada: '+res.sRGBHex;
    }}
  }}catch(e){{
    if(msg)msg.textContent='Pincel cancelado';
  }}
}}
document.getElementById('mf_pick_acc').onclick=()=>pickColor('mf_acento');
document.getElementById('mf_pick_acc2').onclick=()=>pickColor('mf_acento_claro');

async function extractColors(opts){{
  opts=opts||{{}};
  const msg=document.getElementById('mf_colors_msg');
  if(msg)msg.textContent='Extraindo cores…';
  const body={{}};
  if(EDIT) body.slug=EDIT;
  // usa fila pendente + (servidor usa slug para as salvas)
  if(REFS_DATA.length) body.imagens=REFS_DATA.map(x=>x.dataurl).filter(Boolean);
  const nLocal=REFS_DATA.length+(REFS_SAVED||[]).length;
  if(!body.slug&&!nLocal){{
    if(msg)msg.textContent='Adicione referências primeiro';
    return null;
  }}
  // se tem salvas mas body.imagens vazio, slug basta; se tem ambos, backend prioriza imagens e
  // nós também pedimos merge: força slug sempre que houver salvas
  if(EDIT&&REFS_SAVED.length&&!body.imagens) body.slug=EDIT;
  if(EDIT&&REFS_SAVED.length&&body.imagens) body.também_slug=true; // dica
  const r=await api('/marca-extrair-cores', body);
  if(!r.ok){{
    if(msg)msg.textContent=(r.erro||'falhou')+(r.n_imgs!=null?(' · '+r.n_imgs+' img lida(s)'):'');
    return null;
  }}
  if(r.acento) document.getElementById('mf_acento').value=r.acento;
  if(r.acento_claro) document.getElementById('mf_acento_claro').value=r.acento_claro;
  showSwatches(r.cores||[]);
  if(msg)msg.textContent='Sugestão de '+(r.n_imgs||0)+' img(s) — clique num swatch pra aplicar';
  return r;
}}
document.getElementById('mf_extract_colors').onclick=()=>extractColors();

/** Upload imediato de refs (não espera Salvar marca). */
async function uploadRefFiles(fileList){{
  const files=[...fileList].slice(0,12);
  if(!files.length)return;
  if(!EDIT){{
    // marca nova: mantém na fila até criar; ao salvar envia junto
    for(const f of files){{
      if(f.size>12*1024*1024){{alert(f.name+' > 12 MB');continue}}
      const dataurl=await new Promise(res=>{{const rd=new FileReader();rd.onload=()=>res(rd.result);rd.onerror=()=>res(null);rd.readAsDataURL(f)}});
      if(!dataurl)continue;
      REFS_DATA.push({{nome:f.name.replace(/\\.[^.]+$/,''), dataurl}});
    }}
    renderRefGrid();
    if(REFS_DATA.length) extractColors();
    return;
  }}
  const msg=document.getElementById('mf_msg');
  let ok=0, err=0;
  for(const f of files){{
    if(f.size>12*1024*1024){{err++;continue}}
    const dataurl=await new Promise(res=>{{const rd=new FileReader();rd.onload=()=>res(rd.result);rd.onerror=()=>res(null);rd.readAsDataURL(f)}});
    if(!dataurl){{err++;continue}}
    // mostra pending
    REFS_DATA.push({{nome:f.name.replace(/\\.[^.]+$/,''), dataurl}});
    renderRefGrid();
    const r=await api('/marca-ref',{{slug:EDIT,nome:f.name.replace(/\\.[^.]+$/,''),dataurl}});
    REFS_DATA=REFS_DATA.filter(x=>x.dataurl!==dataurl);
    if(r.ok){{ok++}}else{{err++; console.warn(r.erro)}}
  }}
  await loadSavedRefs(EDIT);
  if(msg){{msg.className=err&&!ok?'err':'ok'; msg.textContent=ok?('✓ '+ok+' ref(s) salva(s)'+(err?(' · '+err+' falhou'):'')):(err?'Falha ao salvar refs':'')}}
  if(ok||REFS_SAVED.length) extractColors();
}}
// drop zone
(function(){{
  const drop=document.getElementById('mf_refdrop');
  const inp=document.getElementById('mf_refs');
  if(!drop||!inp)return;
  drop.onclick=()=>inp.click();
  drop.ondragover=e=>{{e.preventDefault();drop.classList.add('drag')}};
  drop.ondragleave=()=>drop.classList.remove('drag');
  drop.ondrop=e=>{{
    e.preventDefault(); drop.classList.remove('drag');
    if(e.dataTransfer&&e.dataTransfer.files) uploadRefFiles(e.dataTransfer.files);
  }};
  inp.onchange=e=>{{
    if(e.target.files&&e.target.files.length) uploadRefFiles(e.target.files);
    e.target.value='';
  }};
}})();

function showBbPreview(r){{
  const prev=document.getElementById('mf_bb_preview');
  const assets=document.getElementById('mf_bb_assets');
  const el=document.getElementById('mf_bb_status');
  if(el){{
    if(r&&r.existe) el.textContent='Book pronto ✓'+(r.assets_n?(' · '+r.assets_n+' anexo(s)'):'');
    else el.textContent='ainda sem book';
  }}
  if(prev){{
    if(r&&r.preview_md){{
      // tira frontmatter pra leitura
      let md=r.preview_md;
      if(md.startsWith('---')){{const p=md.split('---'); if(p.length>=3) md=p.slice(2).join('---').trim()}}
      prev.style.display='block';
      prev.textContent=md.slice(0,2500)+(md.length>2500?'\\n…':'');
    }}else{{prev.style.display='none';prev.textContent=''}}
  }}
  if(assets){{
    const list=(r&&r.assets)||[];
    assets.innerHTML=list.filter(a=>/\\.(png|jpe?g|webp)$/i.test(a.nome||'')).slice(0,12)
      .map(a=>`<img src="${{esc(a.url)}}?t=${{Date.now()}}" alt="${{esc(a.nome)}}" title="${{esc(a.nome)}}">`).join('');
  }}
}}
async function refreshBbStatus(slug){{
  if(!slug){{showBbPreview(null);return}}
  try{{
    const r=await(await fetch('/marca-branding-book?slug='+encodeURIComponent(slug))).json();
    if(!r.ok){{showBbPreview(null);return}}
    showBbPreview(r);
  }}catch(e){{showBbPreview(null)}}
}}
document.getElementById('mf_bb_gen').onclick=async()=>{{
  const msg=document.getElementById('mf_msg');
  if(!EDIT){{msg.className='err';msg.textContent='Salve a marca (passo final) antes de gerar o book — ou salve agora e volte.';return}}
  msg.className='';msg.textContent='Gerando branding book…';
  const r=await api('/marca-branding-book',{{slug:EDIT,forcar:true}});
  if(!r.ok){{msg.className='err';msg.textContent=r.erro||'falhou';return}}
  msg.className='ok';msg.textContent='Book gerado — veja o preview abaixo';
  showBbPreview(r);
}};
document.getElementById('mf_bb_files').onchange=async e=>{{
  const msg=document.getElementById('mf_msg');
  if(!EDIT){{msg.className='err';msg.textContent='Salve a marca antes de anexar páginas';e.target.value='';return}}
  const files=[...(e.target.files||[])].slice(0,12);
  if(!files.length)return;
  msg.className='';msg.textContent='Enviando '+files.length+' arquivo(s)…';
  for(const f of files){{
    const dataurl=await new Promise(res=>{{const rd=new FileReader();rd.onload=()=>res(rd.result);rd.readAsDataURL(f)}});
    const r=await api('/marca-branding-book-asset',{{slug:EDIT,dataurl,nome:f.name.replace(/\\.[^.]+$/,'')}});
    if(!r.ok){{msg.className='err';msg.textContent=r.erro||'falhou no anexo';return}}
  }}
  msg.className='ok';msg.textContent='Anexos do book salvos';
  e.target.value='';
  refreshBbStatus(EDIT);
}};

async function refreshLogoVars(){{
  const mono=document.getElementById('lv_mono');
  const col=document.getElementById('lv_color');
  const gly=document.getElementById('lv_glyph');
  const msg=document.getElementById('mf_logo_msg');
  const acc=document.getElementById('mf_acento').value||'#FFFFFF';
  const letter=(document.getElementById('mf_nome').value||'M').trim().charAt(0).toUpperCase()||'M';
  if(gly){{gly.textContent=letter;gly.style.background=acc}}
  // se tem dataurl local
  if(LOGO_DATA){{
    if(msg)msg.textContent='Prévia local — ao salvar, as 3 aplicações ficam disponíveis na arte.';
    if(mono)mono.innerHTML=`<img src="${{LOGO_DATA}}" style="filter:grayscale(1) brightness(10);mix-blend-mode:screen;padding:8px;box-sizing:border-box;width:100%;height:100%;object-fit:contain">`;
    if(col)col.innerHTML=`<img src="${{LOGO_DATA}}">`;
    return;
  }}
  if(!EDIT){{
    if(msg)msg.textContent='Envie a logo ou salve a marca para gerar prévias nítidas.';
    if(mono)mono.textContent=letter;
    if(col)col.textContent=letter;
    return;
  }}
  if(msg)msg.textContent='Gerando variações…';
  const r=await api('/marca-logo-icones',{{slug:EDIT,acento:acc}});
  if(!r.ok){{if(msg)msg.textContent=r.erro||'sem logo';return}}
  if(mono){{
    if(r.mono) mono.innerHTML=`<img src="data:image/png;base64,${{r.mono}}">`;
    else mono.textContent=letter;
  }}
  if(col){{
    if(r.color) col.innerHTML=`<img src="data:image/png;base64,${{r.color}}">`;
    else col.textContent=letter;
  }}
  if(gly){{gly.textContent=r.glyph||letter;gly.style.background=acc}}
  if(msg)msg.textContent='Escolha um estilo — mono costuma funcionar melhor na tab.';
  // marca estilo atual
  const cur=r.estilo||document.getElementById('mf_logo_estilo').value||'mono';
  document.getElementById('mf_logo_estilo').value=cur;
  document.querySelectorAll('.logo-var').forEach(v=>v.classList.toggle('on',v.dataset.estilo===cur));
}}
document.querySelectorAll('.logo-var').forEach(v=>v.onclick=async()=>{{
  const est=v.dataset.estilo;
  document.getElementById('mf_logo_estilo').value=est;
  document.querySelectorAll('.logo-var').forEach(x=>x.classList.toggle('on',x===v));
  LOGO_ESTILO=est;
  if(EDIT){{
    const r=await api('/marca-logo-estilo',{{slug:EDIT,estilo:est}});
    if(!r.ok) document.getElementById('mf_logo_msg').textContent=r.erro||'';
    else document.getElementById('mf_logo_msg').textContent='Estilo “'+est+'” salvo para a arte.';
  }}
}});

function openNew(){{
  EDIT=null; LOGO_DATA=null; LOGO_RM=false; LOGO_ESTILO='mono'; clearRefsPrev();
  document.getElementById('mtitle').textContent='Nova marca';
  document.getElementById('msub').textContent='Assistente em 4 passos — site e fotos primeiro.';
  document.getElementById('fld_slug').style.display='none';
  document.getElementById('mf_slug').value='';
  document.getElementById('mf_nome').value='';
  document.getElementById('mf_acento').value='#1CA5B2';
  document.getElementById('mf_acento_claro').value='#3DC4D0';
  document.getElementById('mf_handle').value='';
  document.getElementById('mf_glyph_mode').value='auto';
  syncGlyphMode();
  document.getElementById('mf_wordmark').value='';
  document.getElementById('mf_mood').value='';
  document.getElementById('mf_segmento').value='';
  document.getElementById('mf_site').value='';
  document.getElementById('mf_logoprev').innerHTML='sem logo';
  document.getElementById('mf_logo').value='';
  document.getElementById('mf_logo_estilo').value='mono';
  document.getElementById('mf_msg').textContent='';
  document.getElementById('mf_ia_dica').textContent='';
  document.getElementById('mf_bb_status').textContent='';
  document.getElementById('mf_dna_msg').textContent='';
  document.getElementById('mf_dna_box').style.display='none';
  showBbPreview(null);
  document.getElementById('mf_del').style.display='none';
  setMolduraUI({{chip:true,tab:true,logo:true,footer:true,page:true,grade:true}});
  renderRefGrid();
  goWiz(1);
  document.getElementById('mmodal').classList.add('on');
  setTimeout(()=>document.getElementById('mf_site').focus(),80);
}}
function openEdit(slug){{
  const m=MARCAS.find(x=>x.slug===slug); if(!m)return;
  EDIT=slug; LOGO_DATA=null; LOGO_RM=false; clearRefsPrev();
  document.getElementById('mtitle').textContent='Editar · '+m.nome;
  document.getElementById('msub').textContent='Mesmo assistente — altere o que precisar e salve no passo 4.';
  document.getElementById('fld_slug').style.display='none';
  document.getElementById('mf_slug').value=m.slug;
  document.getElementById('mf_nome').value=m.nome||'';
  document.getElementById('mf_acento').value=m.acento||'#8B3CF7';
  document.getElementById('mf_acento_claro').value=m.acento_claro||m.acento||'#A472FF';
  document.getElementById('mf_handle').value=m.handle||'';
  const g=m.glyph;
  if(g===''||g===null) setGlyphUI('');
  else setGlyphUI(g||'');
  document.getElementById('mf_wordmark').value=m.wordmark||'';
  document.getElementById('mf_mood').value=m.mood||'';
  document.getElementById('mf_segmento').value=m.segmento||'';
  document.getElementById('mf_site').value=m.site||'';
  document.getElementById('mf_logoprev').innerHTML=m.logo_url?`<img src="${{esc(m.logo_url)}}?t=${{Date.now()}}">`:'sem logo';
  document.getElementById('mf_logo').value='';
  document.getElementById('mf_logo_estilo').value=(m.logo_estilo||'mono');
  LOGO_ESTILO=m.logo_estilo||'mono';
  document.getElementById('mf_msg').textContent='';
  document.getElementById('mf_ia_dica').textContent='';
  setMolduraUI(m.moldura||{{}});
  const del=document.getElementById('mf_del');
  if(m.canonica){{del.style.display='none'}}
  else{{del.style.display='inline-flex';del.onclick=()=>excluirMarca(slug)}}
  goWiz(1);
  document.getElementById('mmodal').classList.add('on');
  loadSavedRefs(slug);
  refreshBbStatus(slug);
}}
async function loadSavedRefs(slug){{
  if(!slug){{REFS_SAVED=[];renderRefGrid();return}}
  const rc=document.getElementById('mf_refcount');
  if(rc)rc.textContent='Carregando refs…';
  try{{
    const r=await(await fetch('/marca-refs?slug='+encodeURIComponent(slug))).json();
    if(!r.ok){{REFS_SAVED=[];renderRefGrid();return}}
    REFS_SAVED=r.refs||[];
    renderRefGrid();
  }}catch(e){{REFS_SAVED=[];renderRefGrid()}}
}}
document.getElementById('bm_new').onclick=openNew;
document.getElementById('mf_cancel').onclick=()=>document.getElementById('mmodal').classList.remove('on');
document.getElementById('mmodal').onclick=e=>{{if(e.target.id==='mmodal')e.currentTarget.classList.remove('on')}};
let LOGO_RM=false;
document.getElementById('mf_logo').onchange=e=>{{
  const f=e.target.files&&e.target.files[0]; if(!f)return;
  if(f.size>8*1024*1024){{alert('Logo maior que 8 MB');e.target.value='';return}}
  LOGO_RM=false;
  const rd=new FileReader();
  rd.onload=async()=>{{
    LOGO_DATA=rd.result;
    document.getElementById('mf_logoprev').innerHTML=`<img src="${{rd.result}}">`;
    // se marca já existe, grava logo na hora e gera ícones
    if(EDIT){{
      const r=await api('/marca-logo',{{slug:EDIT,logo_dataurl:LOGO_DATA}});
      if(r.ok){{LOGO_DATA=null; refreshLogoVars(); document.getElementById('mf_logo_msg').textContent='Logo salva — escolha o estilo abaixo';}}
      else document.getElementById('mf_logo_msg').textContent=r.erro||'falha ao salvar logo';
    }}else refreshLogoVars();
  }};
  rd.onerror=()=>{{alert('Não consegui ler o arquivo');LOGO_DATA=null}};
  rd.readAsDataURL(f);
}};
document.getElementById('mf_logo_rm').onclick=async()=>{{
  if(EDIT){{
    if(!confirm('Remover o logo desta marca?'))return;
    const r=await api('/marca-logo-del',{{slug:EDIT}});
    if(!r.ok){{alert(r.erro||'falhou');return}}
  }}
  LOGO_DATA=null; LOGO_RM=true;
  document.getElementById('mf_logoprev').innerHTML='sem logo';
  document.getElementById('mf_logo').value='';
}};
async function runIaMarca(mode){{
  const msg=document.getElementById('mf_msg');
  msg.className=''; msg.textContent='Gerando sugestões…';
  const body={{
    nome:document.getElementById('mf_nome').value.trim(),
    slug:EDIT||document.getElementById('mf_slug').value.trim(),
    segmento:document.getElementById('mf_segmento').value,
    acento:document.getElementById('mf_acento').value,
    site:document.getElementById('mf_site').value.trim(),
    mode:mode||'all',
  }};
  const r=await api('/marca-ia', body);
  if(!r.ok){{msg.className='err';msg.textContent=r.erro||'falhou';return}}
  if(r.mood) document.getElementById('mf_mood').value=r.mood;
  if(mode==='all'){{
    if(r.handle) document.getElementById('mf_handle').value=r.handle;
    if(r.glyph) setGlyphUI(r.glyph);
    if(r.wordmark) document.getElementById('mf_wordmark').value=r.wordmark;
    if(r.segmento) document.getElementById('mf_segmento').value=r.segmento;
  }}
  document.getElementById('mf_ia_dica').textContent=r.dica||'';
  msg.className='ok'; msg.textContent='Sugestões aplicadas — revise e salve';
}}
document.getElementById('mf_ia_mood').onclick=()=>runIaMarca('mood');
document.getElementById('mf_ia_all').onclick=()=>runIaMarca('all');
// DNA do site — opcional, preenche o form; não salva sozinho
document.getElementById('mf_ler_site').onclick=async()=>{{
  const site=(document.getElementById('mf_site').value||'').trim();
  const dmsg=document.getElementById('mf_dna_msg');
  const msg=document.getElementById('mf_msg');
  const box=document.getElementById('mf_dna_box');
  const btn=document.getElementById('mf_ler_site');
  if(!site){{
    if(dmsg)dmsg.textContent='Cole a URL do site do cliente primeiro.';
    return;
  }}
  if(btn){{btn.disabled=true;btn.textContent='Lendo…'}}
  if(dmsg)dmsg.textContent='Lendo o site (home + uma página)…';
  if(msg){{msg.className='';msg.textContent=''}}
  if(box)box.style.display='none';
  let r;
  try{{
    r=await api('/marca-ler-site',{{url:site}});
  }}catch(e){{
    r={{ok:false,erro:'falha de rede'}};
  }}
  if(btn){{btn.disabled=false;btn.textContent='Ler site'}}
  if(!r||!r.ok){{
    if(dmsg)dmsg.textContent=r&&r.erro?r.erro:'Não consegui ler o site';
    if(msg){{msg.className='err';msg.textContent=r&&r.erro?r.erro:'falhou'}}
    return;
  }}
  const f=r.formulario||{{}};
  const fill=(id,val,force)=>{{
    if(!val)return;
    const el=document.getElementById(id); if(!el)return;
    if(force||!el.value.trim()) el.value=val;
  }};
  const temDados=!!(
    document.getElementById('mf_nome').value.trim()||
    document.getElementById('mf_mood').value.trim()
  );
  let ok=true;
  if(temDados){{
    ok=confirm('Já há dados no formulário. Aplicar as sugestões do site?');
  }}
  if(!ok){{
    // mesmo cancelando o fill, mostra o resumo para o usuário ler
    if(dmsg)dmsg.textContent='Sugestões não aplicadas — veja o resumo abaixo.';
  }}else{{
    fill('mf_nome', f.nome, true);
    fill('mf_handle', f.handle, !document.getElementById('mf_handle').value.trim());
    fill('mf_wordmark', f.wordmark, !document.getElementById('mf_wordmark').value.trim());
    fill('mf_mood', f.mood, true);
    fill('mf_site', f.site||site, true);
    if(f.segmento) document.getElementById('mf_segmento').value=f.segmento;
    if(f.acento&&/^#[0-9A-Fa-f]{{6}}$/.test(f.acento)){{
      document.getElementById('mf_acento').value=f.acento;
    }}
    if(document.getElementById('mf_glyph_mode').value==='auto') syncGlyphMode();
    if(dmsg)dmsg.textContent='Campos preenchidos. Abra o resumo, revise e salve.';
    if(msg){{msg.className='ok';msg.textContent='Site lido — revise e salve'}}
  }}
  // resumo em sanfona
  const resumoEl=document.getElementById('mf_dna_resumo');
  const metaEl=document.getElementById('mf_dna_meta');
  if(box&&resumoEl&&metaEl){{
    resumoEl.textContent=r.resumo||r.proposta||'Sem resumo textual.';
    const lines=[];
    if(r.score!=null) lines.push('Confiança geral: ~'+r.score+'%');
    if(r.proposta) lines.push('Proposta: '+r.proposta);
    if(r.publico) lines.push('Público: '+r.publico);
    if(r.tom) lines.push('Tom: '+r.tom);
    if(r.restricoes&&r.restricoes.length) lines.push('Evitar: '+r.restricoes.slice(0,4).join(' · '));
    if(r.paginas_lidas&&r.paginas_lidas.length) lines.push('Páginas lidas: '+r.paginas_lidas.length);
    metaEl.innerHTML=lines.map(l=>'<div style="margin:3px 0">'+esc(l)+'</div>').join('');
    box.style.display='block';
    box.open=true;
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
    glyph:glyphFromForm(),
    glyph_explicit:true,
    wordmark:document.getElementById('mf_wordmark').value.trim(),
    mood:document.getElementById('mf_mood').value.trim(),
    site:document.getElementById('mf_site').value.trim(),
    segmento:document.getElementById('mf_segmento').value,
    moldura:molduraFromForm(),
    logo_estilo:document.getElementById('mf_logo_estilo').value||'mono',
  }};
  if(LOGO_DATA) body.logo_dataurl=LOGO_DATA;
  // refs pendentes (só marca nova — em edição o upload já é imediato)
  if(REFS_DATA.length) body.referencias=REFS_DATA;
  let r;
  if(EDIT){{
    body.slug=EDIT;
    r=await api('/editar-marca', body);
  }}else{{
    if(!body.nome){{msg.className='err';msg.textContent='Informe o nome da empresa';return}}
    // slug automático a partir do nome
    body.slug=slugifyNome(body.nome);
    if(!body.segmento) body.segmento='outro';
    // handle auto se vazio
    if(!body.handle) body.handle='@'+body.slug.replace(/-/g,'');
    if(!body.wordmark) body.wordmark=body.nome;
    r=await api('/nova-marca', body);
  }}
  if(!r.ok){{msg.className='err';msg.textContent=r.erro||'erro';return}}
  const nref=(r.referencias||[]).filter(x=>x&&x.feed).length;
  const nerr=(r.referencias||[]).filter(x=>x&&x.erro).length;
  msg.className='ok';
  msg.textContent='Salvo ✓'+(nref?(' · '+nref+' ref(s)'):'')+(nerr?(' · '+nerr+' com erro'):'')+(r.aviso_logo?(' · logo: '+r.aviso_logo):'');
  if(!EDIT&&r.slug){{
    EDIT=r.slug;
    document.getElementById('fld_slug').style.display='';
    document.getElementById('mf_slug').value=r.slug;
    document.getElementById('mf_slug').disabled=true;
  }}
  await loadMarcas();
  REFS_DATA=[];
  if(EDIT){{await loadSavedRefs(EDIT);refreshBbStatus(EDIT)}}
  LOGO_DATA=null;
}};
loadMarcas();
// deep-link /config?editar=slug  + retorno OAuth canais=ok
(function(){{
  try{{
    const sp=new URLSearchParams(location.search);
    const q=sp.get('editar')||sp.get('marca');
    if(q) setTimeout(()=>openEdit(q),400);
    if(sp.get('canais')==='ok'){{
      const m=sp.get('marca')||'';
      setTimeout(()=>{{
        const el=document.createElement('div');
        el.style.cssText='position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a3;color:#fff;padding:12px 18px;border-radius:12px;font:600 13px system-ui;z-index:999;box-shadow:0 8px 30px rgba(0,0,0,.3)';
        el.textContent='✓ Instagram conectado'+(m?(' · '+m):'');
        document.body.appendChild(el);
        setTimeout(()=>el.remove(),4200);
        loadMarcas();
      }},500);
    }}
  }}catch(e){{}}
}})();


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
window._PLOG_PAGE=0;
window._PLOG_PER=10;
function renderPostLog(){{
  const list=document.getElementById('plog_list');
  const pager=document.getElementById('plog_pager');
  if(!list)return;
  const marca=document.getElementById('plog_marca').value;
  const q=(document.getElementById('plog_q').value||'').toLowerCase();
  let rows=window._PLOG||[];
  if(marca)rows=rows.filter(p=>p.marca===marca);
  if(q)rows=rows.filter(p=>((p.titulo||'')+' '+(p.slug||'')).toLowerCase().includes(q));
  document.getElementById('plog_count').textContent='('+rows.length+')';
  const per=window._PLOG_PER||10;
  const pages=Math.max(1, Math.ceil(rows.length/per));
  if(window._PLOG_PAGE>=pages) window._PLOG_PAGE=pages-1;
  if(window._PLOG_PAGE<0) window._PLOG_PAGE=0;
  const start=window._PLOG_PAGE*per;
  const slice=rows.slice(start, start+per);
  if(!rows.length){{
    list.innerHTML='<div style="color:var(--muted);font-size:13px;padding:12px 4px">Nenhum post neste filtro.</div>';
    if(pager)pager.style.display='none';
    return;
  }}
  list.innerHTML='<table class=plog-table><thead><tr>'
    +'<th>Título</th><th>Marca</th><th>Tempo</th><th>Custo</th><th>Quando</th><th></th>'
    +'</tr></thead><tbody>'
    +slice.map(p=>{{
      const custo=p.total_brl!=null?('R$ '+Number(p.total_brl).toFixed(2)):(p.total_usd!=null?('US$ '+Number(p.total_usd).toFixed(3)):'—');
      const tempo=fmtMin(p.total_minutes);
      return '<tr>'
        +'<td class=t title="'+esc(p.titulo)+'">'+esc(p.titulo||p.slug||'—')+'</td>'
        +'<td><span class=pill>'+esc(p.marca||'—')+'</span></td>'
        +'<td style="white-space:nowrap;color:var(--muted)">'+tempo+'</td>'
        +'<td style="white-space:nowrap;color:var(--muted)">'+custo+'</td>'
        +'<td style="white-space:nowrap;color:var(--muted)">'+relTime(p.updated_at||p.created_at)+'</td>'
        +'<td><a class="sk-btn sk-btn--secondary sk-btn--sm" href="/editor?post='+p.idx+'">Abrir</a></td>'
        +'</tr>';
    }}).join('')
    +'</tbody></table>';
  if(pager){{
    pager.style.display=rows.length>per?'flex':'none';
    document.getElementById('plog_pginfo').textContent=
      'Página '+(window._PLOG_PAGE+1)+' de '+pages+' · '+rows.length+' post(s) · '+per+' por página';
    document.getElementById('plog_prev').disabled=window._PLOG_PAGE<=0;
    document.getElementById('plog_next').disabled=window._PLOG_PAGE>=pages-1;
  }}
}}
document.getElementById('plog_marca').onchange=()=>{{window._PLOG_PAGE=0;renderPostLog()}};
document.getElementById('plog_q').oninput=()=>{{clearTimeout(window._plogT);window._plogT=setTimeout(()=>{{window._PLOG_PAGE=0;renderPostLog()}},180)}};
document.getElementById('plog_prev').onclick=()=>{{window._PLOG_PAGE--;renderPostLog()}};
document.getElementById('plog_next').onclick=()=>{{window._PLOG_PAGE++;renderPostLog()}};
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
<link rel="stylesheet" href="/design-system/dist/smark-ds.css">
__HEAD_THEME__<style>
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
    +'<div class="sk-empty-title">'+((nActiveFilters()||Q)?'Nada com esse filtro':'Nenhuma publicação ainda')+'</div>'
    +'<div class="sk-empty-text">'+((nActiveFilters()||Q)?'Ajuste ou limpe os filtros.':'Crie a primeira no editor.')+'</div>'
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
</script></body></html>""").replace("__TOPBAR__", topbar("painel")).replace("__LOGOSTORE__", smark_logo(34, suffix="STORE")).replace("__HEAD_THEME__", HEAD_THEME)


def vitrine_html():
    """Vitrine — feed Instagram, mosaico 3 colunas, ordenação e filtro de marca."""
    return ("""<!doctype html><html lang=pt-BR data-theme="escuro"><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Vitrine · smark</title>
<link rel="stylesheet" href="/design-system/dist/smark-ds.css">
__HEAD_THEME__<style>
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
</script></body></html>""").replace("__TOPBAR__", topbar("vitrine")).replace("__HEAD_THEME__", HEAD_THEME)


# Segurança (CSRF / DNS rebinding): o servidor é local, mas tem rotas que gastam
# dinheiro (regerar-fundo→OpenAI) e escrevem em disco. Um site malicioso aberto no
# navegador poderia dar POST em localhost. Defesa: Host + Origin + token de sessão.
# Token persiste em arquivo local para não quebrar abas abertas após restart.
_TOKEN_FILE = os.path.join(VAULT, ".editor-token")


def _load_or_make_token():
    try:
        if os.path.isfile(_TOKEN_FILE):
            t = open(_TOKEN_FILE, encoding="utf-8").read().strip()
            if re.fullmatch(r"[a-f0-9]{32}", t or ""):
                return t
    except OSError:
        pass
    t = secrets.token_hex(16)
    try:
        open(_TOKEN_FILE, "w", encoding="utf-8").write(t)
    except OSError:
        pass
    return t


ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"[::1]:{PORT}"}
TOKEN = _load_or_make_token()
DATA = os.path.join(VAULT, "editor.json")
UI = os.path.join(HERE, "_editor2.html")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".svg": "image/svg+xml", ".css": "text/css",
        ".js": "application/javascript", ".html": "text/html; charset=utf-8"}

# Ícone IA canônico (igual botão Estúdio na tela principal do Super Editor)
ICON_IA = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" '
           'style="margin-right:5px;vertical-align:-2px;flex:0 0 auto" aria-hidden="true">'
           '<path d="M12 2l1.7 5.5L19 9l-5.3 1.5L12 16l-1.7-5.5L5 9l5.3-1.5z"/>'
           '<path d="M18.5 13l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9z"/></svg>')
ICON_IA_SM = ICON_IA.replace('width="15"', 'width="13"').replace('height="15"', 'height="13"')


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


def _erro_cli_limpo(stderr, stdout="", max_len=220):
    """Extrai a última linha legível de ERRO/AVISO do CLI (sem stack/ruído)."""
    blob = (stderr or "") + "\n" + (stdout or "")
    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
    # prioriza linhas de erro humanas
    for ln in reversed(lines):
        low = ln.lower()
        if any(k in low for k in ("erro", "error", "fail", "gate", "timeout", "quota",
                                   "rate", "billing", "credit", "denied", "invalid")):
            # corta lixo unicode/ANSI
            clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", ln)
            clean = re.sub(r"\s+", " ", clean).strip()
            if len(clean) >= 8:
                return clean[:max_len]
    if lines:
        clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", lines[-1])
        clean = re.sub(r"\s+", " ", clean).strip()
        return (clean or "geração falhou")[:max_len]
    return "geração falhou (sem detalhe do provedor)"


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
            gate_fail = (r.returncode == 3 or "GATE_FALHOU" in (r.stdout or "")
                         or bool(meta.get("gate_falhou")))
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
                        if gate_fail:
                            f["bg_gate_falhou"] = True
                            f["bg_publicavel"] = False
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
            # exit 3 = gate de texto; arquivo MANTIDO como rascunho
            if gate_fail:
                job["gate_falhou"] = True
                job["publicavel"] = False
            JOBS[job_id] = job
        else:
            JOBS[job_id] = {
                "status": "erro",
                "erro": _erro_cli_limpo(r.stderr, r.stdout),
            }


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

    # moldura: herda defaults da marca se o frame não define a chave
    md = _marcas.moldura_defaults(marca)
    def _on(key, default=True):
        if key in fr:
            return bool(fr.get(key))
        return bool(md.get(key, default))

    k = dict(marca=marca, headline=hl(fr.get("headline", "")), sub=hl(fr.get("sub", "")),
             cta=fr.get("cta", ""), page=fr.get("page", ""), no_chip=not _on("chip", True),
             no_tab=not _on("tab", True),
             no_logo=not _on("logo", True),
             no_footer=not _on("footer", True),
             no_page=not _on("page", True) or not fr.get("page"),
             tema=fr.get("tema", "escuro"), size=size, hsize=int(fr.get("hsize", 0) or 0),
             accent=fr.get("accent") or acc, bright=fr.get("bright") or acc2,
             square=fr.get("square") or grad,
             no_grade=not _on("grade", True),
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
    if not raw or len(raw) < 32:
        raise ValueError("logo vazio ou inválido")
    # valida que é imagem real (evita gravar lixo/base64 quebrado)
    if ext != ".svg":
        try:
            from PIL import Image
            import io
            im = Image.open(io.BytesIO(raw))
            im.verify()
            im = Image.open(io.BytesIO(raw))  # reabre após verify
            if min(im.size) < 16:
                raise ValueError("logo muito pequeno")
        except Exception as e:
            raise ValueError(f"arquivo de logo não é imagem válida: {e}") from e
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
            if not raw or len(raw) < 32:
                raise ValueError("referência vazia")
            try:
                from PIL import Image
                import io
                Image.open(io.BytesIO(raw)).verify()
            except Exception as ve:
                raise ValueError(f"não é imagem válida: {ve}") from ve
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
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in ("application/x-www-form-urlencoded", "multipart/form-data"):
            # OAuth fake e forms HTML
            if ctype == "application/x-www-form-urlencoded":
                q = urllib.parse.parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
                return {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in q.items()}
            return {"_raw": raw}
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            # tenta form como fallback
            q = urllib.parse.parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
            if q:
                return {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in q.items()}
            raise

    def _host_ok(self):
        host = (self.headers.get("Host") or "").strip().lower()
        if host in ALLOWED_HOSTS:
            return True
        # aceita host sem porta explícita se for loopback
        bare = host.split(":")[0].strip("[]")
        return bare in ("127.0.0.1", "localhost", "::1")

    def _origin_ok(self):
        """Origin ausente = same-origin clássico; se presente, tem que ser loopback."""
        origin = (self.headers.get("Origin") or "").strip()
        if not origin or origin == "null":
            # null/ausente: ainda confere Referer se houver
            ref = (self.headers.get("Referer") or "").strip()
            if not ref:
                return True
            try:
                netloc = urllib.parse.urlparse(ref).netloc.lower()
            except Exception:
                return False
            bare = netloc.split(":")[0].strip("[]")
            return bare in ("127.0.0.1", "localhost", "::1") or netloc in ALLOWED_HOSTS
        try:
            netloc = urllib.parse.urlparse(origin).netloc.lower()
        except Exception:
            return False
        if netloc in ALLOWED_HOSTS:
            return True
        bare = netloc.split(":")[0].strip("[]")
        return bare in ("127.0.0.1", "localhost", "::1")

    def _oauth_path(self, path=None):
        """Callbacks OAuth (Meta redirect / form fake) não carregam X-Editor-Token."""
        p = path or urllib.parse.urlparse(self.path).path
        return p.startswith("/oauth/")

    def _post_allowed(self):
        """POST muda estado / gasta dinheiro → exige Host + Origin próprios + token."""
        if not self._host_ok():
            return False
        path = urllib.parse.urlparse(self.path).path
        if self._oauth_path(path):
            # redirect do Instagram / form fake — Origin pode ser null; Host já checado
            return True
        if not self._origin_ok():
            return False
        tok = self.headers.get("X-Editor-Token") or self.headers.get("x-editor-token") or ""
        return tok == TOKEN

    def _post_block_reason(self):
        """Detalhe do bloqueio (só p/ debug na UI — sem vazar o token)."""
        reasons = []
        if not self._host_ok():
            reasons.append(f"host={self.headers.get('Host')!r}")
        if not self._origin_ok():
            reasons.append(f"origin={self.headers.get('Origin')!r}")
        tok = self.headers.get("X-Editor-Token") or ""
        if tok != TOKEN:
            reasons.append("token" if tok else "token-ausente")
        return " · ".join(reasons) or "desconhecido"

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
                marcas = _marcas.listar_detalhes()
                for m in marcas:
                    try:
                        m["canais"] = _canais.status_marca(m["slug"]).get("canais") or {}
                    except Exception:
                        m["canais"] = {}
                return self._send(200, {
                    "ok": True,
                    "marcas": marcas,
                    "canais_modo": _canais.modo_instagram(),
                })
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
        if path == "/canais":
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                slug = (qs.get("marca") or qs.get("slug") or [""])[0].strip().lower()
                if slug:
                    slug = _marcas.require(slug)
                    return self._send(200, {"ok": True, **_canais.status_marca(slug)})
                slugs = _marcas.list_slugs()
                return self._send(200, {
                    "ok": True,
                    "modo_app": _canais.modo_instagram(),
                    "marcas": _canais.status_todas(slugs),
                })
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
        # ── OAuth Instagram (fake + real callback) ──────────────────────────
        if path == "/oauth/instagram/fake":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            state = (qs.get("state") or [""])[0]
            # lê pending só pra mostrar a marca (não consome)
            pending = {}
            try:
                pth = os.path.join(VAULT, ".secrets", "oauth_pending", f"{state}.json")
                if os.path.isfile(pth):
                    pending = json.load(open(pth, encoding="utf-8"))
            except Exception:
                pending = {}
            html = _canais.html_fake_login(state, marca=pending.get("marca") or "")
            return self._send(200, html, MIME[".html"])
        if path == "/oauth/instagram/callback":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if qs.get("error"):
                html = _canais.html_oauth_done(
                    False, erro=urllib.parse.unquote((qs.get("error_description") or ["negado"])[0]))
                return self._send(200, html, MIME[".html"])
            code = (qs.get("code") or [""])[0]
            state = (qs.get("state") or [""])[0]
            try:
                r = _canais.trocar_code_real(code, state)
            except Exception as e:
                r = {"ok": False, "erro": str(e)}
            if r.get("ok"):
                html = _canais.html_oauth_done(
                    True, marca=r.get("marca", ""), username=r.get("username", ""),
                    return_to=r.get("return_to") or "/config")
            else:
                html = _canais.html_oauth_done(False, erro=r.get("erro") or "falha OAuth")
            return self._send(200, html, MIME[".html"])
        if path == "/marca-refs":
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                slug = (qs.get("slug") or [""])[0].strip().lower()
                return self._send(200, {"ok": True, "slug": slug, "refs": _marcas.listar_refs(slug)})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})
        if path == "/marca-branding-book":
            try:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                slug = (qs.get("slug") or [""])[0].strip().lower()
                st = _marcas.branding_book_status(slug)
                return self._send(200, {"ok": True, **st})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
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
            why = self._post_block_reason()
            return self._send(403, {
                "ok": False,
                "erro": f"bloqueado ({why}) — recarregue a página (F5) e tente de novo",
                "reload": True,
            })
        try:
            req = self._body()
        except Exception as e:
            return self._send(400, {"ok": False, "erro": f"body inválido: {e}"})

        # OAuth fake: form HTML → grava vínculo e redireciona
        if path == "/oauth/instagram/fake":
            try:
                r = _canais.conectar_fake(
                    req.get("state") or "",
                    req.get("username") or "",
                    req.get("nome") or "",
                )
            except Exception as e:
                r = {"ok": False, "erro": str(e)}
            if r.get("ok"):
                html = _canais.html_oauth_done(
                    True, marca=r.get("marca", ""), username=r.get("username", ""),
                    return_to=r.get("return_to") or "/config")
            else:
                # reexibe formulário se o state ainda vale; senão página de erro
                if r.get("keep_state") or "informe o @" in (r.get("erro") or ""):
                    pending = {}
                    st = req.get("state") or ""
                    try:
                        pth = os.path.join(VAULT, ".secrets", "oauth_pending", f"{st}.json")
                        if os.path.isfile(pth):
                            pending = json.load(open(pth, encoding="utf-8"))
                    except Exception:
                        pass
                    html = _canais.html_fake_login(
                        st, marca=pending.get("marca") or "", erro=r.get("erro") or "falhou")
                else:
                    html = _canais.html_oauth_done(False, erro=r.get("erro") or "falhou")
            return self._send(200, html, MIME[".html"])

        if path == "/canais/conectar":
            try:
                marca = _marcas.require(req.get("marca") or req.get("slug") or "")
                canal = (req.get("canal") or "instagram").lower()
                return_to = req.get("return_to") or f"/config?editar={marca}"
                r = _canais.iniciar_oauth(marca, canal, return_to=return_to)
                code = 200 if r.get("ok") else 400
                return self._send(code, r)
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/canais/desconectar":
            try:
                marca = _marcas.require(req.get("marca") or req.get("slug") or "")
                canal = (req.get("canal") or "instagram").lower()
                r = _canais.desconectar(marca, canal)
                return self._send(200 if r.get("ok") else 400, r)
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/canais/publicar":
            try:
                marca = _marcas.require(req.get("marca") or req.get("slug") or "")
                canal = (req.get("canal") or "instagram").lower()
                if canal != "instagram":
                    return self._send(400, {"ok": False, "erro": "só Instagram por enquanto"})
                r = _canais.publicar_instagram(
                    marca,
                    image_path=req.get("image_path") or req.get("path") or "",
                    image_url=req.get("image_url") or "",
                    caption=req.get("caption") or "",
                    dry_run=bool(req.get("dry_run")),
                )
                return self._send(200 if r.get("ok") else 400, r)
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

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
            fr = _marcas.frame_from_moldura(marca, tema=tema, headline="SEU TÍTULO|*AQUI.*")
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
                try:
                    pi = int(req.get("post", -1))
                    fi = int(req.get("frame", -1))
                except (TypeError, ValueError):
                    return self._send(400, {"ok": False,
                                            "erro": "post/frame inválidos — salve o post e tente de novo"})
                posts = d.get("posts") or []
                if not (0 <= pi < len(posts)):
                    return self._send(400, {
                        "ok": False,
                        "erro": (f"post #{pi} não existe no servidor (tem {len(posts)}). "
                                 "Salve o editor antes de gerar o fundo."),
                    })
                post = posts[pi]
                frames = post.get("frames") or []
                if not (0 <= fi < len(frames)):
                    return self._send(400, {
                        "ok": False,
                        "erro": (f"card #{fi + 1} não existe neste post "
                                 f"({len(frames)} card(s)). Salve e tente de novo."),
                    })
                fr = frames[fi]
                slug = safe_slug(post.get("slug", ""))
                if not slug:
                    return self._send(400, {"ok": False,
                                            "erro": "post sem slug — salve o post antes de gerar fundo"})
                try:
                    marca = require_marca(post.get("marca", "smark"))
                except ValueError as e:
                    return self._send(400, {"ok": False, "erro": str(e)})
                dd = os.path.join(VAULT, "marcas", marca, "publicacoes", "social", "instagram",
                                  "arte", slug, "_regen")
                os.makedirs(dd, exist_ok=True)
                out = os.path.join(dd, f"{fi+1:02d}-{secrets.token_hex(3)}.png")
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
                threading.Thread(target=_run_gen, args=(job_id, cmd, out, pi, fi),
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
                # glyph: key presente (mesmo "") = explícito; ausente = auto no criar
                _glyph = req["glyph"] if "glyph" in req else None
                if _glyph is not None:
                    _glyph = str(_glyph).strip()[:2]
                r = _marcas.criar(
                    slug, nome, acento,
                    acento_claro=str(req.get("acento_claro") or "") or None,
                    handle=str(req.get("handle") or "") or None,
                    glyph=_glyph,
                    wordmark=str(req.get("wordmark") or "") or None,
                    mood=str(req.get("mood") or ""),
                )
                # segmento / site / moldura pós-criação
                try:
                    campos_pos = {}
                    if req.get("segmento"):
                        campos_pos["segmento"] = str(req.get("segmento") or "") or None
                    if req.get("site"):
                        campos_pos["site"] = str(req.get("site") or "") or None
                    if isinstance(req.get("moldura"), dict):
                        campos_pos["moldura"] = req["moldura"]
                    if campos_pos:
                        _marcas.atualizar(r["slug"], **campos_pos)
                    if req.get("logo_estilo"):
                        try:
                            _marcas.set_logo_estilo(r["slug"], str(req["logo_estilo"]))
                        except Exception:
                            pass
                except Exception:
                    pass
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
                          "wordmark", "mood", "gradiente", "segmento", "site"):
                    if k not in req:
                        continue
                    # glyph pode ser "" (nenhum) — não tratar como ausente
                    if k == "glyph":
                        campos[k] = str(req[k] if req[k] is not None else "").strip()[:2]
                    elif req[k] is not None:
                        campos[k] = req[k]
                if isinstance(req.get("moldura"), dict):
                    campos["moldura"] = req["moldura"]
                if "endossa" in req:
                    campos["endossa"] = bool(req["endossa"])
                r = _marcas.atualizar(slug, **campos)
                if req.get("logo_estilo"):
                    try:
                        _marcas.set_logo_estilo(slug, str(req["logo_estilo"]))
                    except Exception:
                        pass
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

        if path == "/marca-logo-icones":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                meta = _marcas.get(slug)
                brasao = (meta or {}).get("brasao") or {}
                rel = brasao.get("principal") or (meta or {}).get("logo_file") or ""
                path = os.path.join(VAULT, rel) if rel and not os.path.isabs(rel) else rel
                acc = str(req.get("acento") or (meta or {}).get("acento") or "#FFFFFF")
                vars_ = compositor.logo_variantes(path if path and os.path.isfile(path) else "",
                                                  color=acc, px=64)
                glyph = (meta or {}).get("logo_glyph") or ((meta or {}).get("nome") or "M")[:1]
                return self._send(200, {
                    "ok": True,
                    "mono": vars_.get("mono"),
                    "color": vars_.get("color"),
                    "glyph": str(glyph)[:2].upper(),
                    "estilo": brasao.get("estilo") or "mono",
                })
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-logo-estilo":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                r = _marcas.set_logo_estilo(slug, str(req.get("estilo") or "mono"))
                return self._send(200, {"ok": True, **r})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/excluir-marca":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                apagar = bool(req.get("apagar_pasta", True))
                r = _marcas.excluir(slug, apagar_pasta=apagar)
                return self._send(200, {"ok": True, **r})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-ler-site":
            # DNA leve: crawl + LLM → sugere campos do form (não grava)
            try:
                url = str(req.get("url") or req.get("site") or "").strip()
                if not url:
                    return self._send(400, {"ok": False, "erro": "informe a URL do site"})
                dna = _dna_marca.extrair_de_url(url)
                form = _dna_marca.para_formulario(dna)
                return self._send(200, {
                    "ok": True,
                    "formulario": form,
                    "score": dna.get("score"),
                    "resumo": dna.get("resumo") or "",
                    "proposta": dna.get("proposta"),
                    "publico": dna.get("publico"),
                    "tom": dna.get("tom"),
                    "restricoes": dna.get("restricoes") or [],
                    "confianca": dna.get("confianca") or {},
                    "paginas_lidas": dna.get("paginas_lidas") or [],
                    "meta_llm": dna.get("meta_llm") or {},
                })
            except ValueError as e:
                return self._send(422, {"ok": False, "erro": str(e)})
            except RuntimeError as e:
                return self._send(503, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": f"falha na leitura: {e}"})

        if path == "/marca-ref":
            # upload imediato de uma referência (não espera salvar o form da marca)
            try:
                slug = str(req.get("slug", "")).strip().lower()
                if not slug:
                    return self._send(400, {"ok": False, "erro": "slug obrigatório"})
                du = req.get("dataurl") or req.get("data") or ""
                nome = str(req.get("nome") or "ref").strip()
                raw, ext = _decode_dataurl(du)
                if not raw or len(raw) < 32:
                    return self._send(400, {"ok": False, "erro": "imagem vazia ou inválida"})
                try:
                    from PIL import Image
                    import io
                    Image.open(io.BytesIO(raw)).verify()
                except Exception as ve:
                    return self._send(400, {"ok": False, "erro": f"não é imagem válida: {ve}"})
                out = _marcas.salvar_referencia_bytes(slug, raw, nome=nome, ext=ext)
                return self._send(200, {"ok": True, **out, "refs": _marcas.listar_refs(slug)})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-ref-del":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                nome = str(req.get("nome", "")).strip()
                removed = _marcas.remover_ref(slug, nome)
                return self._send(200, {"ok": True, "removed": removed, "refs": _marcas.listar_refs(slug)})
            except FileNotFoundError as e:
                return self._send(404, {"ok": False, "erro": str(e)})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-logo-del":
            try:
                slug = str(req.get("slug", "")).strip().lower()
                removed = _marcas.remover_logo(slug)
                return self._send(200, {"ok": True, "removed": removed})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-ia":
            try:
                sug = _marcas.gerar_texto_ia_marca(
                    slug=str(req.get("slug") or ""),
                    nome=str(req.get("nome") or ""),
                    segmento=str(req.get("segmento") or ""),
                    acento=str(req.get("acento") or ""),
                    site=str(req.get("site") or ""),
                )
                mode = str(req.get("mode") or "all")
                if mode == "mood":
                    return self._send(200, {"ok": True, "mood": sug["mood"], "dica": sug["dica"],
                                            "segmento": sug["segmento"]})
                return self._send(200, {"ok": True, **sug})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-extrair-cores":
            try:
                slug = str(req.get("slug") or "").strip().lower()
                imgs = req.get("imagens") or req.get("dataurls") or []
                blobs = []
                for it in (imgs or [])[:16]:
                    du = it.get("dataurl") if isinstance(it, dict) else it
                    if not du:
                        continue
                    try:
                        raw, _ext = _decode_dataurl(du)
                        if raw and len(raw) >= 32:
                            blobs.append(raw)
                    except Exception:
                        continue
                # também puxa refs salvas no disco (merge)
                if slug and _marcas.exists(slug):
                    pal_disk = _marcas.extrair_paleta_marca(slug)
                else:
                    pal_disk = {"cores": [], "n_imgs": 0, "acento": "", "acento_claro": ""}
                cores_live = _marcas.extrair_paleta_de_imagens(blobs, n=6) if blobs else []
                # união: live primeiro (mais recentes), depois disco
                cores = []
                for c in (cores_live + (pal_disk.get("cores") or [])):
                    if c and c not in cores:
                        cores.append(c)
                n_imgs = len(blobs) + int(pal_disk.get("n_imgs") or 0)
                if not cores:
                    if n_imgs == 0:
                        return self._send(200, {
                            "ok": False,
                            "erro": "sem referências — envie fotos ou abra uma marca que já tenha refs salvas",
                            "n_imgs": 0, "cores": [],
                        })
                    return self._send(200, {
                        "ok": False,
                        "erro": "li " + str(n_imgs) + " img(s) mas as cores são muito neutras — use o pincel 🖌",
                        "n_imgs": n_imgs, "cores": [],
                    })

                def _sat(h):
                    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
                    mx, mn = max(r, g, b), min(r, g, b)
                    return (mx - mn) / max(1, mx)

                ranked = sorted(cores, key=lambda h: -_sat(h))
                acento = ranked[0]
                acento_claro = next((c for c in ranked[1:] if c != acento), ranked[0])
                # se disco já tinha acento e live não, prefira o mais saturado
                return self._send(200, {
                    "ok": True, "acento": acento, "acento_claro": acento_claro,
                    "cores": cores[:6], "n_imgs": n_imgs,
                })
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-branding-book":
            try:
                slug = str(req.get("slug") or "").strip().lower()
                if not slug:
                    return self._send(400, {"ok": False, "erro": "slug obrigatório"})
                forcar = bool(req.get("forcar") or req.get("force"))
                if forcar or req.get("gerar"):
                    st = _marcas.gerar_branding_book(slug, forcar=True)
                else:
                    st = _marcas.branding_book_status(slug)
                return self._send(200, {"ok": True, **st})
            except ValueError as e:
                return self._send(400, {"ok": False, "erro": str(e)})
            except Exception as e:
                return self._send(500, {"ok": False, "erro": str(e)})

        if path == "/marca-branding-book-asset":
            try:
                slug = str(req.get("slug") or "").strip().lower()
                du = req.get("dataurl") or req.get("data") or ""
                nome = str(req.get("nome") or "page")
                raw, ext = _decode_dataurl(du)
                st = _marcas.salvar_branding_book_asset(slug, raw, nome=nome, ext=ext)
                return self._send(200, {"ok": True, **st})
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
