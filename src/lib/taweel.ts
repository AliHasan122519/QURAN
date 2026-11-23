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

/** one line of the message: a heading, a paragraph, or a piece of evidence (with its kind) */
export interface Line { k: 'h' | 'p' | 'e'; l?: string; t: string }
export interface Result { opening: string; story: Line[]; rules: { title: string; text: string }[]; closing: string; found: number; }

// ===== أصول التأويل: the curated rules (content/taweel.json) — each is a symbol, what it points to, why, and the text that proves it =====
interface Ev { t: string; q: string }
interface Rule { dyn?: boolean; rx?: RegExp; root?: string; cn?: string; ex?: string[]; id: string; stems: string[]; name: string; kind: 'head' | 'mod'; family: string; verdict: string; m?: string; tail?: string; acts?: Record<string, string>; why?: string; dua?: boolean; ev: Ev[]; play?: string; alts?: { ctx: string[]; verdict: string; why?: string; ev: Ev[] }[]; }
interface Acts { [id: string]: { stems: string[]; noun: string; label: string } }
interface Fam { label: string; maal: string; ev: Ev[] }
interface Combo { id: string; m: string; all: string[][]; name: string; family: string; verdict: string; why: string; ev: Ev[] }
const kcache = new WeakMap<Doc[], { rules: Rule[]; acts: Acts; fams: Record<string, Fam>; combos: Combo[]; gen: Rule[] }>();
/** a word of the root «r» (the three radicals, with the letters that Arabic adds: a prefix, a long vowel inside, an ending): «سباحة» ← سبح، «مفتاح» ← فتح، «مستشفى» ← شفي */
function rootRx(root: string): RegExp {
  const [a, b, c] = [...normalize(root)];
  const R1 = a === 'ا' ? '[اوي]' : a, R2 = /[وي]/.test(b) ? '[وي]' : b, R3 = c === 'ي' ? '(?:ي|ء|ا?ء)' : c === 'و' ? '[وي]' : c;
  // one long vowel at most inside the word (فاعل، فعال، فعيل، مفعول)، a prefix and an ending from the few that Arabic adds
  return new RegExp(`^(?:[متينا]|است|مست|مت)?(?:${R1}[اوي]${R2}${R3}|${R1}${R2}[اوي]?${R3})(?:ه|ات|ان|ين|ون|ي|ا|ك|نا|ها|هم)?$`);
}
const empty = { ev: [] as Ev[], acts: undefined, kind: 'head' as const, name: '' };
/** the general lexicon (roots, analogies, colours) as rules: read when no specific rule has the word */
function fromLexicon(o: any): Rule {
  if (o.t === 'root') return { ...empty, dyn: true, id: 'جذر-' + o.r, stems: [], rx: rootRx(o.r), root: o.r, cn: o.cn, ex: o.ex, family: o.fam, verdict: o.rd, m: 'التأويل بالاشتقاق', ev: o.ev };
  if (o.t === 'color') return { ...empty, dyn: true, id: 'لون-' + o.id, stems: o.words, kind: 'mod', family: o.fam, verdict: o.rd, m: 'التشبيه', why: o.why, ev: o.ev };
  return { ...empty, dyn: true, id: 'باب-' + o.id, stems: o.words, family: o.fam, verdict: o.rd, m: o.m, why: o.why, ev: o.ev };
}
function knowledge(docs: Doc[]) {
  let k = kcache.get(docs); if (k) return k;
  const rules: Rule[] = []; let acts: Acts = {}; let fams: Record<string, Fam> = {}; const combos: Combo[] = []; const gen: Rule[] = [];
  for (const d of docs) { try { if (d.by === 'rule') rules.push(JSON.parse(d.text)); else if (d.by === 'acts') acts = JSON.parse(d.text); else if (d.by === 'fams') fams = JSON.parse(d.text); else if (d.by === 'combo') combos.push(JSON.parse(d.text)); else if (d.by === 'gen') gen.push(fromLexicon(JSON.parse(d.text))); } catch { /* a malformed row is skipped */ } }
  k = { rules, acts, fams, combos, gen: [...gen.filter((g) => g.stems.length), ...gen.filter((g) => !g.stems.length)] }; kcache.set(docs, k); return k;
}
/** the word without its attached particles (و ف ب ك ل and the article), to meet the stem of a rule */
const forms = (t: string) => [t, t.replace(/^[وفبكل]?ال/, ''), t.replace(/^[وفبكل](?=[ء-ي]{3,})/, '')];       // the word as written, without «ال», without one particle («لبنا» is not «ل + بنا»)
/** forms of a word for the general lexicon: as written, without «ال» (and a conjunction/preposition before it), without one attached particle only when what remains is a real word (4 letters: «كبير» is not «ك + بير») */
const formsG = (t: string) => [t, t.replace(/^[وفبكل]?ال/, ''), /^[وف]/.test(t) && t.length - 1 >= 3 ? t.slice(1) : /^[بلك]/.test(t) && t.length - 1 >= 4 ? t.slice(1) : t];
const SUF = new Set(['', 'ا', 'ي', 'ه', 'ها', 'ك', 'نا', 'ات', 'ان', 'ين', 'ون', 'ة']);      // what may follow a stem: the accusative, a pronoun, a plural — not a verb ending («ذهبت» is not «ذهب»)
const meets = (tok: string, stem: string) => forms(tok).some((a) => a === stem || (stem.length >= 3 && a.startsWith(stem) && SUF.has(a.slice(stem.length))));
const KINDS: Record<string, { label: string; order: number; q: (t: string) => string }> = {
  'آية': { label: 'الآية', order: 0, q: (t) => `﴿${t}﴾` }, 'حديث': { label: 'الحديث', order: 1, q: (t) => `«${t.replace(/«/g, '“').replace(/»/g, '”')}»` },
  'ألفية': { label: 'الألفية الوردية', order: 2, q: (t) => t }, 'بيت': { label: 'البيت', order: 3, q: (t) => t }, 'مثل': { label: 'المثل', order: 4, q: (t) => `«${t}»` } };
