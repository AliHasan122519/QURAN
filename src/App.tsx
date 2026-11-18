import { useEffect, useRef, useState } from 'react';
import { Sparkles, Download } from 'lucide-react';
import { ICONS } from './components/icons';
import { ThemeToggle } from './components/ThemeToggle';
import { Engine } from './lib/engine';
import { loadContent, loadTab, checkForUpdate, type Content } from './lib/data';
import type { Kind, Manifest, SourceId } from './lib/types';
import { SearchPanel, type SourceState } from './components/SearchPanel';

export function App() {
  const [engine, setEngine] = useState(() => new Engine());
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [tab, setTab] = useState<SourceId>('quran');
  const [states, setStates] = useState<Record<SourceId, SourceState>>({});
  const [attempt, setAttempt] = useState(0);
  const [apkNotice, setApkNotice] = useState<Manifest['apk']>();
  const content = useRef<Content | null>(null);

  // 1) load the content in use (bundled, or a newer downloaded one) and index every tab
  useEffect(() => {
    let dead = false;
    const eng = engine;
    (async () => {
      let c: Content;
      try { c = await loadContent(); } catch { if (!dead) setStates({ quran: 'error' }); return; }
      if (dead) return;
      content.current = c; setManifest(c.manifest);
      setStates(Object.fromEntries(c.manifest.tabs.map((t) => [t.id, 'loading' as SourceState])));
      setTab((cur) => (c.manifest.tabs.some((t) => t.id === cur) ? cur : c.manifest.tabs[0]?.id ?? cur));
      for (const t of c.manifest.tabs) {
        const set = (s: SourceState) => !dead && setStates((p) => ({ ...p, [t.id]: s }));
        try {
          const docs = await loadTab(t, c);
          if (dead) return;
          if (!docs) { set('absent'); continue; }
          await eng.addSource(t.id, docs, t.kind); await eng.finalize(); set('ready');
        } catch { set('error'); }
      }
      if (dead) return;
      // 2) in the background: look for newer content (only in builds that have a content URL, i.e. the Android app)
      const r = await checkForUpdate(c.manifest);
      if (dead) return;
      if (r.apkNotice) setApkNotice(r.apkNotice);
      if (r.status === 'updated') { setEngine(new Engine()); setAttempt((a) => a + 1); }          // re-index with the new content
    })();
    return () => { dead = true; };
  }, [engine, attempt]);

  const tabs = manifest?.tabs ?? [{ id: 'quran', label: 'القرآن الكريم', kind: 'quran' as Kind, file: null, sha256: null }];
  return (
    <main className="page">
      <ThemeToggle />
      <header className="hero">
        <div className="hero-in">
          <div className="badge-top"><Sparkles size={14} />بحث نصّي دقيق مع توسعة دلالية اشتقاقية</div>
          <h1>الباحث القرآني</h1>
          <p>منصّة بحث شرعي في القرآن الكريم والسنة النبوية الصحيحة، تبدأ من اللفظ المطابق ثم تتوسّع إلى الجذر اللغوي والألفاظ القريبة دون أي تفسير شخصي.</p>
          <div className="ornament-divider" />
        </div>
      </header>

      {apkNotice && <a className="apk-notice" href={apkNotice.url} target="_blank" rel="noreferrer"><Download size={16} />يتوفر إصدار جديد من التطبيق{apkNotice.notes ? ` — ${apkNotice.notes}` : ''}. اضغط للتنزيل.</a>}

      <section className="sheet">
        <div className="tabs" role="tablist" aria-label="مصادر البحث">
          {tabs.map(({ id, label, kind }) => { const Icon = ICONS[kind]; return (
            <button key={id} role="tab" id={`tab-${id}`} aria-selected={tab === id} aria-controls={`panel-${id}`} data-state={tab === id ? 'active' : 'inactive'} className="tab" onClick={() => setTab(id)}>
              <Icon size={16} />{label}
            </button>
          ); })}
        </div>
        {tabs.map((t) => (
          <div key={t.id} role="tabpanel" id={`panel-${t.id}`} aria-labelledby={`tab-${t.id}`} hidden={tab !== t.id}>
            <SearchPanel tab={t} engine={engine} state={states[t.id] ?? 'loading'} retry={() => { setEngine(new Engine()); setAttempt((a) => a + 1); }} />
          </div>
        ))}
      </section>

      <footer className="foot">
        <p>منصّة بحث في القرآن الكريم والسنة النبوية. لا يُعرض أي تفسير أو رأي شخصي.</p>
      </footer>
    </main>
  );
}
