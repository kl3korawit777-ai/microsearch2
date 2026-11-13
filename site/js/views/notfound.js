import { T } from '../i18n.js';

export function viewNotFound() {
  return `<div class="empty" style="margin-top:20px"><h1 tabindex="-1" style="margin:0;font-size:28px">${T('notFound')}</h1><p>${T('notFoundBody')}</p><a class="btn" href="#home">${T('backHome')}</a></div>`;
}
