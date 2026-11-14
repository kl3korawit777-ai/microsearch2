// e2e: the made-up test species (tests/fixtures/sample-species.json, all 8 content sections) in both languages.
// It lives in a temporary copy of the site, never in data/. Run: npm run test:sample
import puppeteer from 'puppeteer-core';
import { buildSite, findChrome, serveSite } from './lib.mjs';
import { FIXTURE_ID, withFixture } from './fixture.mjs';

const THAI = /[฀-๿]/;
const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

buildSite();
const { server, base, cleanup } = await withFixture();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });

async function open(lang, hash) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.evaluateOnNewDocument((l) => { try { if (!sessionStorage.getItem('init')) { sessionStorage.setItem('init', '1'); localStorage.setItem('ms2.lang', l); } } catch { /* ignore */ } }, lang);
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error' && (m.location()?.url || '').startsWith(base)) errs.push(m.text()); });
  page.on('response', (r) => { if (r.url().startsWith(base) && r.status() >= 400) errs.push(`HTTP ${r.status()} ${r.url()}`); });
  await page.goto(`${base}/#${hash}`, { waitUntil: 'load' });
  await page.waitForFunction((h) => document.documentElement.getAttribute('data-ready') === h, { timeout: 15000 }, hash);
  return { page, errs };
}

const count = (page, sel) => page.$$eval(sel, (e) => e.length);
const text = (page, sel) => page.$$eval(sel, (e) => e.map((x) => x.textContent.trim()));
const tab = async (page, id) => { await page.click(`#tab-${id}`); await page.waitForSelector(`#tab-${id}[aria-selected="true"]`); };

for (const lang of ['th', 'en']) {
  const t = `[${lang}]`;
  const { page, errs } = await open(lang, FIXTURE_ID);
  ok(errs.length === 0, `${t} errors: ${errs.slice(0, 3).join(' | ')}`);
  ok((await text(page, 'h1'))[0] === 'Testium exemplaris', `${t} h1 is the plain scientific name`);
  ok((await text(page, '.sp-namerow .authority'))[0] === '(Exemplar, 2000) Sample & Demo, 2010', `${t} authority after the name`);
  const names = (await text(page, '.sp-names p')).join(' | ');
  ok(/Fictum vetus, Fictum antiquum/.test(names) && /Testium novum/.test(names), `${t} synonyms and accepted name: ${names}`);
  ok((await text(page, '.badge.iucn'))[0].startsWith('IUCN LC'), `${t} IUCN badge`);
  ok((await page.$eval('.badge.iucn', (e) => e.getAttribute('href'))) === 'https://www.iucnredlist.org/', `${t} IUCN badge links to IUCN`);
  ok((await count(page, '.callout.warning li')) === 2, `${t} warning box with 2 misunderstandings`);
  ok((await count(page, '.callout.disease dl.facts > div')) === 4, `${t} disease box with 4 rows`);
  ok((await count(page, '.callout.disease .callout-note')) === 1, `${t} medical disclaimer in disease box`);
  ok((await count(page, '[role="tab"]')) === 4, `${t} four tabs (traits, life, why, name)`);
  ok((await count(page, '#tabpanel dl.facts > div')) >= 12, `${t} traits tab has all rows`);
  const traits = (await text(page, '#tabpanel dl.facts dd')).join(' | ');
  ok(/40–55 °C/.test(traits) && /6\.5–7\.5/.test(traits) && !/pH$/.test(traits.split(' | ').find((x) => /6\.5/.test(x))) && /15–30 % NaCl/.test(traits), `${t} range traits shown as ranges: ${traits}`);
  await tab(page, 'life');
  ok((await count(page, '#tabpanel dl.facts')) === 2 && (await count(page, '#tabpanel h3.facts-h')) === 1, `${t} life tab: habitat rows and life cycle rows`);
  ok((await count(page, '#tabpanel dl.facts > div')) === 5, `${t} life tab rows`);
  await tab(page, 'why');
  ok((await count(page, '#tabpanel dl.facts > div')) === 3, `${t} importance rows`);
  await tab(page, 'name');
  ok((await count(page, '#tabpanel dl.facts > div')) === 2, `${t} name rows`);
  ok((await count(page, '.aside li')) === 3, `${t} aside items`);
  ok((await count(page, '.refs ol li a[href^="https://"]')) === 3, `${t} three https references`);
  ok((await count(page, '.refs ol li .ref-date')) === 3, `${t} reference dates`);
  ok((await count(page, '.sp-lede a.cite')) === 2, `${t} reference numbers in the text are links`);
  await page.click('.sp-lede a.cite[data-v="2"]');
  ok(await page.evaluate(() => document.activeElement.id === 'ref-2') && page.url().endsWith(`#${FIXTURE_ID}`), `${t} reference link focuses its item and keeps the page`);
  // keyboard: ArrowRight moves through the four tabs and wraps
  await page.focus('#tab-name');
  await page.keyboard.press('ArrowRight');
  ok(await page.$eval('#tab-traits', (e) => e.getAttribute('aria-selected') === 'true'), `${t} ArrowRight wraps to the first tab`);
  if (lang === 'en') {
    const leaks = await page.evaluate(() => {
      const out = [];
      const w = document.createTreeWalker(document.querySelector('main') || document.body, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()) if (/[฀-๿]/.test(n.textContent) && !n.parentElement.closest('[data-native],[lang="th"]')) out.push(n.textContent.trim().slice(0, 40));
      return out;
    });
    ok(leaks.length === 0, `${t} Thai text in English page: ${leaks.slice(0, 3).join(' | ')}`);
    ok((await count(page, '.th-fb')) === 0, `${t} no Thai fallback blocks`);
  } else {
    ok(THAI.test((await text(page, '.callout.warning h2'))[0]), `${t} warning title is Thai`);
  }
  // group page: the new filter appears (the group now has values for it), works, and hides filters nobody uses
  await page.evaluate(() => { document.documentElement.removeAttribute('data-ready'); location.hash = 'archaea'; });
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'archaea', { timeout: 15000 });
  ok((await count(page, '.opt[data-k="metab"]')) === 5 && (await count(page, '.opt[data-k="wall"]')) === 4, `${t} metabolism and cell wall filters shown`);
  ok((await count(page, '.opt[data-k="arrange"]')) === 0, `${t} filters of other groups are not shown`);
  await page.click('.opt[data-k="metab"][data-v="halo"]');
  ok((await count(page, '.rows li')) === 1 && (await text(page, '.rows .sci'))[0] === 'Testium exemplaris', `${t} metabolism filter finds the one species`);
  ok(page.url().includes('metab=halo'), `${t} filter is in the URL`);
  ok(errs.length === 0, `${t} errors after navigation: ${errs.slice(0, 3).join(' | ')}`);
  await page.close();
}

// the real site: no species has the new fields yet, so no new filter or tab shows up
const realServer = await serveSite();
const realPage = await browser.newPage();
await realPage.goto(`${realServer.base}/#archaea`, { waitUntil: 'load' });
await realPage.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'archaea', { timeout: 15000 });
ok((await count(realPage, '.opt[data-k="metab"]')) === 0 && (await count(realPage, '.filters fieldset')) === 4, 'real data: unused filters are not shown (level, conditions, oxygen, importance)');
await realPage.close();
realServer.server.close();

await browser.close();
server.close();
cleanup();
console.log(`sample species: ${checks} checks`);
if (failures.length) { for (const f of failures) console.log(`FAIL ${f}`); process.exit(1); }
console.log('all passed');
