// e2e for the rank diagram: click every name of all 6 groups in both languages. Run: npm run test:diagram
import puppeteer from 'puppeteer-core';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SITE, buildSite, findChrome, serveSite, readJson } from './lib.mjs';

const THAI = /[฀-๿]/;
const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

buildSite();
const { server, base } = await serveSite();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const meta = readJson('data/meta.json');
const strings = { th: JSON.parse(readFileSync(join(SITE, 'i18n', 'th.json'), 'utf8')), en: JSON.parse(readFileSync(join(SITE, 'i18n', 'en.json'), 'utf8')) };

// Expected tree for a group, computed straight from the data file: key (path joined by "/") -> species count
function expectedNodes(gid) {
  const { organisms, taxa } = readJson(`data/${gid}.json`);
  const counts = new Map();
  for (const o of organisms) {
    const names = o.lineage.map((x) => x.name);
    names.forEach((_, i) => { const k = names.slice(0, i + 1).join('/'); counts.set(k, (counts.get(k) || 0) + 1); });
  }
  return { counts, taxa };
}

// Open the home page showing group `gid`; wait until the diagram of that group is rendered
// (a hash-only navigation keeps the old document, so data-ready alone would match the previous group).
async function open(page, hash, gid) {
  await page.goto(`${base}/#${hash}`, { waitUntil: 'load' });
  await page.waitForFunction((g) => document.documentElement.getAttribute('data-ready') === 'home' && document.querySelector('.dg-chip[aria-pressed="true"]')?.dataset.v === g, { timeout: 15000 }, gid);
}

const panelScan = (page) => page.evaluate(() => {
  const re = /[฀-๿]/;
  const out = { leaks: [], fallback: 0 };
  for (const root of document.querySelectorAll('.dg, #dgPanel')) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (!re.test(n.nodeValue)) continue;
      if (n.parentElement.closest('.th-fb')) out.fallback++; else out.leaks.push(n.nodeValue.trim().slice(0, 50));
    }
    for (const e of root.querySelectorAll('[aria-label],[title]')) {
      for (const a of ['aria-label', 'title']) { const v = e.getAttribute(a); if (v && re.test(v)) out.leaks.push(`${a}: ${v.slice(0, 50)}`); }
    }
  }
  return out;
});

