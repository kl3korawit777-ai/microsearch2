// Renders site/icons/*.svg to PNG with headless Chrome (app icons, maskable icon, apple-touch icon, favicon).
// Run only when an SVG changes: node scripts/make-icons.mjs   (the PNGs are committed)
import puppeteer from 'puppeteer-core';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { ROOT, findChrome } from '../tests/e2e/lib.mjs';

const dir = join(ROOT, 'site', 'icons');
const jobs = [['icon.svg', 192, 'icon-192.png'], ['icon.svg', 512, 'icon-512.png'], ['icon.svg', 180, 'apple-touch-icon.png'],
  ['icon.svg', 32, 'favicon-32.png'], ['icon-maskable.svg', 512, 'icon-maskable-512.png']];
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
for (const [svg, size, out] of jobs) {
  await page.setViewport({ width: size, height: size, deviceScaleFactor: 1 });
  const data = readFileSync(join(dir, svg)).toString('base64');
  await page.setContent(`<body style="margin:0;background:transparent"><img src="data:image/svg+xml;base64,${data}" width="${size}" height="${size}" style="display:block"></body>`);
  const png = await page.screenshot({ type: 'png', omitBackground: true, clip: { x: 0, y: 0, width: size, height: size } });
  writeFileSync(join(dir, out), png);
  console.log(`${svg} -> ${out} (${size}px, ${png.length} bytes)`);
}
await browser.close();
