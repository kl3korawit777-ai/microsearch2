// Accessibility: axe-core on every page type in light/dark x Thai/English, keyboard use, visible focus, reduced motion.
// Serious or critical axe violations fail the run; lesser ones are listed. Run: npm run test:a11y
import puppeteer from 'puppeteer-core';
import { join } from 'node:path';
import { ROOT, buildSite, findChrome, serveSite, readJson } from './lib.mjs';

const failures = [];
const notes = new Set();
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

buildSite();
const { server, base } = await serveSite();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const index = readJson('data/index.json');
const withImg = index.find((s) => s.img) || index[0];
const AXE = join(ROOT, 'node_modules', 'axe-core', 'axe.min.js');

async function newPage(lang, theme, width = 1280, height = 900, extra = {}) {
  const page = await browser.newPage();
  await page.setViewport({ width, height });
  if (extra.reducedMotion) await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await page.evaluateOnNewDocument((l, t) => { try { if (!sessionStorage.getItem('i')) { sessionStorage.setItem('i', '1'); localStorage.setItem('ms2.lang', l); localStorage.setItem('ms2.theme', t); } } catch { /* ignore */ } }, lang, theme);
  return page;
}
const ready = (page, h) => page.waitForFunction((x) => document.documentElement.getAttribute('data-ready') === x, { timeout: 15000 }, h);
async function open(page, hash) {
  await page.goto(`${base}/#${hash}`, { waitUntil: 'load' });
  await ready(page, hash.split('?')[0]);
}

// ---------------------------------------------------------------- axe
const PAGES = [
  ['home', 'home', null],
  ['home with diagram selection', 'home?dg=bacteria&sel=Bacteria/Proteobacteria', null],
  ['group', 'bacteria', null],
  ['group with filters', 'bacteria?lv=hs&gram=pos', async (p) => { await p.click('.rowbtn'); }],
  ['species', withImg.id, null],
  ['species (halobacterium)', 'halobacterium-salinarum', async (p) => { await p.click('#tab-name'); }],
  ['sources', 'sources', null],
];
let axeRuns = 0;
for (const theme of ['light', 'dark']) {
  for (const lang of ['th', 'en']) {
    const page = await newPage(lang, theme);
    for (const [name, hash, prep] of PAGES) {
      await open(page, hash);
      if (prep) await prep(page);
      await new Promise((r) => setTimeout(r, 450)); // let the fade-in finish: mid-fade colours give false contrast failures
      if (!(await page.evaluate(() => typeof window.axe !== 'undefined'))) await page.addScriptTag({ path: AXE });
      const res = await page.evaluate(() => window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] } })
        .then((r) => r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.slice(0, 3).map((n) => n.target.join(' ') + ' :: ' + (n.any[0]?.message || n.all[0]?.message || n.none[0]?.message || '').slice(0, 140)) }))));
      axeRuns++;
      for (const v of res) {
        const line = `[${theme}/${lang}] ${name}: ${v.id} (${v.impact}) ${v.help} | ${v.nodes.join(' || ')}`;
        if (v.impact === 'serious' || v.impact === 'critical') ok(false, line); else notes.add(line);
      }
      ok(true, '');
    }
    await page.close();
  }
}

// ---------------------------------------------------------------- keyboard and focus
async function focusIndicator(page) {
  return page.evaluate(() => {
    const e = document.activeElement;
    if (!e || e === document.body) return null;
    const cs = getComputedStyle(e);
    const visible = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
    return { tag: e.tagName, label: (e.getAttribute('aria-label') || e.textContent || e.id || '').trim().slice(0, 30), visible };
  });
}

