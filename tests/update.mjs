// End-to-end test of the content-update chain:  MCP server edits content  →  files on «GitHub»  →  an installed app downloads, verifies and applies them.
// The «GitHub» here is a local static server; the app is a build made with VITE_CONTENT_URL pointing at it (as the Android build does).
// usage: NODE_PATH=$(npm root -g) node tests/update.mjs
import { createServer as http } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync, cpSync, rmSync, readdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { extname, join } from 'node:path';
import { createRequire } from 'node:module';
import { createServer, githubClient } from '../mcp-server/core.js';
const { chromium } = createRequire(import.meta.url)('playwright');
const PORT = 4181, BASE = `http://127.0.0.1:${PORT}`;
const results = []; const log = (n, c, d = '') => { results.push(c); console.log(c ? 'PASS' : 'FAIL', '|', n, d ? '— ' + d : ''); };

// 1) the app, built like the Android build (bundled content version 1 + a remote content URL)
execSync(`node scripts/sync_content.mjs && npx vite build --outDir dist-update`, { stdio: 'ignore', env: { ...process.env, VITE_CONTENT_URL: `${BASE}/remote/`, VITE_APK_VERSION: '3' } });

// 2) the «repository»: starts as the bundled content; the MCP server edits it through a fake GitHub API
const repo = new Map(); for (const f of readdirSync('content')) if (f.endsWith('.json')) repo.set('content/' + f, readFileSync('content/' + f, 'utf8'));
const pending = new Map(); let head = 'c0', n = 0;
const fakeFetch = async (url, init = {}) => { const p = new URL(url).pathname.replace('/repos/o/r', ''); const b = init.body ? JSON.parse(init.body) : null; const S = (o) => new Response(JSON.stringify(o));
  let m; if ((m = p.match(/^\/contents\/(.+)$/))) { const t = repo.get(m[1]); return t === undefined ? new Response('', { status: 404 }) : new Response(t); }
  if (p === '/git/ref/heads/main') return S({ object: { sha: head } }); if (p.startsWith('/git/commits/') && !b) return S({ tree: { sha: 't' } });
  if (p === '/git/trees') { const id = 'T' + ++n; pending.set(id, b.tree); return S({ sha: id }); }
  if (p === '/git/commits') { const id = 'C' + ++n; pending.set(id, pending.get(b.tree)); return S({ sha: id }); }
  if (p === '/git/refs/heads/main') { for (const e of pending.get(b.sha)) e.sha === null ? repo.delete(e.path) : repo.set(e.path, e.content); head = b.sha; return S({}); }
  return new Response('', { status: 404 }); };
const mcp = createServer({ gh: githubClient({ token: 't', repo: 'o/r', fetchImpl: fakeFetch }) });
const tool = (name, args) => mcp.handle({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } });
const publish = () => { rmSync('tests/.remote', { recursive: true, force: true }); mkdirSync('tests/.remote', { recursive: true }); for (const [p, t] of repo) writeFileSync('tests/.remote/' + p.replace('content/', ''), t); };
let tamper = false, offline = false;
const axeSrc = readFileSync('node_modules/axe-core/axe.min.js', 'utf8');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.svg': 'image/svg+xml' };
const srv = http((req, res) => {
  const u = new URL(req.url, BASE); let f = u.pathname.startsWith('/remote/') ? join('tests/.remote', u.pathname.slice(8)) : join('dist-update', u.pathname === '/' ? 'index.html' : u.pathname);
  if (u.pathname.startsWith('/remote/') && offline) { res.writeHead(503); return res.end(); }
  if (!existsSync(f)) { res.writeHead(404); return res.end('not found'); }
  let body = readFileSync(f); if (tamper && u.pathname.startsWith('/remote/') && u.pathname.endsWith('alfiya.json')) body = Buffer.from(body.toString().replace('والليث', 'والذيب'));
  res.writeHead(200, { 'Content-Type': mime[extname(f)] ?? 'application/octet-stream', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'no-store' }); res.end(body);
}).listen(PORT);

const browser = await chromium.launch(); const ctx = await browser.newContext({ locale: 'ar' }); const page = await ctx.newPage();
const ready = async () => { await page.waitForFunction(() => document.querySelector('#panel-quran button.go') && !document.querySelector('.pulse'), null, { timeout: 30000 }); await page.waitForTimeout(1500); };
const tabs = async () => page.locator('.tab').allInnerTexts();
const search = async (id, q) => { await page.locator(`#tab-${id}`).click(); await page.locator(`#panel-${id} input`).fill(q); await page.locator(`#panel-${id} button.go`).click(); await page.locator(`#panel-${id} article, #panel-${id} .soft`).first().waitFor({ timeout: 20000 }); await page.waitForTimeout(300); return page.locator(`#panel-${id}`).innerText(); };

// A) nothing new in the repository: the app runs on its bundled content
publish(); await page.goto(BASE + '/'); await ready();
log('A: no update → the 5 bundled tabs', JSON.stringify(await tabs()) === JSON.stringify(['القرآن الكريم', 'السنة النبوية', 'الأمثال', 'الألفية الوردية', 'الكتب']));

