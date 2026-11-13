import { T } from '../i18n.js';
import { all } from '../data.js';

export function viewSources() {
  const li = (k) => `<li>${T(k)}</li>`;
  return `<header class="ghead"><nav class="crumbs" aria-label="breadcrumb"><a href="#home">${T('explorePath')}</a> › ${T('sources')}</nav>` +
    `<div class="gtitle"><h1 tabindex="-1">${T('sources')}</h1></div></header>` +
    `<div class="prose"><p>${T('srcIntro', { n: all().length })}</p>` +
    `<h2>${T('srcH1')}</h2><ul>${['srcL1', 'srcL2', 'srcL3', 'srcL4'].map(li).join('')}</ul>` +
    `<h2>${T('srcH2')}</h2><p>${T('srcP2')}</p><h2>${T('srcH3')}</h2><p>${T('srcP3')}</p><h2>${T('srcH4')}</h2><p>${T('srcP4')}</p></div>`;
}
