// Shared view helpers: names, badges, trait values, small SVG icons.
import { S } from './state.js';
import { T, loc, thFallback } from './i18n.js';
import { esc } from './util.js';
import { getMeta, reading } from './data.js';
import { art } from './art.js';

export const chev = '<svg class="chev" width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 8 4 4 4-4"/></svg>';
export const arrowR = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="m6 3 5 5-5 5"/></svg>';
export const searchIcon = (n) => `<svg class="lead" width="${n}" height="${n}" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="9" cy="9" r="5.5"/><path d="M13.2 13.2 17 17"/></svg>`;

export const isEn = () => S.lang === 'en';
export const gName = (g) => (isEn() ? g.en : g.th);
export const rankName = (g) => (isEn() ? g.rankEn : g.rankTh);

export function tagName(key) {
  const t = getMeta().tags.find((x) => x.key === key);
  return t ? (isEn() ? t.en : t.th) : key;
}

export function lvBadge(s) {
  return `<span class="lv lv-${s.lv}" title="${esc(T(s.lv === 'hs' ? 'lvHsTip' : 'lvUniTip'))}">${T(s.lv === 'hs' ? 'lvHs' : 'lvUni')}</span>`;
}

// Thai reading of a taxon name (hidden in English mode)
export const rd = (label, gid) => (isEn() ? '' : reading(label, gid));
// Thai reading of a species, falling back to its Thai common name
export const spRd = (s) => (isEn() ? '' : s.rd || s.th);
// Thai common name, shown separately only when it differs from the reading
export const spCommon = (s) => (isEn() || !s.th || s.th === s.rd ? '' : s.th);
// Name line under the scientific name: Thai reading in Thai mode, English name (if any) in English mode
export const nameLine = (s) => (isEn() ? esc(s.en || '') : esc(spRd(s)));

// Numeric range trait {min, max, unit}: "40–55 °C", "pH" values have no unit suffix (the row label already says pH)
export const rangeText = (v) => {
  const span = v.min === v.max ? `${v.min}` : `${v.min}–${v.max}`;
  return v.unit && v.unit !== 'pH' ? `${span} ${v.unit}` : span;
};

// Value of one trait of a species: enumerated label from groups meta, otherwise free text from the detail file
export function traitValue(s, key) {
  const v = s.d?.traits?.[key];
  if (v !== undefined && typeof v === 'object') return esc(rangeText(v));
  if (v !== undefined) {
    const lab = getMeta().trait_values[key]?.[v];
    return lab ? esc(isEn() ? lab.en : lab.th) : esc(v);
  }
  const th = s.d?.traits_text_th?.[key];
  const en = s.d?.traits_text_en?.[key];
  return th || en ? loc(th, en) : '';
}

// Plain-text version of a trait value, for filters and the compact row summary
export function traitText(s, key) {
  const v = s.d?.traits?.[key];
  if (v !== undefined && typeof v === 'object') return rangeText(v);
  if (v !== undefined) {
    const lab = getMeta().trait_values[key]?.[v];
    return lab ? (isEn() ? lab.en : lab.th) : v;
  }
  const en = s.d?.traits_text_en?.[key];
  const th = s.d?.traits_text_th?.[key] || '';
  return isEn() ? en || '' : th;
}

export function traitChip(s, key) {
  const v = s.d?.traits?.[key];
  const plain = v !== undefined ? traitText(s, key) : null;
  if (plain !== null) return esc(plain.replace(/ \(.*\)/, ''));
  const th = s.d?.traits_text_th?.[key];
  const en = s.d?.traits_text_en?.[key];
  return isEn() && !en ? thFallback(th) : esc(isEn() ? en : th);
}

// The two compact chips shown on each row of a group page (keys depend on the group)
export function rowSummary(s) {
  const t = (k) => traitChip(s, k);
  switch (s.g) {
    case 'bacteria': return [t('gram'), t('shape')];
    case 'archaea': return [t('env'), t('shape')];
    case 'fungi': return [t('form')];
    case 'plants': return [t('seed'), esc(T(s.d?.traits?.vasc === 'yes' ? 'vascYes' : 'vascNo'))];
    case 'animals': return [t('sym'), t('coel')];
    default: return [t('diet'), t('move')];
  }
}

// Small picture of a species in lists and previews: always the drawing. Real photos appear on the species page.
export function thumb(s) {
  return art(s.art);
}

// Link text for the original page of a picture, by where it came from.
export const sourceLabel = (img) => T(img.source === 'inaturalist' ? 'imgOnInat' : img.source === 'gbif' ? 'imgOnGbif' : 'imgOn');

export const footer = () => `<footer class="foot" id="foot"><p>${T('taxSource')}</p></footer>`;

export function searchBox(id, cls, placeholder) {
  return `<div class="search ${cls}" data-search><label for="${id}" class="sr">${T('searchLabel')}</label>${searchIcon(20)}` +
    `<input id="${id}" type="search" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="${id}-res" placeholder="${esc(placeholder)}"><button type="button" class="s-clear" hidden aria-label="${esc(T('searchClear'))}"><span aria-hidden="true">×</span></button><div class="results" id="${id}-res" role="listbox" hidden></div></div>`;
}
