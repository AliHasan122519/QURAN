import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { X, BookOpen, Download, ArrowRight, FileText, Images } from 'lucide-react';
import type { Doc } from '../lib/types';
import { parseJson } from '../lib/data';
import { downloadFile, saveTextFile, fileName, type SaveResult } from '../lib/downloader';
import { toAr } from '../lib/format';
import { BookCover } from './BookCover';
import { BookReader, type BookData } from './BookReader';
import { BookEmbed, type ScanToc } from './BookEmbed';
import { topmost } from './DreamsPanel';

interface BookCard {
  kind: string; era: string; author: string; authorFull: string; coverTitle: string; cover: { p: number; m: number; img?: string };
  info: [string, string][]; infoSrc: string; about: { t: string; s: string }[]; note: string; inApp: boolean;
  reader: { mode: 'text'; file: string; src: string; ocr: boolean; scan: string; count: number } | { mode: 'embed'; id: string; src: string };
  toc: [number, string, number | null, (number | null)?][]; tocSrc: string;
  dls: { label: string; url: string; size: string; id: string; sub?: string; view?: boolean }[];
}
interface Book { id: string; title: string; card: BookCard; }
export type LoadFile = (rel: string) => Promise<ArrayBuffer | null>;
const parse = (docs: Doc[]): Book[] => docs.flatMap((d) => { try { const c = JSON.parse(d.extra ?? '') as BookCard; return c?.reader && c.toc ? [{ id: d.id, title: d.ref ?? '', card: c }] : []; } catch { return []; } });
const SHOWN = 14;

/** the picture of the printed cover (a content file, opened on demand and kept by the app) as an address the page can show; nothing until it is read, so the drawn cover is shown meanwhile */
function useCover(load: LoadFile, img?: string): string | undefined {
  const [url, setUrl] = useState<string>();
  useEffect(() => {
    if (!img) return; let dead = false, made = '';
    load(img).then((b) => { if (b && !dead) { made = URL.createObjectURL(new Blob([b], { type: 'image/jpeg' })); setUrl(made); } }).catch(() => undefined);
    return () => { dead = true; if (made) URL.revokeObjectURL(made); };
  }, [img, load]);
  return url;
}
function Cover({ book, load, className }: { book: Book; load: LoadFile; className: string }) {
  const c = book.card; const photo = useCover(load, c.cover.img);
  return <BookCover className={className} title={c.coverTitle} author={c.author} kind={c.kind} p={c.cover.p} m={c.cover.m} photo={photo} />;
}

/** the text of a book as a plain file (its title, its author, then the paragraphs; the titles of the table of contents stand out) */
function textOf(title: string, c: BookCard, d: BookData): string {
  const heads = new Map(d.toc.map(([l, , i]) => [i, l] as const));
  return [title, c.authorFull, '', ...d.p.map((p, i) => (heads.has(i) ? `\n${'#'.repeat(heads.get(i)!)} ${p}\n` : p))].join('\n\n').replace(/\n{4,}/g, '\n\n\n');
}

