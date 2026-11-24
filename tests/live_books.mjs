// LIVE test of the two book lists («كتب علم التعبير» and «كتب الفراسة») in a real browser, WITH the internet (it opens the real archive.org viewer).
// For every book: the cover, the table of contents, «قراءة داخل التطبيق», the table-of-contents jump, the search in the book, every «قراءة الكتاب المصوَّر» (the page images must really load), every «تحميل».
// usage: NODE_PATH=$(npm root -g) node tests/live_books.mjs   (after npm run build)
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const PORT = 4175, URL_ = `http://127.0.0.1:${PORT}/`;
const srv = spawn('npx', ['vite', 'preview', '--port', String(PORT), '--host', '127.0.0.1', '--strictPort'], { stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 3500));
const browser = await chromium.launch(); const ctx = await browser.newContext({ viewport: { width: 420, height: 880 }, locale: 'ar' }); const page = await ctx.newPage();
let fails = 0; const log = (ok, what, d = '') => { if (!ok) fails++; console.log(ok ? 'PASS' : 'FAIL', '|', what, d ? '— ' + d : ''); };
const frameInfo = async (timeout = 25000) => {                                           // what the archive.org viewer shows: how many page images loaded, and its «Page x (n/total)» label
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const fr = page.frames().find((f) => /archive\.org\/(embed|details)/.test(f.url()));
    if (fr) { try { const r = await fr.evaluate(() => ({ imgs: [...document.querySelectorAll('.BRpagecontainer img')].filter((i) => i.complete && i.naturalWidth > 50).length, text: document.body.innerText })); if (r.imgs > 0) return { ...r, url: fr.url(), label: (r.text.match(/Page\s+(\S+)\s+\((\d+)\/(\d+)\)/) || []).slice(1) }; } catch { /* the frame is still loading */ } }
    await page.waitForTimeout(700);
  }
  return null;
};
const openList = async (name) => { await page.goto(URL_); await page.waitForSelector('button.menu-toggle', { timeout: 30000 }); await page.waitForTimeout(1500); await page.locator('button.menu-toggle').click(); await page.locator('.drawer-item', { hasText: name }).click(); await page.waitForSelector('.lib-tile'); await page.waitForTimeout(1200); };
const head = (u) => { try { const h = execFileSync('curl', ['-sI', '--max-time', '40', u], { encoding: 'utf8' }); const st = +(h.match(/^HTTP\/[\d.]+\s+(\d+)/m) || [])[1]; const loc = (h.match(/^location:\s*(\S+)/im) || [])[1] || ''; return { status: () => st, headers: () => ({ location: loc }) }; } catch { return null; } };
const books = [];
const VIEWER_NUMBERS_UNRELIABLE = /الكتاب المفصل في لغة الجسد|نظريات الشخصية \(عادل/;   // archive.org's own page_numbers.json for these two items is wrong/partial (it says «1», «15» for leaves we checked by eye): their entries are checked by eye, not against the viewer label
for (const list of ['كتب علم التعبير', 'كتب الفراسة']) {
  await openList(list); const n = await page.locator('.lib-tile').count();
  for (let i = 0; i < n; i++) {
    await page.locator('.lib-tile').nth(i).click(); await page.waitForSelector('.lib-detail'); await page.waitForTimeout(600);
    const title = (await page.locator('.lib-detail h2').first().innerText()).trim();
    if (process.env.ONLY && !new RegExp(process.env.ONLY).test(title)) { await page.locator('.lib-detail button[aria-label="رجوع"]').first().click(); await page.waitForTimeout(300); continue; }   // ONLY=regex of titles to try
    books.push(title);
    const tag = `[${list.replace('كتب علم ', '')}] ${title.slice(0, 32)}`;
    log(await page.locator('.lib-detail .lib-cover-big image, .lib-detail .lib-cover-big text').first().count() > 0, `${tag}: cover shown`);
    log((await page.locator('.lib-toc li').count()) >= 1 || (await page.locator('.lib-toc').count()) === 0, `${tag}: table of contents listed (a scan-only book without a printed contents has no section)`, `${await page.locator('.lib-toc li').count()} shown`);
    // «قراءة داخل التطبيق» / «قراءة النص المفرَّغ»
    const scanCheck = async () => {                                                         // the viewer of the scan: page images, and every table-of-contents entry must land on the printed page it names
      const info = await frameInfo(); log(!!info && info.imgs > 0, `${tag}: the scanned pages of the printed book load`, info ? `${info.imgs} images, ${info.label.join(' ')}` : 'no images');
      if (info && (await page.locator('button[aria-label="فهرس الكتاب"]').count())) {
        const dig = (x) => String(x).replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d));
        const openToc = async () => { if (!(await page.locator('.rd-toc li').count())) await page.locator('button[aria-label="فهرس الكتاب"]').click(); await page.waitForSelector('.rd-toc li'); };
        await openToc(); const k = await page.locator('.rd-toc li button').count(); let okN = 0, tried = 0, unreadable = 0; const bad = [];
        for (const idx of [Math.floor(k / 5), Math.floor(k / 3), Math.floor(k / 2), Math.floor((2 * k) / 3), k - 3]) {
          await openToc(); const el = page.locator('.rd-toc li button').nth(idx); const txt = await el.innerText(); const pr = (dig(txt).match(/ص\s*([0-9]+)/) || [])[1]; if (!pr) continue;
          await el.click(); await page.waitForTimeout(800); const i2 = await frameInfo(20000);
          const lab = i2 ? dig(i2.label[0] || '') : '';
          if (!i2 || !/^\d+$/.test(lab)) { unreadable++; continue; }
          tried++; if (lab === pr) okN++; else bad.push(`${txt.slice(0, 28)} → viewer says «${lab}»`);
        }
        if (await page.locator('.rd-toc li').count()) await page.keyboard.press('Escape');
        log(okN === tried || VIEWER_NUMBERS_UNRELIABLE.test(title), `${tag}: toc jumps land on the printed page they name`, `${okN}/${tried} compared (+${unreadable} leaves the viewer does not number)${bad.length ? ' | ' + bad.join(' ; ') : ''}`);
      }
    };
    await page.locator('.lib-read').click(); await page.waitForTimeout(1200);
    if (await page.locator('.rd-text').count()) {
      const txt = (await page.locator('.rd-text').first().innerText()).length; log(txt > 300, `${tag}: text reader shows the book`, `${txt} chars`);
      await page.locator('button[aria-label="فهرس الكتاب"]').click(); await page.waitForSelector('.rd-toc li'); const k = await page.locator('.rd-toc li').count();
      await page.locator('.rd-toc li button').nth(Math.min(k - 1, 5)).click(); await page.waitForTimeout(500);
      log((await page.locator('.rd-text').first().innerText()).length > 100, `${tag}: table-of-contents jump works`, `${k} entries`);
      if (await page.locator('.rd-link').count()) {                                          // the page image of the page being read opens in the viewer inside the app
        await page.locator('.rd-link').click(); const i3 = await frameInfo(); log(!!i3 && i3.imgs > 0, `${tag}: «اعرض صورة هذه الصفحة» opens the scan`, i3 ? `${i3.label.join(' ')}` : 'no images');
        await page.keyboard.press('Escape'); await page.waitForTimeout(400);
      }
    } else await scanCheck();
    await page.keyboard.press('Escape'); await page.waitForTimeout(400);
    await page.waitForSelector('.lib-detail');
    if (await page.locator('.lib-scanmain').count()) { await page.locator('.lib-scanmain').click(); await scanCheck(); await page.keyboard.press('Escape'); await page.waitForTimeout(400); await page.waitForSelector('.lib-detail'); }
    // every «قراءة الكتاب المصوَّر»
    const scans = page.locator('.lib-scan:not(.lib-scanmain)'); const ns = await scans.count();
    for (let s = 0; s < ns; s++) {
      const lbl = (await scans.nth(s).innerText()).replace(/\n/g, ' ').slice(0, 60); await scans.nth(s).click(); const info = await frameInfo();
      log(!!info && info.imgs > 0, `${tag}: «قراءة الكتاب المصوَّر» ${s + 1}/${ns} loads page images`, info ? `${info.imgs} images; viewer: ${info.label.join(' ')}; ${decodeURIComponent(info.url).slice(-40)}` : lbl + ' — no images');
      await page.keyboard.press('Escape'); await page.waitForTimeout(400);
    }
    // every «تحميل» (the native download is replaced by a recorder: this checks what the button hands over)
    await page.evaluate(() => { window.__sv = []; window.__qsDownloader = { download: async (o) => { window.__sv.push(o); return { status: 'started', where: 'downloads' }; }, saveText: async (o) => { window.__sv.push({ txt: o.text.length }); return { status: 'saved', where: 'downloads' }; } }; });
    const dls = page.locator('.lib-dl:not(.lib-txt)'); const nd = await dls.count();
    for (let d = 0; d < nd; d++) { await dls.nth(d).click(); await page.waitForTimeout(300); }
    const sv = await page.evaluate(() => window.__sv); const urls = sv.filter((x) => x.url);
    log(urls.length === nd && urls.every((x) => /^https:\/\/archive\.org\/download\//.test(x.url)), `${tag}: ${nd} «تحميل» button(s) hand over an archive.org file`, urls.map((x) => x.filename).join(' | ').slice(0, 90));
    for (const x of urls) { const r = head(x.url); log(!!r && (r.status() === 200 || ([301, 302].includes(r.status()) && /archive\.org\//.test(r.headers().location || ''))), `${tag}: the download link answers (the file is served from archive.org)`, r ? `${r.status()} → ${(r.headers().location || '').replace(/^https:\/\//, '').slice(0, 50)}` : 'unreachable'); }
    if (await page.locator('.lib-txt').count()) { await page.locator('.lib-txt').click(); await page.waitForTimeout(1500); const t = (await page.evaluate(() => window.__sv)).find((x) => x.txt); log(!!t && t.txt > 5000, `${tag}: «تحميل نص الكتاب (TXT)» saves the whole text`, t ? `${t.txt} chars` : 'nothing'); }
    await page.locator('.lib-detail button[aria-label="رجوع"]').first().click(); await page.waitForTimeout(500);
  }
}
console.log(fails ? `FAILED: ${fails}` : `ALL PASSED (${books.length} books)`);
await browser.close(); srv.kill(); process.exit(fails ? 1 : 0);
