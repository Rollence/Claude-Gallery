#!/usr/bin/env python3
"""Builds a project-board gallery site from HTML files organized in folders.

content/<project>/<page>.html  ->  site/index.html (board) + copied pages.
Optional: site.json (project names, colors, status) and layout.json (saved order).
Standard library only. Run:  python3 build.py
"""
import json
import re
import shutil
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "site"

PALETTE = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#8b5cf6", "#22c55e", "#ef4444", "#0ea5e9"]
EMOJI_HINTS = [
    ("design", "🎨"), ("ui", "🎨"), ("research", "🔬"), ("science", "🔬"),
    ("dash", "📊"), ("data", "📈"), ("chart", "📈"), ("code", "💻"),
    ("dev", "💻"), ("writ", "✍️"), ("doc", "📄"), ("learn", "📚"),
    ("edu", "📚"), ("game", "🎮"), ("plan", "🗺️"), ("finance", "💰"),
]


def read_json(name):
    p = ROOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def pretty(name):
    return re.sub(r"[-_]+", " ", name).strip().title()


def pick_emoji(slug):
    s = slug.lower()
    for key, emo in EMOJI_HINTS:
        if key in s:
            return emo
    return "📁"


def meta(text, name):
    m = re.search(
        r'<meta[^>]+name=["\']%s["\'][^>]*content=["\']([^"\']*)["\']' % re.escape(name),
        text, re.I)
    if not m:
        m = re.search(
            r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']%s["\']' % re.escape(name),
            text, re.I)
    return unescape(m.group(1)).strip() if m else ""


