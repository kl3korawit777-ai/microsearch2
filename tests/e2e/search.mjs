// e2e for site search and group filters: fixed queries, timing (< 100 ms), URL-backed filters. Run: npm run test:search
import puppeteer from 'puppeteer-core';
import { buildSite, findChrome, serveSite, readJson } from './lib.mjs';

const LIMIT_MS = 100;
const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

buildSite();
const { server, base } = await serveSite();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const meta = readJson('data/meta.json');
const index = readJson('data/index.json');
const groupData = Object.fromEntries(meta.groups.map((g) => [g.id, readJson(`data/${g.id}.json`).organisms]));

// ---------------------------------------------------------------- fixed queries
// first = expected id of the first result, has = ids that must appear, via = synonym label expected on a result
const QUERIES = [
  { q: 'Escherichia coli', first: 'escherichia-coli' },
  { q: 'ESCHERICHIA', first: 'escherichia-coli' },          // case-insensitive
  { q: 'escherichia', has: ['escherichia-coli'] },
  { q: 'bacil', has: ['bacillus-subtilis', 'bacillus-thuringiensis'] }, // prefix of a genus
  { q: 'bacillus subtilis', first: 'bacillus-subtilis' },
  { q: 'subtilis bacillus', first: 'bacillus-subtilis' },    // words in any order
  { q: 'ข้าวตอกฤๅษี', first: 'sphagnum-palustre' },           // Thai common name
  { q: 'สแฟกนัม', first: 'sphagnum-palustre' },               // Thai reading
  { q: 'ยีสต์', has: ['saccharomyces-cerevisiae'] },
  { q: 'saccharomyces', first: 'saccharomyces-cerevisiae' },
  { q: 'pisum', first: 'pisum-sativum' },
  { q: 'lathyrus oleraceus', first: 'pisum-sativum', via: 'Lathyrus oleraceus' },   // currently accepted name
  { q: 'bacterium coli', first: 'escherichia-coli', via: 'Bacterium coli' },        // synonym
  { q: 'limnospira', first: 'arthrospira-platensis' },
  { q: 'proteobacteria', has: ['escherichia-coli', 'vibrio-cholerae'] },             // lineage name
  { q: 'pseudomonadota', has: ['escherichia-coli'] },                                // new phylum name
  { q: 'enterobacteriaceae', has: ['escherichia-coli'] },                            // family
  { q: 'archaea', has: ['halobacterium-salinarum'] },                                // group name
  { q: 'rhizopus fungi', has: ['rhizopus-stolonifer'] },                           // words from different fields
  { q: 'black bread mold', first: 'rhizopus-stolonifer' },                         // English common name
  { q: "baker's yeast", first: 'saccharomyces-cerevisiae' },
  { q: 'whale shark', first: 'rhincodon-typus' },
  { q: 'homo sapiens', first: 'homo-sapiens' },
  { q: 'zzzzqq', none: true },
  { q: '   ', none: true },
];

async function runQueries(page, tag) {
  for (const c of QUERIES) {
    const out = await page.evaluate((q) => {
      const inp = document.getElementById('heroQ');
      inp.value = q;
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      return [...document.querySelectorAll('#heroQ-res a')].map((a) => ({ id: a.getAttribute('href').slice(1), via: a.querySelector('.r-via .sci')?.textContent || '' }));
    }, c.q);
    const label = `${tag} "${c.q}"`;
    if (c.none) { ok(out.length === 0, `${label}: expected no results, got ${out.map((x) => x.id)}`); continue; }
    ok(out.length > 0 && out.length <= 8, `${label}: ${out.length} results`);
    if (c.first) ok(out[0]?.id === c.first, `${label}: first is ${out[0]?.id}, expected ${c.first}`);
    for (const id of c.has || []) ok(out.some((x) => x.id === id), `${label}: missing ${id} in ${out.map((x) => x.id)}`);
    if (c.via) ok(out[0]?.via === c.via, `${label}: synonym label "${out[0]?.via}"`);
  }
}

