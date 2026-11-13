// Shared helpers for the e2e scripts: build the site data, serve site/, find Chrome.
import { spawnSync } from 'node:child_process';
import { gzipSync } from 'node:zlib';
import { createServer } from 'node:http';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = resolve(fileURLToPath(new URL('../..', import.meta.url)));
export const SITE = join(ROOT, 'site');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon',
};

export function findPython() {
  for (const cmd of ['python3', 'python', 'py']) {
    const r = spawnSync(cmd, ['--version'], { encoding: 'utf8' });
    if (r.status === 0 && /Python 3/.test(`${r.stdout}${r.stderr}`)) return cmd;
  }
  throw new Error('Python 3 not found (tried python3, python, py)');
}

// Runs `microsearch.py build` (validate first). Throws if it fails.
export function buildSite() {
  const r = spawnSync(findPython(), [join(ROOT, 'scripts', 'microsearch.py'), 'build'], { encoding: 'utf8', cwd: ROOT });
  if (r.status !== 0) throw new Error(`build failed:\n${r.stdout}\n${r.stderr}`);
}

export function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);
  const found = candidates.find((p) => existsSync(p));
  if (!found) throw new Error('Chrome/Edge not found (set CHROME_PATH)');
  return found;
}

// Static file server for site/ on a random local port.
export function serveSite(dir = SITE) {
  const server = createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = normalize(join(dir, p));
    if (!file.startsWith(dir) || !existsSync(file) || !statSync(file).isFile()) { res.writeHead(404); res.end('not found'); return; }
    const type = MIME[extname(file)] || 'application/octet-stream';
    const body = readFileSync(file);
    const gz = /gzip/.test(req.headers['accept-encoding'] || '') && /^(text|application\/json|image\/svg)/.test(type);
    res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store', ...(gz ? { 'content-encoding': 'gzip', vary: 'accept-encoding' } : {}) });
    res.end(gz ? gzipSync(body) : body);
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => ok({ server, base: `http://127.0.0.1:${server.address().port}` })));
}

export const readJson = (rel) => JSON.parse(readFileSync(join(SITE, rel), 'utf8'));
