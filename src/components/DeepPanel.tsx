import { useEffect, useMemo, useRef, useState } from 'react';
import { Wand2, X } from 'lucide-react';
import type { Doc } from '../lib/types';
import { AGES, MARITALS, interpret } from '../lib/taweel';
import type { Age, Marital, Result } from '../lib/taweel';
import { Rich } from './Cards';
import { topmost } from './DreamsPanel';

const NONE = new Set<string>();
/** «التأويل العميق»: the dream, the age and the marital state (both chosen, for the sake of accuracy), and the interpretation as one interpreter would address the dreamer. */
export function DeepPanel({ title, books, rules, onClose }: { title: string; books: Doc[]; rules: Doc[]; onClose: () => void }) {
  const [dream, setDream] = useState(''); const [age, setAge] = useState<Age | ''>(''); const [marital, setMarital] = useState<Marital | ''>('');
  const [res, setRes] = useState<Result | null>(null); const [busy, setBusy] = useState(false);
  const back = useRef<HTMLDivElement>(null); const top = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null); const out = useRef<HTMLDivElement>(null);
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key); const prev = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', key); document.body.style.overflow = prev; };
  }, [onClose]);
  const ready = dream.trim().length >= 3 && !!age && !!marital;
  const need = !dream.trim() ? 'اكتب رؤياك أو رموزها' : !age ? 'اختر عمرك' : !marital ? 'اختر حالتك الاجتماعية' : '';
  const submit = (e: React.FormEvent) => {
    e.preventDefault(); if (!ready || !age || !marital) return;
    setBusy(true);
    setTimeout(() => { setRes(interpret(dream, books, rules, age, marital)); setBusy(false); setTimeout(() => out.current?.scrollIntoView({ block: 'start', behavior: 'smooth' }), 60); }, 30);
  };
  const empty = useMemo(() => books.length === 0, [books]);
  return (
    <div ref={back} className="panel-back" onClick={onClose}>
      <div className="panel deep" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head" ref={top}>
          <div><h2>{title}</h2><p className="panel-sub">اكتب رؤياك، فيأتيك تأويلها من الأصول</p></div>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <form className="deep-form" onSubmit={submit}>
          <label className="sr" htmlFor="q-deep">اكتب رؤياك</label>
          <textarea id="q-deep" value={dream} dir="rtl" rows={5} placeholder="اكتب رؤياك أو رموزها هنا" onChange={(e) => { setDream(e.target.value); }} />
          <fieldset className="deep-group"><legend>عمرك</legend>
            <div role="radiogroup" aria-label="العمر" className="deep-chips">
              {AGES.map((a) => <button type="button" role="radio" aria-checked={age === a.id} data-on={age === a.id} key={a.id} className="deep-chip" onClick={() => setAge(a.id)}>{a.label}</button>)}
            </div>
          </fieldset>
          <fieldset className="deep-group"><legend>حالتك الاجتماعية</legend>
            <div role="radiogroup" aria-label="الحالة الاجتماعية" className="deep-chips">
              {MARITALS.map((m) => <button type="button" role="radio" aria-checked={marital === m.id} data-on={marital === m.id} key={m.id} className="deep-chip" onClick={() => setMarital(m.id)}>{m.label}</button>)}
            </div>
          </fieldset>
          <p className="deep-note">يُختار العمر والحالة الاجتماعية لأن الأصول تُغيّر التأويل بحسب حال الرائي.</p>
          <button type="submit" className="go deep-go" disabled={!ready || busy || empty}><Wand2 size={16} aria-hidden="true" />{busy ? 'جارٍ التأويل…' : 'التأويل'}</button>
          {!ready && dream.length > 0 && <p className="deep-need" role="status">{need}</p>}
        </form>
        <div ref={out} className="deep-out" aria-live="polite">
          {res && (
            <>
              {res.sections.map((s, i) => (
                <article className="verse-card deep-card" key={s.symbol + i}>
                  {i === 0 && <p dir="rtl" className="deep-open">{res.opening}</p>}
                  <h3 className="rule-title">رؤيتك «{s.symbol}»</h3>
                  <p dir="rtl" className="deep-verdict"><Rich text={s.verdict} words={NONE} /></p>
                  {s.why && <p dir="rtl" className="deep-why"><b>ووجه ذلك:</b> <Rich text={s.why} words={NONE} /></p>}
                  {s.mine.length > 0 && <><h3 className="dream-label">وبحسب حالك</h3>{s.mine.map((m, j) => <p dir="rtl" className="deep-verdict" key={j}><Rich text={m} words={NONE} /></p>)}</>}
                </article>
              ))}
              {res.found === 0 && <article className="verse-card deep-card"><p dir="rtl" className="deep-open">{res.opening}</p></article>}
              {res.rules.length > 0 && (
                <article className="verse-card deep-card">
                  <h3 className="rule-title">وعلى ماذا بُني هذا التأويل</h3>
                  {res.rules.map((r, i) => <div key={i}><h3 className="dream-label">{r.title}</h3><p dir="rtl" className="bio-line"><Rich text={r.text} words={NONE} /></p></div>)}
                </article>
              )}
              <p dir="rtl" className="deep-close">{res.closing}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
