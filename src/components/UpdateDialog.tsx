import { useEffect, useRef, useState } from 'react';
import { Download, Loader2, RefreshCw } from 'lucide-react';
import { getInstaller } from '../lib/installer';
import { toAr } from '../lib/format';

type Phase = 'idle' | 'downloading' | 'installing' | 'needs_permission' | 'opened' | 'error';

/** Shown when the app opens and a newer version of the app exists: «تحديث الآن» downloads it inside the app and opens Android's installer. */
export function UpdateDialog({ apk, onClose }: { apk: { versionCode: number; url: string; notes?: string }; onClose: () => void }) {
  const [phase, setPhase] = useState<Phase>('idle'); const [pct, setPct] = useState(0);
  const primary = useRef<HTMLButtonElement>(null);
  useEffect(() => { primary.current?.focus(); const k = (e: KeyboardEvent) => { if (e.key === 'Escape' && phase !== 'downloading') onClose(); }; window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k); }, [phase, onClose]);
  const start = async () => {
    setPhase('downloading'); setPct(0);
    try { setPhase(await getInstaller().install(apk.url, setPct)); } catch { setPhase('error'); }
  };
  const busy = phase === 'downloading';
  return (
    <div className="modal-back" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="upd-title" aria-describedby="upd-desc">
        <div className="modal-ic" aria-hidden="true"><RefreshCw size={26} /></div>
        <h2 id="upd-title">يتوفر تحديث جديد</h2>
        <p id="upd-desc" className="modal-p">
          {phase === 'idle' && <>هناك إصدار أحدث من التطبيق{apk.notes ? ` — ${apk.notes}` : ''}. اضغط «تحديث الآن» لتنزيله وتثبيته فوق النسخة الحالية، وتبقى بياناتك كما هي.</>}
          {phase === 'downloading' && <>جارٍ تنزيل التحديث… {toAr(pct)}%</>}
          {phase === 'installing' && <>اكتمل التنزيل. اضغط «تثبيت» في النافذة التي ظهرت من النظام.</>}
          {phase === 'needs_permission' && <>اسمح للتطبيق بتثبيت التحديثات من الإعدادات التي فُتحت، ثم ارجع واضغط «تحديث الآن» مرة أخرى.</>}
          {phase === 'opened' && <>فُتح رابط التنزيل. بعد اكتمال التنزيل افتح الملف واضغط «تثبيت».</>}
          {phase === 'error' && <>تعذّر تنزيل التحديث الآن. تأكد من الإنترنت ثم حاول مرة أخرى.</>}
        </p>
        {busy && <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label="تقدّم التنزيل"><i style={{ width: `${pct}%` }} /></div>}
        <div className="modal-actions">
          <button ref={primary} type="button" className="go" onClick={start} disabled={busy}>
            {busy ? <><Loader2 size={16} className="spin" />جارٍ التنزيل…</> : <><Download size={16} />تحديث الآن</>}
          </button>
          <button type="button" className="later" onClick={onClose} disabled={busy}>لاحقاً</button>
        </div>
      </div>
    </div>
  );
}
