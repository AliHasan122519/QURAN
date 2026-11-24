// Test of the standalone site of the library (dist-library, built by scripts/build_library_site.mjs): the two lists only, with the pages of the books.
// usage: node scripts/build_library_site.mjs && NODE_PATH=$(npm root -g) node tests/library_site.mjs
import { spawn } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const axeSrc = readFileSync(new URL('../node_modules/axe-core/axe.min.js', import.meta.url), 'utf8');
const PORT = 4178, URL_ = `http://127.0.0.1:${PORT}/`;
const srv = spawn('npx', ['vite', 'preview', '--config', 'vite.library.config.ts', '--port', String(PORT), '--host', '127.0.0.1', '--strictPort'], { stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 3500));
let fails = 0; const log = (ok, what, d = '') => { if (!ok) fails++; console.log(ok ? 'PASS' : 'FAIL', '|', what, d ? '— ' + d : ''); };
const browser = await chromium.launch(); const ctx = await browser.newContext({ viewport: { width: 400, height: 860 }, locale: 'ar' }); const page = await ctx.newPage();
const errors = []; page.on('pageerror', (e) => errors.push(e.message)); page.on('console', (m) => { if (m.type() === 'error' && !/archive\.org|ERR_|Failed to load resource/.test(m.text())) errors.push(m.text().slice(0, 140)); });
await page.goto(URL_); await page.waitForSelector('.site-list', { timeout: 20000 }); await page.waitForTimeout(1500);
log((await page.title()) === 'مكتبة التعبير والفراسة', 'the page has its own title', await page.title());
log((await page.locator('h1').innerText()).includes('مكتبة التعبير والفراسة'), 'the heading names the library');
const intro = (await page.locator('.hero p').innerText()).trim(); log(intro.length > 20 && intro.length < 110, 'the introduction is one short sentence', `${intro.length} letters: ${intro}`);
log((await page.locator('[role="tab"], input[type="search"]').count()) === 0, 'the home has no search and no tabs (the lists open from the entries and from the side menu)');
const entries = await page.locator('.site-list').allInnerTexts(); log(entries.length === 2 && /كتب علم التعبير/.test(entries[0]) && /12/.test(entries[0]) && /كتب الفراسة والشخصيات/.test(entries[1]) && /27/.test(entries[1]), 'the two lists are the two entries, with the number of books', entries.map((x) => x.replace(/\n/g, ' ')).join(' | '));
const html = readdirSync('dist-library/content'); log(html.sort().join(',') === 'books,covers,kutubfiras.json,kutubtabir.json,manifest.json', 'the site carries only the two lists, their books and their covers', html.join(','));
// the side menu: the same two lists, like «المزيد» of the app
await page.locator('button.menu-toggle').click(); await page.waitForSelector('.drawer');
const items = await page.locator('.drawer-item').allInnerTexts(); log(items.length === 2 && (await page.locator('.drawer h2').innerText()) === 'المزيد', 'the side menu «المزيد» lists the two lists only', items.join(' | '));
await page.locator('.drawer-item', { hasText: 'كتب علم التعبير' }).click(); await page.waitForSelector('.lib-tile'); await page.waitForTimeout(900);
log(/عدد الكتب: 12/.test(await page.locator('.lib-count').innerText()), 'the first list opens as its own panel: «عدد الكتب: 12»');
log((await page.locator('.lib-tile').count()) === 12, '12 books of interpretation');
await page.waitForFunction(() => document.querySelectorAll('.lib-tile svg image').length >= 11, null, { timeout: 15000 }).catch(() => {});
log((await page.locator('.lib-tile svg image').count()) === 11, 'the real covers of the printed editions are shown (11 of 12)');
await page.locator('.lib-find').fill('قتيبة'); await page.waitForTimeout(200);
log((await page.locator('.lib-tile').count()) === 2, 'search by name: «قتيبة» → the two editions of Ibn Qutayba');
await page.locator('.lib-find').fill('المرقبه'); await page.waitForTimeout(200);
log((await page.locator('.lib-tile').count()) === 1, 'search folds the ta marbuta: «المرقبه» finds «المرقبة العليا»');
await page.locator('.lib-find').fill('');
// a book with a text: reading inside the page, the contents, the scan
await page.locator('.lib-tile', { hasText: 'المنامات' }).click(); await page.waitForSelector('.lib-detail');
await page.waitForSelector('.lib-detail .lib-cover-big image', { timeout: 8000 }).catch(() => {}); log((await page.locator('.lib-detail .lib-cover-big image').count()) === 1, 'the book page shows the real cover');
log((await page.locator('.lib-detail .lib-read').count()) === 1 && (await page.locator('.lib-detail .lib-scan').count()) === 1 && (await page.locator('.lib-detail .lib-dl').count()) >= 1, 'read inside the page, read the scanned book, and download are there');
await page.locator('.lib-read').click(); await page.waitForSelector('.rd-text'); await page.waitForTimeout(400);
log((await page.locator('.rd-text').first().innerText()).length > 300, 'the text of the book is read inside the site');
await page.keyboard.press('Escape'); await page.waitForTimeout(300); await page.keyboard.press('Escape'); await page.waitForTimeout(300); await page.keyboard.press('Escape'); await page.waitForTimeout(300);
log((await page.locator('.panel-back').count()) === 0, 'Escape closes the book, then the list, back to the home');
// the second list, opened from its entry on the home
await page.locator('.site-list', { hasText: 'الفراسة والشخصيات' }).click(); await page.waitForSelector('.lib-tile'); await page.waitForTimeout(500);
log(/عدد الكتب: 27/.test(await page.locator('.lib-count').innerText()), 'the second list opens from its entry: «عدد الكتب: 27»');
await page.locator('.lib-find').fill('الجسد'); await page.waitForTimeout(200);
log((await page.locator('.lib-tile').count()) >= 6, 'search «الجسد» finds the body-language books', String(await page.locator('.lib-tile').count()));
await page.keyboard.press('Escape'); await page.waitForTimeout(300);
// layout and accessibility
log(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'no horizontal scroll at 400px');
await page.evaluate(axeSrc); const ax = await page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'best-practice'] })).violations.map((v) => ({ id: v.id, impact: v.impact, n: v.nodes.length })));
const bad = ax.filter((v) => v.impact === 'serious' || v.impact === 'critical'); log(bad.length === 0, 'axe: no serious or critical violation', ax.map((v) => `${v.id}(${v.impact}×${v.n})`).join(' ') || 'none');
await page.locator('.theme-toggle').click(); await page.waitForTimeout(200); log((await page.evaluate(() => document.documentElement.getAttribute('data-theme'))) !== null, 'the theme toggle works');
log(errors.length === 0, 'no script error', errors.join(' | '));
await page.setViewportSize({ width: 1280, height: 900 }); await page.waitForTimeout(400); log(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'no horizontal scroll at 1280px');
await page.screenshot({ path: 'tests/screenshots/library_site_desktop.png' });
console.log(fails ? `FAILED: ${fails}` : 'ALL PASSED'); await browser.close(); srv.kill(); process.exit(fails ? 1 : 0);