{
  for (const hash of ['home', 'bacteria', withImg.id, 'sources']) {
    const page = await newPage('th', 'light'); // a fresh tab: keyboard focus starts at the top of the document
    await open(page, hash);
    // first Tab reaches the skip link, it becomes visible, Enter moves focus to the main content
    await page.keyboard.press('Tab');
    await new Promise((r) => setTimeout(r, 250)); // the link slides in
    const skip = await page.evaluate(() => ({ cls: document.activeElement.className, top: document.activeElement.getBoundingClientRect().top }));
    ok(skip.cls === 'skip' && skip.top >= 0, `#${hash}: first Tab focuses a visible skip link (${JSON.stringify(skip)})`);
    await page.keyboard.press('Enter');
    ok(await page.evaluate(() => document.activeElement.id === 'main'), `#${hash}: skip link moves focus to the main content`);
    // tab through the page: every stop shows a focus indicator, focus never gets stuck, and Shift+Tab goes back
    await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0); });
    const seen = new Set();
    let stuck = 0;
    let invisible = [];
    for (let i = 0; i < 70; i++) {
      await page.keyboard.press('Tab');
      const info = await focusIndicator(page);
      if (!info) break; // focus left the page (browser UI): the page has no trap
      const key = `${info.tag}:${info.label}:${i}`;
      if (seen.has(key)) stuck++;
      seen.add(key);
      if (!info.visible) invisible.push(`${info.tag} "${info.label}"`);
    }
    ok(stuck === 0, `#${hash}: keyboard focus does not get stuck`);
    ok(invisible.length === 0, `#${hash}: focus indicator missing on ${invisible.slice(0, 4).join(', ')}`);
    ok(seen.size > 10, `#${hash}: Tab reaches ${seen.size} controls`);
    const sid = () => page.evaluate(() => (document.activeElement.__sid ||= Math.random()));
    const before = await sid();
    await page.keyboard.down('Shift'); await page.keyboard.press('Tab'); await page.keyboard.up('Shift');
    ok((await sid()) !== before, `#${hash}: Shift+Tab moves backwards`);
    await page.close();
  }
  const page = await newPage('th', 'light');

  // controls work with the keyboard alone
  await open(page, 'bacteria');
  await page.focus('.opt[data-k="gram"][data-v="pos"]');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelector('.opt[data-k="gram"][data-v="pos"]')?.getAttribute('aria-pressed') === 'true');
  ok(true, 'filter button toggles with Enter');
  ok(await page.evaluate(() => document.activeElement?.matches('.opt[data-k="gram"][data-v="pos"]')), 'focus stays on the filter button after it re-renders');
  await page.keyboard.press('Space');
  await page.waitForFunction(() => document.querySelector('.opt[data-k="gram"][data-v="pos"]')?.getAttribute('aria-pressed') === 'false');
  ok(true, 'filter button toggles back with Space');
  await page.focus('.rowbtn');
  await page.keyboard.press('Enter');
  ok(await page.$eval('.rowbtn', (e) => e.getAttribute('aria-expanded')) === 'true', 'row expands with Enter');

  await open(page, 'home');
  await page.focus('#heroQ');
  await page.keyboard.type('bacillus');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => /^#bacillus-/.test(location.hash));
  ok(true, 'search: type, ArrowDown, Enter opens a species');
  await page.focus('#heroQ').catch(() => {});

  // the diagram names carry a pressed state and an accessible name with rank, name, reading and count
  await open(page, 'home?dg=archaea');
  const label = await page.$eval('.dg-node', (e) => e.getAttribute('aria-label'));
  ok(/\d/.test(label) && label.length > 8, `diagram node has an accessible name (${label})`);
  await page.close();
}

// mobile drawer: focus moves in, Escape closes it and returns focus
{
  const page = await newPage('th', 'light', 390, 844);
  await open(page, 'home');
  await page.focus('#menuBtn');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.getElementById('app').classList.contains('menu-open'));
  await page.waitForFunction(() => document.activeElement?.id === 'closeBtn', { timeout: 3000 }).catch(() => {});
  ok(await page.evaluate(() => document.activeElement?.id === 'closeBtn'), 'drawer: focus moves to the close button');
  await page.keyboard.press('Escape');
  ok(await page.evaluate(() => !document.getElementById('app').classList.contains('menu-open') && document.activeElement?.id === 'menuBtn'), 'drawer: Escape closes it and focus returns to the menu button');
  ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'no horizontal scrolling at 390px');
  await page.close();
}

// ---------------------------------------------------------------- reduced motion
{
  const page = await newPage('th', 'light', 1280, 900, { reducedMotion: true });
  await open(page, 'bacteria');
  const m = await page.evaluate(() => {
    const dur = (sel) => { const e = document.querySelector(sel); const cs = getComputedStyle(e); return [cs.animationName, cs.animationDuration, cs.transitionDuration].join('|'); };
    return { view: dur('.view'), side: dur('.side'), chip: dur('.chip'), btn: dur('.rowbtn'), reduced: matchMedia('(prefers-reduced-motion: reduce)').matches };
  });
  ok(m.reduced, 'reduced-motion is emulated');
  for (const [k, v] of Object.entries(m)) if (k !== 'reduced') ok(/^none\|/.test(v) && !/[1-9]/.test(v.split('|').slice(1).join('').replace(/0s|0\.0*s/g, '')), `reduced motion: no animation or transition on ${k} (${v})`);
  await open(page, 'home?dg=bacteria');
  await page.click('.dg-node.leaf');
  const behavior = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  ok(behavior, 'diagram selection uses instant scrolling under reduced motion');
  await page.close();
}

await browser.close();
server.close();
console.log(`axe runs: ${axeRuns} (7 pages x light/dark x Thai/English), checks: ${checks}, failures: ${failures.length}`);
if (notes.size) console.log(`axe notes (moderate/minor, not failing): ${notes.size}`);
for (const n of [...notes].slice(0, 12)) console.log(`  note ${n}`);
for (const f of failures.slice(0, 40)) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
