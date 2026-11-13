// Rank diagram (domain -> genus) for one group, plus the panel for the selected name.
// Nodes are buttons (keyboard: Tab, Enter/Space, arrows, Escape). Selection lives in the URL (#home?dg=..&sel=..).
import { T, loc } from './i18n.js';
import { esc } from './util.js';
import { G, inGroup, groupTaxa } from './data.js';
import { art } from './art.js';
import { lvBadge, rd, spRd, spCommon, isEn } from './ui.js';

const COL_W = 198;
const PILL_W = 174;
const TOP = 34;

const labelOf = (name) => (name === '?' ? T('unplaced') : esc(name));
const lineageNames = (s) => s.d.lineage.map((x) => x.name);

// Build the tree of nodes from the lineages of every species in the group.
function buildNodes(gid) {
  const items = inGroup(gid).map((s) => ({ s, path: lineageNames(s) }));
  items.sort((a, b) => a.s.p - b.s.p || a.path.join('/').localeCompare(b.path.join('/')));
  const nodes = new Map();
  const order = [];
  items.forEach((item, row) => {
    const trail = [];
    item.path.forEach((label, level) => {
      const key = item.path.slice(0, level + 1).join('/');
      let nd = nodes.get(key);
      if (!nd) {
        nd = { id: `n${order.length}`, key, label, level, rows: [], items: [], parent: level ? nodes.get(item.path.slice(0, level).join('/')) : null };
        nodes.set(key, nd);
        order.push(nd);
      }
      nd.rows.push(row);
      nd.items.push(item);
      trail.push(nd.id);
      if (!nd.trail) nd.trail = trail.slice();
      if (level === item.path.length - 1) nd.leaf = item.s;
    });
  });
  return { items, nodes, order };
}

// Description of a name: about text from taxa.json (Thai or English), else nothing.
function aboutOf(gid, name) {
  const t = groupTaxa(gid)[name];
  return t && (t.about_th || t.about_en) ? loc(t.about_th, t.about_en) : '';
}

