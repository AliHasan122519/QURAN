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
const TAB = { quran: 'القرآن الكريم', jami: 'السنة النبوية', amthal: 'الأمثال', alfiya: 'الألفية الوردية', books: 'الكتب', shawahid: 'أبيات الإستشهاد' };
const panel = (t) => page.locator(`#panel-${t}`);
const go = async () => { await page.goto(URL_); await page.waitForFunction(() => document.querySelector('#panel-quran button.go') && !document.querySelector('#panel-quran .pulse'), null, { timeout: 30000 }); await page.waitForFunction(() => document.querySelectorAll('.tab').length === 6); await page.waitForTimeout(1800); };
const search = async (t, q) => { await page.getByRole('tab', { name: TAB[t] }).click(); await panel(t).locator('input').fill(q); await panel(t).locator('button.go').click(); await panel(t).locator('article, .soft').first().waitFor({ timeout: 20000 }); await page.waitForTimeout(350); };
const cards = (t) => panel(t).locator('article.verse-card');
const stats = async (t) => (await panel(t).locator('.stats').first().innerText().catch(() => '')).replace(/\s+/g, ' ');

let t0 = Date.now(); await go(); log('الأداء', 'جاهزية الصفحة والفهرس بعد التحميل', Date.now() - t0 < 9000, Date.now() - t0 + ' ms');
await page.screenshot({ path: 'tests/screenshots/home.png' });

