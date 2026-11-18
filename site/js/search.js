// Site-wide search over site/data/index.json. Each row carries a pre-built lowercase haystack (row.q:
// scientific, Thai, reading, English names, group, phylum and lineage names, tags) and row._sy, its
// lowercase synonyms / currently accepted names (from the GBIF + NCBI fetch).
import { S } from './state.js';
import { T, TA } from './i18n.js';
import { esc, store } from './util.js';
import { all, byId, G } from './data.js';
import { lvBadge, gName, spRd, spCommon, isEn } from './ui.js';

const LIMIT = 8;
const RECENT_MAX = 5;

// All matches, best first: [{ s, score, via }]. via = the synonym that matched, when no other field did.
function matchAll(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const tokens = q.split(/\s+/);
  const out = [];
  for (const s of all()) {
    let score = -1;
    let via = '';
    const i = s.q.indexOf(q);
    if (i !== -1) {
      score = s.sci.toLowerCase().startsWith(q) || s.th.startsWith(q) || s.en.toLowerCase().startsWith(q) ? 0 : 1 + i;
    } else if (tokens.length > 1 && tokens.every((t) => s.q.includes(t))) {
      score = 500;
    } else {
      const j = s._sy.findIndex((x) => x.includes(q));
      if (j !== -1) { score = 1000 + j; via = s.sy[j]; }
    }
    if (score >= 0) out.push({ s, score, via });
  }
  out.sort((a, b) => a.score - b.score || a.s.sci.localeCompare(b.s.sci));
  return out;
}

// The best LIMIT matches: [{ s, via }].
export const searchRows = (query) => matchAll(query).slice(0, LIMIT);

export const searchAll = (query) => searchRows(query).map((x) => x.s);

// Escape the text first, then wrap the parts that match the query words in <mark>.
export function highlight(text, query) {
  const words = [...new Set(query.trim().toLowerCase().split(/\s+/).filter(Boolean))].sort((a, b) => b.length - a.length);
  if (!words.length) return esc(text);
  const re = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  return String(text ?? '').split(re).map((part, i) => (i % 2 ? `<mark>${esc(part)}</mark>` : esc(part))).join('');
}

// Recently opened species (ids), newest first. localStorage may be unavailable: then there is no history.
const readRecent = () => {
  try {
    const v = JSON.parse(store.get('recent', '[]'));
    return Array.isArray(v) ? v.filter((id) => typeof id === 'string' && byId(id)).slice(0, RECENT_MAX) : [];
  } catch { return []; }
};
const writeRecent = (ids) => store.set('recent', JSON.stringify(ids));