const inline = (e: Ev) => (e.t === 'آية' ? `وذلك لقوله تعالى: ﴿${e.q}﴾` : `وذلك للحديث النبوي الشريف: «${e.q.replace(/«/g, '“').replace(/»/g, '”')}»`);
const evLines = (ev: Ev[]): Line[] => [...ev].filter((e) => KINDS[e.t]).sort((a, b) => KINDS[a.t].order - KINDS[b.t].order).slice(0, 4).map((e) => ({ k: 'e' as const, l: KINDS[e.t].label, t: KINDS[e.t].q(e.q) }));
const AR = (n: number) => String(n).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[+d]);
const PLAY: Record<string, string> = { اشتقاق: 'التأويل بالاشتقاق', اسم: 'التأويل بالاسم', تصحيف: 'التأويل بالتصحيف', عكس: 'التأويل بالعكس' };
const methodOf = (r: Rule) => r.m ?? (r.play ? PLAY[r.play] : 'التشبيه');
const LABEL: Record<string, string> = { رزق: 'المال والرزق', رحمة: 'الرحمة والرزق', ثبات: 'الثبات', عافية: 'العافية', فرج: 'الفرج', عودة: 'العودة', ارتفاع: 'الارتفاع', خسارة: 'الخسارة', سرور: 'السرور', رجل: 'الرجال', سلطان: 'السلطان', خير: 'الخير', خبر: 'الخبر' };

/** The whole message of one dream, told as an interpreter tells it, point by point: what he saw; each thing with the method that reads it, its reason and its proofs (verse, hadith, poem, proverb);
 *  what the whole of it comes to; and the message of the dream to him, with where it ends (the maal) and the verse that proves it. */
