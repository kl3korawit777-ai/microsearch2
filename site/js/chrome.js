// Sidebar, mobile drawer, language and theme switches.
import { S } from './state.js';
import { T } from './i18n.js';
import { store, esc } from './util.js';
import { groups } from './data.js';
import { gName } from './ui.js';
import { render, updateNav } from './router.js';
import { focusHeroSearch } from './search.js';
import { parseHash } from './query.js';

const app = document.getElementById('app');
const menuBtn = document.getElementById('menuBtn');

export function applyChrome() {
  app.classList.toggle('collapsed', S.collapsed);
  const cb = document.getElementById('collapseBtn');
  cb.setAttribute('aria-expanded', String(!S.collapsed));
  cb.setAttribute('aria-label', T(S.collapsed ? 'expand' : 'collapse'));
  document.documentElement.lang = S.lang;
  if (S.theme === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', S.theme);
  document.querySelectorAll('[data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === S.lang)));
  document.querySelectorAll('[data-theme-set]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-theme-set') === S.theme)));
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = T(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-aria]').forEach((el) => { if (el.id !== 'collapseBtn') el.setAttribute('aria-label', T(el.getAttribute('data-i18n-aria'))); });
  const nav = document.getElementById('groupNav');
  nav.querySelectorAll('a').forEach((a) => a.remove());
  for (const g of groups()) {
    const a = document.createElement('a');
    a.href = `#${g.id}`;
    a.setAttribute('data-route', g.id);
    a.setAttribute('data-g', g.id);
    a.setAttribute('aria-label', gName(g));
    a.innerHTML = `<span class="dot"></span><span class="lbl">${esc(gName(g))}</span>`;
    nav.appendChild(a);
  }
}

export function openMenu() {
  app.classList.add('menu-open');
  menuBtn.setAttribute('aria-expanded', 'true');
  setTimeout(() => document.getElementById('closeBtn').focus(), 30);
}

export function closeMenu() {
  if (!app.classList.contains('menu-open')) return;
  app.classList.remove('menu-open');
  menuBtn.setAttribute('aria-expanded', 'false');
}

function goSearch() {
  if (!focusHeroSearch()) location.hash = 'home';
}

export function wireChrome() {
  document.getElementById('collapseBtn').addEventListener('click', () => {
    S.collapsed = !S.collapsed;
    store.set('collapsed', S.collapsed ? '1' : '0');
    applyChrome();
  });
  document.querySelectorAll('[data-lang]').forEach((b) => b.addEventListener('click', () => {
    S.lang = b.getAttribute('data-lang') === 'en' ? 'en' : 'th';
    store.set('lang', S.lang);
    applyChrome();
    render(true);
    updateNav(parseHash().path);
  }));
  document.querySelectorAll('[data-theme-set]').forEach((b) => b.addEventListener('click', () => {
    S.theme = b.getAttribute('data-theme-set');
    store.set('theme', S.theme);
    applyChrome();
  }));
  menuBtn.addEventListener('click', openMenu);
  document.getElementById('topSearchBtn').addEventListener('click', goSearch);
  document.getElementById('closeBtn').addEventListener('click', () => { closeMenu(); menuBtn.focus(); });
  document.getElementById('scrim').addEventListener('click', closeMenu);
  document.getElementById('side').addEventListener('click', (e) => { if (e.target.closest('a[href^="#"]')) closeMenu(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && app.classList.contains('menu-open')) { closeMenu(); menuBtn.focus(); }
    const tag = (e.target.tagName || '').toLowerCase();
    if (e.key === '/' && tag !== 'input' && tag !== 'textarea' && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      closeMenu();
      goSearch();
    }
  });
}
