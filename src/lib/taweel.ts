import type { Doc } from './types';
import { normalize, tokens } from './arabic';

/** «التأويل العميق»: the dreamer writes the dream, says his age and his marital state, and gets what the reference books say of every symbol of it — the books' own sentences, put as one
 *  interpreter would speak to him, without naming any author or book. Nothing is invented: every interpretation, every reason and every rule is a sentence of the books; only the
 *  linking phrases (the opening «والله أعلم»، «أما رؤيتك…»، «وبحسب حالك…») are the app's. Offline, on the device. */
export type Age = 'child' | 'young' | 'adult' | 'elder';
export type Marital = 'single' | 'married' | 'divorced' | 'widowed';
/** the age group that the books speak of (a boy, a youth, a man in his prime, an old man), from the dreamer's age in years */
export const ageGroup = (years: number): Age => (years < 18 ? 'child' : years <= 35 ? 'young' : years <= 55 ? 'adult' : 'elder');
/** «سنة واحدة»، «سنتان»، «٣ سنوات»… «١١ سنة» */
export const ageLabel = (n: number) => (n === 1 ? 'سنة واحدة' : n === 2 ? 'سنتان' : n <= 10 ? `${n} سنوات` : `${n} سنة`);
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
export interface Result { opening: string; story: string[]; sections: Section[]; rules: { title: string; text: string }[]; closing: string; found: number; }

// ===== أصول التأويل: the curated rules (content/taweel.json) — each is a symbol, what it points to, why, and the text that proves it =====
interface Ev { t: string; q: string }
interface Rule { id: string; stems: string[]; name: string; kind: 'head' | 'mod'; family: string; verdict: string; acts?: Record<string, string>; why?: string; dua?: boolean; ev: Ev[]; play?: string; alts?: { ctx: string[]; verdict: string; why?: string; ev: Ev[] }[]; }
interface Acts { [id: string]: { stems: string[]; noun: string } }
const kcache = new WeakMap<Doc[], { rules: Rule[]; acts: Acts }>();
function knowledge(docs: Doc[]) {
  let k = kcache.get(docs); if (k) return k;
  const rules: Rule[] = []; let acts: Acts = {};
  for (const d of docs) { try { if (d.by === 'rule') rules.push(JSON.parse(d.text)); else if (d.by === 'acts') acts = JSON.parse(d.text); } catch { /* a malformed row is skipped */ } }
  k = { rules, acts }; kcache.set(docs, k); return k;
}
/** the word without its attached particles (و ف ب ك ل and the article), to meet the stem of a rule */
const forms = (t: string) => [t, t.replace(/^[وفبكل]?ال/, ''), t.replace(/^[وفبكل](?=[ء-ي]{3,})/, '')];       // the word as written, without «ال», without one particle («لبنا» is not «ل + بنا»)
const SUF = new Set(['', 'ا', 'ي', 'ه', 'ها', 'ك', 'نا', 'ات', 'ان', 'ين', 'ون', 'ة']);      // what may follow a stem: the accusative, a pronoun, a plural — not a verb ending («ذهبت» is not «ذهب»)
const meets = (tok: string, stem: string) => forms(tok).some((a) => a === stem || (stem.length >= 3 && a.startsWith(stem) && SUF.has(a.slice(stem.length))));
const proof = (e: Ev) => e.t === 'آية' ? `وذلك لقوله تعالى: ﴿${e.q}﴾` : `وذلك للحديث النبوي الشريف: «${e.q.replace(/«/g, '“').replace(/»/g, '”')}»`;       // (a quotation inside the quotation takes curly marks)

