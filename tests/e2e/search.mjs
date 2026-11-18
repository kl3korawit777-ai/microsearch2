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

// ---------------------------------------------------------------- hero search box: clear, retype, recent
const ids = (page) => page.$$eval('#heroQ-res a', (a) => a.map((x) => x.getAttribute('href').slice(1)));
const state = (page) => page.evaluate(() => ({
  value: document.getElementById('heroQ').value,
  focused: document.activeElement?.id === 'heroQ',
  open: !document.getElementById('heroQ-res').hidden,
  clearShown: !document.querySelector('.s-clear').hidden,
}));
const settle = (page) => new Promise((r) => setTimeout(r, 250)); // the list closes 120 ms after a blur

async function searchBoxChecks(page, tag, words) {
  const label = (m) => `${tag} box: ${m}`;
  await page.evaluate(() => { try { localStorage.removeItem('ms2.recent'); } catch { /* none */ } });
  await page.evaluate(() => {
    const inp = document.getElementById('heroQ');
    inp.value = ''; // earlier checks left text behind
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.blur();
  });
  await settle(page);
  await page.click('#heroQ');
  let st = await state(page);
  ok(st.value === '' && !st.clearShown, label('empty field shows no × button'));
  const chips = await page.$$eval('#heroQ-res .chip', (c) => c.map((x) => x.dataset.q));
  ok(st.open && (await ids(page)).length === 0 && chips.length >= 40, label(`empty field, no history: list open with ${chips.length} suggestions and no recent items`));
  ok((await page.$$('#heroQ-res [data-act="clear-recent"]')).length === 0, label('no clear-history link without history'));
  // every suggested word finds something, and clicking one fills the field and shows its results
  for (const w of chips) {
    const n = await page.evaluate((q) => {
      const inp = document.getElementById('heroQ');
      inp.value = q; inp.dispatchEvent(new Event('input', { bubbles: true }));
      const c = document.querySelectorAll('#heroQ-res a').length;
      inp.value = ''; inp.dispatchEvent(new Event('input', { bubbles: true }));
      return c;
    }, w);
    ok(n > 0, label(`suggestion "${w}" has no results`));
  }
  await page.click('#heroQ-res .chip');
  st = await state(page);
  ok(st.value === chips[0] && st.focused && st.open && (await ids(page)).length > 0 && st.clearShown, label(`clicking a suggestion searches it ${JSON.stringify(st)}`));
  await page.click('.s-clear');
  ok(!(await state(page)).open, label('list closed after ×'));
  await page.click('#heroQ'); // field still focused: a click reopens the suggestions
  ok((await state(page)).open && (await page.$$('#heroQ-res .chip')).length > 0, label('clicking the focused empty field reopens the list'));
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
  ok(!(await state(page)).open, label('Esc closes the list'));
  await page.keyboard.press('ArrowDown');
  ok((await state(page)).open, label('arrow down reopens a closed list'));
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  ok((await state(page)).value === chips[0], label('arrow + Enter picks the first suggestion'));
  await page.click('.s-clear');
  await page.evaluate(() => document.activeElement.blur());
  await settle(page);

  // type, find, clear with ×
  await page.type('#heroQ', words.first);
  st = await state(page);
  ok(st.open && (await ids(page)).length > 0 && st.clearShown, label(`"${words.first}" gives results and the × button`));
  const box = await page.$eval('.s-clear', (b) => { const r = b.getBoundingClientRect(); return [r.width, r.height, b.getAttribute('aria-label')]; });
  ok(box[0] >= 44 && box[1] >= 44 && box[2], label(`× button is ${box[0]}x${box[1]} with label "${box[2]}"`));
  ok(await page.$eval('#heroQ-res .r-head', (e) => /\d/.test(e.textContent)), label('result list starts with a count line'));
  await page.click('.s-clear');
  st = await state(page);
  ok(st.value === '' && st.focused && !st.open && !st.clearShown, label(`× clears, keeps focus, closes the list ${JSON.stringify(st)}`));

  // retype right away
  await page.keyboard.type(words.second);
  const secondIds = await ids(page);
  ok(secondIds.includes('aedes-aegypti'), label(`"${words.second}" lists aedes-aegypti: ${secondIds}`));
  ok(await page.$eval('#heroQ-res mark', (m) => m.textContent.length > 0).catch(() => false), label('matching text is wrapped in <mark>'));

  // delete one character at a time down to two characters, results follow
  const firstIds = secondIds;
  let changed = false;
  while ((await state(page)).value.length > words.keep) {
    await page.keyboard.press('Backspace');
    const now = await ids(page);
    if (JSON.stringify(now) !== JSON.stringify(firstIds)) changed = true;
    ok(now.length > 0 || (await state(page)).value.length === 0, label('results stay in step while deleting'));
  }
  ok(changed, label('deleting characters changed the results'));
  const shortQ = (await state(page)).value;
  ok(shortQ.length === words.keep && (await ids(page)).length > 0, label(`left with "${shortQ}": ${(await ids(page)).length} results`));

  // Esc clears and keeps focus; Esc again closes nothing more
  await page.keyboard.press('Escape');
  st = await state(page);
  ok(st.value === '' && st.focused && !st.open, label('Esc clears the text, keeps focus'));

  // choose a species, go back, the query is still there and the list reopens
  await page.keyboard.type(words.second);
  await page.click('#heroQ-res a[href="#aedes-aegypti"]');
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'aedes-aegypti');
  await page.goBack();
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
  st = await state(page);
  ok(st.value === words.second && st.focused && st.open, label(`back to home keeps "${words.second}", focus and list ${JSON.stringify(st)}`));
  ok((await ids(page)).includes('aedes-aegypti'), label('the earlier list is back'));

  // empty field + focus: recently opened
  await page.click('.s-clear');
  await page.evaluate(() => document.activeElement.blur());
  await settle(page);
  await page.focus('#heroQ');
  st = await state(page);
  ok(st.open && (await ids(page))[0] === 'aedes-aegypti', label(`empty + focus lists recent: ${await ids(page)}`));
  ok((await page.$eval('#heroQ-res .r-head', (e) => e.textContent)).length > 0, label('recent list has a heading'));
  await page.keyboard.press('ArrowDown');
  ok(await page.$eval('#heroQ-res a.active', (a) => a.getAttribute('href') === '#aedes-aegypti'), label('arrow key selects a recent item'));
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'aedes-aegypti');
  await page.goBack();
  await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');

  // clear history (the field is already empty after the Enter on a recent item)
  ok((await state(page)).value === '', label('field stays empty after opening a recent item'));
  await page.evaluate(() => document.activeElement.blur());
  await settle(page);
  await page.focus('#heroQ');
  await page.click('#heroQ-res [data-act="clear-recent"]');
  st = await state(page);
  ok((await ids(page)).length === 0, label('clearing the history empties the recent items'));
  await page.evaluate(() => document.activeElement.blur());
  await settle(page);
  await page.focus('#heroQ');
  ok((await ids(page)).length === 0, label('no history after clearing it'));

  await page.evaluate(() => { document.activeElement.blur(); });
}