function compose(words: string[], K: { rules: Rule[]; acts: Acts; fams: Record<string, Fam>; combos: Combo[]; gen: Rule[] }) {
  const { rules, acts, fams, combos, gen } = K;
  const toks = words.map((w) => normalize(w));
  const at = (stems: string[]) => { const ss = stems.map((x) => normalize(x)); return toks.findIndex((t) => ss.some((x) => meets(t, x))); };
  const met = combos.filter((c) => c.all.every((g) => at(g) >= 0));
  const partOf = (r: Rule) => met.some((c) => c.all.some((g) => g.some((x) => r.stems.includes(x))));
  const found0 = rules.map((r) => ({ r, i: at(r.stems) })).filter((x) => x.i >= 0).sort((a, b) => a.i - b.i);
  // a pair that the books of the method read together (the opposite, the analogy) is read as one thing: «ظلمة + نور»، «بحر + سفينة»
  const asRules: Rule[] = met.map((c) => ({ id: c.id, stems: c.all.flat(), name: c.name, kind: 'head' as const, family: c.family, verdict: c.verdict, m: c.m, why: c.why, ev: c.ev }));
  const spec = [...found0.filter((x) => !partOf(x.r)), ...asRules.map((r, k) => ({ r, i: Math.min(...met[k].all.map((g) => at(g))) }))].map((x) => ({ ...x, nm: x.r.kind === 'mod' ? words[x.i] : x.r.name }));   // a thing joined to another is named as he said it («من دم»)
  // the general lexicon reads every other word (a root, an analogy, a colour); a word that a specific rule, an action or a context word already has is not read twice
  const taken = (t: string) => rules.some((r) => r.stems.some((x) => meets(t, normalize(x)))) || Object.values(acts).some((a) => a.stems.some((x) => meets(t, normalize(x)))) || combos.some((c) => c.all.some((g) => g.some((x) => meets(t, normalize(x)))));
  const genHit: typeof spec = [];
  const hit = (r: Rule, f: string) => (r.rx ? r.rx.test(f) && !(r.ex ?? []).includes(f) : r.stems.some((x) => { const q = normalize(x); return f === q || (q.length >= 3 && f.startsWith(q) && SUF.has(f.slice(q.length))); }));
  toks.forEach((t, j) => {
    if (t.length < 3 || taken(t) || genHit.length >= 4) return;
    const fs = formsG(t); let g: Rule | undefined, fm = '';
    for (const r of gen) { const f = fs.find((x) => hit(r, x)); if (f) { g = r; fm = f; break; } }
    if (!g) return;
    // the word as he said it, without the conjunction/preposition/article/tanween that is not part of it («وأمي» → «أمي»، «مفتاحا» → «مفتاح»)
    let nm = words[j].slice(Math.max(0, t.length - fm.length)).replace(/^ال/, 'ال');
    const cut = nm.replace(/ا$/, ''); if (cut !== nm && cut.length >= 3 && hit(g, normalize(cut))) nm = cut;
    genHit.push({ r: g, i: j, nm });
  });
  const found = [...spec, ...genHit].sort((a, b) => a.i - b.i);
  const heads = found.filter((x) => x.r.kind === 'head').slice(0, 5); const mods = found.filter((x) => x.r.kind === 'mod');
  const actHit = Object.entries(acts).filter(([, a]) => at(a.stems) >= 0).map(([id]) => ({ id, a: acts[id], i: at(acts[id].stems) }));
  const lines: Line[] = []; const methods = new Set<string>();
  if (!heads.length) return { lines, methods, heads: [] as Rule[] };
  // 1) what he saw, in the order he told it
  const seen = [...actHit.map((x) => ({ i: x.i, n: x.a.label })), ...heads.map((x) => ({ i: x.i, n: x.nm })), ...mods.map((x) => ({ i: x.i, n: x.nm }))].sort((a, b) => a.i - b.i).map((x) => x.n);
  lines.push({ k: 'h', t: 'أولاً: ما رأيتَ' }, { k: 'p', t: `عناصر رؤياك: ${[...new Set(seen)].join('، ')}.` }, { k: 'h', t: 'ثانياً: التأويل نقطةً نقطة' });
  // 2) each thing, then what is joined to it
  let n = 0; const verdicts: string[] = []; const tails: string[] = [];
  heads.forEach(({ r, nm }) => {
    const act = actHit.find((x) => r.acts?.[x.id]);
    const alt = r.alts?.find((a) => at(a.ctx) >= 0);       // the same word read in the sense that the rest of the dream calls for («ورد» + طبيب: the vein, not the dhikr)
    const verdict = alt ? alt.verdict : act ? r.acts![act.id] : r.verdict; const why = alt ? alt.why ?? r.why : r.root ? `«${nm}» من جذر «${r.root}» الذي منه ${r.cn}` : r.why; const ev = alt && alt.ev.length ? alt.ev : r.ev;
    const m = methodOf(r); methods.add(m); verdicts.push(verdict);
    const subject = act ? `${act.a.noun} ${nm}` : `رؤيتك ${nm}`;
    lines.push({ k: 'p', t: `${AR(++n)}. ${subject} — ${m}: تدلّ على ${verdict}${r.dua ? '، والله المستعان' : ''}.` });
    if (why) lines.push({ k: 'p', t: `ووجه ذلك: أن ${why}.` });
    lines.push(...evLines(ev));
    for (const x of mods) {
      const own = heads.reduce((b, h) => (Math.abs(h.i - x.i) < Math.abs(b.i - x.i) ? h : b), heads[0]);
      if (own.r !== r) continue;
      const via = toks[x.i - 1] === 'من'; const w = x.nm; const same = x.r.family === r.family; const mm = methodOf(x.r); methods.add(mm); if (x.r.tail) tails.push(x.r.tail);
      lines.push({ k: 'p', t: `${AR(++n)}. ${via ? `وبما أنه من ${w}` : `وبما اقترن به من ${w}`} — ${mm}: ${same ? 'فزاد الأمر تأكيداً' : `يُضاف إلى ما سبق أنه يدلّ على ${x.r.verdict}`}${x.r.why ? `، لأن ${x.r.why}` : ''}.` });
      lines.push(...evLines(x.r.ev));
    }
  });
  // 3) what the whole comes to: the family that most of what he saw points to; when each points elsewhere, what he began with
  const grp = (f: string) => (f === 'رزق' ? 'مال' : f);
  const tally = new Map<string, string[]>();
  for (const x of [...heads, ...mods]) { const f = grp(x.r.family); tally.set(f, [...(tally.get(f) ?? []), x.nm]); }
  const top = [...tally].sort((a, b) => b[1].length - a[1].length)[0]; const fam = top[1].length >= 2 || heads.length === 1 ? top[0] : grp(heads[0].r.family);
  const label = fams[fam]?.label ?? LABEL[fam] ?? fam;
  if (heads.length + mods.length >= 2) {
    lines.push({ k: 'h', t: 'ثالثاً: الجمع بين ما رأيت' });
    lines.push({ k: 'p', t: top[1].length >= 2 ? `فاجتمع في رؤياك ${top[1].join(' و')}، وكلها من باب ${label}، فالغالب على رؤياك ${label}.` : `ولم يجتمع في رؤياك ما يتفق في باب واحد، فالمقدَّم فيها ${heads[0].nm} لأنه أول ما رأيتَ، وبابه ${label}.` });
  }
  // 4) the message of the dream to him, and where it ends
  lines.push({ k: 'h', t: heads.length + mods.length >= 2 ? 'رابعاً: رسالة منامك' : 'ثالثاً: رسالة منامك' });
  const f = fams[fam];
  lines.push({ k: 'p', t: `رسالة منامك إليك: أن رؤياك تدلّ على ${verdicts.join('، وعلى ')}${tails.length ? `، ${tails.join('، ')}` : ''}${f ? `؛ ${f.maal}${f.ev[0] ? `، ${inline(f.ev[0])}` : ''}` : ''}.` });
  return { lines, methods, heads: heads.map((h) => h.r) };
}

