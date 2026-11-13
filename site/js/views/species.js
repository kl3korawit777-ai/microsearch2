import { S } from '../state.js';
import { T, loc, thFallback } from '../i18n.js';
import { esc } from '../util.js';
import { G, inGroup } from '../data.js';
import { art } from '../art.js';
import { gName, tagName, lvBadge, rd, spRd, spCommon, isEn, arrowR, traitValue } from '../ui.js';

// Text from the extra_th / extra_en blocks: English when available, otherwise flagged Thai.
const extraText = (text, fallback) => (fallback ? thFallback(text) : esc(text));

export function viewSpecies(s) {
  const g = G(s.g);
  const d = s.d;
  const useEn = isEn() && d.extra_en;
  const ex = (isEn() ? d.extra_en : null) || d.extra_th || {};
  const fb = isEn() && !useEn; // extra content falls back to Thai
  const ranks = g.ranks;

  const steps = d.lineage.map((x, i) => ({
    rank: isEn() ? ranks[i].en : ranks[i].th,
    name: x.name,
    last: i === d.lineage.length - 1,
  }));
  let h = `<header style="display:flex;flex-direction:column;gap:22px"><nav class="ladder" aria-label="${esc(T('domain'))}"><ol>` +
    steps.map((st, i) => {
      const label = st.name === '?' ? T('unplaced') : esc(st.name);
      const rr = st.name === '?' ? '' : rd(st.name, s.g);
      const inner = `<span class="rank">${esc(st.rank)}</span><span class="nm${st.last ? ' sci' : ''}">${label}</span>${rr ? `<span class="rd">${esc(rr)}</span>` : ''}`;
      const key = steps.slice(0, i + 1).map((x) => x.name).join('/');
      const node = `<a class="step" href="#home?${new URLSearchParams({ dg: s.g, sel: key })}" title="${esc(T('openInDiagram'))}">${inner}</a>`;
      return `<li>${i ? arrowR : ''}${node}</li>`;
    }).join('') + '</ol></nav>' +
    `<div class="sp-title"><h1 class="sci" tabindex="-1">${esc(s.sci)}</h1><div class="sp-sub">` +
    (isEn()
      ? (s.en ? `<p class="sp-common">${esc(s.en)}</p>` : '')
      : `<p class="th"><span class="sp-rd-l">${T('reading')}</span> ${esc(spRd(s))}</p>${spCommon(s) ? `<p class="sp-common"><span class="sp-rd-l">${T('commonName')}</span> ${esc(spCommon(s))}</p>` : ''}`) +
    lvBadge(s).replace('class="lv ', 'class="lv big ') +
    `<a class="badge grp" href="#${g.id}"><span class="dot" style="width:10px;height:10px"></span>${esc(gName(g))}</a>` +
    (d.review === 'ai_draft' ? `<span class="badge draft" title="${esc(T('draftTip'))}">${T('draft')}</span>` : '') +
    '</div></div></header>';
  if (T('enNote')) h += `<p class="notice">${T('enNote')}</p>`;

  // Traits tab: one row per trait of the group; extra rows (traitsExtra) go after the first trait.
  let traits = g.traits.map((tk) => [esc(isEn() ? tk.en : tk.th), traitValue(s, tk.key)]).filter((r) => r[1]);
  if (ex.traitsExtra) traits = traits.slice(0, 1).concat(ex.traitsExtra.map((r) => [extraText(r[0], fb), extraText(r[1], fb)]), traits.slice(1));
  const why = ex.why ? ex.why.map((r) => [extraText(r[0], fb), extraText(r[1], fb)]) : [[s.tags.map((t) => esc(tagName(t))).join(', '), loc(s.sm[0], s.sm[1])]];
  const tabs = [['traits', T('traits'), traits], ['why', T('why'), why]];
  if (ex.name) tabs.push(['name', T('name'), ex.name.map((r) => [extraText(r[0], fb), extraText(r[1], fb)])]);
  const tab = tabs.some((t) => t[0] === S.tab) ? S.tab : 'traits';
  const cur = tabs.find((t) => t[0] === tab);

  h += `<div class="sp-body"><figure class="art"><div class="art-box">${art(s.art)}</div><figcaption>${T('artCaption')}</figcaption></figure>` +
    `<div class="sp-text"><p class="sp-lede">${ex.lede ? extraText(ex.lede, fb) : loc(s.sm[0], s.sm[1])}</p>` +
    `<div class="tabs" role="tablist" aria-label="${esc(T('traits'))}">` + tabs.map((t) =>
      `<button type="button" role="tab" class="tab" id="tab-${t[0]}" data-act="tab" data-v="${t[0]}" aria-selected="${t[0] === tab}" aria-controls="tabpanel" tabindex="${t[0] === tab ? 0 : -1}">${t[1]}</button>`).join('') + '</div>' +
    `<div role="tabpanel" id="tabpanel" aria-labelledby="tab-${tab}"><dl class="facts">${cur[2].map((f) => `<div><dt>${f[0]}</dt><dd>${f[1]}</dd></div>`).join('')}</dl></div></div></div>`;

  if (ex.aside) {
    h += `<aside class="aside" aria-labelledby="asideH"><h2 id="asideH">${extraText(ex.asideTitle, fb)}</h2><ul>${ex.aside.map((x) => `<li>${extraText(x, fb)}</li>`).join('')}</ul></aside>`;
  }

  const mates = inGroup(s.g);
  const idx = mates.indexOf(s);
  const near = mates.filter((m) => m !== s).sort((a, b) => (a.p === s.p ? 0 : 1) - (b.p === s.p ? 0 : 1)).slice(0, 6);
  h += `<section class="section" aria-labelledby="nearH"><h2 class="h2" id="nearH">${T('others', { g: esc(gName(g)) })}</h2><div class="near">` +
    near.map((m) => `<a href="#${m.id}" data-g="${m.g}"><span class="thumb">${art(m.art)}</span><span class="rowtxt"><span class="sci">${esc(m.sci)}</span>${isEn() ? '' : `<span class="th">${esc(spRd(m))}</span>`}</span></a>`).join('') + '</div></section>';
  const prev = mates[(idx - 1 + mates.length) % mates.length];
  const next = mates[(idx + 1) % mates.length];
  h += `<nav class="pager" aria-label="${esc(T('prev'))} / ${esc(T('next'))}"><a href="#${prev.id}"><small>${T('prev')}</small><span class="sci">${esc(prev.sci)}</span></a>` +
    `<a href="#${next.id}"><small>${T('next')}</small><span class="sci">${esc(next.sci)}</span></a></nav>`;
  return h + `<footer class="foot"><p>${T('taxSource')}</p><p>${T('updated')}</p></footer>`;
}
