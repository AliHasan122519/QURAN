"""Checks the list «قواعد علم التعبير» (content/qawaid.json) against the books it is copied from — the check does NOT trust data/qawaid/excerpts.json or the extractor:
 1) every passage, taken as a stream of Arabic letters, is a contiguous run of the letters of its book's digital text (the plain misprints listed in data/qawaid/typos.json mended in the book's stream,
    the editor's doubtful-reading notes «[…؟؟]» left out, as the extractor does); a Qur'anic phrase ﴿…﴾ is checked in the mushaf (content/quran.json) and its letters-skeleton in the book;
 2) the list is exactly what excerpts.json holds; every rule has a passage that states it; groups are the four known ones; no printing marks remain.
usage: python3 -I tests/qawaid_check.py"""
import json, re, sys
sys.path.insert(0, 'scripts')
L = re.compile('[ء-ي]')
def letters(s): return ''.join(L.findall(s))
MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۨ-ۭـ]')
def skel(s): return re.sub('[ٱأإآ]', 'ا', MARKS.sub('', s)).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي').replace('ا', '').replace('ي', '').replace(' ', '')
FILES = {'البدر المنير في علم التعبير': 'badr_munir.txt', 'منتخب الكلام في تفسير الأحلام': 'muntakhab.txt', 'تعطير الأنام في تعبير المنام': 'tatir_anam.txt',
         'الإشارات في علم العبارات': '0873IbnShahinZahiri.Isharat.Shamela0009968-ara1', 'تعبير الرؤيا (ابن غنام المقدسي)': 'ibn_ghannam.txt',
         'الإشارة إلى علم العبارة': 'isharah_salimi.txt', 'القادري في التعبير': 'qadiri.txt'}
KEY = {'badr': 'البدر المنير في علم التعبير', 'muntakhab': 'منتخب الكلام في تفسير الأحلام', 'tatir': 'تعطير الأنام في تعبير المنام', 'isharat': 'الإشارات في علم العبارات',
       'ghannam': 'تعبير الرؤيا (ابن غنام المقدسي)', 'salimi': 'الإشارة إلى علم العبارة', 'qadiri': 'القادري في التعبير'}
typos = json.load(open('data/qawaid/typos.json', encoding='utf8'))
STREAM = {}; SKEL = {}
for name, fn in FILES.items():
    raw = open('data/books/' + fn, encoding='utf8').read()
    raw = raw[raw.index('Header#End') + 10:] if 'Header#End' in raw else raw
    raw = re.sub(r'\[[^\]]*؟؟\s*\]', ' ', raw)                                  # the editor's doubtful-reading notes
    raw = re.sub(r'\[\s*ص\s*\d+\s*\]', ' ', raw)                               # page marks «[ ص 355 ]»
    raw = re.sub(r'@\s*\d+\s*/?\s*[أب]\s*@', ' ', raw); raw = re.sub(r'\[\s*\d+\s*/\s*[أب]\s*\]', ' ', raw)       # folio marks «@ 17 / أ @»
    st = letters(raw)
    for c in typos:
        if KEY[c['book']] != name: continue
        f, r = letters(c['find']), letters(c['replace'])
        st = re.sub(re.escape(f) + '(?!' + re.escape(r[len(f):]) + ')', r, st) if r.startswith(f) and len(r) > len(f) else st.replace(f, r)
    STREAM[name] = st; SKEL[name] = skel(st)
Q = json.load(open('content/quran.json', encoding='utf8'))
MUSHAF = ' '.join(t for _, _, t in Q['a']); MUSHAF_SK = skel(MUSHAF)
rows = json.load(open('content/qawaid.json', encoding='utf8'))['h']
ex = json.load(open('data/qawaid/excerpts.json', encoding='utf8'))
bad = []
GROUPS = {'أصول التأويل ووجوهه', 'ما يُغيّر التأويل: حال الرائي والمرئي', 'ضبط الرؤيا والتأويل', 'آداب المعبِّر وضوابطه'}
if len(rows) != len(ex): bad.append(f'rows {len(rows)} != excerpts {len(ex)}')
n = 0
for r, e in zip(rows, ex):
    ref, text, expl, source, by = r
    if ref != e['title'] or by != e['group']: bad.append(f'row/excerpt mismatch: {ref}')
    if by not in GROUPS: bad.append(f'unknown group: {by}')
    if not text.strip(): bad.append(f'no stating passage: {ref}')
    for field, kind in ((text, 'rule'), (expl, 'ex')):
        got = [ln.split('\t') for ln in field.split('\n') if ln]
        want = [(p['text'], p['book']) for p in e[kind]]
        if [(a, b) for a, b in got] != want: bad.append(f'content differs from excerpts: {ref} [{kind}]')
        for t, book in got:
            n += 1
            if book not in STREAM: bad.append(f'unknown book {book}'); continue
            if re.search(r'PageV|\bms\d|@Q|\^|\[؟؟|\d', t): bad.append(f'printing mark in: {ref}: {t[:50]}')
            if t.count('(') != t.count(')') or t.count('«') != t.count('»') or t.count('﴿') != t.count('﴾'): bad.append(f'unbalanced marks: {ref}: {t[:50]}')
            parts = re.split(r'﴿([^﴾]*)﴾', t)                                  # even = plain text, odd = a Qur'anic phrase
            for i, p in enumerate(parts):
                if i % 2 == 0:
                    lt = letters(p)
                    if lt and lt not in STREAM[book]: bad.append(f'NOT in {book}: {ref}: {p[:70]}')
                else:
                    sk = skel(p)
                    if sk not in MUSHAF_SK and sk not in SKEL[book]: bad.append(f'verse neither in mushaf nor book: {ref}: {p[:60]}')
                    if sk not in SKEL[book]: bad.append(f'verse not in {book}: {ref}: {p[:60]}')
print(len(rows), 'rules,', n, 'passages checked against the books')
if bad: print('\n'.join(bad[:40])); sys.exit(1)
print('OK')
