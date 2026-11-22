import { useEffect, useRef } from 'react';
import { X, BookOpen, ScrollText, Quote, Music4, Library, Feather, MoonStar, Scale, GitCompareArrows, ShieldCheck, RefreshCw, Sparkles } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { Doc, Tab } from '../lib/types';
import { toAr } from '../lib/format';
import { topmost } from './DreamsPanel';

/** the counters of the app: tab id -> [icon, what it counts] */
const STAT: Record<string, [LucideIcon, string]> = {
  quran: [BookOpen, 'آية'], jami: [ScrollText, 'حديث'], amthal: [Quote, 'مثل'], alfiya: [Music4, 'بيت من الألفية'], books: [Library, 'مدخل في كتب التعبير'], shawahid: [Feather, 'بيت استشهاد'],
  ruaa: [MoonStar, 'رؤيا مع تعبيرها'], qawaid: [Scale, 'قاعدة في علم التعبير'], muqaranat: [GitCompareArrows, 'رمز مقارَن بين الكتب'], ruyahadith: [ScrollText, 'حديث من أحاديث الرؤيا'] };

/** «حول التطبيق»: what the app is, what it holds (the counters come live from the content manifest), how it searches, and the privacy notice. The paragraphs are the rows of the list (content/about.json). */
export function AboutPanel({ title, docs, tabs, version, updated, onClose }: { title: string; docs: Doc[]; tabs: Tab[]; version?: number; updated?: string; onClose: () => void }) {
  const back = useRef<HTMLDivElement>(null); const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && topmost(back.current)) onClose(); };
    document.addEventListener('keydown', key); const prev = document.body.style.overflow; document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', key); document.body.style.overflow = prev; };
  }, [onClose]);
  const stats = tabs.filter((t) => STAT[t.id] && t.count);
  const date = updated ? new Date(updated).toLocaleDateString('en-GB', { year: 'numeric', month: '2-digit', day: '2-digit' }) : '';
  return (
    <div ref={back} className="panel-back" onClick={onClose}>
      <div className="panel about" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="panel-head">
          <div><h2>{title}</h2><p className="panel-sub">الباحث القرآني</p></div>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <div className="about-hero"><Sparkles size={26} aria-hidden="true" /><p>{docs[0]?.text}</p></div>
        <div className="stat-grid" role="list" aria-label="محتوى التطبيق">
          {stats.map((t, i) => { const [Ic, what] = STAT[t.id]; return (
            <div className="stat" role="listitem" key={t.id} style={{ animationDelay: `${i * 55}ms` }}>
              <Ic size={20} aria-hidden="true" /><b>{toAr(t.count ?? 0)}</b><span>{what}</span>
            </div>); })}
        </div>
        {docs.slice(1).map((d, i) => (
          <article className="verse-card about-card" key={d.id} style={{ animationDelay: `${(i + 4) * 70}ms` }}>
            <h3 className="about-title">{d.ref === 'الخصوصية' ? <ShieldCheck size={18} aria-hidden="true" /> : d.ref === 'التحديث' ? <RefreshCw size={18} aria-hidden="true" /> : null}{d.ref}</h3>
            {d.text.split('\n').map((l, j) => <p dir="rtl" className="bio-line" key={j}>{l}</p>)}
          </article>
        ))}
        {version ? <p className="about-ver">إصدار المحتوى {toAr(version)}{date ? ` · ${date}` : ''}</p> : null}
      </div>
    </div>
  );
}
