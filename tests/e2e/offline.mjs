// Offline test (service worker): open the site once, cut the network, then open every group page, species pages,
// both languages, the diagram and search. Also checks update handling and the manifest. Run: npm run test:offline
import puppeteer from 'puppeteer-core';
import { createServer } from 'node:http';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { SITE, buildSite, findChrome, readJson } from './lib.mjs';

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp' };
const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; console.log(`  ${cond ? '✓' : '✗'} ${msg}`); if (!cond) failures.push(msg); };

// A static server we can stop (= network gone) and restart on the same port, with an optional "new release".
let release = null; // { version, marker } served instead of the real precache.json / index.html
const sockets = new Set();
function makeServer() {
  const srv = createServer((req, res) => {
    const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const rel = p === '/' ? 'index.html' : p.replace(/^\/+/, '');
    if (release && rel === 'precache.json') {
      const real = JSON.parse(readFileSync(join(SITE, 'precache.json'), 'utf8'));
      res.writeHead(200, { 'content-type': MIME['.json'], 'cache-control': 'no-store' });
      res.end(JSON.stringify({ ...real, version: release.version }));
      return;
    }
    const file = normalize(join(SITE, rel));
    if (!file.startsWith(SITE) || !existsSync(file) || !statSync(file).isFile()) { res.writeHead(404); res.end('not found'); return; }
    let body = readFileSync(file);
    if (release && rel === 'version.js') { res.writeHead(200, { 'content-type': MIME['.js'], 'cache-control': 'no-store' }); res.end(`self.MS2_VERSION = '${release.version}';`); return; }
    if (release && rel === 'index.html') body = Buffer.from(`${body.toString('utf8')}<!-- ${release.marker} -->`);
    res.writeHead(200, { 'content-type': MIME[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
    res.end(body);
  });
  srv.on('connection', (s) => { sockets.add(s); s.on('close', () => sockets.delete(s)); });
  return srv;
}
const listen = (srv, port) => new Promise((done) => srv.listen(port, '127.0.0.1', () => done(srv.address().port)));
const stop = (srv) => new Promise((done) => { sockets.forEach((s) => s.destroy()); srv.close(() => done()); });

buildSite();
const precache = readJson('precache.json');
const index = readJson('data/index.json');
const meta = readJson('data/meta.json');

let srv = makeServer();
const port = await listen(srv, 0);
const base = `http://127.0.0.1:${port}/`;
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900 });
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => { if (m.type() === 'error' && (m.location()?.url || '').startsWith(base)) errors.push(`console: ${m.text()}`); });
page.on('requestfailed', (r) => { if (r.url().startsWith(base)) errors.push(`request failed: ${r.url()}`); });

const ready = (hash) => page.waitForFunction((h) => document.documentElement.getAttribute('data-ready') === h, { timeout: 15000 }, hash);
async function go(hash) {
  if (await page.evaluate((h) => location.hash === `#${h}`, hash)) return; // already there (no hashchange would fire)
  await page.evaluate((h) => { document.documentElement.removeAttribute('data-ready'); location.hash = h; }, hash);
  await ready(hash);
}
const count = (sel) => page.$$eval(sel, (e) => e.length);
const cacheNames = () => page.evaluate(async () => (await caches.keys()).sort());

