// Builds the standalone site of the library: only «كتب علم التعبير» and «كتب الفراسة والشخصيات» (no search tabs, no other list of the menu).
// usage: node scripts/build_library_site.mjs   ->  dist-library/ (static files: open index.html through any web server, or upload the folder to any static host)
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, renameSync, rmSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit' });
run('node', ['scripts/sync_content.mjs']); run('npx', ['tsc', '--noEmit']); run('npx', ['vite', 'build', '--config', 'vite.library.config.ts']);
const out = 'dist-library'; renameSync(join(out, 'library.html'), join(out, 'index.html'));
// keep only what the two lists need: their tabs, the texts of their books, their covers
const mp = join(out, 'content', 'manifest.json'); const m = JSON.parse(readFileSync(mp, 'utf8'));
const tabs = m.tabs.filter((t) => t.card === 'library'); const keep = new Set(['manifest.json']);
for (const t of tabs) {
  keep.add(t.file);
  for (const r of JSON.parse(readFileSync(join(out, 'content', t.file), 'utf8')).h) { const c = JSON.parse(r[6]); if (c.reader?.file) keep.add(c.reader.file); if (c.cover?.img) keep.add(c.cover.img); }
}
const files = (m.files ?? []).filter((f) => keep.has(f.file)); for (const f of files) if (!existsSync(join(out, 'content', f.file))) throw new Error('missing ' + f.file);
delete m.apk; m.tabs = tabs; m.files = files; writeFileSync(mp, JSON.stringify(m)); 
const walk = (d, base = '') => readdirSync(d).flatMap((n) => { const p = join(d, n), r = base ? `${base}/${n}` : n; return statSync(p).isDirectory() ? walk(p, r) : [r]; });
for (const r of walk(join(out, 'content'))) if (!keep.has(r)) rmSync(join(out, 'content', r));
for (const d of ['books', 'covers']) { const p = join(out, 'content', d); if (existsSync(p) && !readdirSync(p).length) rmSync(p, { recursive: true }); }
const all = walk(out); const size = all.reduce((n, r) => n + statSync(join(out, r)).size, 0);
console.log(`library site: ${tabs.length} lists, ${files.length} extra files, ${all.length} files, ${(size / 1e6).toFixed(1)} MB -> ${out}/`);
