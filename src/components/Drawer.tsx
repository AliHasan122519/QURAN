import { useEffect, useRef } from 'react';
import { Menu, X, MoonStar } from 'lucide-react';
import { toAr } from '../lib/format';

export interface DrawerItem { id: string; label: string; count?: number; }

/** Button fixed at the top (the side opposite the theme button): opens the side menu. */
export function MenuButton({ open, onClick }: { open: boolean; onClick: () => void }) {
  return (
    <button type="button" className="menu-toggle" aria-label="فتح القائمة" title="القائمة" aria-haspopup="dialog" aria-expanded={open} onClick={onClick}>
      <Menu size={22} aria-hidden="true" />
    </button>
  );
}

/** The side menu: slides in from the side, lists what the content update adds there (today: «رؤى وتعبيرها»). Closes with Escape, with the × or by touching outside. */
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
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="القائمة" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <h2>القائمة</h2>
          <button type="button" ref={close} className="drawer-x" aria-label="إغلاق القائمة" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>
        <nav className="drawer-list" aria-label="أقسام القائمة">
          {items.map((it) => (
            <button type="button" key={it.id} className="drawer-item" onClick={() => onPick(it.id)}>
              <MoonStar size={20} aria-hidden="true" />
              <span className="drawer-label">{it.label}</span>
              {it.count ? <span className="drawer-count">{toAr(it.count)}</span> : null}
            </button>
          ))}
          {!items.length && <p className="drawer-empty">لا توجد أقسام الآن.</p>}
        </nav>
      </aside>
    </div>
  );
}
