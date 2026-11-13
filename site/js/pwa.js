// Registers the service worker (offline use). Skipped on file:// and where service workers are unavailable.
export function registerServiceWorker() {
  if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).catch(() => { /* offline support is optional */ });
  });
}