def page_info(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    t = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    title = unescape(re.sub(r"\s+", " ", t.group(1))).strip() if t else ""
    if not title:
        h = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
        title = unescape(re.sub(r"<[^>]+>", "", h.group(1))).strip() if h else pretty(path.stem)
    date = meta(text, "date")
    try:
        iso = datetime.fromisoformat(date).replace(tzinfo=timezone.utc).isoformat() if date else ""
    except ValueError:
        iso = ""
    if not iso:
        iso = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    tags = [x.strip() for x in meta(text, "tags").split(",") if x.strip()]
    return {"title": title, "desc": meta(text, "description"), "tags": tags, "date": iso}


def main():
    cfg = read_json("site.json")
    proj_cfg = cfg.get("projects", cfg.get("categories", {}))
    layout = read_json("layout.json")
    if not CONTENT.exists():
        raise SystemExit("Create a content/ folder with one subfolder per project first.")

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(CONTENT, OUT)
    (OUT / ".nojekyll").write_text("")

    pages = []
    home = {}
    for f in sorted(CONTENT.rglob("*.html")):
        rel = f.relative_to(CONTENT)
        if any(p.startswith(("_", ".")) for p in rel.parts):
            continue
        slug = rel.parts[0] if len(rel.parts) > 1 else "general"
        info = page_info(f)
        info["id"] = "/".join(rel.parts)
        info["cat"] = slug
        info["path"] = "/".join(quote(p) for p in rel.parts)
        pages.append(info)
        home.setdefault(slug, 0)
        home[slug] += 1

    # Projects come from folders and from site.json, so planned projects with no pages still show.
    slugs = set(home) | set(proj_cfg)
    ordered = sorted(slugs, key=lambda s: (proj_cfg.get(s, {}).get("order", 999), s))
    projects = []
    for i, slug in enumerate(ordered):
        c = proj_cfg.get(slug, {})
        projects.append({
            "id": slug,
            "name": c.get("title", pretty(slug)),
            "emoji": c.get("emoji", pick_emoji(slug)),
            "color": c.get("color", PALETTE[i % len(PALETTE)]),
            "desc": c.get("description", ""),
            "status": c.get("status", ""),
        })

    data = json.dumps({"pages": pages, "projects": projects, "layout": layout or None},
                      ensure_ascii=False)
    data = data.replace("</", "<\\/")
    page = (TEMPLATE
            .replace("__TITLE__", cfg.get("title", "My Claude Gallery"))
            .replace("__SUBTITLE__", cfg.get("subtitle", "Projects and the pages that belong to them"))
            .replace("__DATA__", data))
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"Built {len(pages)} pages in {len(projects)} projects -> {OUT}/index.html")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7fb;--surface:#fff;--text:#14161f;--muted:#6b7080;--line:#e4e6ef;--shadow:0 1px 2px rgba(20,22,31,.06),0 8px 24px rgba(20,22,31,.06);--accent:#6366f1;--thumb:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d0f16;--surface:#171a24;--text:#eceef6;--muted:#9096aa;--line:#262a38;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35);color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0d0f16;--surface:#171a24;--text:#eceef6;--muted:#9096aa;--line:#262a38;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35);color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
body.is-dragging{cursor:grabbing;user-select:none;-webkit-user-select:none}
.wrap{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.hero{background:radial-gradient(1200px 400px at 10% -10%,color-mix(in srgb,var(--accent) 24%,transparent),transparent),radial-gradient(900px 380px at 100% 0,color-mix(in srgb,#ec4899 18%,transparent),transparent);padding:34px 0 14px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
h1{margin:0;font-size:clamp(28px,5vw,42px);letter-spacing:-.02em;line-height:1.1}
.sub{margin:8px 0 0;color:var(--muted);font-size:17px}
.icon-btn{border:1px solid var(--line);background:var(--surface);color:var(--text);width:42px;height:42px;border-radius:12px;cursor:pointer;font-size:18px;flex:none}
.tools{display:flex;gap:10px;margin-top:22px;flex-wrap:wrap}
.search{flex:1 1 240px;position:relative;min-width:0}
.search input{width:100%;height:44px;border-radius:14px;border:1px solid var(--line);background:var(--surface);color:var(--text);padding:0 14px 0 42px;font-size:16px;outline:none}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 25%,transparent)}
.search span{position:absolute;left:14px;top:9px;font-size:18px;opacity:.6}
.btn{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:12px;padding:0 14px;height:44px;font-size:14px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center}
.btn:hover{border-color:var(--accent)}
.chips{display:flex;gap:8px;overflow-x:auto;padding:12px 0 6px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:none;border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:99px;padding:6px 12px;font-size:14px;cursor:pointer;display:inline-flex;gap:8px;align-items:center}
.chip i{width:9px;height:9px;border-radius:50%;background:var(--c);display:block}
.chip small{color:var(--muted);font-variant-numeric:tabular-nums}
.chip:hover{border-color:var(--c)}
.board{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding:10px max(16px,env(safe-area-inset-right,0px)) 22px max(16px,env(safe-area-inset-left,0px),calc((100% - 1148px)/2));scrollbar-width:thin}
.board::after{content:"";flex:none;width:max(0px,calc((100% - 1148px)/2))}
.col{flex:none;width:min(330px,84vw);background:color-mix(in srgb,var(--c) 7%,var(--bg));border:1px solid var(--line);border-radius:20px;padding:12px;display:flex;flex-direction:column;gap:10px}
.col-head{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:10px;align-items:center}
.col-head h2{margin:0;font-size:18px;letter-spacing:-.01em;line-height:1.25;overflow-wrap:anywhere}
.count{font-variant-numeric:tabular-nums;font-size:13px;font-weight:600;color:var(--c);background:color-mix(in srgb,var(--c) 14%,transparent);padding:2px 10px;border-radius:99px}
.col-meta{display:flex;flex-direction:column;gap:6px;padding-left:2px}
.status{align-self:flex-start;font-size:12px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:99px;padding:1px 9px;background:var(--surface)}
.col-desc{margin:0;color:var(--muted);font-size:13px;line-height:1.4}
.col-list{display:flex;flex-direction:column;gap:12px;min-height:96px;max-height:min(68vh,820px);overflow-y:auto;padding:2px;scrollbar-width:thin}
.drop-hint{display:grid;place-items:center;text-align:center;min-height:92px;padding:10px;border:2px dashed var(--line);border-radius:14px;color:var(--muted);font-size:14px}
.col-list.has-items .drop-hint{display:none}
.card{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:var(--shadow);cursor:pointer;transition:transform .15s,opacity .15s;display:flex;flex-direction:column;flex:none}
.card:hover{transform:translateY(-2px)}
.card:focus-visible{outline:3px solid var(--c);outline-offset:2px}
.card.dim{opacity:.28}
.thumb{position:relative;aspect-ratio:8/5;background:var(--thumb);overflow:hidden;border-bottom:1px solid var(--line)}
.thumb iframe{position:absolute;left:0;top:0;width:1280px;height:800px;border:0;transform-origin:0 0;pointer-events:none;background:var(--thumb)}
.thumb::after{content:"";position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 -40px 40px -40px rgba(0,0,0,.12)}
.rank{position:absolute;left:10px;top:10px;z-index:2;min-width:28px;height:28px;padding:0 8px;border-radius:99px;background:var(--text);color:var(--bg);font-size:13px;font-weight:700;display:grid;place-items:center;font-variant-numeric:tabular-nums}
.grip{border:1px solid var(--line);background:var(--surface);color:var(--muted);border-radius:10px;width:36px;height:36px;display:grid;place-items:center;cursor:grab;touch-action:none;padding:0;flex:none}
.grip:hover{color:var(--text);border-color:var(--c,var(--accent))}
.grip:focus-visible{outline:3px solid var(--c,var(--accent));outline-offset:2px}
.card-grip{position:absolute;right:8px;top:8px;z-index:2}
.body{padding:12px 14px 14px}
.card h3{margin:0 0 4px;font-size:16px;line-height:1.3}
.card p{margin:0;color:var(--muted);font-size:13px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em}
.meta{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:10px;color:var(--muted);font-size:12px}
.tags{display:flex;gap:6px;flex-wrap:wrap;min-width:0}
.tags span{background:var(--bg);border:1px solid var(--line);border-radius:99px;padding:1px 8px}
.placeholder{flex:none;border:2px dashed var(--c,var(--accent));border-radius:16px;background:color-mix(in srgb,var(--c,var(--accent)) 10%,transparent)}
.card.dragging,.col.dragging{position:fixed;z-index:1000;margin:0;pointer-events:none;cursor:grabbing;transform:rotate(1.5deg);box-shadow:0 18px 44px rgba(0,0,0,.3);opacity:.97}
.hint{color:var(--muted);text-align:center;font-size:13px;padding:8px 16px 40px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
dialog{border:0;padding:0;border-radius:18px;background:var(--surface);color:var(--text);overflow:hidden}
dialog::backdrop{background:rgba(5,6,12,.65);backdrop-filter:blur(3px)}
#viewer{width:min(1200px,96vw);height:min(860px,92vh)}
#lay{width:min(560px,94vw)}
.dlg{display:flex;flex-direction:column;height:100%}
.dlg header{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line)}
.dlg header b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dlg .btn{height:36px;font-size:14px}
.dlg iframe{flex:1;border:0;width:100%;background:var(--thumb)}
.lay-body{padding:16px;display:flex;flex-direction:column;gap:12px}
.lay-body p{margin:0;color:var(--muted);font-size:14px}
.lay-body textarea{width:100%;height:180px;border:1px solid var(--line);border-radius:12px;background:var(--bg);color:var(--text);font:12px/1.5 ui-monospace,Menlo,Consolas,monospace;padding:10px;resize:vertical}
.lay-actions{display:flex;gap:8px;justify-content:flex-end}
</style>
</head>
<body>
<div class="hero"><div class="wrap">
  <div class="top">
    <div><h1>__TITLE__</h1><p class="sub">__SUBTITLE__</p></div>
    <button class="icon-btn" id="theme" aria-label="Toggle dark mode">🌓</button>
  </div>
  <div class="tools">
    <label class="search"><span>🔍</span><input id="q" type="search" placeholder="Search pages, tags, projects" autocomplete="off"></label>
    <button class="btn" id="save">Save layout</button>
    <button class="btn" id="reset">Reset order</button>
  </div>
  <div class="chips" id="chips"></div>
</div></div>
<main class="board" id="board"></main>
<p class="hint" id="foot"></p>
<p class="hint" style="padding-top:0">Drag the handle on a card or project to reorder. The top card in a project is its highest priority. Your arrangement is saved in this browser.</p>
<div class="sr" id="live" aria-live="polite"></div>
<dialog id="viewer"><div class="dlg">
  <header><b id="vt"></b><a class="btn" id="vo" target="_blank" rel="noopener">Open in new tab</a><button class="btn" id="vc">Close</button></header>
  <iframe id="vf" title="Page preview"></iframe>
</div></dialog>
<dialog id="lay"><div class="lay-body">
  <b>Make this layout permanent</b>
  <p>Your order is saved in this browser only. To publish it for everyone, save the text below as <code>layout.json</code> next to <code>build.py</code> and push.</p>
  <textarea id="laytext" readonly aria-label="Layout JSON"></textarea>
  <div class="lay-actions"><button class="btn" id="laycopy">Copy</button><button class="btn" id="layclose">Close</button></div>
</div></dialog>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const projById = Object.fromEntries(DATA.projects.map(p => [p.id, p]));
const pageById = Object.fromEntries(DATA.pages.map(p => [p.id, p]));
const STATUS = {idea: 'Idea', planned: 'Planned', active: 'In progress', done: 'Done'};
const KEY = 'gallery-layout-v1';
const GRIP = '<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" focusable="false"><circle cx="4" cy="3" r="1.4" fill="currentColor"/><circle cx="10" cy="3" r="1.4" fill="currentColor"/><circle cx="4" cy="7" r="1.4" fill="currentColor"/><circle cx="10" cy="7" r="1.4" fill="currentColor"/><circle cx="4" cy="11" r="1.4" fill="currentColor"/><circle cx="10" cy="11" r="1.4" fill="currentColor"/></svg>';
const board = $('#board');
let layout = null;
let query = '';
let drag = null;
let suppressClick = false;

function buildLayout(base) {
  const order = ((base && base.projects) || []).filter(id => projById[id]);
  DATA.projects.forEach(p => { if (!order.includes(p.id)) order.push(p.id); });
  const items = {};
  order.forEach(id => { items[id] = []; });
  const placed = new Set();
  order.forEach(id => {
    const ids = (base && base.items && base.items[id]) || [];
    ids.forEach(pid => { if (pageById[pid] && !placed.has(pid)) { items[id].push(pid); placed.add(pid); } });
  });
  DATA.pages.filter(p => !placed.has(p.id)).sort((a, b) => new Date(b.date) - new Date(a.date))
    .forEach(p => { (items[p.cat] || items[order[0]]).push(p.id); });
  return {projects: order, items: items};
}
function loadSaved() {
  try { const s = JSON.parse(localStorage.getItem(KEY)); return s && Array.isArray(s.projects) ? s : null; }
  catch (e) { return null; }
}
function save() { try { localStorage.setItem(KEY, JSON.stringify(layout)); } catch (e) {} }

function cardHTML(p, rank) {
  const date = new Date(p.date).toLocaleDateString(undefined, {year: 'numeric', month: 'short', day: 'numeric'});
  return `<article class="card" tabindex="0" data-id="${esc(p.id)}" data-path="${esc(p.path)}" data-title="${esc(p.title)}">
    <div class="thumb"><iframe loading="lazy" tabindex="-1" sandbox="allow-scripts" src="${esc(p.path)}" title=""></iframe>
      <span class="rank" title="Priority within this project">${rank}</span>
      <button class="grip card-grip" aria-label="Reorder ${esc(p.title)}. Drag, or use the arrow keys.">${GRIP}</button></div>
    <div class="body"><h3>${esc(p.title)}</h3><p>${esc(p.desc || 'Open to view this page.')}</p>
      <div class="meta"><div class="tags">${p.tags.slice(0, 2).map(t => `<span>${esc(t)}</span>`).join('')}</div><span>${date}</span></div></div></article>`;
}
function colHTML(id) {
  const p = projById[id];
  const ids = layout.items[id];
  const status = p.status ? `<span class="status">${esc(STATUS[p.status] || p.status)}</span>` : '';
  const desc = p.desc ? `<p class="col-desc">${esc(p.desc)}</p>` : '';
  return `<section class="col" data-proj="${esc(id)}" style="--c:${p.color}">
    <div class="col-head"><button class="grip col-grip" aria-label="Reorder project ${esc(p.name)}. Drag, or use the left and right arrow keys.">${GRIP}</button>
      <h2>${p.emoji} ${esc(p.name)}</h2><span class="count">${ids.length}</span></div>
    ${status || desc ? `<div class="col-meta">${status}${desc}</div>` : ''}
    <div class="col-list ${ids.length ? 'has-items' : ''}"><div class="drop-hint">No pages yet. Drag one here.</div>${ids.map((pid, i) => cardHTML(pageById[pid], i + 1)).join('')}</div></section>`;
}
function chips() {
  $('#chips').innerHTML = layout.projects.map(id => {
    const p = projById[id];
    return `<button class="chip" style="--c:${p.color}" data-proj="${esc(id)}"><i></i>${esc(p.name)} <small>${layout.items[id].length}</small></button>`;
  }).join('');
}
function render() {
  board.innerHTML = layout.projects.map(colHTML).join('');
  chips();
  applySearch();
  fit();
}

function pageMatches(p) {
  if (!query) return true;
  const hay = [p.title, p.desc, p.tags.join(' '), projById[p.cat].name].join(' ').toLowerCase();
  return query.toLowerCase().split(/\s+/).every(w => hay.includes(w));
}
function applySearch() {
  let n = 0;
  board.querySelectorAll('.card').forEach(c => {
    const m = pageMatches(pageById[c.dataset.id]);
    c.classList.toggle('dim', !m);
    if (m) n++;
  });
  $('#foot').textContent = query ? `${n} of ${DATA.pages.length} pages match` : `${DATA.pages.length} pages in ${layout.projects.length} projects`;
}

function fit() {
  document.querySelectorAll('.thumb').forEach(t => {
    t.firstElementChild.style.transform = `scale(${t.clientWidth / 1280})`;
  });
}
function updateHints() {
  board.querySelectorAll('.col-list').forEach(l => l.classList.toggle('has-items', !!l.querySelector('.card, .placeholder')));
}
function sync() {
  const cols = [...board.querySelectorAll('.col')];
  layout.projects = cols.map(c => c.dataset.proj);
  layout.items = {};
  cols.forEach(col => {
    const cards = [...col.querySelectorAll('.col-list .card')];
    layout.items[col.dataset.proj] = cards.map(c => c.dataset.id);
    cards.forEach((c, i) => { c.querySelector('.rank').textContent = i + 1; });
    col.querySelector('.count').textContent = cards.length;
  });
  updateHints();
  chips();
  save();
}
function announce(el) {
  let msg;
  if (el.classList.contains('col')) {
    const i = layout.projects.indexOf(el.dataset.proj);
    msg = `${projById[el.dataset.proj].name} is now project ${i + 1} of ${layout.projects.length}`;
  } else {
    const proj = el.closest('.col').dataset.proj;
    msg = `${pageById[el.dataset.id].title} is now number ${layout.items[proj].indexOf(el.dataset.id) + 1} in ${projById[proj].name}`;
  }
  $('#live').textContent = msg;
}

/* Pointer-based dragging works with mouse, touch and pen. */
board.addEventListener('pointerdown', e => {
  const g = e.target.closest('.grip');
  if (!g || (e.pointerType === 'mouse' && e.button !== 0)) return;
  e.preventDefault();
  startDrag(g.closest('.card') || g.closest('.col'), e);
});
function startDrag(el, e) {
  const isCol = el.classList.contains('col');
  const r = el.getBoundingClientRect();
  const ph = document.createElement('div');
  ph.className = 'placeholder';
  ph.style.height = r.height + 'px';
  if (isCol) ph.style.width = r.width + 'px';
  ph.style.setProperty('--c', getComputedStyle(el).getPropertyValue('--c') || 'var(--accent)');
  el.parentNode.insertBefore(ph, el);
  el.style.width = r.width + 'px';
  el.style.left = r.left + 'px';
  el.style.top = r.top + 'px';
  el.classList.add('dragging');
  document.body.classList.add('is-dragging');
  drag = {el: el, ph: ph, isCol: isCol, dx: e.clientX - r.left, dy: e.clientY - r.top, x: e.clientX, y: e.clientY, raf: 0};
  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  tick();
}
function onMove(e) { if (drag) { drag.x = e.clientX; drag.y = e.clientY; } }
function place() {
  const el = drag.el, ph = drag.ph, x = drag.x, y = drag.y;
  el.style.left = (x - drag.dx) + 'px';
  el.style.top = (y - drag.dy) + 'px';
  if (drag.isCol) {
    const next = [...board.querySelectorAll('.col:not(.dragging)')].find(c => {
      const r = c.getBoundingClientRect(); return x < r.left + r.width / 2;
    });
    if (next) { if (ph.nextSibling !== next) board.insertBefore(ph, next); }
    else if (board.lastElementChild !== ph) board.appendChild(ph);
    return;
  }
  const under = document.elementFromPoint(x, y);
  const col = under && under.closest('.col');
  if (!col) return;
  const list = col.querySelector('.col-list');
  const next = [...list.querySelectorAll('.card:not(.dragging)')].find(c => {
    const r = c.getBoundingClientRect(); return y < r.top + r.height / 2;
  });
  if (next) { if (ph.nextSibling !== next) list.insertBefore(ph, next); }
  else if (list.lastElementChild !== ph) list.appendChild(ph);
  updateHints();
}
function tick() {
  if (!drag) return;
  const br = board.getBoundingClientRect(), edge = 70, speed = 18;
  if (drag.x < br.left + edge) board.scrollLeft -= speed * (1 - Math.max(0, drag.x - br.left) / edge);
  else if (drag.x > br.right - edge) board.scrollLeft += speed * (1 - Math.max(0, br.right - drag.x) / edge);
  if (!drag.isCol) {
    const under = document.elementFromPoint(drag.x, drag.y);
    const col = under && under.closest('.col');
    if (col) {
      const list = col.querySelector('.col-list'), lr = list.getBoundingClientRect();
      if (drag.y < lr.top + 50) list.scrollTop -= 12;
      else if (drag.y > lr.bottom - 50) list.scrollTop += 12;
    }
  }
  place();
  drag.raf = requestAnimationFrame(tick);
}
function endDrag() {
  if (!drag) return;
  cancelAnimationFrame(drag.raf);
  window.removeEventListener('pointermove', onMove);
  window.removeEventListener('pointerup', endDrag);
  window.removeEventListener('pointercancel', endDrag);
  const el = drag.el;
  el.classList.remove('dragging');
  el.style.left = ''; el.style.top = ''; el.style.width = '';
  drag.ph.replaceWith(el);
  document.body.classList.remove('is-dragging');
  drag = null;
  suppressClick = true;
  setTimeout(() => { suppressClick = false; }, 120);
  sync(); fit(); announce(el);
}

/* Keyboard reordering: arrows on a focused handle. */
board.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.classList.contains('card')) {
    openViewer(e.target.dataset.path, e.target.dataset.title); return;
  }
  const g = e.target.closest('.grip');
  if (!g || !['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;
  e.preventDefault();
  const el = g.closest('.card') || g.closest('.col');
  if (el.classList.contains('col')) {
    if (e.key === 'ArrowLeft' && el.previousElementSibling) el.previousElementSibling.before(el);
    else if (e.key === 'ArrowRight' && el.nextElementSibling && el.nextElementSibling.classList.contains('col')) el.nextElementSibling.after(el);
    else return;
  } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    const s = e.key === 'ArrowUp' ? el.previousElementSibling : el.nextElementSibling;
    if (!s || !s.classList.contains('card')) return;
    if (e.key === 'ArrowUp') s.before(el); else s.after(el);
  } else {
    const col = el.closest('.col');
    const side = e.key === 'ArrowLeft' ? col.previousElementSibling : col.nextElementSibling;
    if (!side || !side.classList.contains('col')) return;
    const idx = [...col.querySelectorAll('.col-list .card')].indexOf(el);
    const list = side.querySelector('.col-list');
    const ref = [...list.querySelectorAll('.card')][idx];
    if (ref) ref.before(el); else list.appendChild(el);
  }
  sync(); fit(); g.focus(); announce(el);
});