// the rule of the method that stands behind each way of reading (word for word from the books, in «قواعد علم التعبير»)
const BASIS: Record<string, string> = { 'التأويل بالسنة': 'التأويل بالسنة', 'التأويل بالقرآن': 'التأويل بالقرآن', 'التأويل بالاشتقاق': 'الاشتقاق', 'التأويل بالاسم': 'التأويل بالأسماء', 'التأويل بالتصحيف': 'التصحيف', 'التأويل بالعكس': 'المعكوس',
  'القياس': 'العبارة قياس واعتبار وتشبيه وظن', 'التشبيه': 'العبارة قياس واعتبار وتشبيه وظن', 'الضد': 'التأويل بالضد والمقلوب' };

export function interpret(dream: string, _books: Doc[], rules: Doc[], _age: Age, _marital: Marital, know: Doc[] = []): Result {
  const surface = dream.trim().split(/\s+/).map((w) => w.replace(/^[^ء-ي]+|[^ء-ي]+$/g, '')).filter(Boolean);
  const chain = compose(surface, knowledge(know));
  const found = chain.lines.length;
  const opening = found ? 'بدايةً نقول والله أعلم، وهذا في أصل التفسير وليس أعلى منه.' : 'بدايةً نقول والله أعلم، لم أقف في رؤياك على رمز أبني عليه تأويلاً قاطعاً؛ فسمِّ أبرز ما رأيت بكلمة واضحة (مثل: بحر، حية، لبن، قميص، مطر، ورد، بركة، سيارة) أو اكتبه بكلمات أخرى.';
  const pick = (title: string) => { const r = rules.find((d) => d.ref === title); const t = r?.text.split('\n')[0]?.split('\t')[0]; return r && t ? { title, text: clean(t, 420) } : null; };
  const used = found ? [...new Set([...chain.methods].map((m) => BASIS[m]).filter(Boolean))].map(pick) : [];
  return { opening, story: chain.lines, rules: used.filter((x): x is { title: string; text: string } => !!x), found,
    closing: 'والله أعلم وأحكم. وهذا اجتهادٌ في التأويل بحسب أصوله وليس فتوى؛ فاعرض رؤياك على عالمٍ ناصح.' };
}
