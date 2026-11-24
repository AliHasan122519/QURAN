import { useEffect, useRef } from 'react';
import { Menu, X, MoonStar, CloudMoon, Sparkles, BookUser, Scale, GitCompareArrows, ScrollText, Info, ChevronLeft, LibraryBig, Eye } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** a small icon that says what each button of the side menu is (a dream, the prophets and the righteous, the interpreters); a new list falls back to the moon */
const ICONS: Record<string, LucideIcon> = { ruaa: CloudMoon, anbiya: Sparkles, muabbirun: BookUser, qawaid: Scale, muqaranat: GitCompareArrows, ruyahadith: ScrollText, kutubtabir: LibraryBig, kutubfiras: Eye, about: Info };

export interface DrawerItem { id: string; label: string; }

/** Button fixed at the top (the side opposite the theme button): opens the side menu. */
export function MenuButton({ open, onClick }: { open: boolean; onClick: () => void }) {
  return (
    <button type="button" className="menu-toggle" aria-label="المزيد" title="المزيد" aria-haspopup="dialog" aria-expanded={open} onClick={onClick}>
      <Menu size={22} aria-hidden="true" />
    </button>
  );
}

/** The side menu: slides in from the side, lists what the content update adds there (today: «رؤى عبّرت»). Closes with Escape, with the × or by touching outside. */
export function Drawer({ open, items, onPick, onClose }: { open: boolean; items: DrawerItem[]; onPick: (id: string) => void; onClose: () => void }) {
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    close.current?.focus();
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="drawer-back" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="المزيد" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <h2>المزيد</h2>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <nav className="drawer-list" aria-label="أقسام المزيد">
          {items.map((it) => (
            <button type="button" key={it.id} className="drawer-item" onClick={() => onPick(it.id)}>
              <span className="drawer-ic" aria-hidden="true">{(() => { const Ic = ICONS[it.id] ?? MoonStar; return <Ic size={20} strokeWidth={1.9} />; })()}</span>
              <span className="drawer-label">{it.label}</span>
              <ChevronLeft className="drawer-go" size={20} aria-hidden="true" />
            </button>
          ))}
          {!items.length && <p className="drawer-empty">لا توجد أقسام الآن.</p>}
        </nav>
      </aside>
    </div>
  );
}
