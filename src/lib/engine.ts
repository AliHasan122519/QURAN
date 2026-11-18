import { normalize, normalizeB, tokens, stemKeys, queryKeys, queryStem, approxRoot, hasMarks, stripTatweel, CLITICS, refTextMatch } from './arabic';
import { relatedFor } from './semantic';
import type { Doc, Hit, Kind, Lookup, MatchType, SearchResult, SourceId } from './types';

interface Idx {
  src: SourceId; docs: Doc[]; norm: string[]; normB: (string | null)[];
  post: Map<string, number[]>;            // normalised word -> doc indexes (sorted, unique)
}
export interface Options { sources: Set<SourceId>; expand: 'off' | 'auto' | 'always'; }
const MAX_RESULTS = 80;            // same cap as the original site

/** Literal comparison form: the typed sukun (ْ) and the Uthmani sukun (ۡ) are one sign, tatweel is ignored, and the order of
 *  stacked marks is canonical (shadda+fatha == fatha+shadda). Letters are never changed. */
const MARK_RUN = /[\u064B-\u065F\u0670\u06D6-\u06ED]{2,}/g;
const unify = (t: string) => t.replace(/\u06E1/g, '\u0652').replace(/\u0640/g, '').replace(MARK_RUN, (m) => [...m].sort().join(''));
const KIND_WEIGHT: Record<Kind, number> = { quran: 40, hadith: 0, poem: 0, generic: 0 };
const yieldUI = () => new Promise<void>((r) => setTimeout(r, 0));

export class Engine {
  private idx = new Map<SourceId, Idx>();
  private kinds = new Map<SourceId, Kind>();
  private skel = new Map<string, Set<string>>();   // stem/skeleton key -> vocabulary words
  private vocab = new Map<string, number>();       // word -> document frequency (all sources)
  private sorted: string[] = [];
  private byId = new Map<string, Doc>();
  private quranByRef = new Map<string, Doc>();

  getDoc(id: string) { return this.byId.get(id); }
  quranAt(s: number, a: number) { return this.quranByRef.get(`${s}:${a}`); }
  docsOf(src: SourceId) { return this.idx.get(src)?.docs ?? []; }

  /** Build the index for one source. Yields to the UI every few thousand documents. */
  async addSource(src: SourceId, docs: Doc[], kind: Kind) {
    this.kinds.set(src, kind);
    const isQ = kind === 'quran';
    const ix: Idx = { src, docs, norm: new Array(docs.length), normB: new Array(docs.length), post: new Map() };
    for (let i = 0; i < docs.length; i++) {
      const d = docs[i]; this.byId.set(d.id, d);
      if (isQ) this.quranByRef.set(`${d.surah}:${d.ayah}`, d);
      const a = normalize(d.text); ix.norm[i] = a;
      let b: string | null = null;
      if (isQ) { const nb = normalizeB(d.text); if (nb !== a) b = nb; }
      ix.normB[i] = b;
      const seen = new Set<string>();
      for (const w of tokens(a)) { seen.add(w); if (kind === 'hadith' && w.length > 3 && w.endsWith('ء')) seen.add(w.slice(0, -1)); } // OCR reads the Arabic comma as a trailing ء
      if (b) for (const w of tokens(b)) seen.add(w);
      for (const w of seen) { const l = ix.post.get(w); if (l) l.push(i); else ix.post.set(w, [i]); }
      if (i % 2500 === 2499) await yieldUI();
    }
    this.idx.set(src, ix);
    for (const [w, l] of ix.post) {
      this.vocab.set(w, (this.vocab.get(w) ?? 0) + l.length);
    }
    await yieldUI();
  }
  /** Call once after all sources are added. */
  async finalize() {
    this.skel.clear();
    for (const w of this.vocab.keys()) for (const k of stemKeys(w)) { let s = this.skel.get(k); if (!s) this.skel.set(k, (s = new Set())); s.add(w); }
    this.sorted = [...this.vocab.keys()].sort();
    await yieldUI();
  }
  has(src: SourceId) { return this.idx.has(src); }

