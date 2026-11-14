// Hash router + rendering + view event delegation.
// Routes: #home[?dg=&sel=], #sources, #<group-id>[?filters], #<species-id>. State of filters and the
// rank diagram lives in the URL query so every view can be linked and reloaded.
import { S } from './state.js';
import { T } from './i18n.js';
import { G, byId, loadGroup, loadCredits } from './data.js';
import { gName } from './ui.js';
import { parseHash, replaceHash } from './query.js';
import { readFilters, writeFilters } from './filters.js';
import { diagramKey, trailHighlight } from './diagram.js';
import { viewHome } from './views/home.js';
import { viewGroup } from './views/group.js';
import { viewSpecies } from './views/species.js';
import { viewSources } from './views/sources.js';
import { viewNotFound } from './views/notfound.js';
import { wireSearch } from './search.js';
import { closeMenu } from './chrome.js';

const view = document.getElementById('view');
let lastPath = null;
let renderToken = 0;

async function route() {
  const { path, params } = parseHash();
  const base = 'Microsearch 2.0';
  if (path === 'home') {
    const dg = G(params.get('dg')) ? params.get('dg') : 'bacteria';
    await loadGroup(dg);
    return { path, params, html: viewHome(params), g: '', title: base };
  }
  if (path === 'sources') return { path, params, html: viewSources(await loadCredits()), g: '', title: `${T('sources')} | ${base}` };
  if (G(path)) {
    await loadGroup(path);
    return { path, params, html: viewGroup(path, params), g: path, title: `${gName(G(path))} | ${base}` };
  }
  const s = byId(path);
  if (s) {
    await loadGroup(s.g);
    return { path, params, html: viewSpecies(s), g: s.g, title: `${s.sci} | ${base}` };
  }
  return { path, params, html: viewNotFound(), g: '', title: base };
}

