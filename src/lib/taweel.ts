import type { Doc } from './types';
import { normalize, tokens } from './arabic';
import { dialectVariants } from './dialect';

/** «التأويل العميق»: the dreamer writes the dream, says his age and his marital state, and gets what the reference books say of every symbol of it — the books' own sentences, put as one
 *  interpreter would speak to him, without naming any author or book. Nothing is invented: every interpretation, every reason and every rule is a sentence of the books; only the
 *  linking phrases (the opening «والله أعلم»، «أما رؤيتك…»، «وبحسب حالك…») are the app's. Offline, on the device. */
export type Age = 'child' | 'young' | 'adult' | 'elder';
export type Marital = 'single' | 'married' | 'divorced' | 'widowed';
export const AGES: { id: Age; label: string }[] = [
  { id: 'child', label: 'دون الثامنة عشرة' }, { id: 'young', label: 'من 18 إلى 35' }, { id: 'adult', label: 'من 36 إلى 55' }, { id: 'elder', label: 'فوق 55' }];
export const MARITALS: { id: Marital; label: string }[] = [
  { id: 'single', label: 'أعزب / عزباء' }, { id: 'married', label: 'متزوج / متزوجة' }, { id: 'divorced', label: 'مطلّق / مطلّقة' }, { id: 'widowed', label: 'أرمل / أرملة' }];
// how the books speak of each state (a clause that names it is the clause that concerns him)
const MARITAL_RX: Record<Marital, RegExp> = {
  single: /(?:^|\s)(?:ل|ال|إن كان |ان كان )?(?:أ)?عزب|عازب|بكر[اً]?(?:\s|$)|لم يتزوج|غير متزوج|للعزاب/,
  married: /متزوج|ذات زوج|ذات بعل|له زوجة|له امرأة|لمن له امرأة|لمن له زوجة|المتزوجين/,
  divorced: /مطلق|مطلقة|طلق/, widowed: /أرمل|ترمل|أرامل|ارمل/ };
const AGE_RX: Record<Age, RegExp> = {
  child: /صبي|غلام|طفل|الصبيان|للأطفال/, young: /(?:^|\s)(?:ل|ال)?شاب(?:اً)?(?:\s|$)|شباب|للشاب/, adult: /كهل|متوسط العمر|بين الشباب والشيخوخة/, elder: /شيخ|كبير السن|مسن|عجوز|هرم/ };
const AGE_TEXT: Record<Age, string> = { child: 'دون الثامنة عشرة', young: 'شاب', adult: 'في منتصف العمر', elder: 'كبير في السن' };
const MAR_TEXT: Record<Marital, string> = { single: 'أعزب', married: 'متزوج', divorced: 'مطلّق', widowed: 'أرمل' };
// the verbs and the pronouns of the telling of a dream are not symbols
const VERB = /^[أاتين]?(?:ركض|ركب|مشي|مش|جري|جر|سقط|وقع|نزل|طلع|دخل|خرج|اكل|شرب|فتح|اخذ|اعط|ضحك|بكي|صرخ|هرب|طار|طير|سبح|غرق|كلم|قتل|عمل|لقي|وجد|ذهب|رجع|جلس|وقف|نام|قام|سمع|قال|قلت|جاء|اجي|اتي|اري|ارا|اشوف|اشاهد)\w*$/;

const STOP = new Set(('في من على الى إلى عن ان أن إن إني اني انه إنه انها إنها كان كانت كنت كنا يكون تكون وكان وكانت فكان فكانت ثم مع بعد قبل كل لا ما هل قد كأن كان كاني كأني كانني كأنني رأيت رايت رأى ' +
  'رايتني رأيتني شفت شفنا حلمت حلم رؤيا رؤيتي رويا المنام منام منامي بالمنام نومي نمت فجأة فجاة وهو وهي هو هي هذا هذه ذلك تلك الذي التي الى حتى لكن لكني بس مرة اخرى أخرى ثم ثمة هناك هنا ' +
  'فيه فيها منه منها عليه عليها له لها لي لك به بها بي مني ثم أنا انا نحن انت أنت وكانوا كانوا لم لن ليس ولم ولا وما وقد وإن وان إذا اذا حين عندما لما عند بين تحت فوق وكأن يعني قال قلت ' +
  'أحد احد واحد شخص شيء شي اشياء كثير كثيرا كبير صغير جدا يوم ليلة اليوم').split(/\s+/));
