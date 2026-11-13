// Small shared helpers: HTML escaping and safe localStorage access.
const ENT = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ENT[c]);

export const store = {
  get(k, d) { try { const v = localStorage.getItem('ms2.' + k); return v === null ? d : v; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('ms2.' + k, v); } catch { /* storage unavailable */ } },
};
