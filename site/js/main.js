import { loadI18n } from './i18n.js';
import { loadCore } from './data.js';
import { applyChrome, wireChrome } from './chrome.js';
import { render } from './router.js';
import { wireSearch } from './search.js';
import { goTo } from './router.js';

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

start();