const core = (w: string) => w.replace(/^(?:وال|فال|بال|كال|لل|ولل|ال|و)/, '');
const same = (w: string, q: string) => w === q || (q.length >= 3 && w.length >= 3 && (w.startsWith(q) || q.startsWith(w)) && Math.abs(w.length - q.length) <= 2);
// the books that tell meanings of symbols (the dream tales and the author's own «قلت» are not rules)
const ANECDOTE = /(?:^|\s)(?:رأيت|رايت|رأيتني|قلت|سألني|أتاني|جاءني|كنت|وفي يدي|في يدي)(?:\s|$)|^(?:و?قال|و?قالت|و?حكي|و?روي|قيل لي)\b|(?:أتى|جاء|جاءه|أتاه|سأل)\s+(?:رجل|امرأة|إنسان|شخص|ابن سيرين)/;
// an attribution inside a sentence: the sentence is cut before it
const ATTR = /\s*[(\[]?\s*(?:و?قال|و?قالت|و?حكى|و?حكي|و?روى|و?روي عن|و?ذكر|و?نقل)\s+(?:ابن|أبو|أبا|(?!الله|النبي|الرسول|الكتاب)ال[ء-ي]+|جعفر|دانيال|أرطاميدورس|المعبرون|المصنف|المؤلف|بعضهم|بعض|آخر|رجل|إنسان|عن)(?=\s|$)/;
const BOOKS_OK = (s?: string) => !!s && !/المنامات/.test(s);
// explicit words are left out of what is shown (the passage is simply not chosen)
const DECENCY = /ذكره|إحليل|فرجه|فرجها|جماع|يجامع|مجامعة|لواط|زنا|زنى|يزني|سفاح|ينكح|عورته/;

function sentenceCut(t: string, max: number) {
  if (t.length <= max) return t;
  const head = t.slice(0, max); const k = Math.max(head.lastIndexOf('. '), head.lastIndexOf('؛ '), head.lastIndexOf('؟ '));
  if (k > 60) return head.slice(0, k + 1);
  // no punctuation (some books print none): cut where a new clause begins, never inside one
  let at = -1; for (const m of head.matchAll(/\s(?:فإن رأى|فإن كان|وإن رأى|وإن كان|ومن رأى|ولو رأى|وأما|وكذلك|وقيل)(?=\s)/g)) if (m.index! > 60) at = m.index!;
  return at > 0 ? head.slice(0, at).replace(/[\s،؛:]+$/, '') : t;
}
/** a book passage as the interpreter says it: the attribution and anything after it dropped, the long ones cut at a sentence end */
function clean(t: string, max = 380) {
  let x = t.replace(/^[\s\-–—]+/, '').replace(/\s+/g, ' ').trim();
  x = x.replace(/\s*وجه الشبه\s*:\s*/g, ' ').trim();
  x = x.replace(/^(?:و?قال|و?قالت)\s+(?!الله|رسول|النبي)\S+(?:\s+\S+){0,2}\s*:\s*/, '').replace(/^وجه الشبه\s*(?::|مأخوذ من)\s*/, '');       // «قال المصنف: …» / the «وجه الشبه:» label of the app
  const m = ATTR.exec(x); if (m && m.index > 20) x = x.slice(0, m.index).replace(/[\s،؛:]+$/, '');
  x = x.replace(/﴾\s*\d{1,3}\)/g, '﴾)').replace(/(?<=[ء-ي])\d{1,3}(?=[\s.،)]|$)/g, '');       // the footnote numbers of the digital copy
  return sentenceCut(x, max).trim();
}

interface Entry { d: Doc; pos: number }
const cache = new WeakMap<Doc[], Map<string, { i: number; pos: number }[]>>();
function indexOf(books: Doc[]) {
  let ix = cache.get(books); if (ix) return ix;
  ix = new Map(); books.forEach((d, i) => {
    if (!BOOKS_OK(d.source) || d.text.length < 25 || ANECDOTE.test(normalize(d.text).split(' ').slice(0, 9).join(' ')) || /علاوة|ما جاء منها على حرف|الرؤيا المعبرة|\s[ء-ي]{1,3}\s-\s(?:في|ف)\s/.test(d.text) || ((d.text.match(/،/g) ?? []).length >= 6 && d.text.length / ((d.text.match(/،/g) ?? []).length + 1) < 14)) return;
    tokens(normalize(d.text)).slice(0, 4).forEach((w, pos) => { const k = core(w); if (k.length < 2) return; let l = ix!.get(k); if (!l) ix!.set(k, l = []); l.push({ i, pos }); });
  });
  cache.set(books, ix); return ix;
}
function lookup(books: Doc[], word: string): Entry[] {
  const ix = indexOf(books); const best = new Map<number, number>();
  for (const [k, l] of ix) if (same(k, word)) for (const { i, pos } of l) { const b = best.get(i); if (b === undefined || pos < b) best.set(i, pos); }
  return [...best].map(([i, pos]) => ({ d: books[i], pos }));
}

