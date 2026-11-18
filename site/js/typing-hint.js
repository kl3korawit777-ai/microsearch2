// Typing animation shown over the empty home search box: the species name typed, held, erased, next name.
// It is an aria-hidden overlay (see searchBox in ui.js), never a placeholder, so the real field is untouched.
import { all, groups } from './data.js';
import { isEn } from './ui.js';

// Timing in milliseconds: edit here.
export const TIMING = { type: 90, hold: 1600, erase: 40, gap: 400, resume: 1500 };
const NAMES = 8; // species used per page load, at least one from every group

let pool = null; // chosen once per page load
let stopCurrent = null;

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

function choosePool() {
  const rows = all();
  const chosen = [];
  for (const g of groups()) {
    const of = rows.filter((s) => s.g === g.id);
    if (of.length) chosen.push(pick(of));
  }
  const rest = rows.filter((s) => !chosen.includes(s));
  while (chosen.length < NAMES && rest.length) chosen.push(rest.splice(Math.floor(Math.random() * rest.length), 1)[0]);
  for (let i = chosen.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [chosen[i], chosen[j]] = [chosen[j], chosen[i]]; }
  return chosen;
}

// [{ text, sci }] for the current language: common name and scientific name alternate.
function entries() {
  pool = pool || choosePool();
  return pool.map((s, i) => {
    const common = isEn() ? s.en : s.th;
    return i % 2 === 0 && common ? { text: common, sci: false } : { text: s.sci, sci: true };
  });
}

const graphemes = (text) => {
  if (typeof Intl !== 'undefined' && Intl.Segmenter) return [...new Intl.Segmenter(isEn() ? 'en' : 'th', { granularity: 'grapheme' }).segment(text)].map((x) => x.segment);
  return Array.from(text);
};

export const hintActive = () => !!stopCurrent;

// Call after every render. Stops any earlier animation, then starts one if the home search box is on the page.
export function startTypingHint(root) {
  if (stopCurrent) stopCurrent();
  const inp = root.querySelector('#heroQ');
  const wrap = inp?.closest('.search');
  const hint = wrap?.querySelector('.s-hint');
  if (!inp || !hint) return;
  const txtEl = hint.querySelector('.s-hint-txt');
  const list = entries();
  if (!list.length) return;

  let timer = 0;
  let idle = !inp.value; // the hint plays while the field is empty, focused or not
  let visible = !document.hidden;
  let inView = true;
  let i = 0;
  let chars = graphemes(list[0].text);
  let n = 0;
  let phase = 'type';

  const show = (on) => wrap.classList.toggle('hint-on', on);
  const render = () => {
    txtEl.textContent = chars.slice(0, n).join('');
    txtEl.classList.toggle('sci', list[i].sci);
  };
  const clearTimer = () => { clearTimeout(timer); timer = 0; };
  const later = (fn, ms) => { clearTimer(); timer = setTimeout(fn, ms); };

  const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) { // a still hint, no motion
    n = chars.length; render();
    wrap.classList.add('hint-static');
    show(idle);
    const onStill = () => show(!inp.value);
    inp.addEventListener('input', onStill); inp.addEventListener('ms-clear', onStill);
    stopCurrent = () => { inp.removeEventListener('input', onStill); inp.removeEventListener('ms-clear', onStill); wrap.classList.remove('hint-on', 'hint-static'); stopCurrent = null; };
    return;
  }

  const tick = () => {
    if (phase === 'type') {
      if (n < chars.length) { n++; render(); later(tick, n === chars.length ? TIMING.hold : TIMING.type); if (n === chars.length) phase = 'erase'; }
    } else if (phase === 'erase') {
      if (n > 0) { n--; render(); later(tick, n === 0 ? TIMING.gap : TIMING.erase); if (n === 0) phase = 'next'; }
    } else { // next name
      i = (i + 1) % list.length;
      chars = graphemes(list[i].text);
      phase = 'type';
      later(tick, 0);
    }
  };
  // The call that finishes typing schedules the hold; the one after it starts erasing.
  const run = () => { clearTimer(); if (idle && visible && inView) { show(true); later(tick, phase === 'type' && n === 0 ? TIMING.type : TIMING.type); } };
  const restart = () => { clearTimer(); i = 0; chars = graphemes(list[0].text); n = 0; phase = 'type'; render(); };

  // Typing hides the hint; when the field is empty again (deleted, or cleared with x) it starts over.
  const onInput = () => {
    if (inp.value) { idle = false; clearTimer(); show(false); }
    else if (!idle) { idle = true; restart(); later(run, TIMING.resume); }
  };
  const onVis = () => {
    visible = !document.hidden;
    if (!visible) clearTimer(); else run();
  };
  const io = typeof IntersectionObserver === 'function' ? new IntersectionObserver((entriesIO) => {
    inView = entriesIO[entriesIO.length - 1].isIntersecting;
    if (!inView) clearTimer(); else run();
  }) : null;

  inp.addEventListener('input', onInput);
  inp.addEventListener('ms-clear', onInput);
  document.addEventListener('visibilitychange', onVis);
  if (io) io.observe(wrap);
  stopCurrent = () => {
    clearTimer();
    inp.removeEventListener('input', onInput);
    inp.removeEventListener('ms-clear', onInput);
    document.removeEventListener('visibilitychange', onVis);
    if (io) io.disconnect();
    wrap.classList.remove('hint-on');
    stopCurrent = null;
  };
  restart();
  run();
}
