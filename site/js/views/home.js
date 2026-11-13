import { S } from '../state.js';
import { T, TA, loc } from '../i18n.js';
import { diagram } from '../diagram.js';
import { esc } from '../util.js';
import { groups, G, inGroup, inPhylum } from '../data.js';
import { gName, rankName, tagName, lvBadge, rd, spRd, spCommon, isEn, footer, searchBox, thumb } from '../ui.js';

// params: URL query of #home (dg = group shown in the rank diagram, sel = selected name path)
export function viewHome(params) {
  const tr = S.tree;
  const grp = G(tr.g);
  const plist = inPhylum(grp.id, tr.p);
  const sp = plist[tr.s] || plist[0];

  let h = `<header class="hero"><h1 tabindex="-1">${T('heroTitle')}</h1><p class="lede">${T('heroLede')}</p>${searchBox('heroQ', 'big', T('searchHero'))}</header>`;
  if (T('enNote')) h += `<p class="notice">${T('enNote')}</p>`;

  h += `<section class="tree" aria-label="${esc(T('explore'))}">`;
  h += `<div class="col" role="group" aria-label="${esc(T('colGroup'))}"><p class="col-h">${T('colGroup')}</p>`;
  for (const g of groups()) {
    const dl = isEn() ? g.domainEn : g.domainTh;
    if (dl) h += `<p class="dom">${esc(dl)}</p>`;
    h += `<button type="button" class="pick" data-g="${g.id}" data-act="tg" data-v="${g.id}" aria-pressed="${g.id === grp.id}"><span class="dot"></span><span>${esc(gName(g))}</span><span class="en sci">${isEn() ? '' : esc(g.en)}</span></button>`;
  }
  h += '</div>';

  const rank = rankName(grp);
  h += `<div class="col" data-g="${grp.id}" role="group" aria-label="${esc(rank)}"><p class="col-h">${esc(rank)}</p>`;
  grp.phyla.forEach((ph, i) => {
    const newName = ph.new_name;
    h += `<button type="button" class="pick" data-act="tp" data-v="${i}" aria-pressed="${i === tr.p}"><span class="two"><span style="font-weight:500">${esc(ph.name)}</span>` +
      (rd(ph.name) ? `<span class="sub">${esc(rd(ph.name))}</span>` : '') +
      (newName ? `<span class="sub">${T('newName')} ${esc(newName)}${rd(newName) ? ` (${esc(rd(newName))})` : ''}</span>` : '') +
      `</span><span class="end">${inPhylum(grp.id, i).length}</span></button>`;
  });
  h += '</div>';

  h += `<div class="col" data-g="${grp.id}" role="group" aria-label="${esc(T('colSpecies'))}"><p class="col-h">${T('colSpecies')}</p>`;
  plist.forEach((s, i) => {
    h += `<button type="button" class="pick" data-act="ts" data-v="${i}" aria-pressed="${s === sp}"><span class="two"><span class="sci">${esc(s.sci)}</span>` +
      (isEn() ? '' : `<span class="sub">${esc(spRd(s))}</span>`) + `</span><span class="end">${lvBadge(s)}</span></button>`;
  });
  h += '</div>';

  const ph = grp.phyla[sp.p];
  const common = isEn() ? '' : `<p class="th">${esc(spRd(sp))}</p>${spCommon(sp) ? `<p class="pv-common">${T('commonName')} ${esc(spCommon(sp))}</p>` : ''}`;
  h += `<div class="pv" data-g="${grp.id}" aria-live="polite"><p class="pv-path">${esc(gName(grp))} › ${esc(ph.name)}${rd(ph.name) ? ` (${esc(rd(ph.name))})` : ''}</p>` +
    `<div class="pv-art">${thumb(sp)}</div><h2 class="sci">${esc(sp.sci)}</h2>${common}` +
    `<p class="note">${loc(sp.sm[0], sp.sm[1])}</p><div class="tags">${lvBadge(sp)}${sp.tags.map((t) => `<span class="tag">${esc(tagName(t))}</span>`).join('')}</div>` +
    `<a class="btn" href="#${sp.id}">${T('openPage')}</a></div>`;
  h += '</section>';

  const dgId = G(params.get('dg')) ? params.get('dg') : 'bacteria';
  h += `<section class="section" data-g="${dgId}" aria-labelledby="dgH"><div style="display:flex;flex-direction:column;gap:8px"><h2 class="h2" id="dgH">${T('dgTitle')}</h2><p class="lede" style="font-size:16px">${T('dgLede')}</p></div>` +
    `<div class="chips" role="group" aria-label="${esc(T('colGroup'))}">${groups().map((g) =>
      `<button type="button" class="chip dg-chip" data-g="${g.id}" data-act="dg" data-v="${g.id}" aria-pressed="${g.id === dgId}"><span class="dot" style="width:10px;height:10px"></span>${esc(gName(g))}</button>`).join('')}</div>` +
    diagram(dgId, params.get('sel') || '') +
    (dgId === 'protists' ? `<p class="notice">${T('dgProtist')}</p>` : '') + `<p class="dg-hint">${T('dgScroll')}</p></section>`;

  h += `<section class="section"><h2 class="h2">${T('browseGroups')}</h2><div class="groups4">`;
  for (const g of groups()) {
    const list = inGroup(g.id);
    h += `<a class="gcard" data-g="${g.id}" href="#${g.id}"><b>${esc(gName(g))}</b><span class="sci">${esc(g.en)}</span><p>${esc(isEn() ? g.short.en : g.short.th)}</p>` +
      `<span class="count">${list.length} ${T('speciesCount')} (${T('lvHs')} ${list.filter((x) => x.lv === 'hs').length})</span></a>`;
  }
  h += '</div></section>';

  h += `<section class="section"><h2 class="h2">${T('compareTitle')}</h2><div class="tablebox" tabindex="0" role="region" aria-label="${esc(T('compareTitle'))}"><table><thead><tr><th scope="col" style="color:var(--muted);font-weight:500">${T('traits')}</th>` +
    groups().map((g) => `<th scope="col" data-g="${g.id}"><span class="thg"><span class="dot" style="width:10px;height:10px"></span>${esc(gName(g))}</span></th>`).join('') + '</tr></thead><tbody>' +
    TA('compareRows').map((r) => `<tr><th scope="row">${esc(r[0])}</th>${r.slice(1).map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('') + '</tbody></table></div></section>';
  return h + footer();
}
