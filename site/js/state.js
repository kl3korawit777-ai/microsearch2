// Single mutable UI state object, shared by every module.
import { store } from './util.js';

const lang = store.get('lang', 'th');
const theme = store.get('theme', 'auto');

export const S = {
  lang: lang === 'en' ? 'en' : 'th',
  theme: ['auto', 'light', 'dark'].includes(theme) ? theme : 'auto',
  collapsed: store.get('collapsed', '0') === '1',
  tree: { g: 'archaea', p: 0, s: 0 }, // home page picker: group, phylum index, species index
  gf: {},   // filters per group id
  open: {}, // expanded row per group id
  tab: 'traits',
  slide: {}, // current picture per species id
  focusSearch: false,
  query: '',            // home search text, kept until reload so going back finds it again
  restoreSearch: false, // a species was opened from the search: refocus the field when home returns
};