/* Opening pages and jumping between projects. */
board.addEventListener('click', e => {
  if (suppressClick || e.target.closest('.grip')) return;
  const c = e.target.closest('.card');
  if (c) openViewer(c.dataset.path, c.dataset.title);
});
$('#chips').addEventListener('click', e => {
  const b = e.target.closest('.chip');
  if (!b) return;
  const col = [...board.querySelectorAll('.col')].find(c => c.dataset.proj === b.dataset.proj);
  if (col) col.scrollIntoView({behavior: 'smooth', inline: 'start', block: 'nearest'});
});
function openViewer(path, title) {
  $('#vt').textContent = title;
  $('#vo').href = path;
  $('#vf').src = path;
  $('#viewer').showModal();
}
$('#q').addEventListener('input', e => { query = e.target.value.trim(); applySearch(); });
$('#vc').addEventListener('click', () => $('#viewer').close());
$('#viewer').addEventListener('close', () => { $('#vf').src = 'about:blank'; });
$('#viewer').addEventListener('click', e => { if (e.target === $('#viewer')) $('#viewer').close(); });

/* Save layout dialog and reset. */
$('#save').addEventListener('click', () => {
  $('#laytext').value = JSON.stringify(layout, null, 2);
  $('#laycopy').textContent = 'Copy';
  $('#lay').showModal();
});
$('#layclose').addEventListener('click', () => $('#lay').close());
$('#laycopy').addEventListener('click', () => {
  const ta = $('#laytext'), b = $('#laycopy');
  const done = () => { b.textContent = 'Copied'; };
  const fallback = () => { ta.focus(); ta.select(); b.textContent = 'Selected, press copy'; };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(done, fallback);
  else fallback();
});
let armed = 0;
$('#reset').addEventListener('click', () => {
  const b = $('#reset');
  if (!armed) {
    b.textContent = 'Tap again to reset';
    armed = setTimeout(() => { armed = 0; b.textContent = 'Reset order'; }, 3000);
    return;
  }
  clearTimeout(armed); armed = 0; b.textContent = 'Reset order';
  try { localStorage.removeItem(KEY); } catch (e) {}
  layout = buildLayout(DATA.layout || {});
  render();
});
$('#theme').addEventListener('click', () => {
  const cur = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('theme', next); } catch (e) {}
});
window.addEventListener('resize', fit);

(function init() {
  let t = null;
  try { t = localStorage.getItem('theme'); } catch (e) {}
  if (t) document.documentElement.dataset.theme = t;
  layout = buildLayout(loadSaved() || DATA.layout || {});
  render();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