// Time the synchronous search + render of the result list for many queries, optionally with a throttled CPU.
async function timing(page, tag) {
  const queries = ['e', 'es', 'esc', 'escherichia', 'bacillus', 'ยี', 'ยีสต์', 'proteobacteria', 'pseudomonadota', 'lathyrus', 'bacterium coli', 'a', 'o', 'zzzz', 'archaea fungi'];
  const times = await page.evaluate((qs) => {
    const inp = document.getElementById('heroQ');
    const out = [];
    for (let round = 0; round < 10; round++) {
      for (const q of qs) {
        const t0 = performance.now();
        inp.value = q;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        out.push(performance.now() - t0);
      }
    }
    return out;
  }, queries);
  const max = Math.max(...times);
  const p95 = [...times].sort((a, b) => a - b)[Math.floor(times.length * 0.95)];
  console.log(`${tag}: ${times.length} searches, p95 ${p95.toFixed(1)} ms, max ${max.toFixed(1)} ms`);
  ok(max < LIMIT_MS, `${tag}: slowest search ${max.toFixed(1)} ms >= ${LIMIT_MS} ms`);
}

// ---------------------------------------------------------------- group filters (reference implementation)
const TRAIT = { shapeF: 'shape', envF: 'env' };
const MERGE = { shapeF: { curvedspiral: ['curved', 'spiral'] }, envF: { hot: ['hot', 'hotacid'] } };
function expectedIds(g, sel) {
  const rows = index.filter((s) => s.g === g.id);
  const detail = Object.fromEntries(groupData[g.id].map((o) => [o.id, o]));
  return rows.filter((s) => {
    const o = detail[s.id];
    if (sel.ph !== undefined && s.p !== +sel.ph) return false;
    if (sel.lv && s.lv !== sel.lv) return false;
    if (sel.tag && !s.tags.includes(sel.tag)) return false;
    for (const fd of g.filters || []) {
      const v = sel[fd[0]];
      if (!v) continue;
      const merged = MERGE[fd[0]]?.[v];
      const val = o.traits[TRAIT[fd[0]] || fd[0]];
      if (merged ? !merged.includes(val) : val !== v) return false;
    }
    if (sel.q && !`${s.sci} ${s.th} ${s.rd} ${s.en}`.toLowerCase().includes(sel.q.toLowerCase())) return false;
    return true;
  }).map((s) => s.id).sort();
}

async function shownIds(page) {
  return (await page.$$eval('.rows .rowbtn', (b) => b.map((x) => x.getAttribute('data-v')))).sort();
}

const hashOf = (gid, sel) => `${gid}?${new URLSearchParams(sel)}`;

async function openGroup(page, gid, sel = {}) {
  await page.evaluate((h) => { document.documentElement.removeAttribute('data-ready'); location.hash = h; }, hashOf(gid, sel));
  await page.waitForFunction((g) => document.documentElement.getAttribute('data-ready') === g, { timeout: 10000 }, gid);
}