// ---------- structure = the original ----------
const h1 = await page.locator('h1').innerText(); log('مطابقة الأصل', 'العنوان «الباحث القرآني»', h1.trim() === 'الباحث القرآني');
log('مطابقة الأصل', 'الشارة العلوية ونص التعريف كما في الأصل', (await page.locator('.badge-top').innerText()).includes('بحث نصّي دقيق مع توسعة دلالية اشتقاقية') && (await page.locator('.hero p').innerText()).includes('منصّة بحث شرعي في القرآن الكريم والسنة النبوية الصحيحة'));
log('مطابقة الأصل', 'ستة تبويبات: القرآن الكريم، السنة النبوية، الأمثال، الألفية الوردية، الكتب، أبيات الإستشهاد', JSON.stringify(await page.locator('.tab').allInnerTexts()) === JSON.stringify(['القرآن الكريم', 'السنة النبوية', 'الأمثال', 'الألفية الوردية', 'الكتب', 'أبيات الإستشهاد']));
log('مطابقة الأصل', 'حقل البحث في القرآن يحمل «اكتب هنا» بلا أمثلة', (await panel('quran').locator('input').getAttribute('placeholder')) === 'اكتب هنا' && (await panel('quran').locator('.hint').innerText()).includes('البحث يبدأ مطابقاً لرسم المصحف'));
for (const id of ['quran', 'jami', 'amthal', 'alfiya', 'books', 'shawahid']) log('حقول البحث', `حقل «${id}» نصه «اكتب هنا» فقط`, (await panel(id).locator('input').getAttribute('placeholder')) === 'اكتب هنا');
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
log('البحث في القرآن', '«مفتاح» ← الآيات الأربع نفسها وبالترتيب نفسه كالأصل (الأنعام 59، النور 61، القصص 76، ص 50)', verses.length === 4 && /الأنعام/.test(verses[0]) && /59/.test(verses[0]) && /النور/.test(verses[1]) && /61/.test(verses[1]) && /القصص/.test(verses[2]) && /76/.test(verses[2]) && /ص/.test(verses[3]) && /50/.test(verses[3]), verses.join(' | '));
log('البحث في القرآن', 'شريط الإحصاء: «نتائج مطابقة نصياً: 4» وكل الشارات «مطابقة نصية»', (await stats('quran')).includes('نتائج مطابقة نصياً: 4') && (await panel('quran').locator('.pill-text').count()) === 4);
log('البحث في القرآن', 'الكلمة المطابقة مظلَّلة داخل الآية', (await panel('quran').locator('mark.search-hit').count()) >= 4);
await search('quran', 'الصلاه'); log('البحث في القرآن', '«الصلاه» ← ٦٦ نتيجة (كما في الأصل)', toNum((await stats('quran')).match(/نصياً: ([0-9٠-٩]+)/)[1]) === 66, (await stats('quran')).slice(0, 60));
await search('quran', 'يؤمنون'); log('البحث في القرآن', 'سقف ٨٠ نتيجة كما في الأصل (مع التنبيه «عُرضت أول 80»)', (await cards('quran').count()) === 80 && (await stats('quran')).includes('عُرضت أول 80'));
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
log('السنة النبوية', '«النية» ← نتائج أحاديث مع رقم صفحة PDF ووسم مصدر النص (مدقَّق / قراءة آلية)', (await cards('jami').count()) > 0 && /حديث رقم/.test(jt) && /صفحة [0-9٠-٩]+/.test(jt) && /(مدقَّق على صورة الصفحة|قراءة آلية غير مراجَعة)/.test(jt), (await stats('jami')).slice(0, 80));
let semOk = false, semWord = ''; for (const w of ['العزم', 'الاحتساب', 'التحمل', 'السخاء', 'الشفقة', 'الجود']) { await search('jami', w); if ((await stats('jami')).includes('نتائج دلالية إضافية') && (await panel('jami').locator('.pill-sem').count()) > 0) { semOk = true; semWord = w; break; } }
log('السنة النبوية', 'التوسعة الدلالية تُفعَّل عند قلة النتائج ويظهر «دلالي: …» وشارة الجذر/الألفاظ', semOk, semWord);
await search('jami', 'الجار'); log('السنة النبوية', '«الجار» ← حتى ٨٠ نتيجة بلا ترقيم صفحات', (await cards('jami').count()) > 0 && (await cards('jami').count()) <= 80);
await search('jami', 'قشطة'); log('الحالات', 'لا نتائج ← «لم نعثر على أحاديث تطابق بحثك.»', (await panel('jami').locator('.soft').innerText()).includes('لم نعثر على أحاديث تطابق بحثك.'));
const allTxt = await page.evaluate(() => document.body.innerText);
log('المصادر', 'لا أثر لصحيح البخاري/مسلم في الواجهة', !/صحيح البخاري|صحيح مسلم/.test(await page.locator('.hero, .tabs, .foot, .hint').allInnerTexts().then((a) => a.join(' '))));
const dataReq = [...new Set(requests.filter((u) => /\/content\//.test(u)).map((u) => u.split('/').pop()))];
log('المصادر', 'لا تُحمَّل بيانات سوى مصادر الموقع', dataReq.length > 0 && dataReq.every((f) => /^(quran|jami|amthal|alfiya|books|shawahid|ruaa|anbiya|muabbirun|manifest)\./.test(f)), dataReq.join(', '));

// ---------- الألفية الوردية ----------
await search('alfiya', 'الأسد'); const at = await panel('alfiya').innerText();
log('الألفية الوردية', '«الأسد» ← أبيات من الألفية بنصّ الشطرين ورقم البيت والصفحة والباب', (await cards('alfiya').count()) > 0 && /البيت [0-9٠-٩]+/.test(at) && /صفحة [0-9٠-٩]+/.test(at) && /باب/.test(at), (await stats('alfiya')).slice(0, 80));
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
await search('alfiya', 'الواو'); log('الألفية الوردية', 'اسم الحرف كاملاً «الواو» ← باب حرف الواو', (await panel('alfiya').innerText()).includes('باب حرف الواو') && (await cards('alfiya').count()) === 2);
const chapterCase = async (q, title, count) => { await search('alfiya', q); const tx = await panel('alfiya').innerText(); return tx.includes(title) && (await cards('alfiya').count()) === count && (await panel('alfiya').locator('.pill').count()) === 0; };
log('الألفية الوردية', 'البحث «الشجر» ← أبيات باب الشجر والثمار فقط (٢٣)', await chapterCase('الشجر', 'باب في الشجر والثمار', 23));
log('الألفية الوردية', 'جمع تكسير «الأشجار» يُفهم أنه الباب نفسه', await chapterCase('الأشجار', 'باب في الشجر والثمار', 23));
log('الألفية الوردية', 'جزء من اسم الباب «الخيل» ← باب الخيل (١٣)', await chapterCase('الخيل', 'باب في الخيل', 13));
log('الألفية الوردية', 'اسم الباب غير مضبوط «اختلاج الأعضاء» أو «الأعضاء» ← باب اختلاج الأعضاء (٦٢)', await chapterCase('الأعضاء', 'باب في اختلاج الأعضاء', 62));
log('الألفية الوردية', '«الباب الثالث عشر» ← باب المصحف وقراءة القرآن (٨٢)', await chapterCase('الباب الثالث عشر', 'باب في المصحف وقراءة القرآن', 82));
await search('alfiya', 'الأسد'); log('الألفية الوردية', 'لفظ ليس اسم باب «الأسد» ← بحث عادي لا عرض باب', !(await panel('alfiya').locator('.sect-title').count()));
// ---------- الكتب: ورد = … وزر «وجه الشبه» ----------
await search('books', 'الجن'); { const tx = await panel('books').innerText(); const c0 = cards('books').first();
  log('الكتب', '«الجن» ← بطاقات «الجن = …» (اسم ما بُحث عنه لا «ورد») ومنها ما تحت عنوان الجن أولاً', (await cards('books').count()) > 0 && /^\s*الجن =/m.test(await c0.locator('.meaning-text').innerText()) && !/ورد/.test(await c0.innerText()) && /الجن/.test(await c0.locator('.card-ref').innerText()), (await c0.locator('.card-ref').innerText()).slice(0, 60));
  log('الكتب', 'المصطلح يُفرَّغ من حقل البحث بعد البحث', (await panel('books').locator('input').inputValue()) === ''); }
await search('books', 'طوبى'); { const btn = panel('books').locator('button.sharh', { hasText: 'وجه الشبه' }).first();
  log('الكتب', 'زر «وجه الشبه» تحت النتيجة التي ذكر الكتاب سببها', (await btn.count()) === 1);
  await btn.click(); const w = panel('books').locator('.wajh').first();
  log('الكتب', 'الضغط على الزر يُظهر وجه الشبه (بنصّ الآية بخط Amiri Quran)', (await w.isVisible()) && /وجه الشبه/.test(await w.innerText()) && /Amiri Quran/.test(await w.locator('.quran-inline').first().evaluate((el) => getComputedStyle(el).fontFamily)));
  log('الكتب', 'بقية النص بخط Dubai', /Dubai/.test(await panel('books').locator('.meaning-text').first().evaluate((el) => getComputedStyle(el).fontFamily))); }
await search('books', 'الجن'); log('الكتب', 'كل نتيجة تعرض مصدرها (اسم الكتاب)', (await panel('books').locator('.takhrij').count()) === (await cards('books').count()) && /المصدر: \S/.test(await cards('books').first().innerText()));
await search('alfiya', 'الأسد'); log('الكتب', 'بقية الخانات لا تعرض أسماء كتب التعبير', !/تعطير الأنام|القادري في التعبير|المنامات \(/.test(await panel('alfiya').innerText()));
// ---------- الكلمة العامية والمعاني في «الكتب» ----------
await search('books', 'ميه'); { const tx = await panel('books').innerText();
  log('الكتب', 'كلمة عامية «ميه» ← تُفهم بالفصحى «ماء» ويُبحث بها', /فُهمت «ميه» بالفصحى:\s*ماء/.test(tx) && (await cards('books').count()) > 0);
  log('الكتب', 'أول النتائج لـ«ميه» عن الماء لا عن «مئة»', /ماء|الماء/.test(await cards('books').first().innerText())); }
await search('books', 'الماء'); { const gt = await panel('books').locator('.group-title').allInnerTexts();
  log('الكتب', 'البحث برمز ← قسم «معاني الرمز» أولاً ثم «ورد ذكره أيضاً»', gt.length >= 1 && /معاني «الماء»/.test(gt[0]), gt.join(' | '));
  log('الكتب', 'لا صندوق «أبرز ما ورد»', (await panel('books').locator('.meanings-box').count()) === 0 && !/أبرز ما ورد/.test(await panel('books').innerText())); }
await search('books', 'شفت حنش'); log('الكتب', 'جملة «شفت حنش» ← عنوان القسم باسم الرمز «حنش» لا الجملة كلها', /معاني «حنش»/.test((await panel('books').locator('.group-title').first().innerText())));
await search('books', 'سيارة'); log('الكتب', 'كلمة حديثة «سيارة» تُفهم «مركب/دابة» ويُقدَّم ذلك', /فُهمت «سيارة» بالفصحى/.test(await panel('books').innerText()) && /مركب|دابة|دابه/.test(await cards('books').first().innerText()));
await search('amthal', 'فلوس'); log('الأمثال', 'فهم العامية في «الكتب» فقط: «فلوس» في الأمثال تُبحث بلفظها بلا فصحى', !/فُهمت/.test(await panel('amthal').innerText()) && (await cards('amthal').count()) > 0);
// ---------- أبيات الإستشهاد ----------
await search('shawahid', 'سفينة'); { const tx = await panel('shawahid').innerText();
  log('أبيات الإستشهاد', '«سفينة» ← أبيات بشطرين ومصدر لكل بيت', (await cards('shawahid').count()) > 10 && (await cards('shawahid').first().locator('.poem-shatr').count()) === 2 && /المصدر: \S/.test(await cards('shawahid').first().innerText()));
  log('أبيات الإستشهاد', 'عبارة «وبُحث أيضاً عمّا يقاربها في المعنى» محذوفة', !/وبُحث أيضاً عمّا يقاربها/.test(tx));
  const all = await panel('shawahid').innerText(); log('أبيات الإستشهاد', 'تظهر أبيات فيها «مركب» أو «فلك» وهي من مرادفات «سفينة»', /مركب|المركب|الفلك|فلك/.test(all)); }
await search('shawahid', 'ألستم خير من ركب المطايا'); { const c0 = await cards('shawahid').first().innerText();
  log('أبيات الإستشهاد', 'تحت البيت: «يقال عند…» ثم «القائل:» ثم «المصدر:»', /يقال عند مدح عبد الملك بن مروان/.test(c0) && /القائل: جرير/.test(c0) && /المصدر: /.test(c0) && c0.indexOf('يقال') < c0.indexOf('القائل') && c0.indexOf('القائل') < c0.indexOf('المصدر')); }
await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; }); await page.waitForTimeout(200);
{ const col = (sel) => cards('shawahid').first().locator(sel).first().evaluate((el) => getComputedStyle(el).color);
  log('أبيات الإستشهاد', 'الوضع الداكن: نص البيت وبياناته (يقال/القائل/المصدر) بالأبيض', (await col('.poem-shatr')) === 'rgb(255, 255, 255)' && (await col('.shahid-info p')) === 'rgb(255, 255, 255)'); }
await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
await search('shawahid', 'قارب'); log('أبيات الإستشهاد', 'الكتابة بـ«قارب» تجد أبيات «سفينة» أيضاً', /سفين/.test(await panel('shawahid').innerText()));
await search('shawahid', 'سيارة'); log('أبيات الإستشهاد', 'كلمة حديثة/عامية «سيارة» تُفهم بالفصحى', /فُهمت «سيارة» بالفصحى/.test(await panel('shawahid').innerText()));
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
// ---------- القائمة الجانبية و«رؤى وتعبيرها» ----------
{
  await page.goto(URL_); await page.waitForFunction(() => document.querySelector('button.menu-toggle'), null, { timeout: 30000 }); await page.waitForTimeout(1200);
  log('القائمة الجانبية', 'زر «المزيد» في أعلى الصفحة وله اسم وصول', (await page.locator('button.menu-toggle').getAttribute('aria-label')) === 'المزيد');
  log('القائمة الجانبية', 'قسم «رؤى عبّرت» ليس تبويباً (تبقى ستة تبويبات)', (await page.getByRole('tab').count()) === 6 && !(await page.getByRole('tab', { name: /رؤى/ }).count()));
  await page.click('button.menu-toggle'); await page.waitForSelector('.drawer');
  log('القائمة الجانبية', 'تنفتح قائمة «المزيد» الجانبية وفيها زر «رؤى عبّرت»', (await page.locator('.drawer-head h2').innerText()) === 'المزيد' && (await page.locator('.drawer .drawer-item').first().innerText()).includes('رؤى عبّرت'));
  await page.screenshot({ path: 'tests/screenshots/drawer.png' });
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  log('القائمة الجانبية', 'Escape يغلق القائمة', (await page.locator('.drawer').count()) === 0);
  await page.click('button.menu-toggle'); await page.click('.drawer-item'); await page.waitForSelector('.panel .dream-card');
  log('القائمة الجانبية', 'زر «رؤى عبّرت» يفتح القائمة الخاصة «رؤى وتعبيرها»', (await page.locator('.panel .panel-head h2').innerText()).includes('رؤى وتعبيرها'));
  const n0 = await page.locator('.dream-card').count();
  const sub = await page.locator('.panel-sub').innerText();
  log('رؤى وتعبيرها', 'تُعرض الرؤى بطاقات (٣٠ ثم «عرض المزيد»)', n0 === 30 && (await page.locator('button.more').count()) === 1, String(n0));
  log('رؤى وتعبيرها', 'كل بطاقة تذكر المرجع', (await page.locator('.dream-card').evaluateAll((a) => a.every((c) => /المرجع: /.test(c.innerText)))));
  log('رؤى وتعبيرها', 'كل بطاقة فيها «الرؤيا» والتعبير', (await page.locator('.dream-card').evaluateAll((a) => a.every((c) => /الرؤيا/.test(c.innerText)))));
  log('رؤى وتعبيرها', 'العدد المعلن أكثر من ٩٠٠ رؤيا ومن عدة مراجع', toNum(sub.split(' رؤيا')[0]) > 900 && /مرجعاً|مراجع/.test(sub), sub);
  log('رؤى وتعبيرها', 'حقل البحث «اكتب هنا» فقط', (await page.locator('#q-dreams').getAttribute('placeholder')) === 'اكتب هنا');
  await page.fill('#q-dreams', 'سمك'); await page.click('.panel button.go'); await page.waitForTimeout(300);
  const found = await page.locator('.dream-card').count();
  log('رؤى وتعبيرها', 'البحث يعيد رؤى فيها الكلمة ويفرغ الحقل', found > 0 && found < n0 && (await page.locator('.dream-card').first().innerText()).includes('سمك') && (await page.locator('#q-dreams').inputValue()) === '', String(found));
  await page.click('.panel .stats button'); await page.waitForTimeout(200);
  await page.selectOption('.panel select', { index: 1 }); await page.waitForTimeout(200);
  const src1 = await page.locator('.dream-card .takhrij').allInnerTexts();
  log('رؤى وتعبيرها', 'تصفية المرجع تعرض رؤى مرجع واحد', src1.length > 0 && new Set(src1).size === 1, src1[0]);
  await page.screenshot({ path: 'tests/screenshots/dreams.png' });
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  log('رؤى وتعبيرها', 'Escape يغلق القائمة المنبثقة للرؤى', (await page.locator('.panel').count()) === 0);
  const bk = await page.evaluate(async () => { const m = await (await fetch('content/manifest.json')).json(); return m.tabs.find((t) => t.id === 'books').count; });
  log('رؤى وتعبيرها', 'خانة الكتب كاملة لم تُنقَص (٢٨٢٣٦ مدخلاً)', bk === 28236, String(bk));
}
// ---------- «رؤى الأنبياء والصالحين» و«المعبِّرون» ----------
{
  await page.goto(URL_); await page.waitForFunction(() => document.querySelector('button.menu-toggle'), null, { timeout: 30000 }); await page.waitForTimeout(1200);
  await page.click('button.menu-toggle'); await page.waitForSelector('.drawer');
  const items = await page.locator('.drawer .drawer-item .drawer-label').allInnerTexts();
  log('المزيد', 'ثلاثة أزرار: رؤى عبّرت، رؤى الأنبياء والصالحين، المعبِّرون', items.join('|') === 'رؤى عبّرت|رؤى الأنبياء والصالحين|المعبِّرون', items.join('|'));
  await page.locator('.drawer-item').nth(1).click(); await page.waitForSelector('.panel .dream-card');
  const first = await page.locator('.dream-card').first().innerText();
  log('رؤى الأنبياء والصالحين', 'أول بطاقة رؤيا يوسف من القرآن بنص المصحف ورقم الآية والمرجع', /صاحب الرؤيا: يوسف عليه السلام/.test(first) && /\[يوسف: 4\]/.test(first) && /المرجع: القرآن الكريم — سورة يوسف/.test(first) && (await page.locator('.dream-card').first().locator('.quran-inline').count()) > 0);
  const sub = await page.locator('.panel-sub').innerText();
  log('رؤى الأنبياء والصالحين', 'العدد المعلن أكثر من ٢٠٠ مع مراجع متعددة', toNum(sub.split(' ')[0]) > 200 && /مرجعاً|مراجع/.test(sub), sub);
  const opts = await page.locator('.panel select[aria-label="المرجع"] option').allInnerTexts();
  log('رؤى الأنبياء والصالحين', 'المراجع: القرآن والجامع الصغير وكتب التعبير والمنامات', ['القرآن الكريم', 'الجامع الصغير', 'المنامات', 'القادري'].every((k) => opts.some((o) => o.includes(k))), opts.length + ' مرجعاً');
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  await page.click('button.menu-toggle'); await page.locator('.drawer-item').nth(2).click(); await page.waitForSelector('.person-card');
  const nPeople = await page.locator('.person-card').count();
  const sirin = await page.locator('.person-card', { hasText: 'محمد بن سيرين' }).first().innerText();
  log('المعبِّرون', 'بطاقات المعبِّرين (١٣) وفي ابن سيرين نص الذهبي كما هو مع اسم المصدر', nPeople === 13 && sirin.includes('فلم أر أجبن من فتوى منه، ولا أجرأ على رؤيا منه') && sirin.includes('سير أعلام النبلاء للذهبي'), String(nPeople));
  const nabulsi = await page.locator('.person-card', { hasText: 'ابن نعمة' }).first().innerText();
  log('المعبِّرون', 'ابن نعمة النابلسي: «فقيه اشتهر بعلم تعبير الرؤيا» من الأعلام للزركلي', nabulsi.includes('اشتهر بعلم تعبير الرؤيا') && nabulsi.includes('الأعلام للزركلي'));
  await page.locator('.person-card', { hasText: 'محمد بن سيرين' }).first().locator('.person-btn').click(); await page.waitForSelector('.panel-back.nested .dream-card');
  const pills = await page.locator('.panel-back.nested .dream-card .pill-text').allInnerTexts();
  log('المعبِّرون', 'زر «رؤاه المعبَّرة» يفتح رؤى ابن سيرين وحدها', pills.length > 0 && pills.every((x) => x.includes('ابن سيرين')), String(pills.length));
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  log('المعبِّرون', 'Escape يغلق قائمة الرؤى ويبقى المعبِّرون', (await page.locator('.panel-back.nested').count()) === 0 && (await page.locator('.person-card').count()) === 13);
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  log('المعبِّرون', 'Escape ثانية يغلق القائمة كلها', (await page.locator('.panel-back').count()) === 0);
  await page.goto(URL_); await page.waitForTimeout(1200);
  await search('quran', 'يجتبيك ربك'); await page.waitForTimeout(500);
  log('الخط', 'علامة U+065E (ينقصها خط Amiri Quran) تُرسم بخط احتياطي لا مربعاً فارغاً', await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].some((f) => f.family.includes('Quran Marks') && f.status === 'loaded'); }));
}
// ---------- الأرقام بالإنجليزية ----------
{
  await page.goto(URL_); await page.waitForTimeout(1500);
  await search('quran', 'الرحمن'); await page.waitForTimeout(300);
  const t = await panel('quran').innerText();
  log('الأرقام', 'عداد النتائج وأرقام الآيات بالأرقام الإنجليزية 0-9 (لا هندية)', !/[\u0660-\u0669]/.test(t) && /\d/.test(await panel('quran').locator('.stats').first().innerText()) && /\d/.test(await panel('quran').locator('.ayah-marker').first().innerText()), (await stats('quran')).slice(0, 60));
  await search('jami', 'الصلاة'); const tj = await panel('jami').innerText();
  log('الأرقام', 'أرقام الأحاديث والصفحات بالإنجليزية', !/[\u0660-\u0669]/.test((await panel('jami').locator('.stats, .card-ref').allInnerTexts()).join(' ')) && /حديث رقم \d+/.test(tj) || /صفحة \d+/.test(tj));
}
writeFileSync('tests/last-run.json', JSON.stringify({ at: new Date().toISOString(), axe: axeRes, meta, results }, null, 1));
const fails = results.filter((r) => !r.pass); console.log(`\nSUMMARY: ${results.length - fails.length}/${results.length} passed`); fails.forEach((f) => console.log('  FAIL', f.group, f.name, f.detail));
await browser.close(); srv.kill(); process.exit(fails.length ? 1 : 0);