/** The chain of one dream, told as an interpreter tells it: what the symbol points to; why (the text that proves it); and what the other things of the dream add to it. */
const proofs = (ev: Ev[]) => ev.slice(0, 2).map((e, i) => (i ? proof(e).replace(/^وذلك /, 'و') : proof(e))).join('، ');
function compose(words: string[], rules: Rule[], acts: Acts) {
  const toks = words.map((w) => normalize(w));
  const at = (stems: string[]) => { const ss = stems.map((x) => normalize(x)); return toks.findIndex((t) => ss.some((x) => meets(t, x))); };
  const found = rules.map((r) => ({ r, i: at(r.stems) })).filter((x) => x.i >= 0).sort((a, b) => a.i - b.i);
  const heads = found.filter((x) => x.r.kind === 'head').slice(0, 3); const mods = found.filter((x) => x.r.kind === 'mod');
  const actHit = Object.entries(acts).filter(([, a]) => at(a.stems) >= 0).map(([id]) => id);
  const story: string[] = []; const claimed = new Set<number>(); const methods = new Set<string>();
  heads.forEach(({ r, i }, n) => {
    claimed.add(i);
    const act = actHit.map((id) => ({ id, a: acts[id] })).find((x) => r.acts?.[x.id]);
    // the same word, read in the sense that the rest of the dream calls for («ورد» + طبيب: the vein, not the dhikr)
    const alt = r.alts?.find((a) => at(a.ctx) >= 0);
    const verdict = alt ? alt.verdict : act ? r.acts![act.id] : r.verdict; const why = alt ? alt.why ?? r.why : r.why; const ev = alt && alt.ev.length ? alt.ev : r.ev;
    if (r.play) methods.add(r.play);
    const subject = act ? `${act.a.noun} ${words[i].replace(/^(?:[وفبكل]?ال)/, '').replace(/^/, 'ال')}` : `رؤيتك ${r.name}`;
    story.push(`${n ? 'وأما ' : ''}${subject}${n ? ' فتدلّ' : ' تدلّ'} على ${verdict}${r.dua ? '، والله المستعان' : ''}.`);
    if (why || ev.length) story.push(`${r.play ? `وهذا من التأويل ${r.play === 'اسم' ? 'بالاسم' : r.play === 'تصحيف' ? 'بالتصحيف' : r.play === 'عكس' ? 'بالعكس' : 'بالاشتقاق'}، ` : ''}والوجه في ذلك${why ? ` أن ${why}` : ''}${ev.length ? `${why ? '،' : ''} ${proofs(ev)}` : ''}.`);
    // what the other things of the dream add: the nearest head takes each modifier
    for (const m of mods) {
      const own = heads.reduce((b, h) => (Math.abs(h.i - m.i) < Math.abs(b.i - m.i) ? h : b), heads[0]);
      if (own.r !== r) continue;
      claimed.add(m.i); const via = toks[m.i - 1] === 'من'; const w = words[m.i];
      const same = m.r.family === r.family;
      story.push(`${same ? `وبما أنه ${via ? `من ${w}` : `اقترن به ${w}`} فزاد الأمر تأكيداً` : `وقد ${via ? `كان من ${w}` : `اقترن به ${w}`}، وهو يدلّ على ${m.r.verdict}، فيُضاف ذلك إلى ما سبق`}${m.r.why ? `، لأن ${m.r.why}` : ''}${m.r.ev.length ? `، ${proofs(m.r.ev)}` : ''}.`);
    }
  });
  // the one face of the dream: the family that most of what he saw points to; when each points elsewhere, what he began with is the main thing
  const grp = (f: string) => (f === 'رزق' ? 'مال' : f);
  const tally = new Map<string, string[]>();
  for (const x of [...heads, ...mods]) { const f = grp(x.r.family); tally.set(f, [...(tally.get(f) ?? []), x.r.name]); }
  if (heads.length + mods.length >= 2) {
    const top = [...tally].sort((a, b) => b[1].length - a[1].length)[0];
    if (top[1].length >= 2) story.push(`فخلاصة رؤياك: أن الغالب عليها ${LABEL[top[0]] ?? top[0]}، فقد اجتمع فيها ${top[1].join(' و')}، وكلها من هذا الباب.`);
    else { const f = heads[0]; story.push(`فخلاصة رؤياك: أن وجهها المقدَّم ${LABEL[grp(f.r.family)] ?? f.r.family}، لأن ${f.r.name} هو أول ما رأيتَ في منامك.`); }
  }
  return { story, claimed, heads: heads.map((h) => h.r), methods };
}
const LABEL: Record<string, string> = { فتنة: 'الفتنة والذنب', علم: 'العلم', دين: 'الدين', عدو: 'العدو', رحمة: 'الرحمة والرزق', سفر: 'السفر', مال: 'المال والرزق', سلطان: 'السلطان', ضلال: 'الضلال والحيرة', خير: 'الخير', ذكر: 'الذكر والقرآن', بركة: 'البركة', ثبات: 'الثبات', عافية: 'العافية', فرج: 'الفرج', عودة: 'العودة', ارتفاع: 'الارتفاع', خسارة: 'الخسارة', سرور: 'السرور', نجاة: 'النجاة', رجل: 'الرجال' };

