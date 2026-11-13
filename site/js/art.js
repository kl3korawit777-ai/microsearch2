import { drawing } from './data.js';

export function art(key) {
  return `<svg class="illo" viewBox="0 0 160 100" role="presentation" aria-hidden="true">${drawing(key)}</svg>`;
}
