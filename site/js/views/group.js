import { S } from '../state.js';
import { T, loc } from '../i18n.js';
import { esc } from '../util.js';
import { G, inGroup, getMeta } from '../data.js';
import { art } from '../art.js';
import { gName, rankName, tagName, lvBadge, spRd, spCommon, isEn, chev, searchIcon, footer, traitValue, rowSummary } from '../ui.js';

// Filters whose key differs from the trait key, or that merge several trait values into one option.
const FILTER_TRAIT = { shapeF: 'shape', envF: 'env' };
const FILTER_MERGE = { shapeF: { curvedspiral: ['curved', 'spiral'] }, envF: { hot: ['hot', 'hotacid'] } };

export function filterState(gid) {
  if (!S.gf[gid]) {
    const f = { ph: -1, tag: '', q: '', lv: '' };
    for (const x of G(gid).filters || []) f[x[0]] = '';
    S.gf[gid] = f;
  }
  return S.gf[gid];
}

function matchesFilter(s, f, g) {
  if (f.ph >= 0 && s.p !== f.ph) return false;
  if (f.lv && s.lv !== f.lv) return false;
  if (f.tag && !s.tags.includes(f.tag)) return false;
  for (const fd of g.filters || []) {
    const k = fd[0];
    if (!f[k]) continue;
    const trait = FILTER_TRAIT[k] || k;
    const merged = FILTER_MERGE[k]?.[f[k]];
    const val = s.d?.traits?.[trait];
    if (merged ? !merged.includes(val) : val !== f[k]) return false;
  }
  const q = (f.q || '').trim().toLowerCase();
  if (q && `${s.sci} ${s.th} ${s.rd} ${s.en}`.toLowerCase().indexOf(q) === -1) return false;
  return true;
}

export function viewGroup(gid) {
  const g = G(gid);
  const f = filterState(gid);
  const all = inGroup(gid);
  const list = all.filter((s) => matchesFilter(s, f, g));
  const any = f.ph >= 0 || f.tag || f.q || f.lv || (g.filters || []).some((x) => f[x[0]]);
  const rank = rankName(g);

  let h = `<header class="ghead"><nav class="crumbs" aria-label="breadcrumb"><a href="#home">${T('explorePath')}</a> › ${esc(gName(g))}</nav>` +
    `<div class="gtitle"><h1 tabindex="-1">${esc(gName(g))}</h1><span class="sci">${esc(g.en)}</span></div>` +
    `<p class="lede">${esc(isEn() ? g.introEn : g.introTh)}</p></header>`;
  if (T('enNote')) h += `<p class="notice">${T('enNote')}</p>`;

  const allLabel = isEn() ? `All ${g.rankEn === 'Phylum' ? 'phyla' : 'supergroups'}` : `${T('allPhyla')}${rank}`;
  h += `<div class="chips" role="group" aria-label="${esc(rank)}"><button type="button" class="chip" data-act="fph" data-v="-1" aria-pressed="${f.ph < 0}">${esc(allLabel)}</button>` +
    g.phyla.map((ph, i) => `<button type="button" class="chip" data-act="fph" data-v="${i}" aria-pressed="${f.ph === i}">${esc(ph.name)}</button>`).join('') + '</div>';

  const placeholder = esc(T('searchIn', { g: gName(g) }));
  h += `<div class="split"><aside class="filters" aria-label="${esc(T('filters'))}">` +
    `<div class="search"><label for="gQ" class="sr">${placeholder}</label>${searchIcon(18)}` +
    `<input id="gQ" type="search" autocomplete="off" data-act="fq" value="${esc(f.q)}" placeholder="${placeholder}"></div>`;

  const sets = [['lv', T('level'), [['hs', T('lvHs')], ['uni', T('lvUni')]]]].concat(g.filters || [])
    .concat([['tag', T('importance'), getMeta().tags.map((t) => [t.key, isEn() ? t.en : t.th])]]);
  for (const fs of sets) {
    const fe = isEn() ? getMeta().filter_en[fs[0]] : null;
    h += `<fieldset><legend>${esc(fe ? fe[0] : fs[1])}</legend><div class="opts">` +
      fs[2].map((o) => `<button type="button" class="opt" data-act="fo" data-k="${fs[0]}" data-v="${esc(o[0])}" aria-pressed="${f[fs[0]] === o[0]}">${esc(fe && fe[1][o[0]] ? fe[1][o[0]] : o[1])}</button>`).join('') + '</div></fieldset>';
  }

  h += `</aside><section class="list-area" aria-labelledby="resH"><div class="list-head"><h2 id="resH" aria-live="polite">${T('found', { n: list.length, t: all.length })}</h2>` +
    (any ? `<button type="button" class="btn quiet" data-act="fclear" style="min-height:40px;padding:0 14px;font-size:14px">${T('clear')}</button>` : '') + '</div>';

  if (list.length) {
    const open = S.open[gid];
    h += '<ul class="rows">' + list.map((s) => {
      const isOpen = open === s.id;
      const th = isEn() ? esc(s.en || '') : `${esc(spRd(s))}${spCommon(s) ? ` (${esc(spCommon(s))})` : ''}`;
      return `<li><button type="button" class="rowbtn" data-act="row" data-v="${s.id}" aria-expanded="${isOpen}" aria-controls="m-${s.id}">` +
        `<span class="thumb">${art(s.art)}</span><span class="rowtxt"><span class="sci">${esc(s.sci)}</span>${th ? `<span class="th">${th}</span>` : ''}</span>` +
        `<span class="meta">${lvBadge(s)}<span class="mini">${esc(g.phyla[s.p].name)}</span>${rowSummary(s).filter(Boolean).map((x) => `<span class="mini">${x}</span>`).join('')}</span>${chev}</button>` +
        (isOpen ? `<div class="rowmore" id="m-${s.id}"><p>${loc(s.sm[0], s.sm[1])}</p><div class="facts-inline">` +
          g.traits.slice(0, 3).map((tk) => `<span>${esc(isEn() ? tk.en : tk.th)}: ${traitValue(s, tk.key)}</span>`).join('') + '</div>' +
          `<div class="tags">${s.tags.map((t) => `<span class="tag">${esc(tagName(t))}</span>`).join('')}</div>` +
          `<a class="btn" style="align-self:flex-start" href="#${s.id}">${T('openSpecies')}</a></div>` : '') + '</li>';
    }).join('') + '</ul>';
  } else {
    h += `<div class="empty"><p>${T('emptyFilter')}</p><button type="button" class="btn" data-act="fclear">${T('clear')}</button></div>`;
  }
  return h + '</section></div>' + footer();
}
