// Screenshot of one page for before/after comparison.
// Usage: node tests/e2e/shot.mjs <out.png> <hash> [th|en] [width] [fixture]   (SHOT_URL=https://... to shoot a deployed site)
//   fixture: serve a copy of site/ with the R0 test species (tests/fixtures/sample-species.json) added
import puppeteer from 'puppeteer-core';
import { buildSite, findChrome, serveSite } from './lib.mjs';
import { withFixture } from './fixture.mjs';

const [out, hash = '#home', lang = 'th', width = '1440', useFixture] = process.argv.slice(2);
const external = process.env.SHOT_URL ? process.env.SHOT_URL.replace(/\/$/, '') : null;
let server = null;
let base = external;
let cleanup = null;
if (!external) {
  buildSite();
  const s = useFixture ? await withFixture() : await serveSite();
  server = s.server;
  base = s.base;
  cleanup = s.cleanup || null;
}
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const page = await browser.newPage();
await page.setViewport({ width: Number(width), height: 900, deviceScaleFactor: 1 });
await page.evaluateOnNewDocument((l) => { try { localStorage.setItem('ms2.lang', l); } catch {} }, lang);
await page.goto(`${base}/${hash}`, { waitUntil: 'networkidle0' });
await page.evaluate(() => document.fonts.ready);
await new Promise((r) => setTimeout(r, 400));
await page.screenshot({ path: out, fullPage: true });
await browser.close();
if (server) server.close();
if (cleanup) cleanup();
console.log('saved', out);