// Attach combobox behaviour to every [data-search] input inside root. onGo(species) navigates.
export function wireSearch(root, onGo) {
  root.querySelectorAll('[data-search] input').forEach((inp) => {
    if (inp._wired) return;
    inp._wired = true;
    const box = document.getElementById(`${inp.id}-res`);
    const clr = inp.parentElement.querySelector('.s-clear');
    let active = -1;
    let items = [];
    let count = 0; // options in the open list: species rows plus suggestion chips
    let composing = false;

    const close = () => { box.hidden = true; inp.setAttribute('aria-expanded', 'false'); inp.removeAttribute('aria-activedescendant'); };
    const sync = () => { S.query = inp.value; if (clr) clr.hidden = !inp.value; };
    const go = (s) => {
      writeRecent([s.id, ...readRecent().filter((id) => id !== s.id)].slice(0, RECENT_MAX));
      S.restoreSearch = true; // coming back to the home page reopens this search
      close();
      onGo(s);
    };
    const mark = () => {
      box.querySelectorAll('[role="option"]').forEach((a, i) => a.classList.toggle('active', i === active));
      if (active >= 0) inp.setAttribute('aria-activedescendant', `${inp.id}-o${active}`); else inp.removeAttribute('aria-activedescendant');
    };
    const row = (s, i, q, via) =>
      `<a href="#${s.id}" role="option" id="${inp.id}-o${i}" data-g="${s.g}" class="${i === active ? 'active' : ''}"><span class="dot" style="width:10px;height:10px"></span><span class="r-sci sci">${highlight(s.sci, q)}</span>` +
      (isEn() ? (s.en ? `<span class="r-th">${highlight(s.en, q)}</span>` : '') : `<span class="r-th">${highlight(spRd(s), q)}</span>` + (spCommon(s) ? `<span class="r-th">${highlight(spCommon(s), q)}</span>` : '')) + (via ? `<span class="r-via">${T('synonymOf')}: <span class="sci">${highlight(via, q)}</span></span>` : '') +
      `<span class="r-g">${lvBadge(s)} ${esc(gName(G(s.g)))}</span></a>`;
    const open = () => { box.hidden = false; inp.setAttribute('aria-expanded', 'true'); mark(); };
    const draw = () => {
      const q = inp.value;
      if (!q) { // empty field: recently opened species, then suggested words
        items = readRecent().map(byId).filter(Boolean);
        active = -1;
        const sug = TA('searchSuggest');
        count = items.length + sug.length;
        box.innerHTML = (items.length ? `<div class="r-head" role="presentation"><span>${esc(T('searchRecent'))}</span><button type="button" data-act="clear-recent">${esc(T('searchRecentClear'))}</button></div>` +
          items.map((s, i) => row(s, i, '')).join('') : '') +
          (sug.length ? `<div class="r-head" role="presentation"><span>${esc(T('searchTry'))}</span></div><div class="r-chips" role="presentation">` +
            sug.map((w, i) => `<button type="button" role="option" class="chip" id="${inp.id}-o${items.length + i}" data-q="${esc(w)}">${esc(w)}</button>`).join('') + '</div>' : '');
        if (!count) { close(); return; }
        open();
        return;
      }
      if (!q.trim()) { items = []; count = 0; active = -1; close(); return; }
      const found = matchAll(q);
      const rows = found.slice(0, LIMIT);
      items = rows.map((x) => x.s);
      count = items.length;
      active = items.length ? 0 : -1;
      box.innerHTML = rows.length
        ? `<div class="r-head" role="presentation"><span>${esc(T(found.length > rows.length ? 'searchCountTop' : 'searchCount', { n: found.length, m: rows.length }))}</span></div>` +
          rows.map(({ s, via }, i) => row(s, i, q, via)).join('')
        : `<p>${esc(T('noResult', { q }))}</p>`;
      open();
    };
    const clear = () => { inp.value = ''; sync(); close(); items = []; count = 0; active = -1; inp.focus(); };

    // Thai typed through an IME: wait until the composition ends before searching.
    inp.addEventListener('compositionstart', () => { composing = true; });
    inp.addEventListener('compositionend', () => { composing = false; sync(); draw(); });
    inp.addEventListener('input', (e) => { sync(); if (!composing && !e.isComposing) draw(); });
    inp.addEventListener('focus', draw);
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && count) { active = (active + 1) % count; mark(); e.preventDefault(); }
      else if (e.key === 'ArrowUp' && count) { active = (active - 1 + count) % count; mark(); e.preventDefault(); }
      else if (e.key === 'Enter' && active >= 0) { box.querySelectorAll('[role="option"]')[active]?.click(); e.preventDefault(); }
      else if (e.key === 'Escape') { e.preventDefault(); if (inp.value) clear(); else close(); }
    });
    box.addEventListener('mousedown', (e) => e.preventDefault());
    box.addEventListener('click', (e) => {
      if (e.target.closest('[data-act="clear-recent"]')) { writeRecent([]); draw(); inp.focus(); return; }
      const chip = e.target.closest('[data-q]');
      if (chip) { inp.value = chip.getAttribute('data-q'); sync(); draw(); inp.focus(); return; }
      const a = e.target.closest('a');
      if (!a) return;
      e.preventDefault();
      go(byId(a.getAttribute('href').slice(1)));
    });
    if (clr) {
      clr.addEventListener('mousedown', (e) => e.preventDefault()); // keep the focus in the field
      clr.addEventListener('click', clear);
    }
    inp.addEventListener('blur', () => setTimeout(close, 120));

    // Back on the page: show the query that was typed last, and reopen its results.
    if (S.query && !inp.value) inp.value = S.query;
    sync();
    if (S.restoreSearch && inp.value) { S.restoreSearch = false; inp.focus({ preventScroll: true }); }
  });
}

export const focusHeroSearch = () => {
  const q = document.getElementById('heroQ');
  if (q) { window.scrollTo(0, 0); q.focus(); return true; }
  S.focusSearch = true;
  return false;
};