async function filterChecks(page) {
  for (const g of meta.groups) {
    const tag = `filters ${g.id}`;
    const sets = [['lv', [['hs'], ['uni']]], ...(g.filters || []).map((fd) => [fd[0], fd[2].map((o) => [o[0]])]), ['tag', meta.tags.map((t) => [t.key])]];
    // every single option, loaded straight from a URL
    for (const [key, opts] of sets) {
      for (const [val] of opts) {
        const sel = { [key]: val };
        await openGroup(page, g.id, sel);
        const got = await shownIds(page);
        const want = expectedIds(g, sel);
        ok(JSON.stringify(got) === JSON.stringify(want), `${tag} ?${key}=${val}: ${got.length} rows, expected ${want.length}`);
        ok((await page.$$eval(`.opt[data-k="${key}"][data-v="${val}"][aria-pressed="true"]`, (e) => e.length)) === 1, `${tag} ?${key}=${val}: option not shown as pressed`);
        ok((await page.$eval('#resH', (e) => e.textContent)).includes(String(want.length)), `${tag} ?${key}=${val}: count heading`);
      }
    }
    // combinations: level + one trait option + tag + phylum chip, all at once
    const trait = (g.filters || [])[0];
    for (const lv of ['hs', 'uni']) {
      for (const tg of meta.tags.slice(0, 3)) {
        const sel = { lv, tag: tg.key, ph: '0' };
        if (trait) sel[trait[0]] = trait[2][0][0];
        await openGroup(page, g.id, sel);
        const got = await shownIds(page);
        const want = expectedIds(g, sel);
        ok(JSON.stringify(got) === JSON.stringify(want), `${tag} combo ${JSON.stringify(sel)}: ${got.length} rows, expected ${want.length}`);
      }
    }
    // free text + a filter
    const text = index.find((s) => s.g === g.id).sci.split(' ')[0].slice(0, 4).toLowerCase();
    await openGroup(page, g.id, { q: text, lv: 'hs' });
    ok(JSON.stringify(await shownIds(page)) === JSON.stringify(expectedIds(g, { q: text, lv: 'hs' })), `${tag} q=${text}&lv=hs`);
    ok((await page.$eval('#gQ', (e) => e.value)) === text, `${tag}: search box shows the q from the URL`);
    // invalid values in the URL are ignored (all rows shown)
    await openGroup(page, g.id, { lv: 'zz', tag: 'nope', ph: '99' });
    ok((await shownIds(page)).length === index.filter((s) => s.g === g.id).length, `${tag}: invalid URL filters ignored`);
  }

  // clicking updates the URL (replace, no history entry), reload keeps the state, clear removes it
  await openGroup(page, 'bacteria');
  const histBefore = await page.evaluate(() => history.length);
  await page.click('.opt[data-k="gram"][data-v="pos"]');
  await page.click('.opt[data-k="lv"][data-v="hs"]');
  await page.click('.opt[data-k="tag"][data-v="medicine"]');
  let hash = await page.evaluate(() => location.hash);
  ok(hash === '#bacteria?lv=hs&gram=pos&tag=medicine', `URL after clicks: ${hash}`);
  ok((await page.evaluate(() => history.length)) === histBefore, 'filter clicks do not add history entries');
  await page.reload({ waitUntil: 'load' });
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'bacteria');
  ok(JSON.stringify(await shownIds(page)) === JSON.stringify(expectedIds(meta.groups[0], { lv: 'hs', gram: 'pos', tag: 'medicine' })), 'combined filters survive reload');
  await page.click('.opt[data-k="gram"][data-v="pos"]'); // toggles off
  hash = await page.evaluate(() => location.hash);
  ok(hash === '#bacteria?lv=hs&tag=medicine', `URL after toggling a filter off: ${hash}`);
  await page.type('#gQ', 'bac');
  ok((await page.evaluate(() => location.hash)).includes('q=bac'), 'typed search text goes into the URL');
  await page.click('[data-act="fclear"]');
  ok((await page.evaluate(() => location.hash)) === '#bacteria', 'clear removes every filter from the URL');
  // switching language keeps the filters
  await openGroup(page, 'bacteria', { gram: 'neg' });
  await page.click('[data-lang="en"]');
  await page.waitForFunction(() => document.documentElement.lang === 'en');
  ok((await page.evaluate(() => location.hash)) === '#bacteria?gram=neg', 'language switch keeps filters in the URL');
  await page.click('[data-lang="th"]');
}

// ---------------------------------------------------------------- run
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900 });
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
page.on('console', (m) => { if (m.type() === 'error' && (m.location()?.url || '').startsWith(base)) errs.push(m.text()); });
await page.goto(`${base}/#home`, { waitUntil: 'load' });
await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');

await runQueries(page, '[th]');
await timing(page, 'search timing');
const cdp = await page.createCDPSession();
await cdp.send('Emulation.setCPUThrottlingRate', { rate: 6 }); // a slow phone
await timing(page, 'search timing, CPU 6x slower');
await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
await page.evaluate(() => { document.getElementById('heroQ').value = ''; });

await filterChecks(page);

// English mode: same queries work, and the UI shows no Thai
await page.click('[data-lang="en"]');
await page.waitForFunction(() => document.documentElement.lang === 'en');
await page.evaluate(() => { document.documentElement.removeAttribute('data-ready'); location.hash = 'home'; });
await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
await runQueries(page, '[en]');
ok(errs.length === 0, `errors: ${errs.slice(0, 3).join(' | ')}`);
await browser.close();
server.close();
console.log(`checks: ${checks}, failures: ${failures.length}`);
for (const f of failures.slice(0, 40)) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
