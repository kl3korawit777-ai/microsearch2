// UI strings live in site/i18n/{th,en}.json. Content fields use loc() with a flagged Thai fallback.
import { S } from './state.js';
import { esc } from './util.js';

const dict = {};

export async function loadI18n() {
  for (const l of ['th', 'en']) {
    const res = await fetch(`i18n/${l}.json`);
    if (!res.ok) throw new Error(`i18n/${l}.json: ${res.status}`);
    dict[l] = await res.json();
  }
}

export function T(key, vars) {
  const cur = dict[S.lang] || dict.th;
  let s = Object.hasOwn(cur, key) ? cur[key] : Object.hasOwn(dict.th, key) ? dict.th[key] : key;
  if (vars) for (const k of Object.keys(vars)) s = s.replaceAll(`{${k}}`, vars[k]);
  return s;
}

// Thai text shown in English mode because the English field is still empty. It is wrapped so that
// tests can count it separately from real UI leaks.
export function thFallback(text) {
  return text ? `<span class="th-fb" lang="th">${esc(text)}</span>` : '';
}

// Pick the field for the current language; in English mode fall back to flagged Thai.
export function loc(th, en) {
  if (S.lang !== 'en') return esc(th ?? '');
  if (en) return esc(en);
  return thFallback(th);
}

// Array-valued entries such as the comparison table rows.
export function TA(key) {
  const cur = dict[S.lang] || dict.th;
  return Object.hasOwn(cur, key) ? cur[key] : dict.th[key] || [];
}
