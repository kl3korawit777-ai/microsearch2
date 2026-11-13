// Lighthouse (mobile emulation, simulated slow 4G + 4x CPU slowdown) on the main page types.
// Every category must score >= 90. Run: npm run test:lighthouse   (set LH_URL to test a deployed site)
import puppeteer from 'puppeteer-core';
import lighthouse from 'lighthouse';
import { buildSite, findChrome, serveSite, readJson } from './lib.mjs';

const MIN = 90;
const CATEGORIES = ['performance', 'accessibility', 'best-practices', 'seo'];
const external = process.env.LH_URL ? process.env.LH_URL.replace(/\/$/, '') : null;

let server = null;
let base = external;
if (!external) {
  buildSite();
  const s = await serveSite();
  server = s.server;
  base = s.base;
}
const index = external ? await (await fetch(`${base}/data/index.json`)).json() : readJson('data/index.json');
const withImg = index.find((s) => s.img) || index[0];

const PAGES = [
  ['home', '#home'],
  ['home + diagram selection', '#home?dg=bacteria&sel=Bacteria/Proteobacteria'],
  ['group', '#bacteria'],
  ['species', `#${withImg.id}`],
  ['sources', '#sources'],
];

const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu', '--remote-debugging-port=0'] });
const port = Number(new URL(browser.wsEndpoint()).port);
const failures = [];
const rows = [];
for (const [name, hash] of PAGES) {
  const result = await lighthouse(`${base}/${hash}`, { port, output: 'json', logLevel: 'error', onlyCategories: CATEGORIES });
  const lhr = result.lhr;
  const scores = Object.fromEntries(CATEGORIES.map((c) => [c, Math.round((lhr.categories[c].score ?? 0) * 100)]));
  rows.push(`${name.padEnd(26)} ${CATEGORIES.map((c) => `${c.replace('best-practices', 'best-pr.')}=${scores[c]}`).join('  ')}  LCP ${Math.round(lhr.audits['largest-contentful-paint'].numericValue)} ms  TBT ${Math.round(lhr.audits['total-blocking-time'].numericValue)} ms  CLS ${lhr.audits['cumulative-layout-shift'].numericValue.toFixed(3)}`);
  for (const c of CATEGORIES) {
    if (scores[c] < MIN) {
      failures.push(`${name}: ${c} ${scores[c]}`);
      const bad = lhr.categories[c].auditRefs.filter((a) => a.weight > 0 && lhr.audits[a.id].score !== null && lhr.audits[a.id].score < 0.9).map((a) => `${a.id} (${Math.round(lhr.audits[a.id].score * 100)})`);
      console.log(`  ${name} / ${c}: ${bad.join(', ')}`);
    }
  }
}
await browser.close();
if (server) server.close();
console.log(rows.join('\n'));
console.log(`minimum required: ${MIN} in every category`);
for (const f of failures) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