/** the clause of a passage that concerns the dreamer's state («…وإن كان عزباً تزوّج…»): from the conditional that names it to the next conditional or the sentence end */
function clauseFor(text: string, rx: RegExp): string | null {
  const m = rx.exec(text); if (!m) return null;
  const before = text.slice(0, m.index + 1); const starts = [...before.matchAll(/(?:^|[\s،.؛])(?:ف|و)?(?:إن كان|ان كان|وإن كان|وللأعزب|ولمن|وللمتزوج|وللمرأة|وإن رأى|فإن رأى|أو إن كان)(?=\s|$)/g)];
  const from = starts.length ? starts[starts.length - 1].index! : Math.max(0, before.lastIndexOf(' ', m.index - 40));
  const rest = text.slice(m.index); const end = rest.search(/(?:\s(?:وإن كان|فإن كان|وإن لم يكن|وإن رأى|ولو|وقيل)\s)|[.؛]\s/);
  const seg = text.slice(from, m.index + (end > 0 ? end : Math.min(rest.length, 170))).replace(/^[\s،؛:.]+/, '').trim();
  const c = clean(seg, 240); return c.length > 12 ? c : null;
}

export interface Section { symbol: string; verdict: string; why?: string; mine: string[]; }
export interface Result { opening: string; sections: Section[]; rules: { title: string; text: string }[]; closing: string; found: number; }

// a passage that hesitates («وقيل»، «وربما»، «أو… أو…») is a weaker word than one that decides
const hedges = (t: string) => (t.match(/(?:\sأو\s|وربما|وقد يكون|ويحتمل|فلعل|لعل|وقيل|ويجوز|وإما)/g) ?? []).length;
/** the passage up to the point where the book itself begins to hesitate or to quote another opinion */
function decisive(t: string) { const m = /\s(?:وقيل|وربما|وقد يكون|ويحتمل|وفيه قول|وقال قوم|ومنهم من قال)(?=\s)/.exec(t); return m && m.index >= 30 ? t.slice(0, m.index).replace(/[\s،؛:]+$/, '') : t; }

