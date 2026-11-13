// e2e: opens every page in both languages with headless Chrome and checks content, console errors,
// Thai leaking into the English UI, and the main interactions. Run: npm test
import puppeteer from 'puppeteer-core';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { ROOT, SITE, buildSite, findChrome, serveSite, readJson } from './lib.mjs';

const THAI = /[฀-๿]/;
const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

// ---------------------------------------------------------------- static checks (no browser)
function walk(dir) {
  return readdirSync(dir).flatMap((n) => { const p = join(dir, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
}

function staticChecks() {
  for (const f of walk(join(SITE, 'js'))) {
    const src = readFileSync(f, 'utf8');
    ok(!THAI.test(src), `Thai text embedded in JS: ${f.replace(ROOT, '')}`);
  }
  const th = JSON.parse(readFileSync(join(SITE, 'i18n', 'th.json'), 'utf8'));
  const en = JSON.parse(readFileSync(join(SITE, 'i18n', 'en.json'), 'utf8'));
  const miss = Object.keys(th).filter((k) => !(k in en)).concat(Object.keys(en).filter((k) => !(k in th)));
  ok(miss.length === 0, `i18n keys differ between th.json and en.json: ${miss.join(', ')}`);
  const used = new Set();
  for (const f of walk(join(SITE, 'js'))) for (const m of readFileSync(f, 'utf8').matchAll(/\bT\('([A-Za-z0-9_]+)'/g)) used.add(m[1]);
  for (const m of readFileSync(join(SITE, 'index.html'), 'utf8').matchAll(/data-i18n(?:-aria)?="([A-Za-z0-9_]+)"/g)) used.add(m[1]);
  const unknown = [...used].filter((k) => !(k in th));
  ok(unknown.length === 0, `i18n keys used in code but missing from th.json: ${unknown.join(', ')}`);
}

// ---------------------------------------------------------------- browser helpers
let browser; let base;
const baseErrors = new WeakMap();

async function newPage(lang, width = 1280, height = 900) {
  const page = await browser.newPage();
  await page.setViewport({ width, height });
  // preset the language once per tab (sessionStorage survives reloads, so reload tests see the saved choice)
  await page.evaluateOnNewDocument((l) => { try { if (!sessionStorage.getItem('e2e-init')) { sessionStorage.setItem('e2e-init', '1'); localStorage.setItem('ms2.lang', l); } } catch { /* ignore */ } }, lang);
  const errs = [];
  baseErrors.set(page, errs);
  page.on('pageerror', (e) => errs.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const url = m.location()?.url || '';
    if (url && !url.startsWith(base)) return; // external (fonts) problems are not ours
    errs.push(`console.error: ${m.text()} ${url}`);
  });
  page.on('response', (r) => { if (r.url().startsWith(base) && r.status() >= 400) errs.push(`HTTP ${r.status()}: ${r.url()}`); });
  page.on('requestfailed', (r) => { if (r.url().startsWith(base)) errs.push(`request failed: ${r.url()}`); });
  return page;
}

const ready = (page, hash) => page.waitForFunction((h) => document.documentElement.getAttribute('data-ready') === h, { timeout: 15000 }, hash);

async function open(page, hash) {
  await page.goto(`${base}/#${hash}`, { waitUntil: 'load' });
  await ready(page, hash);
}

async function visit(page, hash) {
  await page.evaluate((h) => { document.documentElement.removeAttribute('data-ready'); location.hash = h; }, hash);
  await ready(page, hash);
}

const scan = (page) => page.evaluate(() => {
  const THAI_RE = /[฀-๿]/;
  const out = { leaks: [], fallback: 0 };
  for (const root of document.querySelectorAll('#view, .side, .topbar')) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (!THAI_RE.test(n.nodeValue)) continue;
      const el = n.parentElement;
      if (el.closest('[data-native]')) continue;
      if (el.closest('.th-fb')) { out.fallback++; continue; }
      out.leaks.push(n.nodeValue.trim().slice(0, 60));
    }
    for (const e of root.querySelectorAll('[aria-label],[title],[placeholder]')) {
      for (const a of ['aria-label', 'title', 'placeholder']) {
        const v = e.getAttribute(a);
        if (v && THAI_RE.test(v) && !e.closest('[data-native]')) out.leaks.push(`${a}: ${v.slice(0, 60)}`);
      }
    }
  }
  out.h1 = document.querySelector('#view h1')?.textContent.trim() || '';
  out.title = document.title;
  out.lang = document.documentElement.lang;
  out.overflow = document.documentElement.scrollWidth - window.innerWidth;
  return out;
});

const count = (page, sel) => page.$$eval(sel, (els) => els.length);

// ---------------------------------------------------------------- per-page checks
async function checkAllPages(lang, index, meta, credits) {
  const page = await newPage(lang);
  const fb = { pages: 0, nodes: 0 };
  const errs = baseErrors.get(page);
  const targets = [['home', 'home'], ['sources', 'sources'], ...meta.groups.map((g) => [g.id, 'group']), ...index.map((s) => [s.id, 'species'])];
  await open(page, 'home');
  for (const [hash, kind] of targets) {
    if (hash !== 'home') await visit(page, hash);
    const before = errs.length;
    const r = await scan(page);
    const tag = `[${lang}] #${hash}`;
    ok(errs.length === before && errs.length === 0, `${tag}: errors: ${errs.slice(0, 3).join(' | ')}`);
    ok(r.lang === lang, `${tag}: <html lang> is ${r.lang}`);
    ok(r.h1.length > 0, `${tag}: no <h1>`);
    ok(r.title.includes('Microsearch 2.0'), `${tag}: title ${r.title}`);
    if (lang === 'en') {
      ok(r.leaks.length === 0, `${tag}: Thai in English UI: ${r.leaks.slice(0, 3).join(' | ')}`);
      ok(r.fallback === 0, `${tag}: ${r.fallback} Thai content blocks shown in English mode (missing English field)`);
      if (r.fallback) { fb.pages++; fb.nodes += r.fallback; }
    }
    if (kind === 'species') {
      const s = index.find((x) => x.id === hash);
      const g = meta.groups.find((x) => x.id === s.g);
      ok(r.h1 === s.sci, `${tag}: h1 "${r.h1}" != ${s.sci}`);
      ok((await count(page, '.ladder .step')) === g.ranks.length, `${tag}: ladder steps != ${g.ranks.length}`);
      ok((await count(page, '.badge.draft')) === 1, `${tag}: draft badge missing (review=ai_draft)`);
      ok((await count(page, '.sp-title .lv')) === 1, `${tag}: level badge missing`);
      if (s.img) {
        await page.waitForFunction(() => { const i = document.querySelector('.art-box.photo img'); return !i || (i.complete && i.naturalWidth > 0); }, { timeout: 8000 }).catch(() => {});
        const pic = await page.$eval('.art-box.photo img', (i) => ({ ok: i.complete && i.naturalWidth > 0, src: i.getAttribute('src') })).catch(() => null);
        ok(pic && pic.ok && pic.src === s.img, `${tag}: photo missing or not loaded`);
        const cap = await page.$eval('figure.art figcaption', (e) => e.textContent).catch(() => '');
        ok(/\S/.test(cap) && (await count(page, 'figure.art figcaption a')) >= 1, `${tag}: photo credit missing`);
      } else {
        ok((await count(page, '.art-box svg path, .art-box svg circle, .art-box svg rect, .art-box svg ellipse, .art-box svg g')) > 0, `${tag}: no drawing`);
      }
      ok((await count(page, '#tabpanel dl.facts > div')) > 0, `${tag}: empty traits`);
    } else if (kind === 'group') {
      const g = meta.groups.find((x) => x.id === hash);
      ok((await count(page, '.rows li')) === index.filter((s) => s.g === hash).length, `${tag}: row count`);
      ok((await count(page, '.chips .chip')) === g.phyla.length + 1, `${tag}: chips`);
    } else if (hash === 'home') {
      ok((await count(page, '.gcard')) === meta.groups.length, `${tag}: group cards`);
      ok((await count(page, '.tree .col')) === 3, `${tag}: tree columns`);
      ok((await count(page, '.dg-node')) > 20, `${tag}: diagram nodes`);
      ok((await count(page, '.tablebox tbody tr')) === 6, `${tag}: compare table rows`);
    } else if (hash === 'sources') {
      ok((await count(page, '.prose h2')) === 4, `${tag}: sources sections`);
      ok((await count(page, 'table.credits tbody tr')) === credits.length, `${tag}: credits table rows`);
    }
  }
  await page.close();
  return fb;
}

// ---------------------------------------------------------------- interaction checks
async function interactions(index, meta) {
  const page = await newPage('th');
  const errs = baseErrors.get(page);
  const text = (sel) => page.$eval(sel, (e) => e.textContent.trim());

  // group filters, chips, expandable rows
  await open(page, 'bacteria');
  const total = index.filter((s) => s.g === 'bacteria').length;
  await page.click('.opt[data-k="gram"][data-v="pos"]');
  const posRows = await count(page, '.rows li');
  ok(posRows > 0 && posRows < total, `filter gram=pos gave ${posRows} of ${total}`);
  ok(await page.$eval('.opt[data-k="gram"][data-v="pos"]', (e) => e.getAttribute('aria-pressed') === 'true'), 'filter button not pressed');
  await page.click('[data-act="fclear"]');
  ok((await count(page, '.rows li')) === total, 'clear filters restores all rows');
  await page.click('.chip[data-act="fph"][data-v="1"]');
  const ph1 = index.filter((s) => s.g === 'bacteria' && s.p === 1).length;
  ok((await count(page, '.rows li')) === ph1, `phylum chip: ${ph1} expected`);
  await page.click('.chip[data-act="fph"][data-v="-1"]');
  await page.type('#gQ', 'coli');
  ok((await count(page, '.rows li')) >= 1, 'in-group search "coli" finds a row');
  await page.$eval('#gQ', (e) => { e.value = ''; e.dispatchEvent(new Event('input', { bubbles: true })); });
  await page.click('.rowbtn');
  ok((await count(page, '.rowmore')) === 1 && (await page.$eval('.rowbtn', (e) => e.getAttribute('aria-expanded'))) === 'true', 'row expands');
  await page.click('.rowbtn');
  ok((await count(page, '.rowmore')) === 0, 'row collapses');

  // species page: tabs (mouse + keyboard) and the phylum link back to the group page
  await visit(page, 'halobacterium-salinarum');
  ok((await count(page, '[role="tab"]')) === 3, 'halobacterium has 3 tabs');
  await page.click('#tab-why');
  ok((await page.$eval('#tab-why', (e) => e.getAttribute('aria-selected'))) === 'true', 'tab switches on click');
  await page.focus('#tab-why');
  await page.keyboard.press('ArrowRight');
  ok((await page.$eval('#tab-name', (e) => e.getAttribute('aria-selected'))) === 'true', 'tab switches with ArrowRight');
  ok((await count(page, '.aside li')) > 0, 'aside block rendered for halobacterium');
  await page.click('.ladder a.step:nth-child(1)');
  await ready(page, 'home');
  ok(/dg=archaea/.test(page.url()) && (await count(page, '.dg-node.sel')) === 1, 'ladder step opens the diagram with that name selected');

  // site-wide search with Latin and Thai queries, keyboard selection
  await visit(page, 'home');
  await page.type('#heroQ', 'bacillus');
  await page.waitForSelector('#heroQ-res a');
  ok((await page.$$eval('#heroQ-res a', (a) => a.map((x) => x.textContent))).some((t) => /Bacillus/.test(t)), 'search "bacillus" lists Bacillus');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => /^#bacillus-/.test(location.hash) && document.documentElement.getAttribute('data-ready') === location.hash.slice(1));
  ok((await text('h1')).startsWith('Bacillus'), 'Enter opens the first result');
  await visit(page, 'home');
  await page.type('#heroQ', 'ยีสต์');
  await page.waitForSelector('#heroQ-res a');
  ok((await page.$$eval('#heroQ-res a', (a) => a.map((x) => x.textContent))).some((t) => /Saccharomyces/.test(t)), 'Thai search finds Saccharomyces');
  await page.$eval('#heroQ', (e) => { e.value = ''; });
  await page.type('#heroQ', 'zzzzqq');
  ok((await count(page, '#heroQ-res p')) === 1, 'no-result message shown');

  // home picker
  await page.click('.pick[data-act="tg"][data-v="plants"]');
  ok((await page.$eval('.pick[data-v="plants"]', (e) => e.getAttribute('aria-pressed'))) === 'true', 'home picker selects plants');
  ok((await count(page, '.col[data-g="plants"]')) === 2, 'picker columns follow the group');

  // unknown route
  await visit(page, 'no-such-page');
  ok((await count(page, '.empty h1')) === 1, 'unknown hash shows the not-found page');

  // chrome: theme, collapse, language persistence
  await visit(page, 'home');
  await page.click('[data-theme-set="dark"]');
  ok((await page.$eval('html', (e) => e.getAttribute('data-theme'))) === 'dark', 'dark theme applied');
  await page.click('[data-theme-set="auto"]');
  ok((await page.$eval('html', (e) => e.getAttribute('data-theme'))) === null, 'auto theme removes data-theme');
  await page.click('#collapseBtn');
  ok(await page.$eval('#app', (e) => e.classList.contains('collapsed')), 'sidebar collapses');
  await page.click('#collapseBtn');
  await page.click('[data-lang="en"]');
  ok((await page.$eval('html', (e) => e.lang)) === 'en', 'language switches to English');
  await page.reload({ waitUntil: 'load' });
  await ready(page, 'home');
  ok((await page.$eval('html', (e) => e.lang)) === 'en', 'language persists after reload');
  ok(errs.length === 0, `interaction errors: ${errs.slice(0, 3).join(' | ')}`);
  await page.close();

  // direct links open each page type without going through home first
  for (const h of ['sources', 'plants', index[0].id, index[index.length - 1].id, 'halobacterium-salinarum']) {
    const p = await newPage('th');
    await open(p, h);
    ok((await scan(p)).h1.length > 0, `direct link #${h} renders`);
    ok(baseErrors.get(p).length === 0, `direct link #${h} errors: ${baseErrors.get(p).join(' | ')}`);
    await p.close();
  }

  // small screen: drawer, no horizontal overflow
  const m = await newPage('th', 390, 844);
  await open(m, 'home');
  ok(!(await m.$eval('.topbar', (e) => getComputedStyle(e).display === 'none')), 'mobile top bar visible');
  await m.click('#menuBtn');
  ok(await m.$eval('#app', (e) => e.classList.contains('menu-open')), 'mobile drawer opens');
  await m.waitForFunction(() => { const s = document.querySelector('.side'); return getComputedStyle(s).visibility === 'visible' && s.getBoundingClientRect().left >= -1; });
  await m.click('#groupNav a[data-route="fungi"]');
  await ready(m, 'fungi');
  ok(!(await m.$eval('#app', (e) => e.classList.contains('menu-open'))), 'drawer closes after navigation');
  for (const h of ['home', 'fungi', 'sources', 'escherichia-coli']) {
    await visit(m, h);
    ok((await scan(m)).overflow <= 1, `#${h} overflows horizontally at 390px`);
  }
  ok(baseErrors.get(m).length === 0, `mobile errors: ${baseErrors.get(m).join(' | ')}`);
  await m.close();
}

// ---------------------------------------------------------------- main
async function main() {
  buildSite();
  staticChecks();
  const { server, base: b } = await serveSite();
  base = b;
  browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
  const index = readJson('data/index.json');
  const meta = readJson('data/meta.json');
  const credits = readJson('data/credits.json');
  let fbEn;
  try {
    const t0 = Date.now();
    await checkAllPages('th', index, meta, credits);
    fbEn = await checkAllPages('en', index, meta, credits);
    await interactions(index, meta);
    console.log(`pages: ${2 * (2 + meta.groups.length + index.length)} loads in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  } finally {
    await browser.close();
    server.close();
  }
  console.log(`checks: ${checks}, failures: ${failures.length}`);
  console.log(`English mode: Thai content fallbacks on ${fbEn.pages} pages (${fbEn.nodes} blocks), expected 0`);
  for (const f of failures.slice(0, 60)) console.log(`FAIL ${f}`);
  if (failures.length > 60) console.log(`... and ${failures.length - 60} more`);
  process.exit(failures.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });
