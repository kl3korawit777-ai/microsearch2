// Loads site/data/*.json: meta + search index + drawings up front, one detail file per group on demand.
let meta = null;
let index = [];
let drawings = {};
const byIdMap = new Map();
const groupCache = new Map();

async function getJson(name) {
  const res = await fetch(`data/${name}.json`);
  if (!res.ok) throw new Error(`data/${name}.json: ${res.status}`);
  return res.json();
}

export async function loadCore() {
  [meta, index, drawings] = await Promise.all([getJson('meta'), getJson('index'), getJson('illustrations')]);
  index.forEach((r) => byIdMap.set(r.id, r));
}

// Detail (traits text, lineage, extra content) of one group, attached to each row as row.d
export async function loadGroup(id) {
  if (!groupCache.has(id)) {
    const d = await getJson(id);
    d.organisms.forEach((o) => { const r = byIdMap.get(o.id); if (r) r.d = o; });
    groupCache.set(id, d);
  }
  return groupCache.get(id);
}

export const getMeta = () => meta;
export const groups = () => meta.groups;
export const G = (id) => meta.groups.find((g) => g.id === id) || null;
export const byId = (id) => byIdMap.get(id) || null;
export const all = () => index;
export const inGroup = (id) => index.filter((s) => s.g === id);
export const inPhylum = (id, p) => index.filter((s) => s.g === id && s.p === p);
export const drawing = (key) => drawings[key] || drawings.rod || '';
export const groupTaxa = (id) => (groupCache.get(id) || {}).taxa || {};
export const traitDefs = (gid) => G(gid).traits;
export const hasGroup = (id) => !!G(id);
export const reading = (label, gid) => (gid && groupTaxa(gid)[label]?.reading_th) || meta.readings[label] || '';
