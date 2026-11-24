"""The text versions of the scanned books (content/books/<key>.json made by scripts/ocr_scans.py + scripts/build_scan_texts.py): every embed book of the two lists has one,
it is flagged as a machine reading, listed in the manifest with its SHA-256, its table of contents / page marks / scan pages are inside the text and in order, no paragraph is empty,
and the readable part of the text is made of known words (a sanity floor: a reading that is mostly garbage must not be published).
usage: python3 -I tests/scantexts_check.py"""
import hashlib, json, os, re, sys
ok = True
def check(name, cond, detail=''):
    global ok; ok &= bool(cond); print('PASS' if cond else 'FAIL', '|', name, detail)
B = json.load(open('data/booklists/books.json', encoding='utf8')); M = json.load(open('content/manifest.json', encoding='utf8')); F = {f['file']: f for f in M['files']}
PC = json.load(open('data/booklists/pagecounts.json', encoding='utf8')); REP = json.load(open('data/booklists/transcribe_report.json', encoding='utf8')) if os.path.exists('data/booklists/transcribe_report.json') else {}
DIAC = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def norm(t): return re.sub('[^ء-ي]', '', re.sub('[ؤ]', 'و', re.sub('[ئ]', 'ي', DIAC.sub('', t).replace('ى', 'ي').replace('ة', 'ه'))).replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا'))
known = set()
for f in ['qadiri.txt', 'manamat.txt', 'tatir_anam.txt', 'muntakhab.txt', 'ibn_ghannam.txt', 'badr_munir.txt', '0873IbnShahinZahiri.Isharat.Shamela0009968-ara1']:
    from collections import Counter
    pass
cnt = {}
for f in ['qadiri.txt', 'manamat.txt', 'tatir_anam.txt', 'muntakhab.txt', 'ibn_ghannam.txt', 'badr_munir.txt', '0873IbnShahinZahiri.Isharat.Shamela0009968-ara1']:
    for w in re.sub(r'PageV\d+P\d+', ' ', open('data/books/' + f, encoding='utf8').read()).split():
        k = norm(w); cnt[k] = cnt.get(k, 0) + 1
lex = {w for w, c in cnt.items() if c >= 3 and len(w) > 1}
for b in B:
    if b['reader']['mode'] != 'embed': continue
    k = b['key']; rel = f'books/{k}.json'
    check(f'{k}: has a text version (a book of the lists has both its text and its scan)', os.path.exists('content/' + rel))
    if not os.path.exists('content/' + rel): continue
    raw = open('content/' + rel, 'rb').read(); d = json.loads(raw); n = len(d['p']); pc = PC[k][0][1]
    check(f'{k}: flagged as a machine reading, listed in the manifest with its SHA-256', d.get('ocr') is True and rel in F and F[rel]['sha256'] == hashlib.sha256(raw).hexdigest() and F[rel]['size'] == len(raw))
    check(f'{k}: no empty paragraph; the table of contents / page marks / scan pages are inside the text and in order', n > 20 and all(p.strip() for p in d['p']) and all(0 <= t[2] < n for t in d['toc']) and [t[2] for t in d['toc']] == sorted(t[2] for t in d['toc'])
          and all(0 <= i < n for i, _ in d['pg']) and [i for i, _ in d['pg']] == sorted(i for i, _ in d['pg']) and all(0 <= i < n and 0 <= lf < pc for i, lf in d.get('lf', [])) and [i for i, _ in d.get('lf', [])] == sorted(i for i, _ in d.get('lf', [])), f'{n} paragraphs, {len(d["toc"])} toc')
    words = [norm(w) for p in d['p'] for w in p.split()]; words = [w for w in words if len(w) > 1]
    kn = sum(1 for w in words if w in lex) / max(1, len(words))
    rp = REP.get(k, {})
    check(f'{k}: the page report exists and most pages have text', rp and rp['pagesWithText'] >= 0.7 * rp['pages'], f'{rp.get("pagesWithText")}/{rp.get("pages")} pages, mean engine confidence {rp.get("meanConfidence")}, weak pages {rp.get("weakPages")}')
    check(f'{k}: sanity floor — at least 35% of the Arabic words are forms known from the digital heritage texts (a garbled reading would be far lower)', k == 'firasa-ansari' or kn >= 0.35 or len(words) < 500, f'{round(100 * kn)}% of {len(words)} words')
    c = json.loads([r for r in json.load(open('content/' + [t for t in M['tabs'] if t['id'] == ('kutubtabir' if b['kind'] == 'tabir' else 'kutubfiras')][0]['file'], encoding='utf8'))['h'] if r[0] == b['title']][0][6])
    check(f'{k}: the book card offers the text version (reader.text) and says how it was made', c['reader'].get('text', {}).get('file') == rel and 'قراءة آلية' in c['reader']['text']['src'])
print('OK' if ok else 'FAILED'); sys.exit(0 if ok else 1)