// B) the MCP server adds a new reference + corrects a verse; the app (reopened) receives both
await tool('add_tab', { id: 'adhkar', label: 'الأذكار', entries: [{ ref: 'ذكر الصباح', text: 'سبحان الله وبحمده سبحان الله العظيم' }, { ref: 'دعاء', text: 'اللهم أعني على ذكرك وشكرك وحسن عبادتك', explanation: 'دعاء مأثور' }] });
await tool('add_entries', { tab: 'amthal', entries: [{ ref: 'مثل', text: 'الصبر مفتاح الفرج' }] });
const idx = JSON.parse((await tool('search_entries', { tab: 'alfiya', query: 'والليث سلطان' })).result.content[0].text).results[0].index;
await tool('update_entry', { tab: 'alfiya', index: idx, fields: { shatr2: 'يحذر من السلطان في عقابه (معدَّل)' } });
await tool('set_apk_notice', { versionCode: 7, url: 'https://example.com/app.apk', notes: 'تحسينات' });
publish();
await page.reload(); await ready(); await page.waitForTimeout(2500);        // the update downloads in the background and the app re-indexes
log('B: the new tab appears after the update', (await tabs()).includes('الأذكار'), (await tabs()).join(' | '));
log('B: the «update available» dialog appears when the app opens (installed build 3 < 7)', await page.locator('[role=dialog]').isVisible() && (await page.locator('#upd-title').innerText()).includes('يتوفر تحديث جديد'), (await page.locator('[role=dialog]').innerText()).replace(/\s+/g, ' ').slice(0, 120));
await page.evaluate(axeSrc); const axeDlg = await page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa'] })).violations.map((v) => v.id)); log('B: the dialog has no accessibility violations', axeDlg.length === 0, axeDlg.join(' '));
await page.getByRole('button', { name: 'لاحقاً' }).click();
log('B: «لاحقاً» closes the dialog and leaves a reminder banner', !(await page.locator('[role=dialog]').count()) && (await page.locator('button.apk-notice').count()) === 1);
await page.locator('button.apk-notice').click();
log('B: the banner reopens the dialog', await page.locator('[role=dialog]').isVisible());
await ctx.route('https://example.com/**', (r) => r.fulfill({ status: 200, contentType: 'text/plain', body: 'apk' }));
const popupP = page.waitForEvent('popup', { timeout: 5000 }).catch(() => null); await page.getByRole('button', { name: 'تحديث الآن' }).click(); const popup = await popupP;
log('B: on the web the update button opens the download link (no native installer)', !!popup && popup.url().startsWith('https://example.com/app.apk'), popup?.url()); if (popup) await popup.close();
// the Android app uses its native installer: simulated here to check the progress UI and the result
await page.getByRole("button", { name: "لاحقاً" }).click().catch(() => {});
log('B: the new reference is searchable', (await search('adhkar', 'وشكرك')).includes('اللهم أعني على ذكرك'));
log('B: a card of a new generic tab shows its explanation button', (await page.locator('#panel-adhkar button.sharh').count()) === 1);
log('B: the empty «الأمثال» tab now has data (added through the MCP)', (await search('amthal', 'الصبر')).includes('الصبر مفتاح الفرج'));
log('B: the corrected verse reached the app', (await search('alfiya', 'والليث سلطان')).includes('(معدَّل)'));


// B2) native installer (simulated): progress, then the system installer is opened
const ctxN = await browser.newContext({ locale: 'ar' }); const pn = await ctxN.newPage();
await pn.addInitScript(() => { window.__qsInstaller = { install: async (url, cb) => { window.__url = url; for (const p of [10, 55, 100]) { cb(p); await new Promise((r) => setTimeout(r, 250)); } return 'installing'; } }; });
await pn.goto(BASE + '/'); await pn.waitForFunction(() => document.querySelector('[role=dialog]'), null, { timeout: 30000 });
await pn.getByRole('button', { name: 'تحديث الآن' }).click(); await pn.waitForSelector('[role=progressbar]', { timeout: 3000 }).catch(() => {});
log('B2: native update shows a progress bar while downloading', (await pn.locator('[role=progressbar]').count()) === 1);
await pn.waitForFunction(() => document.querySelector('#upd-desc')?.textContent.includes('اضغط «تثبيت»'), null, { timeout: 5000 }).catch(() => {});
log('B2: when the download ends it asks the user to press «تثبيت» in Android\'s installer', (await pn.locator('#upd-desc').innerText()).includes('اضغط «تثبيت»') && (await pn.evaluate(() => window.__url)) === 'https://example.com/app.apk');
await ctxN.close();

// C) offline: the downloaded content is kept and used
offline = true; await page.reload(); await ready();
log('C: offline reopen keeps the updated tabs', (await tabs()).includes('الأذكار'));
log('C: offline reopen keeps the corrected verse', (await search('alfiya', 'والليث سلطان')).includes('(معدَّل)'));
offline = false;

// D) a download whose SHA-256 does not match is rejected: the app keeps the previous, intact content
await tool('add_tab', { id: 'extra', label: 'إضافي', entries: [{ text: 'نص إضافي للاختبار' }] }); await tool('update_entry', { tab: 'alfiya', index: idx, fields: { shatr2: 'نسخة ثالثة' } }); publish(); tamper = true;
const ctx2 = await browser.newContext({ locale: 'ar' }); const p2 = await ctx2.newPage(); await p2.goto(BASE + '/'); await p2.waitForFunction(() => document.querySelector('#panel-quran button.go') && !document.querySelector('.pulse'), null, { timeout: 30000 }); await p2.waitForTimeout(3500);
log('D: a corrupted download is not applied (no half update)', !(await p2.locator('.tab').allInnerTexts()).includes('إضافي'));
tamper = false; await p2.reload(); await p2.waitForTimeout(4500);
log('D: the same update applies once the download is intact', (await p2.locator('.tab').allInnerTexts()).includes('إضافي'));

await browser.close(); srv.close(); rmSync('tests/.remote', { recursive: true, force: true }); rmSync('dist-update', { recursive: true, force: true });
const pass = results.filter(Boolean).length; console.log(`\nSUMMARY: ${pass}/${results.length} passed`); process.exit(pass === results.length ? 0 : 1);
