"""Merge the hand-verified pages (data/manual/pNNN.txt) with the OCR-parsed pages into data/raw/jami_parsed.json.
Manual file format, one entry per line:   N | text (symbols) takhrij      (N = hadith number printed in the book, Western digits)
                                           + | text                         (continuation of the entry cut by the previous page)
                                           # heading                        (ignored)
Pages that have a manual file REPLACE the OCR reading of that page entirely.  usage: python3 -I scripts/merge_manual.py"""
import json, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jami_decode as J
ocr = json.load(open('data/raw/jami_ocr_parsed.json', encoding='utf8'))
rows = []
for r in ocr:
    r = dict(r); r['n'] = r.get('n') or None; r['verified'] = False; rows.append(r)
manual_pages = sorted(int(re.search(r'p(\d+)', f).group(1)) for f in glob.glob('data/manual/p*.txt'))
man = []
for pg in manual_pages:
    for line in open(f'data/manual/p{pg:03d}.txt', encoding='utf8').read().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or '|' not in line: continue
        n, text = [x.strip() for x in line.split('|', 1)]
        if n == '+':
            if man and man[-1]['page'] in (pg, pg - 1): man[-1]['raw'] += ' ' + text; continue
            man.append({'page': pg, 'n': None, 'raw': text}); continue
        man.append({'page': pg, 'n': int(n), 'raw': text})
# an entry cut by the last hand-verified page continues at the top of the next (machine-read) page: join them
if man and manual_pages:
    nxt = [r for r in rows if r.get('top') and r['ocr_n'] is None and r['page'] == manual_pages[-1] + 1]
    if nxt and man[-1]['page'] == manual_pages[-1]:
        r = nxt[0]; man[-1]['raw'] += ' ' + (r['t'] + (' ' + r['k'] if r['k'] else '')).strip(); rows.remove(r)
for m in man:
    matn, k, sym, g = J.decode_text(m['raw'])
    rows.append({'i': 0, 'page': m['page'], 'letter': '', 'mahla': False, 'ocr_n': None, 't': matn, 'k': k, 'sym': sym, 'g': g, 'cov': 1.0, 'flags': [], 'n': m['n'], 'verified': True})
# order: by page, then OCR order / manual order (manual rows keep file order because sort is stable and they were appended per page in order)
rows.sort(key=lambda r: r['page'])
json.dump(rows, open('data/raw/jami_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
v = [r for r in rows if r['verified']]
nums = sorted(r['n'] for r in v if r['n'])
gaps = [(a, b) for a, b in zip(nums, nums[1:]) if b - a != 1]
print(f'manual pages: {len(manual_pages)}  verified entries: {len(v)}  OCR entries: {len(rows) - len(v)}  number gaps/dups inside verified: {gaps[:10]}')