export function interpret(dream: string, books: Doc[], rules: Doc[], age: Age, marital: Marital): Result {
  const surface = dream.trim().split(/\s+/).map((w) => w.replace(/^[^ء-ي]+|[^ء-ي]+$/g, '')).filter(Boolean);
  const seen = new Set<string>(); const syms: { word: string; stems: string[] }[] = [];
  for (const w of surface) {
    const n = normalize(w); if (n.length < 3 || STOP.has(n) || STOP.has(core(n)) || VERB.test(core(n))) continue;
    const stems = [...new Set([n, ...dialectVariants(w).variants.flatMap((v) => tokens(normalize(v))).filter((x) => x.length >= 3 && !STOP.has(x))].map(core))].filter((x) => x.length >= 2);
    const key = stems[0]; if (seen.has(key)) continue; seen.add(key); syms.push({ word: w, stems });
  }
  const sections: Section[] = []; let usedQuran = false;
  const MEAN = /(?:يدل|تدل|دل |تؤول|يؤول|تعبر|يعبر|فهو|فهي|فإنه|فإنها|عدو|مال|امرأة|رجل|خير|شر)/;
  for (const s of syms) {
    const cand = new Map<string, Entry>();
    for (const st of s.stems) for (const e of lookup(books, st)) { const o = cand.get(e.d.id); if (!o || e.pos < o.pos) cand.set(e.d.id, e); }
    const all = [...cand.values()]; if (!all.length) continue;
    // the strongest word for the whole dream: the passage that decides (no hesitation), that is about the symbol itself, that gives its reason, and that meets the other symbols of the dream
    const others = syms.filter((x) => x !== s).map((x) => x.stems);
    const SUBJ2 = new Set(['في', 'عدو', 'عدوا', 'يدل', 'تدل', 'هو', 'هي', 'تؤول', 'فتؤول', 'يؤول', 'يعبر', 'تعبر', 'فهي', 'فهو', 'مال', 'رجل', 'امرأة', 'ملك']);
    const score = (e: Entry) => {
      const c = clean(e.d.text), tk = tokens(normalize(c)).map(core);
      const general = e.pos === 0 && (SUBJ2.has(tk[1] ?? '') || tk.length < 4) ? -16 : 0;          // «الحية عدو…»: the symbol itself, then its meaning
      const meet = others.filter((st) => st.some((q) => tk.some((w) => same(w, q)))).length;
      return e.pos * 10 + hedges(c) * 14 + (c.length > 420 ? 25 : 0) + (e.d.explanation ? -6 : 0) + (MEAN.test(c.slice(0, 160)) ? -8 : 0) + (!/[.؛]/.test(e.d.text) && e.d.text.length > 200 ? 20 : 0) + Math.min(c.length, 420) / 100 - Math.min(meet, 2) * 12 + general;
    };
    const ok = all.filter((e) => { const c = clean(e.d.text); return c.length >= 25 && !DECENCY.test(c) && !/^(?:و?قيل|و?ربما)\b/.test(c); });
    if (!ok.length) continue;
    ok.sort((a, b) => score(a) - score(b));
    let best: Entry | null = null; let verdict = '';
    for (const e of ok) { const v = decisive(clean(e.d.text, 300)); if (v.length >= 30 && (v.split(' ').pop() ?? '').length >= 2 && MEAN.test(v)) { best = e; verdict = v; break; } }       // a complete statement that gives a meaning
    if (!best) continue;
    let why = best.d.explanation ? clean(best.d.explanation, 260) : ''; if (why && verdict.includes(why.replace(/^قوله تعالى\s*:?\s*/, '').slice(0, 25))) why = '';
    const tv = new Set(tokens(normalize(verdict)).map(core).filter((w) => w.length >= 3 && !STOP.has(w))); const shared = tokens(normalize(why)).map(core).filter((w) => w.length >= 3 && tv.has(w)).length;
    if (why && shared < 3 && !/تعالى|﴿/.test(why)) why = '';            // the reason must be about the very sentence that is shown
    const nv = normalize(verdict), nw = normalize(why); if (DECENCY.test(why) || why.length <= 12 || /[:،]\.?$/.test(why) || (nw.length > 24 && nv.includes(nw.slice(4, 24)))) why = '';       // a reason already said, or cut short, is not shown
    if (/تعالى|﴿/.test(verdict + ' ' + why)) usedQuran = true;
    // what concerns his state, from the best passages of the symbol: the clause that names his state is the word for him
    const mine: string[] = [];
    for (const e of ok.slice(0, 40)) {
      for (const rx of [MARITAL_RX[marital], AGE_RX[age]]) { const c = clauseFor(e.d.text, rx); if (c && !DECENCY.test(c) && !mine.some((m) => m.slice(0, 30) === c.slice(0, 30))) mine.push(c); }
      if (mine.length >= 2) break;
    }
    sections.push({ symbol: s.word, verdict, why: why || undefined, mine: mine.slice(0, 2) });
    if (sections.length >= 5) break;
  }
  const found = sections.length;
  const opening = found ? 'بدايةً نقول والله أعلم،' : 'بدايةً نقول والله أعلم، لم أقف في الأصول على رمز يطابق ما كتبت؛ فاكتب ما رأيت بكلمات أخرى، وسمِّ أبرز ما كان في الرؤيا: ما رأيت، وأين، ومع من.';
  const pick = (title: string) => { const r = rules.find((d) => d.ref === title); const t = r?.text.split('\n')[0]?.split('\t')[0]; return r && t ? { title, text: clean(t, 420) } : null; };
  const used = found ? [pick('الشيء الواحد يختلف باختلاف حال الرائي'), usedQuran ? pick('التأويل بالقرآن') : null] : [];
  return { opening, sections, rules: used.filter((x): x is { title: string; text: string } => !!x), found,
    closing: 'والله أعلم وأحكم. وهذا من نصوص أهل العلم بالتعبير، وليس فتوى؛ فاعرض رؤياك على عالمٍ ناصح.' };
}
