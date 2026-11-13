// A copy of site/ (without pictures) whose data also contains the made-up test species
// tests/fixtures/sample-species.json (all 8 content sections, disease and warning boxes, IUCN badge, range traits).
// The real data/ and site/ are not touched: the species is added to a temporary copy of data/ and built there.
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ROOT, SITE, findPython, serveSite } from './lib.mjs';

export const FIXTURE_ID = 'testium-exemplaris';
export const readFixture = () => {
  const o = JSON.parse(readFileSync(join(ROOT, 'tests', 'fixtures', 'sample-species.json'), 'utf8'));
  delete o._comment;
  return o;
};

export async function withFixture() {
  const tmp = mkdtempSync(join(tmpdir(), 'ms2-fixture-'));
  const site = join(tmp, 'site');
  const data = join(tmp, 'data');
  cpSync(SITE, site, { recursive: true, filter: (src) => !/[\\/]images([\\/]|$)/.test(src) });
  cpSync(join(ROOT, 'data'), data, { recursive: true });
  const file = join(data, 'organisms', 'archaea.json');
  const items = JSON.parse(readFileSync(file, 'utf8'));
  items.push(readFixture());
  writeFileSync(file, JSON.stringify(items, null, 2));
  const r = spawnSync(findPython(), [join(ROOT, 'scripts', 'microsearch.py'), 'build', '--data', data, '--out', join(site, 'data')], { encoding: 'utf8', cwd: ROOT });
  if (r.status !== 0) throw new Error(`fixture build failed:\n${r.stdout}\n${r.stderr}`);
  const s = await serveSite(site);
  return { ...s, cleanup: () => rmSync(tmp, { recursive: true, force: true }) };
}