/** one book: its cover, its table of contents (فهرس), what is known of it (every passage quoted from a named source), and the two buttons: read it (inside the app), download it (to the phone) */
function BookDetail({ book, load, onClose }: { book: Book; load: LoadFile; onClose: () => void }) {
  const back = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  const c = book.card; const [read, setRead] = useState<{ at: number | null } | null>(null); const [scan, setScan] = useState<number | null>(null); const [all, setAll] = useState(false);
  const [msg, setMsg] = useState(''); const [busy, setBusy] = useState('');
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [onClose]);
  const said = (r: SaveResult) => setMsg(r === 'started' ? 'بدأ التحميل في الخلفية. سيظهر إشعار عند اكتماله، وتجد الملف في مجلد «التنزيلات» بجهازك.' : r === 'saved' ? 'تم حفظ الملف في مجلد «التنزيلات» بجهازك.' : 'بدأ تنزيل الملف.');
  const fail = (e: unknown) => setMsg('تعذّر التحميل: ' + String((e as { message?: string })?.message ?? e).slice(0, 120));
  const dl = async (k: string, f: () => Promise<SaveResult>) => { setBusy(k); setMsg(''); try { said(await f()); } catch (e) { fail(e); } finally { setBusy(''); } };
  const saveTxt = () => dl('txt', async () => {
    if (c.reader.mode !== 'text') throw new Error('لا نص لهذا الكتاب');
    const buf = await load(c.reader.file); if (!buf) throw new Error('تعذّر فتح نص الكتاب');
    return saveTextFile(fileName(`${book.title} - ${c.author}`, 'txt'), textOf(book.title, c, parseJson<BookData>(buf)));
  });
  const entries = all ? c.toc : c.toc.slice(0, SHOWN);
  const openAt = (e: BookCard['toc'][number]) => setRead({ at: e[2] });
  return (
    <div ref={back} className="panel-back nested" onClick={(e) => { e.stopPropagation(); onClose(); }}>
      <div className="panel lib-detail" role="dialog" aria-modal="true" aria-label={book.title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head">
          <div><h2>{book.title}</h2><p className="panel-sub">{c.authorFull}</p></div>
          <button type="button" ref={close} className="drawer-x" aria-label="رجوع" onClick={onClose}><ArrowRight size={20} aria-hidden="true" /></button>
        </div>
        <div className="lib-hero">
          <Cover book={book} load={load} className="lib-cover-big" />
          <div className="lib-chips"><span className="lib-chip">{c.kind}</span><span className="lib-chip">{c.era}</span>{c.inApp && <span className="lib-chip lib-chip-app">من مراجع تبويب «الكتب»</span>}</div>
        </div>
        <div className="lib-actions">
          <button type="button" className="go lib-read" onClick={() => setRead({ at: null })}><BookOpen size={18} aria-hidden="true" />قراءة داخل التطبيق<small>{c.reader.mode === 'text' ? `${c.reader.ocr ? 'نص مقروء آلياً' : 'نص الكتاب'} مع فهرسه وبحث داخله` : c.toc.length ? 'صفحات الكتاب كما طُبعت مع فهرسه' : 'صور صفحات المخطوطة (تحتاج إنترنت)'}</small></button>
          {c.dls.map((d, i) => (d.view === false || (c.reader.mode === 'embed' && c.reader.id === d.id) ? null : (
            <button type="button" key={'s' + i} className="go lib-scan" onClick={() => setScan(i)}><Images size={18} aria-hidden="true" />قراءة الكتاب المصوَّر<small>{d.label.replace(/\s*\(PDF\)/, '')} · صور الصفحات كما طُبعت (تحتاج إنترنت)</small></button>)))}
          {c.dls.map((d, i) => (
            <button type="button" key={i} className="go lib-dl" disabled={!!busy} onClick={() => dl('d' + i, () => downloadFile(d.url, fileName(`${book.title} - ${c.author}${c.dls.length > 1 ? ' (' + (i + 1) + ')' : ''}`, 'pdf')))}><Download size={18} aria-hidden="true" />{busy === 'd' + i ? 'جارٍ البدء…' : 'تحميل'}<small>{d.label} · {d.size}</small></button>
          ))}
          {c.reader.mode === 'text' && (
            <button type="button" className="go lib-dl lib-txt" disabled={!!busy} onClick={saveTxt}><FileText size={18} aria-hidden="true" />{busy === 'txt' ? 'جارٍ الحفظ…' : 'تحميل نص الكتاب (TXT)'}<small>ملف نصي يُحفظ على جهازك، يُقرأ بلا إنترنت</small></button>
          )}
        </div>
        <p className="lib-status" role="status" aria-live="polite">{msg}</p>
        {c.toc.length > 0 && <section className="lib-sec"><h3 className="dream-label">فهرس الكتاب ({toAr(c.toc.length)})</h3>
          <ol className="lib-toc">{entries.map((e, n) => (<li key={n} className={`lv${e[0]}`}><button type="button" onClick={() => openAt(e)}>{e[1]}{e[3] ? <span className="rd-tocpg"> — ص {toAr(e[3])}</span> : null}</button></li>))}</ol>
          {c.toc.length > SHOWN && <button type="button" className="lib-more" onClick={() => setAll(!all)}>{all ? 'إخفاء بقية الفهرس' : `عرض الفهرس كاملاً (${toAr(c.toc.length)})`}</button>}
          <p className="takhrij" dir="rtl">مصدر الفهرس: {c.tocSrc}</p>
        </section>}
        <section className="lib-sec"><h3 className="dream-label">عن الكتاب</h3>
          {c.about.map((a, i) => (<figure className="lib-quote" key={i}><blockquote dir="rtl">{a.t}</blockquote><figcaption>— {a.s}</figcaption></figure>))}
          {c.note && <p className="lib-note" dir="rtl">{c.note}</p>}
        </section>
        <section className="lib-sec"><h3 className="dream-label">معلومات الكتاب</h3>
          <dl className="lib-info">{c.info.map(([k, v], i) => (<div key={i}><dt>{k}</dt><dd>{v}</dd></div>))}</dl>
          <p className="takhrij" dir="rtl">المصدر: {c.infoSrc}</p>
          <p className="takhrij" dir="rtl">النص في القارئ: {c.reader.src}</p>
        </section>
        <p className="lib-fine" dir="rtl">ملفات «تحميل» نسخ مصورة من أرشيف الإنترنت وقد تختلف طبعتها عن طبعة النص في القارئ.</p>
        {read && c.reader.mode === 'text' && <BookReader title={book.title} file={c.reader.file} load={load} scan={c.reader.scan || undefined} startAt={read.at ?? undefined} onClose={() => setRead(null)} />}
        {scan !== null && <BookEmbed title={`${book.title} — ${c.dls[scan].label.replace(/\s*\(PDF\)/, '')}`} id={c.dls[scan].sub ? `${c.dls[scan].id}/${c.dls[scan].sub}` : c.dls[scan].id} toc={[]} tocSrc="" onClose={() => setScan(null)} />}
        {read && c.reader.mode === 'embed' && <BookEmbed title={book.title} id={c.reader.id} toc={c.toc as ScanToc} tocSrc={c.tocSrc} startLeaf={read.at} manuscript={!c.toc.length} onClose={() => setRead(null)} />}
      </div>
    </div>
  );
}

/** «كتب علم التعبير» and «كتب علم الفراسة»: the books as covers, two by two; touching one opens its page. */
export function LibraryPanel({ title, sub, docs, load, onClose }: { title: string; sub?: string; docs: Doc[]; load: LoadFile; onClose: () => void }) {
  const books = useMemo(() => parse(docs), [docs]); const [open, setOpen] = useState<Book | null>(null);
  const back = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  const shut = useCallback(() => setOpen(null), []);
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
              <Cover book={b} load={load} className="lib-cover" />
              <span className="lib-title">{b.title}</span>
              <span className="lib-author">{b.card.author}</span>
            </button>
          ))}
        </div>
        {!books.length && <p className="drawer-empty">لا توجد كتب الآن.</p>}
      </div>
      {open && <BookDetail book={open} load={load} onClose={shut} />}
    </div>
  );
}