export function diagram(gid, selKey) {
  const g = G(gid);
  const en = isEn();
  const ranks = g.ranks;
  const taxa = groupTaxa(gid);
  const { items, order } = buildNodes(gid);
  const sel = order.find((nd) => nd.key === selKey) || null;
  const selCls = (nd) => {
    if (!sel) return '';
    if (nd === sel) return 'sel';
    if (sel.trail.includes(nd.id)) return 'on';
    if (nd.trail.includes(sel.id)) return 'in';
    return 'dim';
  };
  const two = !en;
  const rowH = two ? 60 : 46;
  const pillH = two ? 48 : 34;
  const W = (ranks.length - 1) * COL_W + PILL_W;
  const H = TOP + items.length * rowH;
  for (const nd of order) {
    nd.x = nd.level * COL_W;
    nd.y = TOP + ((Math.min(...nd.rows) + Math.max(...nd.rows)) / 2) * rowH;
  }

  const edges = order.filter((nd) => nd.parent).map((nd) => {
    const p = nd.parent;
    const x1 = p.x + PILL_W;
    const y1 = p.y + pillH / 2;
    const x2 = nd.x;
    const y2 = nd.y + pillH / 2;
    const mx = x1 + (x2 - x1) / 2;
    const dir = y2 > y1 ? 1 : -1;
    const d = Math.abs(y2 - y1) < 1 ? `M${x1} ${y1}H${x2}`
      : `M${x1} ${y1}H${mx - 6}Q${mx} ${y1} ${mx} ${y1 + 6 * dir}V${y2 - 6 * dir}Q${mx} ${y2} ${mx + 6} ${y2}H${x2}`;
    return `<path data-k="${nd.id}" class="${selCls(nd)}" d="${d}"/>`;
  }).join('');

  let h = `<div class="dg-scroll" tabindex="-1"><div class="dg" style="width:${W}px;height:${H}px">`;
  ranks.forEach((r, i) => { h += `<span class="dg-rank" style="left:${i * COL_W}px">${esc(en ? r.en : r.th)}</span>`; });
  h += `<svg width="${W}" height="${H}" aria-hidden="true">${edges}</svg>`;
  for (const nd of order) {
    const cls = `dg-node${nd.level === 0 ? ' root' : ''}${nd.leaf ? ' leaf sci' : ''}${nd.label === '?' ? ' unplaced' : ''}${selCls(nd) ? ` ${selCls(nd)}` : ''}${two ? ' two' : ''}`;
    const text = labelOf(nd.label);
    const common = !en && taxa[nd.label]?.common_th;
    const tip = nd.leaf ? `${nd.leaf.sci}${en || !nd.leaf.th ? '' : ` (${nd.leaf.th})`}` : common || '';
    const rk = en ? ranks[nd.level].en : ranks[nd.level].th;
    const rdN = nd.label === '?' ? '' : rd(nd.label, gid);
    h += `<button type="button" class="${cls}" data-act="dgsel" data-v="${esc(nd.key)}" data-k="${nd.id}" data-trail="${nd.trail.join(' ')}" data-level="${nd.level}" data-parent="${nd.parent ? nd.parent.id : ''}" aria-pressed="${nd === sel}" ` +
      `aria-label="${esc(`${rk} ${nd.label === '?' ? T('unplaced') : nd.label}${rdN ? ` (${rdN})` : ''}, ${T('nSpecies', { n: nd.items.length })}`)}" style="left:${nd.x}px;top:${nd.y}px"${tip ? ` title="${esc(tip)}"` : ''}>` +
      `<span class="dg-l">${text}</span>${rdN ? `<span class="dg-r">${esc(rdN)}</span>` : ''}</button>`;
  }
  h += '</div></div>';

  // Panel: description, path from the domain, sibling groups and every species inside the chosen name
  h += '<div class="dg-panel" id="dgPanel" aria-live="polite">';
  if (!sel) return `${h}<p class="dg-empty">${T('dgPick')}</p></div>`;

  const selRank = en ? ranks[sel.level].en : ranks[sel.level].th;
  const selRd = sel.label === '?' ? '' : rd(sel.label, gid);
  h += `<div class="dg-panel-head"><div><p class="dg-rk">${esc(selRank)}</p><h3 class="${sel.leaf ? 'sci' : ''}">${labelOf(sel.label)}</h3>` +
    (selRd ? `<p class="dg-read">${T('reading')} ${esc(selRd)}</p>` : '') + `<p class="dg-count">${T('nSpecies', { n: sel.items.length })}</p></div>` +
    `<button type="button" class="btn quiet" data-act="dgsel" data-v="${esc(sel.key)}" style="min-height:40px;padding:0 14px;font-size:14px">${T('dgClear')}</button></div>`;

  const info = sel.label === '?' ? T('unplacedInfo') : aboutOf(gid, sel.label);
  const crumbs = [];
  for (let pn = sel.parent; pn; pn = pn.parent) crumbs.unshift(pn);
  h += '<div class="dg-info">' +
    (crumbs.length ? `<p class="dg-path">${T('dgIn')} ${crumbs.map((c) => `<button type="button" class="dg-crumb" data-act="dgsel" data-v="${esc(c.key)}">${labelOf(c.label)}</button>`).join(' › ')}</p>` : '') +
    (info ? `<h4>${T('dgWhy')}</h4><p class="dg-desc">${info}</p>` : (sel.leaf ? '' : `<p class="dg-desc">${T('dgNoInfo')}</p>`)) + '</div>';

  if (sel.parent) {
    const sibs = order.filter((o) => o.parent === sel.parent && o !== sel);
    const rkName = en ? ranks[sel.level].en.toLowerCase() : ranks[sel.level].th;
    const parentLabel = labelOf(sel.parent.label);
    if (sibs.length) {
      h += `<div class="dg-sibs"><h4>${T('dgCompare', { r: esc(rkName), p: parentLabel })}</h4><ul>` + sibs.map((o) => {
        const oi = o.label === '?' ? T('unplacedInfo') : aboutOf(gid, o.label) || (o.leaf ? loc(o.leaf.sm[0], o.leaf.sm[1]) : '');
        const orr = o.label === '?' ? '' : rd(o.label, gid);
        return `<li><button type="button" data-act="dgsel" data-v="${esc(o.key)}"><span class="dg-sib-h"><span class="${o.leaf ? 'sci' : ''}" style="font-weight:600">${labelOf(o.label)}</span>` +
          (orr ? `<span class="dg-sib-r">${esc(orr)}</span>` : '') + `<span class="dg-sib-n">${T('nSpecies', { n: o.items.length })}</span></span>` +
          (oi ? `<span class="dg-sib-d">${oi}</span>` : '') + '</button></li>';
      }).join('') + `</ul><p class="dg-note">${T('dgOnlyHere')}</p></div>`;
    } else {
      h += `<p class="dg-note">${T('dgOnlyChild', { r: esc(rkName), p: parentLabel })}</p>`;
    }
  }

  h += `<h4 class="dg-list-h">${T('dgSpeciesIn', { n: sel.items.length })}</h4><ul class="dg-list">` + sel.items.map((it) => {
    const below = it.path.slice(sel.level + 1, -1).map((x) => (x === '?' ? T('unplaced') : esc(x)));
    return `<li><a href="#${it.s.id}"><span class="thumb">${art(it.s.art)}</span><span class="rowtxt"><span class="sci">${esc(it.s.sci)} ${lvBadge(it.s)}</span>` +
      (en ? '' : `<span class="th">${esc(spRd(it.s))}${spCommon(it.s) ? ` (${esc(spCommon(it.s))})` : ''}</span>`) +
      (below.length ? `<span class="dg-below">${below.join(' › ')}</span>` : '') + '</span></a></li>';
  }).join('') + '</ul>';
  return `${h}</div>`;
}

// Arrow-key navigation between nodes. Returns true when the key was handled.
export function diagramKey(e) {
  const node = e.target.closest?.('.dg-node');
  if (!node) return false;
  const dg = node.closest('.dg');
  const all = [...dg.querySelectorAll('.dg-node')];
  const level = node.getAttribute('data-level');
  const sameLevel = all.filter((n) => n.getAttribute('data-level') === level).sort((a, b) => a.offsetTop - b.offsetTop);
  let target = null;
  if (e.key === 'ArrowLeft') target = all.find((n) => n.getAttribute('data-k') === node.getAttribute('data-parent'));
  else if (e.key === 'ArrowRight') target = all.filter((n) => n.getAttribute('data-parent') === node.getAttribute('data-k')).sort((a, b) => a.offsetTop - b.offsetTop)[0];
  else if (e.key === 'ArrowUp') target = sameLevel[sameLevel.indexOf(node) - 1];
  else if (e.key === 'ArrowDown') target = sameLevel[sameLevel.indexOf(node) + 1];
  else return false;
  e.preventDefault();
  if (target) target.focus();
  return true;
}

// Highlight the path from the domain to a node while it is hovered or focused.
export function trailHighlight(e, on) {
  const a = e.target.closest?.('[data-trail]');
  if (!a) return;
  const dg = a.closest('.dg');
  for (const k of a.getAttribute('data-trail').split(' ')) {
    dg.querySelectorAll(`[data-k="${k}"]`).forEach((el) => el.classList.toggle('hl', on));
  }
}