  // ----- helpers --------------------------------------------------------------------------------------
  /** vocabulary words derivationally linked to a query word (asymmetric stem / skeleton lookup), including the word itself */
  private derivedWords(w: string): Set<string> {
    const out = new Set<string>(); if (this.vocab.has(w)) out.add(w);
    for (const k of queryKeys(w)) { const s = this.skel.get(k); if (s && s.size < 800) for (const x of s) out.add(x); }
    return out;
  }
  /** the word as typed (and its Uthmani variant) plus the same word with attached clitic particles (و/ف/ب/ك/ل/ال…).
   *  The article is NOT removed from the query: like the original site, «الصبر» is looked up as typed. */
  private exactForms(w: string): Set<string> {
    const out = new Set<string>();
    for (const base of new Set([w, normalizeB(w)])) {
      if (this.vocab.has(base)) out.add(base);
      for (const c of CLITICS) { const f = c + base; if (this.vocab.has(f)) out.add(f); }
    }
    return out;
  }
  private union(ix: Idx, words: Iterable<string>): Set<number> {
    const out = new Set<number>(); for (const w of words) { const l = ix.post.get(w); if (l) for (const i of l) out.add(i); } return out;
  }
  private intersect(sets: Set<number>[]): Set<number> {
    if (!sets.length) return new Set();
    sets = [...sets].sort((a, b) => a.size - b.size);
    const out = new Set<number>();
    for (const i of sets[0]) { let ok = true; for (let k = 1; k < sets.length; k++) if (!sets[k].has(i)) { ok = false; break; } if (ok) out.add(i); }
    return out;
  }
  private hasPhrase(ix: Idx, i: number, phrase: string): boolean {
    const p = ` ${phrase} `;
    if (` ${ix.norm[i]} `.includes(p)) return true;
    const b = ix.normB[i]; return !!b && ` ${b} `.includes(p);
  }