export function updateNav(path) {
  const sp = byId(path);
  const gid = G(path) ? path : sp ? sp.g : '';
  document.querySelectorAll('.side .nav a').forEach((a) => {
    const r = a.getAttribute('data-route');
    const on = r === 'home' ? path === 'home' : r === 'sources' ? path === 'sources' : r === gid;
    if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
}

export async function render(keepFocus) {
  const token = ++renderToken;
  let r;
  try {
    r = await route();
  } catch (e) {
    view.innerHTML = `<p class="notice" role="alert">${String(e.message || e).replace(/</g, '&lt;')}</p>`;
    return;
  }
  if (token !== renderToken) return; // a newer navigation superseded this one
  const changed = r.path !== lastPath;
  if (changed) S.tab = 'traits';
  view.innerHTML = `<div class="view" style="display:flex;flex-direction:column;gap:40px">${r.html}</div>`;
  if (r.g) view.setAttribute('data-g', r.g); else view.removeAttribute('data-g');
  document.title = r.title;
  updateNav(r.path);
  if (changed) {
    lastPath = r.path;
    window.scrollTo(0, 0);
    const arrivedAtName = r.path === 'home' && r.params.get('sel');
    if (arrivedAtName) {
      // coming from a species page ladder: show the diagram with the chosen name focused
      setTimeout(() => {
        document.getElementById('dgH')?.scrollIntoView({ block: 'start' });
        view.querySelector('.dg-node.sel')?.focus({ preventScroll: true });
      }, 0);
    } else if (S.focusSearch && document.getElementById('heroQ')) { S.focusSearch = false; document.getElementById('heroQ').focus(); }
    else if (!keepFocus) view.querySelector('h1')?.focus({ preventScroll: true });
    closeMenu();
  } else {
    const v = view.querySelector('.view');
    if (v) v.style.animation = 'none';
  }
  wireSearch(view, goTo);
  document.documentElement.setAttribute('data-ready', r.path);
}

export function goTo(s) {
  if (location.hash === `#${s.id}`) render(); else location.hash = s.id;
}

// ---- URL-backed state changes (no new history entry)
function updateFilters(mutate) {
  const { path, params } = parseHash();
  if (!G(path)) return;
  const f = readFilters(path, params);
  mutate(f);
  replaceHash(path, writeFilters(path, f));
}

function updateDiagram(mutate) {
  const { params } = parseHash();
  const next = new URLSearchParams();
  const state = { dg: G(params.get('dg')) ? params.get('dg') : 'bacteria', sel: params.get('sel') || '' };
  mutate(state);
  if (state.dg !== 'bacteria' || state.sel) next.set('dg', state.dg);
  if (state.sel) next.set('sel', state.sel);
  replaceHash('home', next);
}

// ---- events inside the view (delegated)
view.addEventListener('click', (e) => {
  const b = e.target.closest('[data-act]');
  if (!b) return;
  const act = b.getAttribute('data-act');
  const v = b.getAttribute('data-v');
  const { path } = parseHash();
  let scrollToPanel = false;
  if (act === 'cite') { // reference number: jump to the reference list item, no re-render
    e.preventDefault();
    const target = document.getElementById(`ref-${v}`);
    if (target) {
      target.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      target.focus({ preventScroll: true });
    }
    return;
  }
  if (act === 'tg') S.tree = { g: v, p: 0, s: 0 };
  else if (act === 'tp') { S.tree.p = +v; S.tree.s = 0; }
  else if (act === 'ts') S.tree.s = +v;
  else if (act === 'fph') updateFilters((f) => { f.ph = +v; });
  else if (act === 'fo') { const k = b.getAttribute('data-k'); updateFilters((f) => { f[k] = f[k] === v ? '' : v; }); }
  else if (act === 'fclear') updateFilters((f) => { Object.assign(f, { ph: -1, lv: '', tag: '', q: '' }); for (const k of Object.keys(f)) if (!['ph', 'lv', 'tag', 'q'].includes(k)) f[k] = ''; });
  else if (act === 'row') S.open[path] = S.open[path] === v ? '' : v;
  else if (act === 'tab') S.tab = v;
  else if (act === 'slide') S.slide[path] = +v;
  else if (act === 'dg') updateDiagram((st) => { st.dg = v; st.sel = ''; });
  else if (act === 'dgsel') { updateDiagram((st) => { st.sel = st.sel === v ? '' : v; }); scrollToPanel = true; }
  else return;
  const sel = `[data-act="${act}"]` + (v !== null ? `[data-v="${v.replace(/"/g, '\\"')}"]` : '') + (b.getAttribute('data-k') ? `[data-k="${b.getAttribute('data-k')}"]` : '');
  render(true).then(() => {
    const again = (b.id && document.getElementById(b.id)) || (act === 'dgsel' && !parseHash().params.get('sel') ? null : view.querySelector(sel)) || view.querySelector(`[data-act="${act}"]`);
    if (again) again.focus({ preventScroll: true });
    if (scrollToPanel && parseHash().params.get('sel')) {
      const pnl = document.getElementById('dgPanel');
      if (pnl && pnl.getBoundingClientRect().top > window.innerHeight - 120) {
        pnl.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      }
    }
  });
});

view.addEventListener('input', (e) => {
  if (e.target.getAttribute('data-act') !== 'fq') return;
  const pos = e.target.selectionStart;
  const text = e.target.value;
  updateFilters((f) => { f.q = text; });
  render(true).then(() => {
    const inp = document.getElementById('gQ');
    if (inp) { inp.focus(); try { inp.setSelectionRange(pos, pos); } catch { /* not supported */ } }
  });
});

view.addEventListener('keydown', (e) => {
  const t = e.target;
  if (t.getAttribute('role') === 'tab') {
    const tabs = [...view.querySelectorAll('[role="tab"]')];
    const i = tabs.indexOf(t);
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
      S.tab = n.getAttribute('data-v');
      render(true).then(() => view.querySelector(`#tab-${S.tab}`)?.focus());
      e.preventDefault();
    }
    return;
  }
  const gal = t.closest?.('[data-gallery]');
  if (gal && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
    const btn = gal.querySelector(e.key === 'ArrowLeft' ? '#galPrev' : '#galNext');
    if (btn) { e.preventDefault(); btn.click(); }
    return;
  }
  if (t.closest?.('.dg')) {
    if (e.key === 'Escape' && parseHash().params.get('sel')) {
      updateDiagram((st) => { st.sel = ''; });
      render(true).then(() => view.querySelector('.dg-node')?.focus({ preventScroll: true }));
      e.preventDefault();
      return;
    }
    diagramKey(e);
  }
});

// swipe on the picture: a horizontal drag of at least 40 px moves to the next or previous picture
let swipe = null;
view.addEventListener('pointerdown', (e) => {
  const box = e.target.closest?.('[data-gallery] .art-box');
  swipe = box && !e.target.closest('button') ? { x: e.clientX, y: e.clientY } : null;
});
view.addEventListener('pointerup', (e) => {
  if (!swipe) return;
  const dx = e.clientX - swipe.x;
  const dy = e.clientY - swipe.y;
  swipe = null;
  if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
  view.querySelector(dx < 0 ? '#galNext' : '#galPrev')?.click();
});
view.addEventListener('pointercancel', () => { swipe = null; });

view.addEventListener('mouseover', (e) => trailHighlight(e, true));
view.addEventListener('mouseout', (e) => trailHighlight(e, false));
view.addEventListener('focusin', (e) => trailHighlight(e, true));
view.addEventListener('focusout', (e) => trailHighlight(e, false));

window.addEventListener('hashchange', () => render(false));
