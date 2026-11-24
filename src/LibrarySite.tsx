import { useCallback, useEffect, useRef, useState } from 'react';
import { LibraryBig, Eye, Sparkles, ChevronLeft } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { ThemeToggle } from './components/ThemeToggle';
import { MenuButton, Drawer } from './components/Drawer';
import { LibraryPanel } from './components/LibraryPanel';
import { loadContent, loadTab, loadContentFile, type Content } from './lib/data';
import type { Doc } from './lib/types';

/** The standalone site of the library: the design of the app, with only the two lists of books of its side menu («المزيد»): «كتب علم التعبير» and «كتب الفراسة والشخصيات».
 *  Each list opens as its own panel (cover, search by name, the page of every book: contents, reading inside the page, the scanned pages, download). It reads its own content/ folder (build_library_site.mjs keeps only these two lists). */
const ICON: Record<string, LucideIcon> = { kutubtabir: LibraryBig, kutubfiras: Eye };
const ABOUT: Record<string, string> = {
  kutubtabir: 'أمهات كتب تأويل الرؤى، قديمها وحديثها',
  kutubfiras: 'معرفة الطباع وأنماط الشخصيات من الظاهر والسلوك',
};

export function LibrarySite() {
  const content = useRef<Content | null>(null);
  const [tabs, setTabs] = useState<{ id: string; label: string }[]>([]);
  const [lists, setLists] = useState<Record<string, Doc[]>>({});
  const [menu, setMenu] = useState(false); const [panel, setPanel] = useState<string | null>(null); const [failed, setFailed] = useState(false);
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const c = await loadContent(); content.current = c;
        const ts = c.manifest.tabs.filter((t) => t.card === 'library'); if (dead) return;
        setTabs(ts.map((t) => ({ id: t.id, label: t.label })));
        for (const t of ts) { const docs = await loadTab(t, c); if (dead) return; if (docs) setLists((p) => ({ ...p, [t.id]: docs })); }
      } catch { if (!dead) setFailed(true); }
    })();
    return () => { dead = true; };
  }, []);
  const load = useCallback((rel: string) => loadContentFile(content.current, rel), []);
  const close = useCallback(() => setPanel(null), []);
  const opened = tabs.find((t) => t.id === panel);
  return (
    <main className="page">
      <ThemeToggle />
      <MenuButton open={menu} onClick={() => setMenu(true)} />
      <Drawer open={menu} items={tabs} onPick={(id) => { setMenu(false); setPanel(id); }} onClose={() => setMenu(false)} />
      {opened && <LibraryPanel title={opened.label} docs={lists[opened.id] ?? []} load={load} onClose={close} />}
      <header className="hero">
        <div className="hero-in">
          <div className="badge-top"><Sparkles size={14} />مكتبة رقمية</div>
          <h1>مكتبة التعبير والفراسة</h1>
          <p>مختاراتٌ من كتب تعبير الرؤيا، وعلم الفراسة وأنماط الشخصيات والطباع، تُقرأ في الموقع أو تُحمَّل.</p>
          <div className="ornament-divider" />
        </div>
      </header>
      <section className="sheet">
        {failed && <p className="drawer-empty">تعذّر تحميل قائمة الكتب. أعد تحميل الصفحة.</p>}
        {!failed && !tabs.length && <p className="drawer-empty" role="status">جارٍ تحميل الكتب…</p>}
        <nav className="site-lists" aria-label="قوائم الكتب">
          {tabs.map((t) => { const Icon = ICON[t.id] ?? LibraryBig; const n = lists[t.id]?.length; return (
            <button type="button" key={t.id} className="site-list" onClick={() => setPanel(t.id)}>
              <span className="site-list-ic" aria-hidden="true"><Icon size={26} strokeWidth={1.8} /></span>
              <span className="site-list-tx"><strong>{t.label}</strong><span>{ABOUT[t.id] ?? ''}</span></span>
              <span className="site-list-n">{n !== undefined ? <><b>{n}</b> كتاباً</> : '…'}</span>
              <ChevronLeft className="site-list-go" size={22} aria-hidden="true" />
            </button>
          ); })}
        </nav>
      </section>
      <footer className="foot"><p>روابط التحميل وصور الصفحات من أرشيف الإنترنت، والكتب لأصحابها وناشريها.</p></footer>
    </main>
  );
}