// localStorage that throws on every call: the box still searches, opens species, and shows no history
async function noStorageChecks(page) {
  const p2 = await page.browser().newPage();
  const errs2 = [];
  p2.on('pageerror', (e) => errs2.push(e.message));
  await p2.evaluateOnNewDocument(() => {
    const boom = () => { throw new Error('storage blocked'); };
    Storage.prototype.getItem = boom; Storage.prototype.setItem = boom; Storage.prototype.removeItem = boom;
  });
  await p2.setViewport({ width: 1280, height: 900 });
  await p2.goto(`${base}/#home`, { waitUntil: 'load' });
  await p2.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
  await p2.type('#heroQ', 'ยุง');
  ok((await ids(p2)).includes('aedes-aegypti'), 'no storage: search still lists results');
  await p2.click('#heroQ-res a[href="#aedes-aegypti"]');
  await p2.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'aedes-aegypti');
  await p2.goBack();
  await p2.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
  await p2.click('.s-clear');
  await p2.evaluate(() => document.activeElement.blur());
  await settle(p2);
  await p2.focus('#heroQ');
  ok((await ids(p2)).length === 0, 'no storage: no history items, no error');
  ok(errs2.length === 0, `no storage: page errors ${errs2.slice(0, 2)}`);
  await p2.close();
}

// ---------------------------------------------------------------- typing hint animation
const THAI = /[\u0E00-\u0E7F]/;
const hintText = (page) => page.$eval('.s-hint-txt', (e) => e.textContent);
const hintOn = (page) => page.$eval('#heroQ', (i) => i.closest('.search').classList.contains('hint-on'));
async function sample(page, ms, every = 60) {
  const seen = [];
  const end = Date.now() + ms;
  while (Date.now() < end) { seen.push(await hintText(page)); await new Promise((r) => setTimeout(r, every)); }
  return seen;
}
// A Thai text that is cut off must end on a whole character: no sample may start with a vowel or tone mark.
const COMBINING = /^[\u0E31\u0E34-\u0E3A\u0E47-\u0E4E]/;

