import { loadI18n } from './i18n.js';
import { loadCore } from './data.js';
import { applyChrome, wireChrome } from './chrome.js';
import { render } from './router.js';
import { wireSearch } from './search.js';
import { goTo } from './router.js';
import { registerServiceWorker } from './pwa.js';
import { art } from './art.js';

async function start() {
  try {
    await Promise.all([loadI18n(), loadCore()]);
  } catch (e) {
    document.getElementById('view').textContent = `Failed to load data: ${e.message}`;
    return;
  }
  applyChrome();
  wireChrome();
  wireSearch(document, goTo);
  await render(true);
}

// A picture that fails to load (offline, removed upstream) is replaced by the species drawing.
document.addEventListener('error', (e) => {
  const img = e.target;
  if (img instanceof HTMLImageElement && img.dataset.art !== undefined) img.replaceWith(Object.assign(document.createElement('span'), { innerHTML: art(img.dataset.art) }).firstElementChild);
}, true);

registerServiceWorker();
start();
