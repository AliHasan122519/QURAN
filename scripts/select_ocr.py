"""Choose, for every page, the best of three OCR readings of the supplied PDF:
   data/ocr_500   : Tesseract 5.3, Ubuntu 'ara' model, page rendered at 500 dpi   (native scan is 300 ppi 1-bit; upsampling helps Tesseract)
   data/ocr_best  : Tesseract 5.3, tessdata_best 'ara' (12.6 MB), 300 dpi
   data/ocr       : Tesseract 5.3, Ubuntu 'ara' model, 300 dpi
Rule: the 500dpi reading is the primary one (best word accuracy on the hand-checked sample, see scripts/ocr_sample_check.py, and highest mean
dictionary coverage); another reading replaces it on a page only when its dictionary coverage is higher by more than 0.03.
Dictionary coverage = share of Arabic words (normalised, >=2 letters) found in a reference word list (data/raw/_vocab.json, 49k words taken from Qur'anic
and hadith corpora, used ONLY as a spell-check dictionary). Higher share = fewer mis-read words.
The choice is recorded per page in data/ocr_selection.json (nothing is hidden).   usage: python3 -I scripts/select_ocr.py"""
import re, json, os, collections
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‎‏]')
def norm(s):
    s = DIAC.sub('', s); s = re.sub('[إأآٱ]', 'ا', s).replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي').replace('ة', 'ه'); return s
vocab = set(json.load(open('data/raw/_vocab.json', encoding='utf8')))
def cov(t):
    toks = re.findall('[ء-ي]{2,}', norm(t)); return ((sum(1 for x in toks if x in vocab) / len(toks)) if toks else 0.0), len(toks)
ENGINES = [('ocr500', 'data/ocr_500'), ('best', 'data/ocr_best'), ('fast', 'data/ocr')]    # tie priority order
os.makedirs('data/ocr_selected', exist_ok=True); sel = {}; cnt = collections.Counter()
for p in range(1, 593):
    n = f'{p:04d}.txt'; cands = []
    for name, d in ENGINES:
        f = f'{d}/{n}'; t = open(f, encoding='utf8').read() if os.path.exists(f) else ''
        c, w = cov(t) if t.strip() else (-1, 0); cands.append((c, name, t, w))
    c500 = next(c for c in cands if c[1] == 'ocr500'); best = c500
    for c in cands:
        if c[0] > c500[0] + 0.03 or (c500[0] < 0 and c[0] > best[0]): best = c
    open(f'data/ocr_selected/{n}', 'w', encoding='utf8').write(best[2])
    sel[p] = {'engine': best[1], **{f'cov_{c[1]}': round(c[0], 3) for c in cands}}; cnt[best[1]] += 1
json.dump(sel, open('data/ocr_selection.json', 'w'), ensure_ascii=False, indent=0)
m = lambda k: sum(max(v[k], 0) for v in sel.values()) / len(sel)
print('pages by engine:', dict(cnt), '| mean dictionary coverage:', {k: round(m('cov_' + k), 3) for k, _ in ENGINES}, 'selected:', round(sum(max(v['cov_ocr500'], v['cov_best'], v['cov_fast']) for v in sel.values()) / len(sel), 3))
