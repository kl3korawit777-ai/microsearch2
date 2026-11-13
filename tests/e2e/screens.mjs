// Screenshots of design/prototype.html and the built site at 1440px and 390px, with a pixel-diff summary.
// Output: reports/screens/*.png (not committed). Run: npm run screens
import puppeteer from 'puppeteer-core';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { ROOT, buildSite, findChrome, serveSite } from './lib.mjs';

const OUT = join(ROOT, 'reports', 'screens');
const PAGES = [['home', 'home'], ['group', 'bacteria'], ['species', 'escherichia-coli']];
const SIZES = [[1440, 900], [390, 844]];
const SHOT_MAX = 2600; // px of the top of the page that is compared

mkdirSync(OUT, { recursive: true });
buildSite();
const { server, base } = await serveSite();
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox', '--disable-gpu'] });
const protoUrl = pathToFileURL(join(ROOT, 'design', 'prototype.html')).href;

async function shot(url, hash, w, h, file) {
  const page = await browser.newPage();
  await page.setViewport({ width: w, height: h });
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }, { name: 'prefers-reduced-motion', value: 'reduce' }]);
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('ms2.lang', 'th'); localStorage.setItem('ms2.theme', 'light'); } catch { /* ignore */ } });
  await page.goto(`${url}#${hash}`, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => document.querySelector('#view h1, #view .hero'));
  await page.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, 400));
  await page.screenshot({ path: file, fullPage: true, clip: undefined });
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.close();
  return height;
}

const rows = [];
for (const [w, h] of SIZES) {
  for (const [name, hash] of PAGES) {
    const a = join(OUT, `${name}-${w}-proto.png`);
    const b = join(OUT, `${name}-${w}-site.png`);
    const ha = await shot(protoUrl, hash, w, h, a);
    const hb = await shot(`${base}/index.html`, hash, w, h, b);
    // diff + montage rendered inside the browser (no image libraries needed)
    const page = await browser.newPage();
    const uri = (f) => `data:image/png;base64,${readFileSync(f).toString('base64')}`;
    await page.setContent('<body style="margin:0;background:#888"></body>');
    const stat = await page.evaluate(async (ua, ub, cap) => {
      const load = (u) => new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.src = u; });
      const [ia, ib] = await Promise.all([load(ua), load(ub)]);
      const W = Math.max(ia.width, ib.width);
      const H = Math.min(cap, Math.max(ia.height, ib.height));
      const mk = (img) => { const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, W, H); x.drawImage(img, 0, 0); return c; };
      const ca = mk(ia); const cb = mk(ib);
      const da = ca.getContext('2d').getImageData(0, 0, W, H).data;
      const db = cb.getContext('2d').getImageData(0, 0, W, H).data;
      const cd = document.createElement('canvas'); cd.width = W; cd.height = H;
      const dx = cd.getContext('2d'); const out = dx.createImageData(W, H);
      let diff = 0;
      for (let i = 0; i < da.length; i += 4) {
        const d = Math.max(Math.abs(da[i] - db[i]), Math.abs(da[i + 1] - db[i + 1]), Math.abs(da[i + 2] - db[i + 2]));
        const bad = d > 40;
        if (bad) diff++;
        out.data[i] = bad ? 220 : 245; out.data[i + 1] = bad ? 40 : 245; out.data[i + 2] = bad ? 60 : 245; out.data[i + 3] = 255;
      }
      dx.putImageData(out, 0, 0);
      const m = document.createElement('canvas'); m.width = W * 3 + 20; m.height = H;
      const mx = m.getContext('2d'); mx.fillStyle = '#888'; mx.fillRect(0, 0, m.width, H);
      mx.drawImage(ca, 0, 0); mx.drawImage(cb, W + 10, 0); mx.drawImage(cd, 2 * W + 20, 0);
      return { pct: (100 * diff) / (W * H), montage: m.toDataURL('image/png'), heights: [ia.height, ib.height] };
    }, uri(a), uri(b), SHOT_MAX);
    writeFileSync(join(OUT, `${name}-${w}-compare.png`), Buffer.from(stat.montage.split(',')[1], 'base64'));
    rows.push(`${name.padEnd(8)} ${String(w).padEnd(5)} proto ${String(ha).padStart(5)}px  site ${String(hb).padStart(5)}px  differing pixels (top ${SHOT_MAX}px): ${stat.pct.toFixed(1)}%`);
    await page.close();
  }
}
await browser.close();
server.close();
console.log(rows.join('\n'));
console.log(`images: ${OUT}`);
