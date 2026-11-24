// Checks content/manifest.json against the data files: every file exists, its SHA-256 and entry count match, tab ids are unique and kinds are known.
// Run by CI on every change of content/ (including the ones made through the MCP server) so a bad commit is caught before it reaches the apps.
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
const m = JSON.parse(readFileSync('content/manifest.json', 'utf8'));
const errs = []; const ids = new Set();
if (!Number.isInteger(m.version) || m.version < 1) errs.push('manifest.version must be a positive integer');
for (const t of m.tabs) {
  if (ids.has(t.id)) errs.push(`duplicate tab id ${t.id}`); ids.add(t.id);
  if (!['quran', 'hadith', 'poem', 'generic'].includes(t.kind)) errs.push(`${t.id}: unknown kind ${t.kind}`);
  if (!t.file) continue;
  if (!existsSync('content/' + t.file)) { errs.push(`${t.id}: missing file ${t.file}`); continue; }
  const raw = readFileSync('content/' + t.file);
  if (createHash('sha256').update(raw).digest('hex') !== t.sha256) errs.push(`${t.id}: sha256 mismatch`);
  const j = JSON.parse(raw.toString('utf8')); const n = (j.a ?? j.h ?? []).length;
  if (n !== t.count) errs.push(`${t.id}: count ${n} != manifest ${t.count}`);
}
for (const f of m.files ?? []) {                                                   // extra files (the texts of the reader's books)
  if (!existsSync('content/' + f.file)) { errs.push(`missing file ${f.file}`); continue; }
  const raw = readFileSync('content/' + f.file);
  if (createHash('sha256').update(raw).digest('hex') !== f.sha256) errs.push(`${f.file}: sha256 mismatch`);
  if (f.size !== undefined && f.size !== raw.length) errs.push(`${f.file}: size ${raw.length} != manifest ${f.size}`);
  if (f.file.endsWith('.json')) { try { JSON.parse(raw.toString('utf8')); } catch { errs.push(`${f.file}: not valid JSON`); } }
  else if (f.file.endsWith('.jpg') && !(raw[0] === 0xff && raw[1] === 0xd8)) errs.push(`${f.file}: not a JPEG`);
}
if (errs.length) { console.error(errs.join('\n')); process.exit(1); }
console.log(`content OK: version ${m.version}, ${m.tabs.length} tabs, ${(m.files ?? []).length} files`);
