// Opens every species page (both languages) on the deployed site. Usage: node tests/e2e/live.mjs <base-url>
import puppeteer from 'puppeteer-core';
import { findChrome } from './lib.mjs';

const base = (process.argv[2] || '').replace(/\/$/, '');
if (!base) { console.log('usage: node tests/e2e/live.mjs <base-url>'); process.exit(2); }
const index = await (await fetch(`${base}/data/index.json`)).json();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox'] });
let bad = 0;
for (const lang of ['th', 'en']) {
  const page = await browser.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.evaluateOnNewDocument((l) => { if (!sessionStorage.getItem('i')) { sessionStorage.setItem('i', '1'); localStorage.setItem('ms2.lang', l); } }, lang);
  await page.goto(`${base}/#home`, { waitUntil: 'load' });
  let ok = 0;
  for (const s of index) {
    await page.evaluate((h) => { document.documentElement.removeAttribute('data-ready'); location.hash = h; }, s.id);
    try {
      await page.waitForFunction((h) => document.documentElement.getAttribute('data-ready') === h, { timeout: 10000 }, s.id);
      const h1 = await page.$eval('#view h1', (e) => e.textContent.trim());
      if (h1 === s.sci) ok++; else { bad++; console.log(`[${lang}] ${s.id}: h1 "${h1}"`); }
    } catch { bad++; console.log(`[${lang}] ${s.id}: timeout`); }
  }
  console.log(`${lang}: ${ok}/${index.length} species pages OK, page errors: ${errs.length}`);
  bad += errs.length;
  await page.close();
}
await browser.close();
process.exit(bad ? 1 : 0);