async function hintChecks(browserRef) {
  const open = async (opts = {}) => {
    const pg = await browserRef.newPage();
    await pg.setViewport({ width: opts.width || 1280, height: 900 });
    if (opts.reduced) await pg.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    const e = [];
    pg.on('pageerror', (x) => e.push(x.message));
    pg.on('console', (m) => { if (m.type() === 'error' && (m.location()?.url || '').startsWith(base)) e.push(m.text()); });
    await pg.goto(`${base}/#home`, { waitUntil: 'load' });
    await pg.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
    return { pg, e };
  };

  // Thai: text really changes, hint disappears on focus, search still works, comes back after blur
  let { pg, e } = await open();
  ok(await hintOn(pg), 'hint: shown on a fresh empty home page');
  ok(await pg.$eval('.s-hint', (h) => h.getAttribute('aria-hidden') === 'true' && getComputedStyle(h).pointerEvents === 'none'), 'hint: aria-hidden and pointer-events none');
  ok((await pg.$eval('#heroQ', (i) => i.getAttribute('aria-label'))) !== null, 'hint: input has a fixed aria-label');
  ok((await pg.$$('.s-hint-pre')).length === 0, 'hint: shows the name only, no lead-in text');
  const seen = await sample(pg, 3000);
  const distinct = new Set(seen);
  ok(distinct.size >= 3 && seen.some((t) => t.length > 0), `hint: text changes within 3 s (${distinct.size} different values)`);
  ok(seen.every((t) => !COMBINING.test(t)), 'hint: Thai text never starts on a vowel or tone mark');
  await pg.click('#heroQ'); // clicking over the animated text lands in the field
  ok(await pg.evaluate(() => document.activeElement.id === 'heroQ'), 'hint: click focuses the field');
  ok(await hintOn(pg), 'hint: keeps playing while the focused field is empty');
  ok(new Set(await sample(pg, 2600)).size >= 2, 'hint: still animating after the field is focused');
  await pg.keyboard.type('bacil');
  ok((await ids(pg)).includes('bacillus-subtilis'), 'hint: normal search still works after the hint');
  ok(!(await hintOn(pg)), 'hint: hidden while there is text');
  await pg.click('.s-clear');
  await new Promise((r) => setTimeout(r, 900));
  ok(!(await hintOn(pg)), 'hint: waits before coming back after the field is cleared');
  await new Promise((r) => setTimeout(r, 1500));
  ok(await hintOn(pg), 'hint: back once the field is empty again');
  ok(new Set(await sample(pg, 3500)).size >= 2, 'hint: animating again after clearing'); // long enough to cross a 1.6 s hold
  await pg.keyboard.type('x');
  ok(!(await hintOn(pg)), 'hint: hidden again by typing');
  await pg.keyboard.press('Backspace');
  await new Promise((r) => setTimeout(r, 1900));
  ok(await hintOn(pg), 'hint: back after deleting the text by hand');

  // leaving the home page stops every timer
  await pg.evaluate(() => { location.hash = 'aedes-aegypti'; });
  await pg.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'aedes-aegypti');
  ok(!(await pg.evaluate(async () => (await import('./js/typing-hint.js')).hintActive())), 'hint: no animation left after leaving home');
  await new Promise((r) => setTimeout(r, 1200));
  ok(e.length === 0, `hint: no console errors after leaving home ${e.slice(0, 2)}`);

  // English: no Thai anywhere in the hint
  await pg.evaluate(() => { location.hash = 'home'; });
  await pg.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
  await pg.click('[data-lang="en"]');
  await pg.waitForFunction(() => document.documentElement.lang === 'en');
  await pg.waitForSelector('.search.hint-on');
  const enSeen = await sample(pg, 6000, 80);
  ok(new Set(enSeen).size >= 4, `hint [en]: ${new Set(enSeen).size} different values`);
  ok(!enSeen.some((t) => THAI.test(t)), 'hint [en]: no Thai text');
  await pg.close();

  // reduced motion: still text, never changes
  ({ pg, e } = await open({ reduced: true }));
  const still = await hintText(pg);
  await new Promise((r) => setTimeout(r, 2500));
  ok(still.length > 0 && (await hintText(pg)) === still, `hint: reduced motion shows fixed text "${still}"`);
  ok(await hintOn(pg), 'hint: reduced motion text is visible');
  await pg.close();

  // phone width: the text stays inside the field
  ({ pg } = await open({ width: 390 }));
  await pg.waitForFunction(() => document.querySelector('.s-hint-txt').textContent.length > 8, { timeout: 8000 }).catch(() => {});
  const fit = await pg.evaluate(() => {
    const box = document.querySelector('#heroQ').getBoundingClientRect();
    const h = document.querySelector('.s-hint').getBoundingClientRect();
    return { inside: h.left >= box.left && h.right <= box.right, over: document.documentElement.scrollWidth > innerWidth };
  });
  ok(fit.inside && !fit.over, `hint: fits at 390 px ${JSON.stringify(fit)}`);
  await pg.close();
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
await searchBoxChecks(page, '[th]', { first: 'เห็ด', second: 'ยุง', keep: 1 });

await noStorageChecks(page);
await hintChecks(browser);
await filterChecks(page);

// English mode: same queries work, and the UI shows no Thai
await page.click('[data-lang="en"]');
await page.waitForFunction(() => document.documentElement.lang === 'en');
await page.evaluate(() => { document.documentElement.removeAttribute('data-ready'); location.hash = 'home'; });
await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
await runQueries(page, '[en]');
await searchBoxChecks(page, '[en]', { first: 'mushroom', second: 'mosquito', keep: 2 });
await timing(page, 'search timing [en]');
ok(errs.length === 0, `errors: ${errs.slice(0, 3).join(' | ')}`);
await browser.close();
server.close();
console.log(`checks: ${checks}, failures: ${failures.length}`);
for (const f of failures.slice(0, 40)) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
