import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { Search, X } from 'lucide-react';
import type { Doc } from '../lib/types';
import { normalize } from '../lib/arabic';
import { dialectVariants } from '../lib/dialect';
import { toAr } from '../lib/format';
import { Rich } from './Cards';

const PAGE = 30;
const CLITIC = '(?:وال|فال|بال|كال|لل|ول|ال|و|ف|ب|ك|ل)?';

/** One dream with its interpretation, as the book tells it: the dream, then the interpretation, then the book (and the interpreter when the passage names him). */
const DreamCard = memo(function DreamCard({ doc, words }: { doc: Doc; words: Set<string> }) {
  return (
    <article className="verse-card dream-card" data-src="dream">
      {doc.by && doc.by !== 'مؤلف الكتاب' && <div className="card-top"><span className="pill pill-text"><i />المعبِّر: {doc.by}</span></div>}
      {doc.by === 'مؤلف الكتاب' && <div className="card-top"><span className="pill pill-text"><i />عبّرها مؤلف الكتاب</span></div>}
      <h3 className="dream-label">{doc.explanation ? 'الرؤيا' : 'الرؤيا وتعبيرها'}</h3>
      <p dir="rtl" className="meaning-text"><Rich text={doc.text} words={words} /></p>
      {doc.explanation && <><h3 className="dream-label">التعبير</h3><p dir="rtl" className="meaning-text"><Rich text={doc.explanation} words={words} /></p></>}
      {doc.source && <p dir="rtl" className="takhrij">المرجع: {doc.source}</p>}
    </article>
  );
});

/** «رؤى وتعبيرها»: the full list (every dream the reference books narrate with its interpretation, from every book, with the book named), searchable and filterable by book. */
export function DreamsPanel({ title, docs, onClose }: { title: string; docs: Doc[]; onClose: () => void }) {
  const [q, setQ] = useState(''); const [applied, setApplied] = useState(''); const [book, setBook] = useState(''); const [limit, setLimit] = useState(PAGE);
  const top = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', key); const prev = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', key); document.body.style.overflow = prev; };
  }, [onClose]);
  const index = useMemo(() => docs.map((d) => ({ d, hay: ' ' + normalize(d.text), hayI: ' ' + normalize(d.explanation ?? '') })), [docs]);
  const books = useMemo(() => { const m = new Map<string, number>(); for (const d of docs) if (d.source) m.set(d.source, (m.get(d.source) ?? 0) + 1); return [...m]; }, [docs]);
  const { list, words } = useMemo(() => {
    const words = new Set<string>(); let rows = index.filter((x) => !book || x.d.source === book);
    const t = applied.trim();
    if (t) {
      const variants = dialectVariants(t).variants.map((v) => normalize(v).split(' ').filter((w) => w.length >= 2)).filter((v) => v.length);
      const rxs = variants.map((toks) => toks.map((w) => new RegExp('(?: )' + CLITIC + w)));
      for (const toks of variants) for (const w of toks) for (const c of ['', 'ال', 'و', 'ف', 'ب', 'ك', 'ل', 'وال', 'بال', 'لل']) words.add(c + w);
      const scored: { d: Doc; s: number }[] = [];
      for (const x of rows) {
        let best = -1;
        for (const toks of rxs) { if (toks.every((r) => r.test(x.hay) || r.test(x.hayI))) best = Math.max(best, toks.every((r) => r.test(x.hay)) ? 2 : 1); }
        if (best > 0) scored.push({ d: x.d, s: best });
      }
      scored.sort((a, b) => b.s - a.s);                         // the dream itself mentions it first, then the interpretation only
      return { list: scored.map((x) => x.d), words };
    }
    return { list: rows.map((x) => x.d), words };
  }, [index, applied, book]);
  const submit = (e: React.FormEvent) => { e.preventDefault(); const t = q.trim(); if (!t) return; setApplied(t); setQ(''); setLimit(PAGE); top.current?.scrollIntoView({ block: 'start' }); };
  const shown = list.slice(0, limit);
  return (
    <div className="panel-back" onClick={onClose}>
      <div className="panel" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head" ref={top}>
          <div><h2>{title}</h2><p className="panel-sub">{toAr(docs.length)} رؤيا مع تعبيرها من {toAr(books.length)} {books.length === 1 ? 'مرجع' : 'مراجع'}</p></div>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <form className="sform" onSubmit={submit}>
          <div className="field">
            <Search size={20} className="field-ic" aria-hidden="true" />
            <label className="sr" htmlFor="q-dreams">اكتب هنا</label>
            <input id="q-dreams" value={q} dir="rtl" enterKeyHint="search" inputMode="search" autoComplete="off" placeholder="اكتب هنا" onChange={(e) => setQ(e.target.value)} />
          </div>
          <div className="form-row">
            <label className="book-pick"><span className="sr">المرجع</span>
              <select value={book} onChange={(e) => { setBook(e.target.value); setLimit(PAGE); }} aria-label="المرجع">
                <option value="">كل المراجع</option>
                {books.map(([b, n]) => <option key={b} value={b}>{b} ({toAr(n)})</option>)}
              </select>
            </label>
            <button type="submit" className="go" disabled={!q.trim()}><Search size={16} />ابحث</button>
          </div>
        </form>
        {applied && <div className="stats"><div><span>نتائج البحث عن «<b>{applied}</b>»: <b>{toAr(list.length)}</b></span></div><button type="button" className="retry" onClick={() => { setApplied(''); setLimit(PAGE); }}>عرض الكل</button></div>}
        <div className="space dream-list" role="region" aria-label="الرؤى" aria-live="polite">
          {shown.map((d) => <DreamCard key={d.id} doc={d} words={words} />)}
          {!list.length && <div className="soft" role="status">لم نعثر على رؤى تطابق بحثك.</div>}
          {list.length > limit && <button type="button" className="go more" onClick={() => setLimit((n) => n + PAGE)}>عرض المزيد ({toAr(list.length - limit)} متبقية)</button>}
        </div>
      </div>
    </div>
  );
}
