// End-to-end test-suite (Playwright + axe-core) against the production build. usage: NODE_PATH=$(npm root -g) node tests/e2e.mjs
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const axeSrc = readFileSync(new URL('../node_modules/axe-core/axe.min.js', import.meta.url), 'utf8');
const meta = JSON.parse(readFileSync(new URL('../data/meta.json', import.meta.url), 'utf8'));
const PORT = 4174, URL_ = `http://127.0.0.1:${PORT}/`;
const srv = spawn('npx', ['vite', 'preview', '--port', String(PORT), '--host', '127.0.0.1', '--strictPort'], { stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 3500)); mkdirSync('tests/screenshots', { recursive: true });
const results = []; const log = (group, name, pass, detail = '') => { results.push({ group, name, pass: !!pass, detail }); console.log(pass ? 'PASS' : 'FAIL', '|', group, '|', name, detail ? '— ' + detail : ''); };
const browser = await chromium.launch(); const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'ar' }); const page = await ctx.newPage();
const errors = [], requests = [];
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message)); page.on('console', (m) => { if (m.type() === 'error' && !/404/.test(m.text())) errors.push('console: ' + m.text().slice(0, 160)); }); page.on('request', (r) => requests.push(r.url()));
const toNum = (s) => +String(s).replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).replace(/\D/g, '');
const TAB = { quran: 'القرآن الكريم', jami: 'السنة النبوية', amthal: 'الأمثال', alfiya: 'الألفية الوردية' };
const panel = (t) => page.locator(`#panel-${t}`);
const go = async () => { await page.goto(URL_); await page.waitForFunction(() => document.querySelector('#panel-quran button.go') && !document.querySelector('#panel-quran .pulse'), null, { timeout: 30000 }); await page.waitForFunction(() => document.querySelectorAll('.tab').length === 4); await page.waitForTimeout(1800); };
const search = async (t, q) => { await page.getByRole('tab', { name: TAB[t] }).click(); await panel(t).locator('input').fill(q); await panel(t).locator('button.go').click(); await panel(t).locator('article, .soft').first().waitFor({ timeout: 20000 }); await page.waitForTimeout(350); };
const cards = (t) => panel(t).locator('article.verse-card');
const stats = async (t) => (await panel(t).locator('.stats').first().innerText().catch(() => '')).replace(/\s+/g, ' ');

let t0 = Date.now(); await go(); log('الأداء', 'جاهزية الصفحة والفهرس بعد التحميل', Date.now() - t0 < 9000, Date.now() - t0 + ' ms');
await page.screenshot({ path: 'tests/screenshots/home.png' });

