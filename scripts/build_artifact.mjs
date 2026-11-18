// Packages the production build as ONE self-contained HTML page (fonts as data: URIs, CSS and JS inline) plus data files,
// as required by the Claude Artifact sandbox (no external fonts/styles/scripts besides an allowlist).
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
const OUT = 'artifact';
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT + '/data', { recursive: true });
execSync('npx vite build --outDir dist-artifact', { stdio: 'inherit', env: { ...process.env, VITE_PDF: '0', VITE_DATA_EXT: '.json' } });
const dir = 'dist-artifact/assets';
const files = readdirSync(dir);
const js = readFileSync(`${dir}/${files.find((f) => f.endsWith('.js'))}`, 'utf8');
let css = readFileSync(`${dir}/${files.find((f) => f.endsWith('.css'))}`, 'utf8');
const dataUri = (f, mime) => `data:${mime};base64,${readFileSync(f).toString('base64')}`;
css = css.replace(/url\(\.\.\/assets\/Dubai-Bold\.ttf\)/g, `url(${dataUri('public/assets/Dubai-Bold.ttf', 'font/ttf')})`)
         .replace(/url\(\.\.\/assets\/AmiriQuran-Regular\.woff2\)/g, `url(${dataUri('public/assets/AmiriQuran-Regular.woff2', 'font/woff2')})`);
if (/url\(\.\.\/assets/.test(css)) throw new Error('unresolved asset url left in CSS');
const safeJs = js.replace(/<\/script/gi, '<\\/script');
const fav = readFileSync('public/favicon.svg', 'utf8');
const html = `<title>الباحث القرآني</title>
<meta name="description" content="منصّة بحث عربي في القرآن الكريم والسنة النبوية والألفية الوردية">
<style>${css}</style>
<div id="root"></div>
<script type="module">${safeJs}</script>
`;
writeFileSync(`${OUT}/index.html`, html);
// data files are published as plain JSON (small: ~4 MB) so no compressed-file hosting rules are involved
for (const f of readdirSync('public/data').filter((x) => x.endsWith('.json.gz'))) writeFileSync(`${OUT}/data/${f.replace('.json.gz', '.json')}`, gunzipSync(readFileSync(`public/data/${f}`)));
console.log('artifact page', (html.length / 1e6).toFixed(2), 'MB; fav bytes', fav.length);