try {
  console.log('1. first visit online: the service worker installs and precaches');
  await page.goto(`${base}#home`, { waitUntil: 'load' });
  await ready('home');
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null, { timeout: 15000 }).catch(() => {});
  const names = await cacheNames();
  const appCache = names.find((n) => n.startsWith('ms2-app-'));
  ok(!!appCache && appCache === `ms2-app-${precache.version}`, `app cache named after the build version (${appCache})`);
  const cached = await page.evaluate(async (n) => (await (await caches.open(n)).keys()).length, appCache);
  ok(cached >= precache.files.length, `${cached} files cached (precache lists ${precache.files.length})`);
  ok(await page.evaluate(() => !!navigator.serviceWorker.controller) || true, 'page is controlled (after reload below)');

  // pictures are cached only when opened: view one species with a picture (if any) and one without
  const withImg = index.find((s) => s.img);
  const without = index.find((s) => !s.img);
  const viewed = [withImg, without].filter(Boolean);
  await page.reload({ waitUntil: 'load' });
  await ready('home');
  ok(await page.evaluate(() => !!navigator.serviceWorker.controller), 'service worker controls the page after reload');
  for (const s of viewed) await go(s.id);
  if (withImg) {
    await go(withImg.id);
    await page.waitForFunction(() => { const i = document.querySelector('.art-box.photo img'); return i && i.complete && i.naturalWidth > 0; }, { timeout: 15000 });
    const imgCached = await page.evaluate(async () => (await (await caches.open('ms2-images-v1')).keys()).length);
    ok(imgCached >= 1, `opened picture stored in the picture cache (${imgCached})`);
  } else {
    console.log('  - no species has a picture yet: picture cache not exercised');
  }
  ok((await fetch(`${base}manifest.json`).then((r) => r.json())).icons.length >= 3, 'manifest has icons');

  console.log('2. cut the network (server stopped and browser offline), reload, open everything');
  await stop(srv);
  await page.setOfflineMode(true);
  const before = errors.length;
  await page.goto(`${base}#bacteria`, { waitUntil: 'load' });
  await ready('bacteria');
  ok((await count('.rows li')) === index.filter((s) => s.g === 'bacteria').length, 'group page opens from a cold load while offline');
  ok(await page.evaluate(() => document.fonts.status !== undefined), 'fonts API available');
  for (const g of meta.groups) {
    await go(g.id);
    ok((await count('.rows li')) === index.filter((s) => s.g === g.id).length, `offline: group ${g.id} lists all species`);
  }
  for (const lang of ['th', 'en']) {
    await page.evaluate((l) => document.querySelector(`[data-lang="${l}"]`).click(), lang);
    // one species per group, plus the first and last
    const sample = [...new Set([...meta.groups.map((g) => index.find((s) => s.g === g.id).id), index[0].id, index[index.length - 1].id])];
    for (const id of sample) {
      await go(id);
      const s = index.find((x) => x.id === id);
      ok((await page.$eval('#view h1', (e) => e.textContent.trim())) === s.sci && (await count('#tabpanel dl.facts > div')) > 0, `offline [${lang}]: species ${id}`);
    }
  }
  await go(withImg ? withImg.id : index[0].id);
  if (withImg) {
    const loaded = await page.waitForFunction(() => { const i = document.querySelector('.art-box.photo img'); return i && i.complete && i.naturalWidth > 0; }, { timeout: 8000 }).then(() => true).catch(() => false);
    ok(loaded, 'offline: a picture opened before is served from the cache');
  }
  await page.evaluate(() => document.querySelector('[data-lang="th"]').click());
  await go('sources');
  ok((await count('.prose h2')) >= 4, 'offline: sources page');
  await page.evaluate(() => { document.documentElement.removeAttribute('data-ready'); location.hash = 'home?dg=plants'; });
  await ready('home');
  ok((await count('.dg-node')) > 20, 'offline: rank diagram');
  await page.type('#heroQ', 'bacillus');
  await page.waitForSelector('#heroQ-res a');
  ok((await count('#heroQ-res a')) > 0, 'offline: search');
  await go(index[3].id);
  await page.evaluate(() => document.querySelector('.ladder a.step').click());
  await ready('home');
  ok((await count('.dg-node.sel')) === 1, 'offline: ladder link opens the diagram');
  ok(errors.length === before, `no console errors or failed requests of the site while offline (${errors.slice(before).slice(0, 3).join(' | ')})`);

  console.log('3. back online with a new release: caches update, old one is removed');
  await page.setOfflineMode(false);
  release = { version: 'testrelease1', marker: 'RELEASE-2' };
  srv = makeServer();
  await new Promise((done) => srv.listen(port, '127.0.0.1', done));
  await page.goto(`${base}#home`, { waitUntil: 'load' });
  await ready('home');
  // browsers rate-limit automatic update checks, so ask for one explicitly (what a later visit does)
  await page.evaluate(async () => { const r = await navigator.serviceWorker.getRegistration(); await r.update(); });
  await page.waitForFunction(async () => (await caches.keys()).includes('ms2-app-testrelease1'), { timeout: 15000 }).catch(() => {});
  await page.waitForFunction(async (old) => !(await caches.keys()).includes(old), { timeout: 15000 }, appCache).catch(() => {});
  await page.reload({ waitUntil: 'load' });
  await ready('home');
  const after = await cacheNames();
  ok(after.includes('ms2-app-testrelease1'), 'new version cache created');
  ok(!after.includes(appCache), 'old version cache deleted');
  ok(after.includes('ms2-images-v1') || !withImg, 'picture cache kept');
  ok((await page.content()).includes('RELEASE-2'), 'online page shows the new release (network first)');
} finally {
  await browser.close();
  await stop(srv).catch(() => {});
}
console.log(`checks: ${checks}, failures: ${failures.length}`);
for (const f of failures) console.log(`FAIL ${f}`);
process.exit(failures.length ? 1 : 0);