// ---------- structure = the original ----------
const h1 = await page.locator('h1').innerText(); log('مطابقة الأصل', 'العنوان «الباحث القرآني»', h1.trim() === 'الباحث القرآني');
log('مطابقة الأصل', 'الشارة العلوية ونص التعريف كما في الأصل', (await page.locator('.badge-top').innerText()).includes('بحث نصّي دقيق مع توسعة دلالية اشتقاقية') && (await page.locator('.hero p').innerText()).includes('منصّة بحث شرعي في القرآن الكريم والسنة النبوية الصحيحة'));
log('مطابقة الأصل', 'أربعة تبويبات: القرآن الكريم، السنة النبوية، الأمثال، الألفية الوردية', JSON.stringify(await page.locator('.tab').allInnerTexts()) === JSON.stringify(['القرآن الكريم', 'السنة النبوية', 'الأمثال', 'الألفية الوردية']));
log('مطابقة الأصل', 'نص الإرشاد والتلميح لتبويب القرآن كما في الأصل', (await panel('quran').locator('input').getAttribute('placeholder')) === 'اكتب كلمة أو عبارة قرآنية… مثال: مفتاح، الصبر، الرحمة' && (await panel('quran').locator('.hint').innerText()).includes('البحث يبدأ مطابقاً لرسم المصحف'));
log('مطابقة الأصل', 'الحالة الأولى: «ابدأ بكتابة كلمة أو عبارة في الأعلى لعرض النتائج هنا.»', (await panel('quran').locator('.soft').innerText()).includes('ابدأ بكتابة كلمة أو عبارة في الأعلى لعرض النتائج هنا.'));
const extras = await page.evaluate(() => ({ links: document.querySelectorAll('a[href]').length, checks: document.querySelectorAll('input[type=checkbox], select').length, nav: document.querySelectorAll('nav, header nav').length, fav: [...document.querySelectorAll('button:not(.theme-toggle)')].some((b) => /المفضلة|السجل|الفلاتر|للأعلى|مشاركة|^نسخ|تغيير الخلفية|الوضع/.test(b.innerText + (b.getAttribute('aria-label') || ''))) }));
log('مطابقة الأصل', 'لا فلاتر ولا مفضلة ولا سجل ولا قوائم ولا روابط ولا أزرار إضافية (عدا زر الوضع الداكن/الفاتح المطلوب)', extras.links === 0 && extras.checks === 0 && extras.nav === 0 && !extras.fav, JSON.stringify(extras));
const geo = await page.evaluate(() => { const g = (s) => document.querySelector(s).getBoundingClientRect(); const c = (s, p) => getComputedStyle(document.querySelector(s))[p]; return { inputH: g('#q-quran').height, inputR: c('#q-quran', 'borderRadius'), btnH: g('#panel-quran button.go').height, btnR: c('#panel-quran button.go', 'borderRadius'), tabR: c('.tab', 'borderRadius'), tabsR: c('.tabs', 'borderRadius') }; });
log('مطابقة الأصل', 'مقاسات عناصر التحكم كما في الأصل (حقل ٥٦px/١٦، زر ٤٠px/١٢، تبويب ١٢، حاوية ١٦)', Math.round(geo.inputH) === 56 && geo.inputR === '16px' && Math.round(geo.btnH) === 40 && geo.btnR === '12px' && geo.tabR === '12px' && geo.tabsR === '16px', JSON.stringify(geo));
const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundImage); log('الخلفية', 'خلفية الصفحة الجديدة (تدرجات + نقش هندسي)', /radial-gradient/.test(bg) && /url\(/.test(bg) && /linear-gradient/.test(bg));
log('الخلفية', 'الورقة المحتوية بلون الأصل الفاتح (القوائم والأزرار على خلفيتها الأصلية)', await page.evaluate(() => /oklch\(0\.97/.test(getComputedStyle(document.querySelector('.sheet')).backgroundColor)));

// ---------- Quran ----------
await search('quran', 'مفتاح');
const verses = await cards('quran').evaluateAll((a) => a.map((x) => x.querySelector('.card-ref .t').textContent + ' ' + x.querySelector('.card-ref .s').textContent));
log('البحث في القرآن', '«مفتاح» ← الآيات الأربع نفسها وبالترتيب نفسه كالأصل (الأنعام ٥٩، النور ٦١، القصص ٧٦، ص ٥٠)', verses.length === 4 && /الأنعام/.test(verses[0]) && /٥٩/.test(verses[0]) && /النور/.test(verses[1]) && /٦١/.test(verses[1]) && /القصص/.test(verses[2]) && /٧٦/.test(verses[2]) && /ص/.test(verses[3]) && /٥٠/.test(verses[3]), verses.join(' | '));
log('البحث في القرآن', 'شريط الإحصاء: «نتائج مطابقة نصياً: ٤» وكل الشارات «مطابقة نصية»', (await stats('quran')).includes('نتائج مطابقة نصياً: ٤') && (await panel('quran').locator('.pill-text').count()) === 4);
log('البحث في القرآن', 'الكلمة المطابقة مظلَّلة داخل الآية', (await panel('quran').locator('mark.search-hit').count()) >= 4);
await search('quran', 'الصلاه'); log('البحث في القرآن', '«الصلاه» ← ٦٦ نتيجة (كما في الأصل)', toNum((await stats('quran')).match(/نصياً: ([٠-٩]+)/)[1]) === 66, (await stats('quran')).slice(0, 60));
await search('quran', 'يؤمنون'); log('البحث في القرآن', 'سقف ٨٠ نتيجة كما في الأصل (مع التنبيه «عُرضت أول ٨٠»)', (await cards('quran').count()) === 80 && (await stats('quran')).includes('عُرضت أول ٨٠'));
await search('quran', 'قل هو الله احد'); log('البحث في القرآن', 'عبارة متعددة الكلمات «قل هو الله احد» ← سورة الإخلاص (يخفق الأصل فيها)', (await cards('quran').first().innerText()).includes('الإخلاص'));
await search('quran', 'بِسْمِ ٱللَّهِ'); log('التشكيل', 'استعلام مشكَّل بالرسم العثماني ← الفاتحة ١', (await cards('quran').first().innerText()).includes('الفاتحة'));
await search('quran', 'بسم الله'); log('التشكيل', 'الاستعلام نفسه بلا تشكيل ← الفاتحة ١ أيضاً', (await cards('quran').first().innerText()).includes('الفاتحة'));
await search('quran', 'ولقد يسرنا القرآن للذكر فهل من مدكر'); log('البحث', 'عبارة طويلة ← سورة القمر', (await cards('quran').first().innerText()).includes('القمر'));
await search('quran', 'xyzqq'); log('الحالات', 'لا نتائج ← «لم نعثر على آيات تطابق بحثك حتى بعد التوسعة الدلالية.»', (await panel('quran').locator('.soft').innerText()).includes('لم نعثر على آيات تطابق بحثك حتى بعد التوسعة الدلالية.'));
await page.getByRole('tab', { name: TAB.quran }).click(); await panel('quran').locator('input').fill('صبر'); await panel('quran').locator('button.go').click(); await page.waitForTimeout(120);
log('الحالات', 'حالة التحميل: «جارٍ البحث…» وهياكل البطاقات أثناء البحث', (await panel('quran').locator('button.go').innerText()).includes('جارٍ البحث') && (await panel('quran').locator('.pulse').count()) >= 0);
await panel('quran').locator('article').first().waitFor();

// ---------- Sunnah = al-Jami' al-Saghir only ----------
await search('jami', 'النية'); const jt = await panel('jami').innerText();
log('السنة النبوية', '«النية» ← نتائج أحاديث مع رقم صفحة PDF ووسم مصدر النص (مدقَّق / قراءة آلية)', (await cards('jami').count()) > 0 && /حديث رقم/.test(jt) && /صفحة [٠-٩]+/.test(jt) && /(مدقَّق على صورة الصفحة|قراءة آلية غير مراجَعة)/.test(jt), (await stats('jami')).slice(0, 80));
let semOk = false, semWord = ''; for (const w of ['العزم', 'الاحتساب', 'التحمل', 'السخاء', 'الشفقة', 'الجود']) { await search('jami', w); if ((await stats('jami')).includes('نتائج دلالية إضافية') && (await panel('jami').locator('.pill-sem').count()) > 0) { semOk = true; semWord = w; break; } }
log('السنة النبوية', 'التوسعة الدلالية تُفعَّل عند قلة النتائج ويظهر «دلالي: …» وشارة الجذر/الألفاظ', semOk, semWord);
await search('jami', 'الجار'); log('السنة النبوية', '«الجار» ← حتى ٨٠ نتيجة بلا ترقيم صفحات', (await cards('jami').count()) > 0 && (await cards('jami').count()) <= 80);
await search('jami', 'قشطة'); log('الحالات', 'لا نتائج ← «لم نعثر على أحاديث تطابق بحثك.»', (await panel('jami').locator('.soft').innerText()).includes('لم نعثر على أحاديث تطابق بحثك.'));
const allTxt = await page.evaluate(() => document.body.innerText);
log('المصادر', 'لا أثر لصحيح البخاري/مسلم في الواجهة', !/صحيح البخاري|صحيح مسلم/.test(await page.locator('.hero, .tabs, .foot, .hint').allInnerTexts().then((a) => a.join(' '))));
const dataReq = [...new Set(requests.filter((u) => /\/content\//.test(u)).map((u) => u.split('/').pop()))];
log('المصادر', 'لا تُحمَّل بيانات سوى مصادر الموقع', dataReq.length > 0 && dataReq.every((f) => /^(quran|jami|amthal|alfiya|manifest)\./.test(f)), dataReq.join(', '));

// ---------- الألفية الوردية ----------
await search('alfiya', 'الأسد'); const at = await panel('alfiya').innerText();
log('الألفية الوردية', '«الأسد» ← أبيات من الألفية بنصّ الشطرين ورقم البيت والصفحة والباب', (await cards('alfiya').count()) > 0 && /البيت [٠-٩]+/.test(at) && /صفحة [٠-٩]+/.test(at) && /باب/.test(at), (await stats('alfiya')).slice(0, 80));
log('الألفية الوردية', 'البيت ٥٢١ «والليث سلطان فمن سطا به» يُعثر عليه بالبحث عن «الليث»', (await (async () => { await search('alfiya', 'الليث'); return /والليث سلطان فمن سطا به/.test(await panel('alfiya').innerText()); })()));
log('الألفية الوردية', 'المصطلح يُفرَّغ من حقل البحث بعد البحث', (await panel('alfiya').locator('input').inputValue()) === '');
log('الألفية الوردية', 'كل بيت شطران (عمودان) في البطاقة', (await cards('alfiya').first().locator('.poem-shatr').count()) === 2);
await search('alfiya', 'قشطة'); log('الحالات', 'لا نتائج ← «لم نعثر على أبيات تطابق بحثك.»', (await panel('alfiya').locator('.soft').innerText()).includes('لم نعثر على أبيات تطابق بحثك.'));

// ---------- الألفية: حرف واحد = باب ذلك الحرف ----------
const letterCase = async (q, title, count) => { await search('alfiya', q); const tx = await panel('alfiya').innerText(); const nCards = await cards('alfiya').count(); const pills = await panel('alfiya').locator('.pill').count(); return tx.includes(title) && nCards === count && pills === 0; };
log('الألفية الوردية', 'كتابة «و» ← باب حرف الواو وأبياته فقط (بيتان)', await letterCase('و', 'باب حرف الواو', 2));
log('الألفية الوردية', 'كتابة «ظ» ← باب حرف الظاء (بيت واحد)', await letterCase('ظ', 'باب حرف الظاء', 1));
log('الألفية الوردية', 'كتابة «أ» ← باب حرف الألف (٦ أبيات)', await letterCase('أ', 'باب حرف الألف', 6));
log('الألفية الوردية', 'كتابة «ي» ← باب حرف الياء بلا أبيات الخاتمة (٢٨ بيتاً)', await letterCase('ي', 'باب حرف الياء', 28));
await search('alfiya', 'الواو'); log('الألفية الوردية', 'لفظ من أكثر من حرف ← بحث كالمعتاد لا عرض باب', !(await panel('alfiya').innerText()).includes('باب حرف') || (await panel('alfiya').locator('.pill').count()) > 0);
// ---------- الوضع الداكن / الفاتح ----------
const themeNow = () => page.evaluate(() => document.documentElement.dataset.theme);
const th0 = await themeNow(); await page.locator(".theme-toggle").click(); const th1 = await themeNow();
log('الوضع الداكن/الفاتح', 'زر في الزاوية العلوية يبدّل بين الداكن والفاتح', (th0 === "dark" || th0 === "light") && th1 !== th0 && (await page.locator('.theme-toggle').getAttribute('aria-label')).includes('التبديل إلى'));
log('الوضع الداكن/الفاتح', 'الاختيار يُحفَظ ويبقى بعد إعادة التحميل', await (async () => { await page.reload(); await page.waitForTimeout(1500); return (await themeNow()) === th1; })());
const bgOf = () => page.evaluate(() => getComputedStyle(document.querySelector('.sheet')).backgroundColor + '|' + getComputedStyle(document.querySelector('.hero h1')).color);
const bgA = await bgOf(); await page.locator('.theme-toggle').click(); const bgB = await bgOf();
log('الوضع الداكن/الفاتح', 'لون الصفحة والعنوان يتغيّران فعلاً عند التبديل', bgA !== bgB, bgA + ' → ' + bgB);
if ((await themeNow()) !== 'dark') await page.locator('.theme-toggle').click();
log('الوضع الداكن', 'عنوان «الباحث القرآني» أبيض في الوضع الداكن', (await page.evaluate(() => getComputedStyle(document.querySelector('.hero h1')).color)) === 'rgb(255, 255, 255)');
await page.evaluate(axeSrc); const axeDark = await page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa'] })).violations.map((v) => v.id));
log('الوضع الداكن', 'بلا مخالفات وصول/تباين (axe)', axeDark.length === 0, axeDark.join(' '));
if ((await themeNow()) !== 'light') await page.locator('.theme-toggle').click();
await page.evaluate(axeSrc); const axeLight = await page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa'] })).violations.map((v) => v.id));
log('الوضع الفاتح', 'بلا مخالفات وصول/تباين (axe)', axeLight.length === 0, axeLight.join(' '));

// ---------- الأمثال ----------
await search('amthal', 'الجار'); const amT = await panel('amthal').innerText();
log('الأمثال', 'البحث في الأمثال يعرض أمثالاً مع باب الحرف وزر «شرح»', (await cards('amthal').count()) > 0 && /حرف /.test(amT) && (await panel('amthal').locator('button.sharh').count()) > 0, (await stats('amthal')).slice(0, 80));
await panel('amthal').locator('button.sharh').first().click(); log('الأمثال', 'زر «شرح» يفتح شرح المثل', (await panel('amthal').locator('.sharh-text').count()) === 1 && (await panel('amthal').locator('.sharh-text').innerText()).length > 20);
await search('amthal', 'xyzqq'); log('الحالات', 'لا نتائج في الأمثال ← «لم نعثر على نتائج تطابق بحثك.»', (await panel('amthal').locator('.soft').innerText()).includes('لم نعثر على نتائج تطابق بحثك.'));

log('مطابقة الأصل', 'لا أمثلة ولا أزرار أمثلة تحت زر البحث', (await page.locator('.ex-chip, .examples').count()) === 0 && !(await page.locator('.sform').first().innerText()).includes('أمثلة:'));
log('مطابقة الأصل', 'التذييل تعريف عام بسيط بلا أسماء كتب', (await page.locator('.foot').innerText()).trim() === 'منصّة بحث في القرآن الكريم والسنة النبوية. لا يُعرض أي تفسير أو رأي شخصي.');

await search('quran', 'الصبر'); log('البحث', 'المصطلح المبحوث عنه يُفرَّغ من حقل البحث تلقائياً بعد البحث', (await panel('quran').locator('input').inputValue()) === '' && (await cards('quran').count()) > 0);
await search('jami', 'الماء البارد'); log('السنة النبوية', 'حديث «إذا حم أحدكم فليشن عليه الماء البارد» مصحَّح ويُعثر عليه', /فليشن عليه الماء البارد/.test(await cards('jami').first().innerText()) || (await panel('jami').innerText()).includes('فليشن عليه الماء البارد'));
// ---------- fonts / rtl / independence ----------
await page.getByRole('tab', { name: TAB.quran }).click(); await search('quran', 'الصبر');
const fr = await page.evaluate(() => { const bad = []; let n = 0; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); const seen = new Set(); let x; while ((x = w.nextNode())) { if (!x.nodeValue.trim()) continue; const el = x.parentElement; if (seen.has(el) || el.closest('[hidden]')) continue; seen.add(el); n++; const ff = getComputedStyle(el).fontFamily; if (el.closest('.quran-font')) { if (!/^"?Amiri Quran"?/.test(ff)) bad.push('verse:' + ff); } else if (!/^"?Dubai"?/.test(ff)) bad.push(el.tagName + '.' + el.className + ':' + ff); } const ctrl = [...document.querySelectorAll('button,input')].filter((e) => !/^"?Dubai/.test(getComputedStyle(e).fontFamily) && !e.closest('.quran-font')).length; return { n, bad: bad.slice(0, 4), count: bad.length, ctrl, loaded: [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family) }; });
log('الخط', 'Dubai Bold على كل عنصر نصي وزر وحقل (عدا نص الآية)', fr.count === 0 && fr.ctrl === 0, `${fr.n} عنصراً؛ مخالفات ${fr.count}؛ ${fr.bad.join(' ; ')}`);
log('الخط', 'ملف Dubai-Bold.ttf محلي ومحمَّل لكل النصوص، ونص الآيات وحده بخط Amiri Quran المحلي ليطابق رسم المصحف', fr.loaded.includes('Dubai') && fr.loaded.includes('Amiri Quran') && requests.some((u) => /Dubai-Bold\.ttf/.test(u)), fr.loaded.join(','));
const rtl = await page.evaluate(() => ({ d: document.documentElement.dir, l: document.documentElement.lang, i: getComputedStyle(document.querySelector('input')).direction })); log('RTL', 'dir=rtl وlang=ar وحقل البحث rtl', rtl.d === 'rtl' && rtl.l === 'ar' && rtl.i === 'rtl');
const hosts = [...new Set(requests.map((u) => new URL(u).host).filter((h) => h !== `127.0.0.1:${PORT}`))]; log('الاستقلال', 'لا طلبات خارجية (خطوط/صور/سكربتات)', hosts.length === 0, hosts.join(','));
log('العلامة المائية', 'لا أي أثر لـLovable في الصفحة أو الشبكة', !/lovable/i.test(await page.content()) && !requests.some((u) => /lovable/i.test(u)));
await page.screenshot({ path: 'tests/screenshots/quran_results.png', fullPage: true });
await page.getByRole('tab', { name: TAB.jami }).click(); await search('jami', 'الصدقة'); await page.screenshot({ path: 'tests/screenshots/jami_results.png' });
await page.getByRole('tab', { name: TAB.amthal }).click(); await page.screenshot({ path: 'tests/screenshots/amthal.png' });

// ---------- responsive ----------
for (const [w, h] of [[390, 844], [768, 1024], [1366, 900]]) {
  const c2 = await browser.newContext({ viewport: { width: w, height: h }, locale: 'ar' }); const p2 = await c2.newPage(); await p2.goto(URL_); await p2.waitForTimeout(2500);
  await p2.locator('#panel-quran input').fill('الصبر'); await p2.locator('#panel-quran button.go').click(); await p2.locator('#panel-quran article').first().waitFor(); await p2.waitForTimeout(300);
  log('الاستجابة', `${w}×${h}: بلا تمرير أفقي مع النتائج`, !(await p2.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)));
  if (w === 390) await p2.screenshot({ path: 'tests/screenshots/mobile_results.png' }); if (w === 768) await p2.screenshot({ path: 'tests/screenshots/tablet_results.png' });
  await c2.close();
}
// ---------- performance ----------
await page.getByRole('tab', { name: TAB.quran }).click(); await panel('quran').locator('input').fill('الرحمة');
const ms = await page.evaluate(async () => { const t = performance.now(); document.querySelector('#panel-quran button.go').click(); while (!document.querySelector('#panel-quran article')) await new Promise((r) => setTimeout(r, 5)); return performance.now() - t; });
log('الأداء', 'زمن البحث حتى ظهور النتائج (يشمل ٢٥٠ م.ث تأخير حالة التحميل المقصود)', ms < 900, Math.round(ms) + ' ms');
// ---------- accessibility ----------
const axeRes = {};
for (const [name, tab] of [['الصفحة الرئيسية (قرآن)', 'quran'], ['السنة النبوية', 'jami']]) { await page.goto(URL_); await page.waitForTimeout(2200); await page.getByRole('tab', { name: TAB[tab] }).click(); await panel(tab).locator('input').fill('الجار'); await panel(tab).locator('button.go').click(); await panel(tab).locator('article, .soft').first().waitFor(); await page.evaluate(axeSrc); const r = await page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'best-practice'] })).violations.map((v) => ({ id: v.id, impact: v.impact, n: v.nodes.length }))); axeRes[name] = r; const bad = r.filter((v) => v.impact === 'serious' || v.impact === 'critical'); log('إمكانية الوصول (axe)', `${name}: بلا مخالفات خطيرة/حرجة`, bad.length === 0, r.map((v) => `${v.id}(${v.impact}×${v.n})`).join(' ') || 'لا مخالفات'); }
log('الأخطاء', 'لا أخطاء JavaScript في وحدة التحكم', errors.length === 0, errors.slice(0, 3).join(' | '));
writeFileSync('tests/last-run.json', JSON.stringify({ at: new Date().toISOString(), axe: axeRes, meta, results }, null, 1));
const fails = results.filter((r) => !r.pass); console.log(`\nSUMMARY: ${results.length - fails.length}/${results.length} passed`); fails.forEach((f) => console.log('  FAIL', f.group, f.name, f.detail));
await browser.close(); srv.kill(); process.exit(fails.length ? 1 : 0);
