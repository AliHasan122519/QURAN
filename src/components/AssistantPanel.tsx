import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { X, Send, BookOpen, Images } from 'lucide-react';
import type { Doc } from '../lib/types';
import type { Engine } from '../lib/engine';
import { parseJson } from '../lib/data';
import { Assistant, parseBooks, type BookMeta, type BookText, type Card, type Open, type Reply } from '../lib/assistant';
import { BookReader } from './BookReader';
import { BookEmbed } from './BookEmbed';
import { topmost } from './DreamsPanel';

type Msg = { id: number; who: 'me' | 'bot'; text: string; cards?: Card[]; chips?: string[] };
const FIRST = ['وش فسّروا رؤية الماء؟', 'مين ابن سيرين؟', 'كم صفحة كتاب المرقبة العليا؟', 'دوّر لي فصل الصداقة في كتاب الأخلاق والسير'];

/** The assistant of the app: a chat that answers only from the references the app holds (see lib/assistant.ts). Every answer shows where it comes from and opens the book at that place. */
export function AssistantPanel({ title, sub, phrases, lists, engine, load, onClose }: { title: string; sub?: string; phrases: Doc[]; lists: Record<string, Doc[]>; engine: Engine; load: (rel: string) => Promise<ArrayBuffer | null>; onClose: () => void }) {
  const books = useMemo(() => [...parseBooks(lists.kutubtabir ?? [], 'kutubtabir'), ...parseBooks(lists.nazm ?? [], 'nazm'), ...parseBooks(lists.kutubfiras ?? [], 'kutubfiras')], [lists]);
  const bank = useMemo(() => { const m: Record<string, string[]> = {}; for (const d of phrases) if (d.ref) (m[d.ref] ??= []).push(d.text); return m; }, [phrases]);
  const [status, setStatus] = useState('');
  const bot = useMemo(() => new Assistant({
    engine, books, people: lists.muabbirun ?? [], phrases: bank, onStatus: setStatus,
    loadBook: async (b: BookMeta) => { if (!b.textFile) return null; const buf = await load(b.textFile); return buf ? parseJson<BookText>(buf) : null; },
  }), [engine, books, lists.muabbirun, bank, load]);
  const [msgs, setMsgs] = useState<Msg[]>([]); const [q, setQ] = useState(''); const [busy, setBusy] = useState(false);
  const [read, setRead] = useState<{ book: BookMeta; para: number } | null>(null); const [scan, setScan] = useState<{ book: BookMeta; leaf: number | null } | null>(null);
  const back = useRef<HTMLDivElement>(null); const end = useRef<HTMLDivElement>(null); const input = useRef<HTMLInputElement>(null); const n = useRef(0);
  const ready = Object.keys(bank).length > 0;
  useEffect(() => {
    input.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key); const prev = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', key); document.body.style.overflow = prev; };
  }, [onClose]);
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }); }, [msgs, busy]);
  useEffect(() => {
    if (!ready || msgs.length) return;
    bot.ask('هلا').then((r) => setMsgs([{ id: ++n.current, who: 'bot', text: r.text, chips: FIRST }])).catch(() => undefined);
  }, [ready, bot, msgs.length]);
  const send = useCallback(async (text: string) => {
    const t = text.trim(); if (!t || busy) return; setQ(''); setBusy(true); setStatus('');
    setMsgs((m) => [...m, { id: ++n.current, who: 'me', text: t }]);
    const t0 = Date.now(); let r: Reply;
    try { r = await bot.ask(t); } catch { r = { text: 'صار عندي خلل وأنا أدوّر، جرّب مرة ثانية.', cards: [], chips: [] }; }
    const wait = Math.max(0, 650 - (Date.now() - t0)); if (wait) await new Promise((x) => setTimeout(x, wait));
    setMsgs((m) => [...m, { id: ++n.current, who: 'bot', text: r.text, cards: r.cards, chips: r.chips }]); setBusy(false); setStatus('');
    input.current?.focus();
  }, [bot, busy]);
  const byId = (id: string) => books.find((b) => b.id === id);
  const open = (o: Open) => { const b = byId(o.book); if (!b) return; if (o.kind === 'text') setRead({ book: b, para: o.para }); else setScan({ book: b, leaf: o.leaf }); };
  return (
    <div ref={back} className="panel-back" onClick={onClose}>
      <div className="panel as-panel" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head">
          <div><h2>{title}</h2>{sub && <p className="panel-sub">{sub}</p>}</div>
          <button type="button" className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <div className="as-chat" role="log" aria-live="polite" aria-label="المحادثة">
          {!ready && <p className="drawer-empty">المساعد يحتاج تحديث المحتوى. افتح التطبيق وأنت متصل بالإنترنت مرة وارجع.</p>}
          {msgs.map((m) => (
            <div key={m.id} className={`as-msg as-${m.who}`}>
              <p className="as-text" dir="rtl">{m.text}</p>
              {m.cards?.map((c, i) => (
                <article key={i} className="as-card" dir="rtl">
                  <h4>{c.title}</h4><p className="as-where">{c.where}</p>
                  {c.quote && <blockquote>{c.quote}</blockquote>}
                  {c.open.length > 0 && <div className="as-open">{c.open.map((o, k) => (
                    <button key={k} type="button" className="as-link" onClick={() => open(o)}>{o.kind === 'text' ? <><BookOpen size={14} aria-hidden="true" />افتح في الكتاب المفرَّغ</> : <><Images size={14} aria-hidden="true" />افتح في الكتاب المصوَّر</>}</button>))}</div>}
                </article>
              ))}
              {m.chips && m.chips.length > 0 && <div className="as-chips">{m.chips.map((c) => <button key={c} type="button" className="as-chip" disabled={busy} onClick={() => send(c)}>{c}</button>)}</div>}
            </div>
          ))}
          {busy && <div className="as-msg as-bot as-typing" aria-label="المساعد يكتب"><span /><span /><span />{status && <em>{status}</em>}</div>}
          <div ref={end} />
        </div>
        <form className="as-form" onSubmit={(e) => { e.preventDefault(); send(q); }}>
          <input ref={input} className="as-input" type="text" dir="rtl" enterKeyHint="send" placeholder="اكتب سؤالك هنا" aria-label="اكتب سؤالك للمساعد" value={q} onChange={(e) => setQ(e.target.value)} disabled={!ready} />
          <button type="submit" className="go as-send" aria-label="إرسال" disabled={!ready || busy || !q.trim()}><Send size={18} aria-hidden="true" /></button>
        </form>
        <p className="as-fine" dir="rtl">أجاوب من المراجع اللي في التطبيق بس، وأنقل كلام الكتب بمصدره؛ وما أقول شي من راسي.</p>
      </div>
      {read && read.book.textFile && <BookReader title={read.book.title} file={read.book.textFile} load={load} scan={read.book.scanId} startAt={read.para} onClose={() => setRead(null)} />}
      {scan && scan.book.scanId && <BookEmbed title={scan.book.title} id={scan.book.scanId} toc={[]} tocSrc="" startLeaf={scan.leaf} manuscript={scan.book.card.reader.mode === 'embed' && !!scan.book.card.reader.manuscript} onClose={() => setScan(null)} />}
    </div>
  );
}