let clicked = 0;
let enFallback = 0;
for (const lang of ['th', 'en']) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]); // no smooth scrolling while clicking
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error' && (m.location()?.url || '').startsWith(base)) errs.push(m.text()); });
  await page.evaluateOnNewDocument((l) => { if (!sessionStorage.getItem('i')) { sessionStorage.setItem('i', '1'); localStorage.setItem('ms2.lang', l); } }, lang);

  for (const g of meta.groups) {
    const tag = `[${lang}] ${g.id}`;
    const { counts, taxa } = expectedNodes(g.id);
    await open(page, `home?dg=${g.id}`, g.id);
    const nodes = await page.$$eval('.dg-node', (els) => els.map((e) => ({ key: e.dataset.v, k: e.dataset.k, level: +e.dataset.level, parent: e.dataset.parent, label: e.querySelector('.dg-l').textContent })));
    ok(nodes.length === counts.size && nodes.every((n) => counts.has(n.key)), `${tag}: diagram nodes ${nodes.length} != ${counts.size} in data`);
    ok((await page.$$eval('.dg-rank', (e) => e.length)) === g.ranks.length, `${tag}: rank headings`);
    ok((await page.$eval('#dgPanel', (e) => e.textContent)).includes(strings[lang].dgPick.slice(0, 12)), `${tag}: empty panel prompt`);

    for (const nd of nodes) {
      const label = `${tag} ${nd.key}`;
      await page.click(`.dg-node[data-k="${nd.k}"]`);
      await page.waitForFunction((k) => document.querySelector('.dg-node.sel')?.dataset.k === k, { timeout: 10000 }, nd.k);
      clicked++;
      const p = await page.evaluate(() => {
        const q = (s) => document.querySelector(s);
        return {
          text: q('#dgPanel').textContent,
          h3: q('#dgPanel h3')?.textContent.trim(),
          desc: q('.dg-desc')?.textContent.trim() || '',
          crumbs: document.querySelectorAll('.dg-crumb').length,
          sibs: document.querySelectorAll('.dg-sibs li').length,
          species: document.querySelectorAll('.dg-list a').length,
          read: q('.dg-read')?.textContent.trim() || '',
          hasNote: !!q('.dg-note'),
          url: location.hash,
        };
      });
      const name = nd.key.split('/').pop();
      const isGenus = nd.level === g.ranks.length - 1;
      ok(!p.text.includes(strings[lang].dgNoInfo), `${label}: shows "${strings[lang].dgNoInfo}"`);
      ok(p.h3 === (name === '?' ? strings[lang].unplaced : name), `${label}: heading "${p.h3}"`);
      ok(p.species === counts.get(nd.key), `${label}: ${p.species} species listed, expected ${counts.get(nd.key)}`);
      ok(p.crumbs === nd.level, `${label}: ${p.crumbs} breadcrumb names, expected ${nd.level}`);
      ok(p.url.includes('sel='), `${label}: selection not in URL`);
      const siblings = nodes.filter((o) => o.parent === nd.parent && o.k !== nd.k).length;
      if (nd.parent) ok(p.sibs === siblings && (siblings > 0 || p.hasNote), `${label}: sibling cards ${p.sibs} != ${siblings}`);
      if (!isGenus) {
        const t = taxa[name];
        const wants = name === '?' ? 'x' : lang === 'en' ? t?.about_en : t?.about_th;
        ok(p.desc.length > 0 && !!wants, `${label}: no description`);
      }
      if (lang === 'th' && name !== '?' && taxa[name]?.reading_th) ok(p.read.includes(taxa[name].reading_th), `${label}: reading "${p.read}"`);
      if (lang === 'en') {
        const r = await panelScan(page);
        ok(r.leaks.length === 0, `${label}: Thai in English UI: ${r.leaks.slice(0, 2).join(' | ')}`);
        enFallback += r.fallback;
        ok(r.fallback === 0, `${label}: Thai fallback text in the English diagram`);
      }
    }

    // toggle, clear button, Escape, reload keeps the selection (URL state)
    const first = nodes[nodes.length - 1];
    await page.click(`.dg-node[data-k="${first.k}"]`); // currently selected -> deselects
    await page.waitForFunction(() => !document.querySelector('.dg-node.sel'));
    ok(!(await page.url()).includes('sel='), `${tag}: second click clears selection from URL`);
    await page.click(`.dg-node[data-k="${first.k}"]`);
    await page.waitForFunction(() => !!document.querySelector('.dg-node.sel'));
    await page.reload({ waitUntil: 'load' });
    await page.waitForFunction(() => document.documentElement.getAttribute('data-ready') === 'home');
    ok((await page.$$eval('.dg-node.sel', (e) => e.length)) === 1, `${tag}: selection survives reload`);
    await page.click('.dg-panel-head .btn');
    await page.waitForFunction(() => !document.querySelector('.dg-node.sel'));
    ok((await page.$$eval('.dg-node.dim', (e) => e.length)) === 0, `${tag}: clear removes dimming`);
  }

  // keyboard: arrows move between nodes, Enter selects, Escape clears; hover highlights the path
  await open(page, 'home?dg=bacteria', 'bacteria');
  const rootBtn = await page.$('.dg-node.root');
  await rootBtn.focus();
  await page.keyboard.press('ArrowRight');
  const child = await page.evaluate(() => ({ parent: document.activeElement.dataset.parent, level: document.activeElement.dataset.level }));
  const rootK = await page.$eval('.dg-node.root', (e) => e.dataset.k);
  ok(child.parent === rootK && child.level === '1', `[${lang}] ArrowRight moves to the first child`);
  await page.keyboard.press('ArrowDown');
  ok((await page.evaluate(() => document.activeElement.dataset.level)) === '1', `[${lang}] ArrowDown stays on the same rank`);
  await page.keyboard.press('ArrowLeft');
  ok((await page.evaluate(() => document.activeElement.dataset.k)) === rootK, `[${lang}] ArrowLeft returns to the parent`);
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => !!document.querySelector('.dg-node.sel'));
  ok((await page.$$eval('.dg-node.sel', (e) => e.length)) === 1, `[${lang}] Enter selects the focused name`);
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.querySelector('.dg-node.sel'));
  await page.waitForFunction(() => document.activeElement?.classList.contains('dg-node')); // Escape returns focus to the diagram
  await page.mouse.move(5, 5);
  await page.evaluate(() => document.activeElement.blur());
  await page.waitForFunction(() => document.querySelectorAll('.dg-node.hl').length === 0);
  const leaf = await page.$('.dg-node.leaf');
  await leaf.hover();
  await page.waitForFunction(() => document.querySelectorAll('.dg-node.hl').length >= 4, { timeout: 3000 }).catch(() => {});
  ok((await page.$$eval('.dg-node.hl', (e) => e.length)) >= 4, `[${lang}] hover highlights the path from the domain`);
  await page.mouse.move(5, 5);
  await page.waitForFunction(() => document.querySelectorAll('.dg-node.hl').length === 0, { timeout: 3000 }).catch(() => {});
  ok((await page.$$eval('.dg-node.hl', (e) => e.length)) === 0, `[${lang}] highlight clears after hover`);
  ok(errs.length === 0, `[${lang}] errors: ${errs.slice(0, 3).join(' | ')}`);
  await page.close();
}

await browser.close();
server.close();
console.log(`names clicked: ${clicked} (6 groups x 2 languages), checks: ${checks}, failures: ${failures.length}`);
console.log(`English diagram: ${enFallback} Thai fallback blocks (expected 0)`);
for (const f of failures.slice(0, 40)) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
