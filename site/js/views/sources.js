import { T } from '../i18n.js';
import { all } from '../data.js';
import { esc } from '../util.js';

export function viewSources(credits) {
  const li = (k) => `<li>${T(k)}</li>`;
  return `<header class="ghead"><nav class="crumbs" aria-label="breadcrumb"><a href="#home">${T('explorePath')}</a> › ${T('sources')}</nav>` +
    `<div class="gtitle"><h1 tabindex="-1">${T('sources')}</h1></div></header>` +
    `<div class="prose"><p>${T('srcIntro', { n: all().length })}</p>` +
    `<h2>${T('srcH1')}</h2><ul>${['srcL1', 'srcL2', 'srcL3', 'srcL4'].map(li).join('')}</ul>` +
    `<h2>${T('srcH2')}</h2><p>${T('srcP2')}</p><h2>${T('srcH3')}</h2><p>${T('srcP3')}</p><h2>${T('srcH4')}</h2><p>${T('srcP4')}</p></div>` + creditsTable(credits);
}

function creditsTable(credits) {
  if (!credits.length) return '';
  const rows = credits.map((c) => {
    const lic = c.license_url ? `<a href="${esc(c.license_url)}" rel="noopener">${esc(c.license)}</a>` : esc(c.license);
    return `<tr><th scope="row"><a href="#${c.id}" class="sci">${esc(c.sci)}</a></th><td data-native>${esc(c.author)}</td><td>${lic}</td><td><a href="${esc(c.source_url)}" rel="noopener">${T('imgOn')}</a></td></tr>`;
  }).join('');
  return `<section class="section"><h2 class="h2" id="credits">${T('imgCreditsH')}</h2><p class="lede" style="font-size:16px">${T('imgCreditsP', { n: credits.length })}</p>` +
    `<div class="tablebox" tabindex="0" role="region" aria-label="${esc(T('imgCreditsH'))}"><table class="credits"><thead><tr><th scope="col">${T('colSpecies')}</th><th scope="col">${T('imgAuthor')}</th><th scope="col">${T('imgLicense')}</th><th scope="col">${T('imgSource')}</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
}
