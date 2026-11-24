import { useEffect, useMemo, useRef, useState } from 'react';
import { X, BookOpen, Download, ArrowRight } from 'lucide-react';
import type { Doc } from '../lib/types';
import { BookCover } from './BookCover';
import { topmost } from './DreamsPanel';

interface BookCard {
  kind: string; era: string; author: string; authorFull: string; coverTitle: string; cover: { p: number; m: number };
  info: [string, string][]; infoSrc: string; about: { t: string; s: string }[]; note: string; inApp: boolean;
  read: { label: string; url: string }; dls: { label: string; url: string; size: string }[];
}
interface Book { id: string; title: string; card: BookCard; }
const parse = (docs: Doc[]): Book[] => docs.flatMap((d) => { try { const c = JSON.parse(d.extra ?? '') as BookCard; return c?.read?.url ? [{ id: d.id, title: d.ref ?? '', card: c }] : []; } catch { return []; } });

/** one book: its cover, what is known of it (every passage is quoted from a named source), and the two buttons: read it, download it */
function BookDetail({ book, onClose }: { book: Book; onClose: () => void }) {
  const back = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  const c = book.card;
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [onClose]);
  return (
    <div ref={back} className="panel-back nested" onClick={(e) => { e.stopPropagation(); onClose(); }}>
      <div className="panel lib-detail" role="dialog" aria-modal="true" aria-label={book.title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head">
          <div><h2>{book.title}</h2><p className="panel-sub">{c.authorFull}</p></div>
          <button type="button" ref={close} className="drawer-x" aria-label="رجوع" onClick={onClose}><ArrowRight size={20} aria-hidden="true" /></button>
        </div>
        <div className="lib-hero">
          <BookCover className="lib-cover-big" title={c.coverTitle} author={c.author} kind={c.kind} p={c.cover.p} m={c.cover.m} />
          <div className="lib-chips"><span className="lib-chip">{c.kind}</span><span className="lib-chip">{c.era}</span>{c.inApp && <span className="lib-chip lib-chip-app">من مراجع تبويب «الكتب»</span>}</div>
        </div>
        <div className="lib-actions">
          <a className="go lib-read" href={c.read.url} target="_blank" rel="noopener noreferrer"><BookOpen size={18} aria-hidden="true" />قراءة<small>{c.read.label}</small></a>
          {c.dls.map((d, i) => (
            <a key={i} className="go lib-dl" href={d.url} target="_blank" rel="noopener noreferrer"><Download size={18} aria-hidden="true" />تحميل<small>{d.label} · {d.size}</small></a>
          ))}
        </div>
        {c.dls.length === 0 && c.note && <p className="lib-nodl">{c.note}</p>}
        <section className="lib-sec"><h3 className="dream-label">عن الكتاب</h3>
          {c.about.map((a, i) => (<figure className="lib-quote" key={i}><blockquote dir="rtl">{a.t}</blockquote><figcaption>— {a.s}</figcaption></figure>))}
          {c.dls.length > 0 && c.note && <p className="lib-note" dir="rtl">{c.note}</p>}
        </section>
        <section className="lib-sec"><h3 className="dream-label">معلومات الكتاب</h3>
          <dl className="lib-info">{c.info.map(([k, v], i) => (<div key={i}><dt>{k}</dt><dd>{v}</dd></div>))}</dl>
          <p className="takhrij" dir="rtl">المصدر: {c.infoSrc}</p>
        </section>
        <p className="lib-fine" dir="rtl">الروابط تفتح في المتصفح (المكتبة الشاملة أو أرشيف الإنترنت). والملفات المرفقة نسخ مصورة قد تختلف طبعتها عن طبعة القراءة.</p>
      </div>
    </div>
  );
}

/** «كتب علم التعبير» and «كتب علم الفراسة»: the books as covers, two by two; touching one opens its page. */
export function LibraryPanel({ title, sub, docs, onClose }: { title: string; sub?: string; docs: Doc[]; onClose: () => void }) {
  const books = useMemo(() => parse(docs), [docs]); const [open, setOpen] = useState<Book | null>(null);
  const back = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key); const prev = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', key); document.body.style.overflow = prev; };
  }, [onClose]);
  return (
    <div ref={back} className="panel-back" onClick={onClose}>
      <div className="panel" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head">
          <div><h2>{title}</h2>{sub && <p className="panel-sub">{sub}</p>}</div>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <div className="lib-grid">
          {books.map((b) => (
            <button type="button" key={b.id} className="lib-tile" data-src="book" onClick={() => setOpen(b)}>
              <BookCover className="lib-cover" title={b.card.coverTitle} author={b.card.author} kind={b.card.kind} p={b.card.cover.p} m={b.card.cover.m} />
              <span className="lib-title">{b.title}</span>
              <span className="lib-author">{b.card.author}</span>
            </button>
          ))}
        </div>
        {!books.length && <p className="drawer-empty">لا توجد كتب الآن.</p>}
      </div>
      {open && <BookDetail book={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
