// Service worker: lets the site work offline.
//   install   fetches every file listed in precache.json (written by `microsearch.py build`) into a cache named after
//             the build version, so every page, both languages and all data work offline right after the first visit
//   activate  deletes the app caches of older versions (picture and font caches are kept)
//   fetch     app files and data: network first (fresh code and data when online, 4 s limit), cached copy when offline
//             pictures (images/*): cache first, stored the first time they are opened
//             Google Fonts: cache first, stored the first time they load
importScripts('version.js'); // changes with every release, which makes the browser install the new worker
const PREFIX = 'ms2-';
const META = 'ms2-meta';
const IMAGES = 'ms2-images-v1';
const FONTS = 'ms2-fonts-v1';
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];
const NETWORK_TIMEOUT_MS = 4000;
const SCOPE = new URL(self.registration.scope);

async function currentAppCache() {
  const meta = await caches.open(META);
  const hit = await meta.match('current');
  return hit ? hit.text() : null;
}

async function precache() {
  const res = await fetch('precache.json', { cache: 'reload' });
  if (!res.ok) throw new Error(`precache.json: ${res.status}`);
  const { version, files } = await res.json();
  const name = `${PREFIX}app-${version}`;
  const cache = await caches.open(name);
  await Promise.all(['./', 'precache.json', ...files].map(async (u) => {
    const r = await fetch(new Request(u, { cache: 'reload' }));
    if (!r.ok) throw new Error(`${u}: ${r.status}`); // a broken precache must not become the active one
    await cache.put(u, r);
  }));
  await (await caches.open(META)).put('current', new Response(name));
}

async function cleanOldCaches() {
  const current = await currentAppCache();
  for (const key of await caches.keys()) {
    if (key.startsWith(`${PREFIX}app-`) && key !== current) await caches.delete(key);
  }
}

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    promise.then((v) => { clearTimeout(t); resolve(v); }, (e) => { clearTimeout(t); reject(e); });
  });
}

async function networkFirst(request) {
  const name = await currentAppCache();
  const cache = name ? await caches.open(name) : null;
  try {
    const res = await withTimeout(fetch(request), NETWORK_TIMEOUT_MS);
    if (res.ok && cache) await cache.put(request, res.clone());
    return res;
  } catch (err) {
    if (cache) {
      const hit = (await cache.match(request, { ignoreSearch: true })) || (request.mode === 'navigate' ? await cache.match('./') : null);
      if (hit) return hit;
    }
    throw err;
  }
}

// Shown in place of a picture that was never opened online (so it is not in the cache) while offline.
const OFFLINE_PICTURE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100"><rect width="160" height="100" fill="#8888" opacity=".15"/></svg>';

async function cacheFirst(cacheName, request) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(request, { ignoreVary: true });
  if (hit) return hit;
  let res;
  try {
    res = await fetch(request);
  } catch (err) {
    if (cacheName === IMAGES) return new Response(OFFLINE_PICTURE, { headers: { 'content-type': 'image/svg+xml' } });
    throw err;
  }
  if (res.ok || res.type === 'opaque') { try { await cache.put(request, res.clone()); } catch { /* storage full: skip */ } }
  return res;
}

self.addEventListener('install', (e) => { e.waitUntil(precache().then(() => self.skipWaiting())); });
self.addEventListener('activate', (e) => { e.waitUntil(cleanOldCaches().then(() => self.clients.claim())); });

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    const p = url.pathname.slice(SCOPE.pathname.length);
    if (p === 'sw.js') return;
    e.respondWith(p.startsWith('images/') ? cacheFirst(IMAGES, req) : networkFirst(req));
  } else if (FONT_HOSTS.includes(url.hostname)) {
    e.respondWith(cacheFirst(FONTS, req));
  }
});
