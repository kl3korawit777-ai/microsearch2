// Hash routes may carry a query string: #bacteria?gram=pos&lv=hs . Filters and diagram selection live there.
export function parseHash() {
  const raw = (location.hash || '').replace(/^#/, '');
  const i = raw.indexOf('?');
  let path = i < 0 ? raw : raw.slice(0, i);
  try { path = decodeURIComponent(path); } catch { /* keep raw */ }
  return { path: path || 'home', params: new URLSearchParams(i < 0 ? '' : raw.slice(i + 1)) };
}

export function hashFor(path, params) {
  const qs = params.toString();
  return `#${path}${qs ? `?${qs}` : ''}`;
}

// Update the URL without adding a history entry (filters change a lot while typing).
export function replaceHash(path, params) {
  history.replaceState(null, '', hashFor(path, params));
}
