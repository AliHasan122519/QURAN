import { useCallback, useEffect, useRef, useState } from 'react';
import { LibraryBig, Eye, Sparkles } from 'lucide-react';
import { ThemeToggle } from './components/ThemeToggle';
import { LibraryView } from './components/LibraryPanel';
import { loadContent, loadTab, loadContentFile, type Content } from './lib/data';
import type { Doc } from './lib/types';

/** The standalone site of the library: only the two lists of books («كتب علم التعبير» and «كتب الفراسة والشخصيات»), with the design of the app and the same pages of the books
 *  (cover, contents, reading inside the page, reading of the scanned pages, download). It reads its own content/ folder (build_library_site.mjs keeps only these two lists). */
const ICON: Record<string, typeof LibraryBig> = { kutubtabir: LibraryBig, kutubfiras: Eye };

export function LibrarySite() {
  const content = useRef<Content | null>(null);
  const [tabs, setTabs] = useState<{ id: string; label: string }[]>([]);
  const [lists, setLists] = useState<Record<string, Doc[]>>({});
  const [tab, setTab] = useState('kutubtabir'); const [failed, setFailed] = useState(false);
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const c = await loadContent(); content.current = c;
        const ts = c.manifest.tabs.filter((t) => t.card === 'library'); if (dead) return;
        setTabs(ts.map((t) => ({ id: t.id, label: t.label }))); setTab((cur) => (ts.some((t) => t.id === cur) ? cur : ts[0]?.id ?? cur));
        for (const t of ts) { const docs = await loadTab(t, c); if (dead) return; if (docs) setLists((p) => ({ ...p, [t.id]: docs })); }
      } catch { if (!dead) setFailed(true); }
    })();
    return () => { dead = true; };
  }, []);
  const load = useCallback((rel: string) => loadContentFile(content.current, rel), []);
  return (
    <main className="page">
      <ThemeToggle />
      <header className="hero">
        <div className="hero-in">
          <div className="badge-top"><Sparkles size={14} />للقراءة داخل الموقع والتحميل</div>
          <h1>مكتبة التعبير والفراسة</h1>
          <p>كتب علم تعبير الرؤيا، وكتب الفراسة وأنماط الشخصيات وطباعها وصفاتها وأساليبها: اقرأ الكتاب داخل الموقع، أو من صور صفحاته، أو حمِّله.</p>
          <div className="ornament-divider" />
        </div>
      </header>
      <section className="sheet">
        <div className="tabs" role="tablist" aria-label="قوائم الكتب">
          {tabs.map(({ id, label }) => { const Icon = ICON[id] ?? LibraryBig; return (
            <button key={id} role="tab" id={`tab-${id}`} aria-selected={tab === id} aria-controls={`panel-${id}`} data-state={tab === id ? 'active' : 'inactive'} className="tab" onClick={() => setTab(id)}>
              <Icon size={16} />{label}
            </button>
          ); })}
        </div>
        {failed && <p className="drawer-empty">تعذّر تحميل قائمة الكتب. أعد تحميل الصفحة.</p>}
        {!failed && !tabs.length && <p className="drawer-empty" role="status">جارٍ تحميل الكتب…</p>}
        {tabs.map((t) => (
          <div key={t.id} role="tabpanel" id={`panel-${t.id}`} aria-labelledby={`tab-${t.id}`} hidden={tab !== t.id} className="lib-site-panel">
            {lists[t.id] ? <LibraryView docs={lists[t.id]} load={load} /> : <p className="drawer-empty" role="status">جارٍ تحميل الكتب…</p>}
          </div>
        ))}
      </section>
      <footer className="foot"><p>روابط التحميل وصور الصفحات من أرشيف الإنترنت. الكتب لأصحابها وناشريها.</p></footer>
    </main>
  );
}