  suggest(prefix: string, limit = 8): string[] {
    const toks = tokens(normalize(prefix)); if (!toks.length) return [];
    const last = toks[toks.length - 1]; const head = toks.slice(0, -1).join(' ');
    let lo = 0, hi = this.sorted.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (this.sorted[m] < last) lo = m + 1; else hi = m; }
    const cands: [string, number][] = [];
    for (let i = lo; i < this.sorted.length && this.sorted[i].startsWith(last) && cands.length < 400; i++) {
      const w = this.sorted[i]; if (w.length < 2) continue; cands.push([w, this.vocab.get(w) ?? 0]);
    }
    cands.sort((a, b) => b[1] - a[1]);
    return cands.filter(([w]) => w !== last || cands.length === 1).slice(0, limit).map(([w]) => (head ? head + ' ' : '') + w);
  }

  // ----- main search ----------------------------------------------------------------------------------
  search(raw: string, opt: Options): SearchResult {
    const t0 = performance.now();
    const query = stripTatweel(raw.trim());
    const nq = normalize(query); const terms = tokens(nq);
    const empty: SearchResult = { query, hits: [], terms, root: '', related: [], highlight: new Set(), ms: 0 };
    if (!terms.length) return empty;
    const literal = hasMarks(query) ? unify(query).replace(/\s+/g, ' ') : '';
        // exact forms per term (A and B spellings of the query term), derivational neighbours
    const exactSets = terms.map((t) => this.exactForms(t));
    const textSets = terms.map((t, k) => { const set = new Set(exactSets[k]); for (const w of this.vocab.keys()) if (!set.has(w) && refTextMatch(w, t)) set.add(w); return set; });
    const derivedSets = terms.map((t) => this.derivedWords(t));
    const highlight = new Set<string>(); for (const s of textSets) for (const w of s) highlight.add(w); for (const s of derivedSets) for (const w of s) highlight.add(w);
    const hits: Hit[] = [];
    const phrase = terms.join(' ');
    const root = terms.length === 1 ? approxRoot(terms[0]) : '';

    for (const src of opt.sources) {
      const ix = this.idx.get(src); if (!ix) continue;
      const exactPer = terms.map((_, k) => this.union(ix, exactSets[k]));
      const derivedPer = terms.map((_, k) => this.union(ix, derivedSets[k]));
      const textPer = terms.map((_, k) => this.union(ix, textSets[k]));
      const exactDocs = this.intersect(exactPer);
      const textDocs = this.intersect(textPer);
      const derivedDocs = this.intersect(derivedPer);
      const all = new Set<number>([...derivedDocs, ...textDocs]);
      for (const i of all) {
        const d = ix.docs[i]; let type: MatchType; let score: number;
        const isExact = exactDocs.has(i);
        if (literal && unify(d.text).includes(literal)) { type = 'literal'; score = 1000; }
        else if (isExact) { type = 'normalized'; score = 600 + (terms.length > 1 && this.hasPhrase(ix, i, phrase) ? 150 : 0); }
        else if (textDocs.has(i)) { type = 'textual'; score = 450; }
        else { type = 'derived'; score = 300; }
        score += Math.max(0, 60 - ix.norm[i].length / 12);        // shorter texts that contain the term rank a little higher
        score += KIND_WEIGHT[this.kinds.get(src) ?? 'generic'];                                   // on ties: the Qur'an first
        let via: string | undefined;
        if (type === 'derived') { for (const w of tokens(ix.norm[i])) if (derivedSets[0].has(w)) { via = w; break; } }
        hits.push({ id: d.id, src, ord: i, score, type, via });
      }
    }
    // ----- optional semantic expansion (curated lists), only for single-term queries and few direct results
    let related: string[] = [];
    if (opt.expand !== 'off' && terms.length === 1 && (opt.expand === 'always' || hits.length < 8)) {
      const keys = [terms[0], queryStem(terms[0])];
      for (const k of keys) { const r = relatedFor(k); if (r.length) { related = r; break; } }
      if (related.length) {
        const seen = new Set(hits.map((h) => h.id));
        for (const src of opt.sources) {
          const ix = this.idx.get(src); if (!ix) continue;
          for (const w of related) {
            const l = ix.post.get(w); if (!l) continue; highlight.add(w);
            let added = 0;
            for (const i of l) { const d = ix.docs[i]; if (seen.has(d.id)) continue; seen.add(d.id); hits.push({ id: d.id, src, ord: i, score: 100 - added, type: 'semantic', via: w }); if (++added >= 25) break; }
          }
        }
      }
    }
    hits.sort((a, b) => b.score - a.score);
    return { query, hits, terms, root, related, highlight, ms: Math.round(performance.now() - t0) };
  }

  /** The original site's behaviour: direct (textual) matches first, in the source's own order; the lexical/semantic expansion is added
   *  only when direct matches are few; at most 80 results are returned and there is no relevance re-ordering. */
  /** al-Alfiya: a query made of ONE letter shows that letter's chapter («حرف الواو») with all its verses. Any longer query is searched normally. */
  letterSection(src: SourceId, raw: string): Lookup | null {
    const q = raw.normalize('NFC').replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\s]/g, '');
    if ([...q].length !== 1) return null;
    const NAMES: Record<string, string> = { ا: 'الألف', أ: 'الألف', إ: 'الألف', آ: 'الألف', ٱ: 'الألف', ب: 'الباء', ت: 'التاء', ج: 'الجيم', ح: 'الحاء', خ: 'الخاء', د: 'الدال', ذ: 'الذال', ر: 'الراء', ز: 'الزاي', س: 'السين', ش: 'الشين', ص: 'الصاد', ض: 'الضاد', ط: 'الطاء', ظ: 'الظاء', ع: 'العين', غ: 'الغين', ف: 'الفاء', ق: 'القاف', ك: 'الكاف', ل: 'اللام', م: 'الميم', ن: 'النون', ه: 'الهاء', و: 'الواو', ي: 'الياء', ى: 'الياء' };
    const name = NAMES[q]; if (!name) return null;
    const title = `حرف ${name}`;
    const docs = this.docsOf(src).filter((d) => d.chapter?.split(' — ').pop() === title);
    if (!docs.length) return null;
    return { query: raw, directCount: docs.length, semanticCount: 0, expansion: null, section: `باب ${title}`, highlight: new Set(),
      results: docs.map((doc, i) => ({ hit: { id: doc.id, src, ord: i, score: 0, type: 'literal' as MatchType }, doc, matchType: 'نصي' as const, matchedTerm: '' })), capped: false };
  }
  lookup(src: SourceId, raw: string): Lookup {
    if (this.kinds.get(src) === 'poem') { const s = this.letterSection(src, raw); if (s) return s; }
    const r = this.search(raw, { sources: new Set([src]), expand: 'always' });
    let direct = r.hits.filter((h) => h.type === 'literal' || h.type === 'normalized' || h.type === 'textual').sort((a, b) => a.ord - b.ord);
    if (r.terms.length > 1) { const contiguous = direct.filter((h) => h.score >= 750); if (contiguous.length) direct = contiguous; }   // a phrase: prefer the words in sequence
    let extra = r.hits.filter((h) => h.type === 'derived' || h.type === 'semantic').sort((a, b) => a.ord - b.ord);
    if (direct.length >= 5 || r.terms.length > 1) extra = [];      // expansion: only when direct matches are few, and only for a single word (it is root-based)
    const all = [...direct, ...extra]; const shown = all.slice(0, MAX_RESULTS);
    const results = shown.map((hit) => {
      const doc = this.byId.get(hit.id)!; const isDirect = hit.type === 'literal' || hit.type === 'normalized' || hit.type === 'textual';
      return { hit, doc, matchType: (isDirect ? 'نصي' : 'دلالي') as 'نصي' | 'دلالي', matchedTerm: hit.via ?? '' };
    });
    const terms = r.related.length ? r.related : [...new Set(extra.map((h) => h.via).filter((x): x is string => !!x))].slice(0, 6);
    const hl = new Set(r.highlight); if (direct.length >= 5) { /* highlight only what was searched */ }
    return { query: r.query, directCount: direct.length, semanticCount: extra.length, expansion: extra.length || r.root ? { root: r.root, terms } : null, results, highlight: hl, capped: all.length > MAX_RESULTS };
  }
}
