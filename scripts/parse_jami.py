"""Parse Tesseract OCR pages of al-Jami' al-Saghir into entries.
Every entry keeps its PDF page. Numbers are OCR-read; when the OCR number breaks the running sequence it is
replaced by the sequence-expected number and flagged 'inferred' (never presented as verified).
usage: python3 -I parse_jami.py OCR_DIR VOCAB_JSON OUT_JSON"""
import re, sys, json, glob, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ocr_dir, vocab_path, out = sys.argv[1:4]
skip = set(int(x) for x in open(sys.argv[4]).read().split()) if len(sys.argv) > 4 else set()   # pages already verified by hand
AR = r'ء-ي'
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‎‏]')
def norm(s):
    s = DIAC.sub('', s)
    s = re.sub('[إأآٱ]', 'ا', s).replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه')
    return s
ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
vocab = set(json.load(open(vocab_path)))
# key of symbols: transcribed from printed pp. 5-6 of the supplied PDF (checked against page images)
SYMBOLS = {
 'خد':'البخاري في الأدب','تخ':'البخاري في التاريخ','حب':'ابن حبان في صحيحه','خ':'البخاري','م':'مسلم','ق':'متفق عليه (البخاري ومسلم)',
 'د':'أبو داود','ت':'الترمذي','ن':'النسائي','ه':'ابن ماجه','4':'أبو داود والنسائي والترمذي وابن ماجه','3':'أبو داود والنسائي والترمذي',
 'حم':'أحمد في مسنده','عم':'عبد الله بن أحمد في زوائده','ك':'الحاكم (المستدرك)','طب':'الطبراني في الكبير','طس':'الطبراني في الأوسط',
 'طص':'الطبراني في الصغير','ص':'سعيد بن منصور في سننه','ش':'ابن أبي شيبة','عب':'عبد الرزاق في الجامع','ع':'أبو يعلى في مسنده',
 'قط':'الدارقطني','فر':'الديلمي في مسند الفردوس','حل':'أبو نعيم في الحلية','هب':'البيهقي في شعب الإيمان','هق':'البيهقي في السنن',
 'عد':'ابن عدي في الكامل','عق':'العقيلي في الضعفاء','خط':'الخطيب'}
GRADES = {'صح':'صحيح','ح':'حسن','ض':'ضعيف'}
SYM_FIX = {'هـ':'ه','ه':'ه','٤':'4','٣':'3'}

start_re = re.compile(r'^[\u200e\u200f\s]*([^\s()«»]{0,8}?)\s*[-–]\s+(?=[\u0600-\u06FF«(])')
close_re = re.compile(r'\(\s*(?:صح|ص ح|ضص|ض|ح)\s*\)\s*\.?\s*$')
paren_re = re.compile(r'\(\s*([^()]{1,24}?)\s*\)')
def digits_of(prefix):
    d = ''.join(ch for ch in prefix.translate(ARABIC_DIGITS) if ch.isdigit())
    return int(d) if d and len(d) <= 5 else None

entries, letter, mahla = [], '', False
cur = None
def flush():
    global cur
    if cur: entries.append(cur); cur = None
prefix_re = re.compile(r'^[\u200e\u200f\s]*([^\u0621-\u064A\s()«»]{1,14}?)\s*(?=[\u0621-\u064A«])')
for pf in sorted(glob.glob(ocr_dir + '/*.txt')):
    page = int(os.path.basename(pf)[:4])
    if page < 7 or page in skip: continue                       # pp.1-6: title, preface, symbol key (not hadith entries)
    prev_blank = True                           # first line of a page counts as a paragraph start
    for raw in open(pf, encoding='utf8').read().split('\n'):
        line = raw.strip()
        if not re.search('[' + AR + ']', line):
            prev_blank = True; continue          # blank or page-number-only line
        n = norm(line)
        m_h = re.match(r'^\s*حرف\s+(.{1,12})$', n)
        if m_h and len(line) < 30: flush(); letter = line.replace('\u200f','').strip(); mahla = False; prev_blank = True; continue
        if n.startswith('فصل في المحلي بال') or n.startswith('فصل في المحلى بال'): flush(); mahla = True; prev_blank = True; continue
        ms = start_re.match(line)
        mp = prefix_re.match(line) if prev_blank else None
        if ms or mp:
            m = ms or mp
            flush()
            cur = {'page': page, 'letter': letter, 'mahla': mahla, 'ocr_n': digits_of(m.group(1)), 'lines': [line[m.end():].strip()]}
        elif cur and cur.get('closed') and not re.match(r'^\s*\(', line):
            flush()   # previous entry ended with a grade marker, so this unnumbered line starts a new entry
            cur = {'page': page, 'letter': letter, 'mahla': mahla, 'ocr_n': None, 'lines': [line]}
        elif cur:
            cur['lines'].append(line)
        if cur and close_re.search(line): cur['closed'] = True
        prev_blank = False
flush()
# ---------- text split + symbols + grade + quality ----------
import jami_decode as J
def decode(entry):
    text = ' '.join(entry['lines']).replace('\u200f', '').replace('\u200e', '')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^[^\s]{0,6}\s*[-–]\s+', '', text)   # leftover OCR number prefix
    matn, takhrij, syms, grade = J.decode_text(text)
    return text, matn, takhrij, syms, grade
quality = lambda toks: sum(1 for t in toks if t in vocab) / max(1, len(toks))
out_rows, prev = [], 0
for i, e in enumerate(entries):
    text, matn, takhrij, syms, grade = decode(e)
    toks = [t for t in re.findall('[' + AR + ']{2,}', norm(matn))]
    cov = quality(toks)
    flags = []
    if cov < 0.75: flags.append('low_vocab_coverage')
    if re.search(r'[A-Za-z]', matn): flags.append('latin_noise')
    if len(matn) < 12: flags.append('very_short')
    if not takhrij: flags.append('no_takhrij_detected')
    out_rows.append({'i': i, 'page': e['page'], 'letter': e['letter'], 'mahla': e['mahla'], 'ocr_n': e['ocr_n'],
                     't': matn, 'k': takhrij, 'sym': syms, 'g': grade, 'cov': round(cov, 2), 'flags': flags})
# ---------- sequence reconstruction of numbers ----------
exp, ok_cnt, inf_cnt = 1, 0, 0
SEQ=False
for i, r in enumerate(out_rows):
    n = r['ocr_n']; nxt = out_rows[i+1]['ocr_n'] if i + 1 < len(out_rows) else None
    if n == exp: r['n'], r['n_status'] = exp, 'ocr_sequence_ok'; ok_cnt += 1
    elif n and n > exp and n - exp <= 3 and nxt == n + 1: exp = n; r['n'], r['n_status'] = n, 'ocr_resync'; ok_cnt += 1
    else: r['n'], r['n_status'] = exp, 'inferred'; inf_cnt += 1
    exp = r['n'] + 1
json.dump(out_rows, open(out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('entries', len(out_rows), 'seq-ok', ok_cnt, 'inferred', inf_cnt, 'last n', out_rows[-1]['n'])
print('flag counts', collections.Counter(f for r in out_rows for f in r['flags']))
print('with symbols', sum(1 for r in out_rows if r['sym']), 'with grade', sum(1 for r in out_rows if r['g']))
print('letters', collections.Counter(r['letter'] for r in out_rows).most_common(40))
