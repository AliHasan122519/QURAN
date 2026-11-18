// Node check of the search engine (Lookup = what each tab shows) against the real data files.
import { build } from 'esbuild'; import { gunzipSync } from 'node:zlib'; import { readFileSync } from 'node:fs';
const out = new URL('../.engine-test.mjs', import.meta.url).pathname;
await build({ entryPoints: ['src/lib/engine.ts'], bundle: true, format: 'esm', platform: 'node', outfile: out, logLevel: 'error' });
const { Engine } = await import(out);
const rd = (n) => JSON.parse(gunzipSync(readFileSync(`public/data/${n}.json.gz`)).toString('utf8'));
const e = new Engine(); const q = rd('quran'); const sm = new Map(q.surahs.map((s) => [s.n, s.name]));
await e.addSource('quran', q.a.map(([s, a, x]) => ({ id: `q:${s}:${a}`, src: 'quran', text: x, surah: s, ayah: a, surahName: sm.get(s) })));
const j = rd('jami'); await e.addSource('jami', j.h.map(([page, letter, x, k, sym, g, tier], i) => ({ id: `j:${i}`, src: 'jami', text: x, page, takhrij: k, grade: g, tier })));
await e.finalize();
const cases = [['quran', 'الصبر'], ['quran', 'الرحمة'], ['quran', 'مفتاح'], ['quran', 'بِسْمِ ٱللَّهِ'], ['quran', 'الصلاه'], ['quran', 'قل هو الله احد'], ['quran', 'xyzqq'], ['quran', 'يؤمنون'],
  ['jami', 'النية'], ['jami', 'الجار'], ['jami', 'الصدقة'], ['jami', 'إنما الأعمال بالنيات'], ['jami', 'قشطة'], ['jami', 'الصبر'], ['quran', 'صبر']];
for (const [src, qq] of cases) { const r = e.lookup(src, qq); console.log(src.padEnd(6), qq.padEnd(22), 'direct', String(r.directCount).padStart(4), 'extra', String(r.semanticCount).padStart(4), 'shown', r.results.length, r.expansion ? 'root=' + r.expansion.root + ' terms=' + r.expansion.terms.slice(0, 4).join('،') : '', r.results[0] ? r.results[0].doc.id : ''); }
const m = e.lookup('quran', 'مفتاح'); console.log('مفتاح verses:', m.results.map((x) => x.doc.surahName + ':' + x.doc.ayah + '(' + x.matchType + ')').join(' '));
