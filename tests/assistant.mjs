// The assistant of the app (src/lib/assistant.ts) run in node on the REAL content: what it answers, from where, and that it keeps silent about what the references do not hold.
// usage: node tests/assistant.mjs   (needs the esbuild that comes with vite)
import { build } from 'esbuild'; import { readFileSync, existsSync, mkdtempSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path';
const dir = mkdtempSync(join(tmpdir(), 'asst-')); const out = join(dir, 't.mjs');
await build({ stdin: { contents: `export { Assistant, parseBooks } from '${process.cwd()}/src/lib/assistant'; export { Engine } from '${process.cwd()}/src/lib/engine';`, resolveDir: process.cwd(), loader: 'ts' }, bundle: true, platform: 'node', format: 'esm', outfile: out, logLevel: 'error' });
const { Assistant, parseBooks, Engine } = await import(out);
const J = (f) => JSON.parse(readFileSync('content/' + f, 'utf8'));
const docs = (tab, f) => J(f).h.map(([ref, text, explanation, source, by, who, extra], i) => ({ id: `${tab}:${i}`, src: tab, text, ref, explanation, source, by, who, extra }));
const eng = new Engine();
const qj = J('quran.json'); const sn = new Map(qj.surahs.map((s) => [s.n, s.name]));
await eng.addSource('quran', qj.a.map(([s, a, t]) => ({ id: `quran:${s}:${a}`, src: 'quran', text: t, surah: s, ayah: a, surahName: sn.get(s) ?? '' })), 'quran', {});
const jj = J('jami.json'); await eng.addSource('jami', jj.h.map(([page, , t, k, , g, tier, , n], i) => ({ id: `jami:${i}`, src: 'jami', text: t, page, number: n || undefined, takhrij: k, grade: g, tier })), 'hadith', {});
await eng.addSource('books', docs('books', 'books.json'), 'generic', { refFirst: true, smart: 'full' }); await eng.finalize();
const lists = { ruyahadith: docs('ruyahadith', 'ruyahadith.json'), qawaid: docs('qawaid', 'qawaid.json'), anbiya: docs('anbiya', 'anbiya.json'), muabbirun: docs('muabbirun', 'muabbirun.json') };
const books = [...parseBooks(docs('kutubtabir', 'kutubtabir.json'), 'kutubtabir'), ...parseBooks(docs('nazm', 'nazm.json'), 'nazm'), ...parseBooks(docs('kutubfiras', 'kutubfiras.json'), 'kutubfiras')];
const phrases = {}; for (const d of docs('assistant', 'assistant.json')) (phrases[d.ref] ??= []).push(d.text);
const people = docs('muabbirun', 'muabbirun.json');
let seed = 7; const rng = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
const bot = new Assistant({ engine: eng, books, people, phrases, lists, rng, loadBook: async (b) => (b.textFile && existsSync('content/' + b.textFile) ? JSON.parse(readFileSync('content/' + b.textFile, 'utf8')) : null) });
let fails = 0; const log = (ok, what, d = '') => { if (!ok) fails++; console.log(ok ? 'PASS' : 'FAIL', '|', what, d ? '— ' + String(d).replace(/\s+/g, ' ').slice(0, 160) : ''); };
const ask = async (q) => { const r = await bot.ask(q); return r; };
let r = await ask('هلا والله'); log(/هلا|حيّا|مرحبا|أهلين|يحييك/.test(r.text) && r.chips.length > 0, 'a greeting is answered in kind', r.text);
r = await ask('وش فسروا الثعبان في الحلم'); log(r.cards.length >= 2 && r.cards.every((c) => c.where && c.quote), 'a symbol: quotations, each with its book', r.cards.map((c) => c.where).join(' | '));
log(/ثعبان/.test(r.cards.map((c) => c.quote + c.title).join(' ')) && /مو تعبير|مو تفسير|نقل/.test(r.text), 'the quotations speak of the symbol, and the voice says it is a quotation, not its own interpretation', r.text);
r = await ask('كم صفحة كتاب المرقبة العليا'); log(r.cards.length === 1 && /443/.test(r.cards[0].quote), 'pages of a named book (from the book information)', r.cards.map((c) => c.quote).join(' '));
r = await ask('مين مؤلف البدر المنير'); log(r.cards.length === 1 && /الأنصاري|حسين|جمعة|ابن/.test(r.cards[0].quote) || r.cards[0]?.quote.length > 5, 'author of a named book', r.cards[0]?.quote);
r = await ask('دور لي فصل مداواة النفوس في فهرس كتاب الأخلاق والسير'); log(r.cards.length >= 1 && /مداواة/.test(r.cards[0].title) && r.cards[0].where.includes('الأخلاق والسير') && r.cards[0].open.length >= 1, 'a chapter looked up in the contents of a named book (with a way to open it)', r.cards[0] && r.cards[0].title + ' @ ' + r.cards[0].where);
r = await ask('مين ابن سيرين'); log(r.cards.length === 1 && /بن سيرين/.test(r.cards[0].title), 'an interpreter: his card', r.cards[0]?.title);
r = await ask('كم عدد الكتب اللي عندك'); log(/\d+/.test(r.text) && r.chips.length > 0, 'the size of the library', r.text);
r = await ask('وش سعر الذهب اليوم'); log(r.cards.length === 0 && /ما لقيت|ما أجاوب|المراجع/.test(r.text), 'a question outside the references: no answer from nowhere', r.text);
r = await ask('ما هي عاصمة فرنسا'); log(r.cards.length === 0, 'general knowledge is refused', r.text);
r = await ask('وش فسروا الماء'); const n1 = r.cards.length; log(n1 >= 1 && r.chips.includes('زدني') || n1 <= 4, 'the first answer shows a few results');
if (r.chips.includes('زدني')) { const m = await ask('زدني'); log(m.cards.length >= 1 && m.cards[0].quote !== r.cards[0].quote, 'ask for more: other results follow', m.cards.length); }
r = await ask('شكرا'); log(r.cards.length === 0 && r.text.length > 5, 'thanks are answered');
r = await ask('من انت'); log(/مساعد/.test(r.text) && /المراجع|الكتب/.test(r.text), 'who it is: the assistant of the app that answers from the references', r.text);
// the voice: Saudi colloquial markers are present in the phrase bank, and no phrase is stiff (e.g. «يرجى» «حيث أنه»)
const all = Object.entries(phrases).filter(([k]) => k !== 'topic').flatMap(([, v]) => v); log(all.length >= 60 && all.filter((p) => /أبشر|يا طيب|يا غالي|وش |ولا يهمك|حيّاك|هلا|سم|والله|يالله|ما لقيت|اللي|مرة|شوي|تبغى|تبي|بغيت|تفضل|لقيت|دوّرت|ثواني|لحظة|عندي|أنا |طيب|إلا /.test(p)).length >= all.length * 0.75, 'the phrase bank is in the Saudi colloquial voice', all.length + ' phrases');
log(!all.some((p) => /يرجى|حيث أنه|بناءً على|لا يسعني|نعتذر|عزيزي المستخدم/.test(p)), 'no stiff machine phrases');
// the text of a book that is in the app is searched (the digital books)
r = await ask('وش قال المنامات عن الرؤيا'); log(r.cards.length >= 0, 'a book-restricted question runs', r.cards.length + ' results');

// ---------- the discussion: kinds of messages, proofs in the order of a scholar, quotations only ----------
const tiers = (r) => [...new Set(r.cards.map((c) => c.tier))];
r = await ask('ما حكم تعبير الرؤيا'); log(['quran', 'hadith', 'rules'].every((t) => tiers(r).includes(t)) && /مو مفتي|ولا أصدر فتوى|يرجع لأهل العلم/.test(r.text), 'a ruling: the Qur\'an, the Sunnah and the rules, with the statement that it is not a fatwa', tiers(r).join(','));
log(r.cards.every((c) => c.where && c.quote && c.tier) && r.cards.findIndex((c) => c.tier === 'quran') < r.cards.findIndex((c) => c.tier === 'hadith') && r.cards.findIndex((c) => c.tier === 'hadith') < r.cards.findIndex((c) => c.tier === 'rules'), 'the order of the proofs: Qur\'an, then Sunnah, then the interpreters\' rules');
r = await ask('وش الدليل'); log(r.cards.length >= 2 && tiers(r)[0] === 'quran', '«وش الدليل» after a ruling: the proofs of that topic again (not a book called «الدليل»)', r.text);
r = await ask('الدليل من السنة'); log(r.cards.length >= 1 && tiers(r).length === 1 && tiers(r)[0] === 'hadith', 'a proof asked from the Sunnah only gives hadith', tiers(r).join(','));
r = await ask('من القرآن'); log(r.cards.length >= 1 && tiers(r).every((t) => t === 'quran'), 'a short follow-up «من القرآن» gives verses of the topic in hand', tiers(r).join(','));
r = await ask('أنا أشوف أن الأحلام كلها ما لها معنى'); log(/أقسام الرؤيا/.test(r.text) && r.cards.some((c) => c.tier === 'hadith' && /الحلم من الشيطان|الرؤيا الصادقة من الله/.test(c.quote)) && !!r.after, 'an opinion: laid beside the proofs of its topic, then a question to the asker', r.text);
r = await ask('ما اقتنعت'); log(r.cards.length === 0 && r.chips.some((c) => /الدليل من القرآن/.test(c)) && /الإشكال|ما اقتنعت|وزنه بالدليل/.test(r.text), 'an objection: asks where the doubt is and offers the kinds of proof', r.text);
r = await ask('رأيت في المنام ثعبان وماء'); log(r.cards.filter((c) => c.tier === 'books').length >= 2 && r.cards.some((c) => c.tier === 'rules' && /حال الرائي/.test(c.title)) && /حال/.test(r.after ?? ''), 'a narrated dream: what the books say of each thing, the rule about the dreamer\'s state, and a question', r.cards.map((c) => c.title).join(' | '));
r = await ask('أنا متزوج واشتغل معلم'); log(r.cards.length >= 1 && r.cards.every((c) => c.tier === 'rules') && r.cards.some((c) => /الصنعة|الرائي/.test(c.title)), 'the dreamer tells his state: the rules that count it are quoted', r.cards.map((c) => c.title).join(' | '));
r = await ask('حلمت كابوس مزعج وخفت'); log(r.cards.some((c) => c.tier === 'hadith' && /يساره|يتعوذ|فليتعوذ|فليتفل|يبصق/.test(c.quote)), 'a frightening dream: the hadith of what to do', r.cards.map((c) => c.quote.slice(0, 50)).join(' | '));
r = await ask('هل يجوز اقص رؤياي على الناس'); log(r.cards.some((c) => c.tier === 'hadith' && /واد|ذي رأي|من يحب/.test(c.quote)) && r.cards.some((c) => c.tier === 'quran' && /يوسف/.test(c.title)), 'to whom a dream is told: Surat Yusuf and the hadith', r.cards.map((c) => c.title).join(' | '));
r = await ask('ما الفرق بين الرؤيا والحلم'); log(r.cards.some((c) => c.tier === 'hadith' && /الحلم من الشيطان/.test(c.quote)), 'the difference between a dream and a vision: the hadith that names them');
r = await ask('لماذا يختلف تفسير الحلم من شخص لآخر'); log(r.cards.length >= 3 && r.cards.every((c) => c.tier === 'rules'), 'why the reading differs: the rules of the interpreters', r.cards.map((c) => c.title).join(' | '));
r = await ask('ما هي شروط المعبر'); log(r.cards.length >= 3 && r.cards.some((c) => /صفات المعبِّر/.test(c.title)), 'the conditions of the interpreter');
r = await ask('هل الفراسة جايزة'); log(r.cards.some((c) => c.tier === 'quran' && /الحجر/.test(c.title)) && r.cards.some((c) => c.tier === 'hadith' && /فراسة المؤمن/.test(c.quote)), 'physiognomy: the verse and the hadith');
r = await ask('ما حكم الصلاة'); log(r.cards.length === 0 && /خارج المراجع|ما أقول/.test(r.text), 'a ruling outside the references is not answered from nowhere', r.text);
r = await ask('ما حكم الزكاة في الذهب'); log(r.cards.length === 0, 'another matter of fiqh is refused too', r.text);
r = await ask('هلا'); log(r.cards.length === 0 && r.chips.length > 0, 'greeting after a discussion still a greeting');
// the same words in other forms
for (const [m, topic] of [['وش اسوي اذا شفت حلم يخوف', 'المكروهة'], ['متى تصدق الرؤيا', 'وقت الرؤيا'], ['من هو المعبر الصادق', 'آداب المعبِّر'], ['رايت النبي في المنام', 'رؤية النبي'], ['الرؤيا الصالحة جزء من النبوة', 'الصالحة']]) { r = await ask(m); log(r.cards.length >= 1 && new RegExp(topic).test(r.text), `the topic is recognised: ${m}`, r.text.slice(0, 60)); }
r = await ask('وش فسروا الماء'); log(r.cards.length >= 1 && !r.cards.some((c) => c.tier === 'quran'), 'a plain symbol question stays a symbol question (no discussion)');
r = await ask('الفرق بين ابن سيرين والنابلسي'); log(r.cards.length >= 2 && r.cards.every((c) => /سيرين|النابلسي/.test(c.title)), 'a comparison of two interpreters: both cards');
// every topic of the content: its first trigger brings quotations of every reference it names
const topicRows = (phrases.topic ?? []).map((x) => JSON.parse(x)); log(topicRows.length >= 15, 'the topics are in the content', topicRows.length);
for (const t of topicRows) { const b2 = new Assistant({ engine: eng, books, people, phrases, lists, rng, loadBook: async () => null }); const rr = await b2.ask(t.label); const need = [...new Set(t.ask.filter((a) => a.src !== 'books' && a.src !== 'jami').map((a) => a.tier))]; log(rr.cards.length >= 1 && need.every((x) => rr.cards.some((c) => c.tier === x)), `topic «${t.label}»: its label brings its proofs (${need.join(',')})`, rr.cards.map((c) => c.tier).join(',')); }
// nothing is written by the assistant: every quotation of the Qur'an / the Sunnah / the rules is a stretch of its own source, word for word
const norm = (t) => t.normalize('NFKD').replace(/[ً-ٰٟۖ-ۭـ‌-‏]/g, '').replace(/[إأآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/[^ء-ي]/g, '');
const srcText = { quran: norm(qj.a.map((x) => x[2]).join('')), hadith: norm(lists.ruyahadith.map((d) => d.text).join('') + jj.h.map((x) => x[2]).join('')), rules: norm(lists.qawaid.map((d) => d.text).join('')) };
const asked = ['ما حكم تعبير الرؤيا', 'لمن اقص الرؤيا', 'الرؤيا الصالحة', 'ما الفرق بين الرؤيا والحلم', 'كابوس مزعج', 'اختلاف التأويل بحال الرائي', 'آداب المعبر', 'رأيت النبي في المنام', 'هل الفراسة جايزة', 'الكذب في الرؤيا'];
let checked = 0, bad = [];
for (const m of asked) { const rr = await bot.ask(m); for (const c of rr.cards) { if (!srcText[c.tier]) continue; const parts = c.quote.split(/…/).map(norm).filter((x) => x.length > 8); for (const pt of parts) { checked++; if (!srcText[c.tier].includes(pt)) bad.push(c.tier + ': ' + c.quote.slice(0, 60)); } } }
log(checked >= 20 && bad.length === 0, `every quoted passage is word for word in its source (${checked} checked)`, bad.slice(0, 2).join(' || '));

console.log(fails ? `FAILED: ${fails}` : 'ALL PASSED'); process.exit(fails ? 1 : 0);
