// Hash router + rendering + view event delegation. Routes: #home, #sources, #<group-id>, #<species-id>.
import { S } from './state.js';
import { T } from './i18n.js';
import { G, byId, loadGroup } from './data.js';
import { gName } from './ui.js';
import { viewHome } from './views/home.js';
import { viewGroup, filterState } from './views/group.js';
import { viewSpecies } from './views/species.js';
import { viewSources } from './views/sources.js';
import { viewNotFound } from './views/notfound.js';
import { wireSearch } from './search.js';
import { closeMenu } from './chrome.js';

const view = document.getElementById('view');
let lastHash = null;
let renderToken = 0;

const currentHash = () => decodeURIComponent((location.hash || '').replace(/^#/, '')) || 'home';

async function route() {
  const hash = currentHash();
  const base = 'Microsearch 2.0';
  if (hash === 'home') return { hash, html: viewHome(), g: '', title: base };
  if (hash === 'sources') return { hash, html: viewSources(), g: '', title: `${T('sources')} | ${base}` };
  if (G(hash)) {
    await loadGroup(hash);
    return { hash, html: viewGroup(hash), g: hash, title: `${gName(G(hash))} | ${base}` };
  }
  const s = byId(hash);
  if (s) {
    await loadGroup(s.g);
    return { hash, html: viewSpecies(s), g: s.g, title: `${s.sci} | ${base}` };
  }
  return { hash, html: viewNotFound(), g: '', title: base };
}

export function updateNav(hash) {
  const sp = byId(hash);
  const gid = G(hash) ? hash : sp ? sp.g : '';
  document.querySelectorAll('.side .nav a').forEach((a) => {
    const r = a.getAttribute('data-route');
    const on = r === 'home' ? hash === 'home' : r === 'sources' ? hash === 'sources' : r === gid;
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
  const changed = r.hash !== lastHash;
  if (changed) S.tab = 'traits';
  view.innerHTML = `<div class="view" style="display:flex;flex-direction:column;gap:40px">${r.html}</div>`;
  if (r.g) view.setAttribute('data-g', r.g); else view.removeAttribute('data-g');
  document.title = r.title;
  updateNav(r.hash);
  if (changed) {
    lastHash = r.hash;
    window.scrollTo(0, 0);
    if (S.focusSearch && document.getElementById('heroQ')) { S.focusSearch = false; document.getElementById('heroQ').focus(); }
    else if (!keepFocus) view.querySelector('h1')?.focus({ preventScroll: true });
    closeMenu();
  } else {
    const v = view.querySelector('.view');
    if (v) v.style.animation = 'none';
  }
  wireSearch(view, goTo);
  document.documentElement.setAttribute('data-ready', r.hash);
}

export function goTo(s) {
  if (location.hash === `#${s.id}`) render(); else location.hash = s.id;
}

// ---- events inside the view (delegated)
view.addEventListener('click', (e) => {
  const b = e.target.closest('[data-act]');
  if (!b) return;
  const act = b.getAttribute('data-act');
  const v = b.getAttribute('data-v');
  const gid = currentHash();
  if (act === 'ph-link') {
    filterState(b.getAttribute('href').slice(1)).ph = +v; // let the link navigate to the group page
    return;
  }
  if (act === 'tg') S.tree = { g: v, p: 0, s: 0 };
  else if (act === 'tp') { S.tree.p = +v; S.tree.s = 0; }
  else if (act === 'ts') S.tree.s = +v;
  else if (act === 'fph') filterState(gid).ph = +v;
  else if (act === 'fo') { const f = filterState(gid); const k = b.getAttribute('data-k'); f[k] = f[k] === v ? '' : v; }
  else if (act === 'fclear') delete S.gf[gid];
  else if (act === 'row') S.open[gid] = S.open[gid] === v ? '' : v;
  else if (act === 'tab') S.tab = v;
  else return;
  const sel = `[data-act="${act}"]` + (v !== null ? `[data-v="${v.replace(/"/g, '\\"')}"]` : '') + (b.getAttribute('data-k') ? `[data-k="${b.getAttribute('data-k')}"]` : '');
  render(true).then(() => {
    const again = view.querySelector(sel) || view.querySelector(`[data-act="${act}"]`);
    if (again) again.focus({ preventScroll: true });
  });
});

view.addEventListener('input', (e) => {
  if (e.target.getAttribute('data-act') !== 'fq') return;
  const pos = e.target.selectionStart;
  filterState(currentHash()).q = e.target.value;
  render(true).then(() => {
    const inp = document.getElementById('gQ');
    if (inp) { inp.focus(); try { inp.setSelectionRange(pos, pos); } catch { /* not supported */ } }
  });
});

view.addEventListener('keydown', (e) => {
  const t = e.target;
  if (t.getAttribute('role') !== 'tab') return;
  const tabs = [...view.querySelectorAll('[role="tab"]')];
  const i = tabs.indexOf(t);
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
    S.tab = n.getAttribute('data-v');
    render(true).then(() => view.querySelector(`#tab-${S.tab}`)?.focus());
    e.preventDefault();
  }
});

window.addEventListener('hashchange', () => render(false));