export function interpret(dream: string, books: Doc[], rules: Doc[], age: Age, marital: Marital, know: Doc[] = []): Result {
  const surface = dream.trim().split(/\s+/).map((w) => w.replace(/^[^ء-ي]+|[^ء-ي]+$/g, '')).filter(Boolean);
  const K = knowledge(know); const chain = compose(surface, K.rules, K.acts);
  // what concerns his own state, for the symbols that the chain explained (the clause of the book that names his state)
  const own: string[] = [];
  for (const h of chain.heads) {
    outer: for (const st of h.stems) for (const e of lookup(books, normalize(st)).sort((a, b) => a.pos - b.pos).slice(0, 40)) {
      for (const rx of [MARITAL_RX[marital], AGE_RX[age]]) { const c = clauseFor(e.d.text, rx); if (c && c.length <= 170 && !DECENCY.test(c) && !own.some((m) => m.slice(0, 30) === c.slice(0, 30))) own.push(c); }
      if (own.length >= 1) break outer;
    }
  }
  const story = [...chain.story]; if (own.length) story.splice(story.length - (story.length > 1 && story[story.length - 1].startsWith('فخلاصة') ? 1 : 0), 0, `وبحسب حالك وأنت ${AGE_TEXT[age]} ${MAR_TEXT[marital]}: ${own[0]}`);
  const found = story.length;
  const opening = found ? 'بدايةً نقول والله أعلم، وهذا في أصل التفسير وليس أعلى منه.' : 'بدايةً نقول والله أعلم، لم أقف في رؤياك على رمز له أصل أبني عليه تأويلاً قاطعاً؛ فسمِّ أبرز ما رأيت بكلمة واضحة (مثل: بحر، حية، لبن، قميص، مطر، ورد، بركة) أو اكتبه بكلمات أخرى.';
  const pick = (title: string) => { const r = rules.find((d) => d.ref === title); const t = r?.text.split('\n')[0]?.split('\t')[0]; return r && t ? { title, text: clean(t, 420) } : null; };
  const said = story.join(' ');
  const METHOD: Record<string, string> = { اشتقاق: 'الاشتقاق', اسم: 'التأويل بالأسماء', تصحيف: 'التصحيف', عكس: 'المعكوس' };
  const used = found ? [...[...chain.methods].map((m) => pick(METHOD[m])), said.includes('«') ? pick('التأويل بالسنة') : null, said.includes('﴿') ? pick('التأويل بالقرآن') : null, own.length ? pick('الشيء الواحد يختلف باختلاف حال الرائي') : null] : [];
  return { opening, story, sections: [], rules: used.filter((x): x is { title: string; text: string } => !!x), found,
    closing: 'والله أعلم وأحكم. وهذا من نصوص أهل العلم بالتعبير، وليس فتوى؛ فاعرض رؤياك على عالمٍ ناصح.' };
}
