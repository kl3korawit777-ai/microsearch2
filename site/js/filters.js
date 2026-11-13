// Group-page filters: level, group traits, importance tag, phylum chip, free-text. State lives in the URL.
import { G, getMeta } from './data.js';

// Filter keys that differ from the trait key, or merge several trait values into one option.
const FILTER_TRAIT = { shapeF: 'shape', envF: 'env' };
const FILTER_MERGE = { shapeF: { curvedspiral: ['curved', 'spiral'] }, envF: { hot: ['hot', 'hotacid'] } };

// Trait key behind a filter key
export const filterTrait = (k) => FILTER_TRAIT[k] || k;

// A filter is offered only when at least one species of the group has a value for its trait
export const filterInUse = (fd, list) => list.some((s) => s.d?.traits?.[filterTrait(fd[0])] !== undefined);

export const emptyFilters = (g) => {
  const f = { ph: -1, lv: '', tag: '', q: '' };
  for (const fd of g.filters || []) f[fd[0]] = '';
  return f;
};

// Read filters from URL params; unknown or invalid values are ignored.
export function readFilters(gid, params) {
  const g = G(gid);
  const f = emptyFilters(g);
  const ph = parseInt(params.get('ph'), 10);
  if (Number.isInteger(ph) && ph >= 0 && ph < g.phyla.length) f.ph = ph;
  if (['hs', 'uni'].includes(params.get('lv'))) f.lv = params.get('lv');
  if (getMeta().tags.some((t) => t.key === params.get('tag'))) f.tag = params.get('tag');
  for (const fd of g.filters || []) {
    const v = params.get(fd[0]);
    if (v && fd[2].some((o) => o[0] === v)) f[fd[0]] = v;
  }
  f.q = params.get('q') || '';
  return f;
}

// Params in a fixed order so equal states give equal URLs.
export function writeFilters(gid, f) {
  const g = G(gid);
  const p = new URLSearchParams();
  if (f.ph >= 0) p.set('ph', String(f.ph));
  if (f.lv) p.set('lv', f.lv);
  for (const fd of g.filters || []) if (f[fd[0]]) p.set(fd[0], f[fd[0]]);
  if (f.tag) p.set('tag', f.tag);
  if (f.q.trim()) p.set('q', f.q);
  return p;
}

export const anyFilter = (g, f) => f.ph >= 0 || !!f.tag || !!f.q.trim() || !!f.lv || (g.filters || []).some((fd) => f[fd[0]]);

export function matchesFilter(s, f, g) {
  if (f.ph >= 0 && s.p !== f.ph) return false;
  if (f.lv && s.lv !== f.lv) return false;
  if (f.tag && !s.tags.includes(f.tag)) return false;
  for (const fd of g.filters || []) {
    const k = fd[0];
    if (!f[k]) continue;
    const merged = FILTER_MERGE[k]?.[f[k]];
    const val = s.d?.traits?.[FILTER_TRAIT[k] || k];
    if (merged ? !merged.includes(val) : val !== f[k]) return false;
  }
  const q = f.q.trim().toLowerCase();
  if (q && `${s.sci} ${s.th} ${s.rd} ${s.en}`.toLowerCase().indexOf(q) === -1) return false;
  return true;
}
