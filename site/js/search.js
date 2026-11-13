// Site-wide search over site/data/index.json. Each row carries a pre-built lowercase haystack (row.q:
// scientific, Thai, reading, English names, group, phylum and lineage names, tags) and row._sy, its
// lowercase synonyms / currently accepted names (from the GBIF + NCBI fetch).
import { S } from './state.js';
import { T } from './i18n.js';
import { esc } from './util.js';
import { all, byId, G } from './data.js';
import { lvBadge, gName, spRd, isEn } from './ui.js';

const LIMIT = 8;

// Returns [{ s, via }] best first. via = the synonym that matched, when no other field did.
export function searchRows(query) {
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
  return out.slice(0, LIMIT);
}

export const searchAll = (query) => searchRows(query).map((x) => x.s);

// Attach combobox behaviour to every [data-search] input inside root. onGo(species) navigates.
export function wireSearch(root, onGo) {
  root.querySelectorAll('[data-search] input').forEach((inp) => {
    if (inp._wired) return;
    inp._wired = true;
    const box = document.getElementById(`${inp.id}-res`);
    let active = -1;
    let items = [];

    const close = () => { box.hidden = true; inp.setAttribute('aria-expanded', 'false'); };
    const go = (s) => { inp.value = ''; close(); onGo(s); };
    const mark = () => {
      box.querySelectorAll('a').forEach((a, i) => a.classList.toggle('active', i === active));
      if (active >= 0) inp.setAttribute('aria-activedescendant', `${inp.id}-o${active}`);
    };
    const draw = () => {
      const q = inp.value;
      const rows = searchRows(q);
      items = rows.map((x) => x.s);
      active = items.length ? 0 : -1;
      if (!q.trim()) { close(); return; }
      box.innerHTML = rows.length ? rows.map(({ s, via }, i) =>
        `<a href="#${s.id}" role="option" id="${inp.id}-o${i}" data-g="${s.g}" class="${i === active ? 'active' : ''}"><span class="dot" style="width:10px;height:10px"></span><span class="r-sci sci">${esc(s.sci)}</span>` +
        (isEn() ? '' : `<span class="r-th">${esc(spRd(s))}</span>`) + (via ? `<span class="r-via">${T('synonymOf')}: <span class="sci">${esc(via)}</span></span>` : '') +
        `<span class="r-g">${lvBadge(s)} ${esc(gName(G(s.g)))}</span></a>`).join('')
        : `<p>${esc(T('noResult', { q }))}</p>`;
      box.hidden = false;
      inp.setAttribute('aria-expanded', 'true');
      if (active >= 0) inp.setAttribute('aria-activedescendant', `${inp.id}-o0`); else inp.removeAttribute('aria-activedescendant');
    };

    inp.addEventListener('input', draw);
    inp.addEventListener('focus', () => { if (inp.value.trim()) draw(); });
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && items.length) { active = (active + 1) % items.length; mark(); e.preventDefault(); }
      else if (e.key === 'ArrowUp' && items.length) { active = (active - 1 + items.length) % items.length; mark(); e.preventDefault(); }
      else if (e.key === 'Enter' && active >= 0) { go(items[active]); e.preventDefault(); }
      else if (e.key === 'Escape') { inp.value = ''; close(); }
    });
    box.addEventListener('mousedown', (e) => e.preventDefault());
    box.addEventListener('click', (e) => {
      const a = e.target.closest('a');
      if (!a) return;
      e.preventDefault();
      go(byId(a.getAttribute('href').slice(1)));
    });
    inp.addEventListener('blur', () => setTimeout(close, 120));
  });
}

export const focusHeroSearch = () => {
  const q = document.getElementById('heroQ');
  if (q) { window.scrollTo(0, 0); q.focus(); return true; }
  S.focusSearch = true;
  return false;
};
