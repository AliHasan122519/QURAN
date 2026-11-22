"""Checks the lists added with «مجمع الأمثال», «أحاديث الرؤيا» and «مقارنة المعبِّرين» against their sources (the check does not trust the builders):
 1) every proverb and every explanation of «مجمع الأمثال» (4756) and «جمهرة الأمثال» (1966) added to «الأمثال» is a contiguous run of the letters of the digital text of the book;
 2) every hadith of «أحاديث الرؤيا» is a contiguous run of the letters of Sahih al-Bukhari / Sahih Muslim, and the counts are 66 + 40;
 3) every passage of «مقارنة المعبِّرين» is, word for word, an entry of the «الكتب» tab of the book named under it, and every symbol has at least two books.
usage: OITI=/home/user/openiti python3 -I tests/new_lists_check.py"""
import json, re, os, sys
OITI = os.environ.get('OITI', '/home/user/openiti')
L = re.compile('[ء-ي]')
def letters(s): return ''.join(L.findall(s))
def stream(path):
    raw = open(path, encoding='utf8').read(); raw = raw[raw.index('Header#End') + 10:] if 'Header#End' in raw else raw
    raw = raw.replace('@MATN@', ' '); raw = re.sub(r'\bms\d+\b', ' ', raw); raw = re.sub(r'\[\s*ص\s*:?\s*\d+\s*\]', ' ', raw); return letters(raw)       # the copy's «msNNN» marks and the editor's page numbers
bad = []
# 1) Majma' al-Amthal
S = stream(f'{OITI}/0525AH/data/0518IbnMuhammadMaydaniNaysaburi/0518IbnMuhammadMaydaniNaysaburi.MajmacAmthal/0518IbnMuhammadMaydaniNaysaburi.MajmacAmthal.Shamela0012929-ara1')
am = json.load(open('content/amthal.json', encoding='utf8'))['h']; M = json.load(open('data/amthal/majma_parsed.json', encoding='utf8'))
J = json.load(open('data/amthal/jamhara_parsed.json', encoding='utf8')); SJ = stream(f'{OITI}/0400AH/data/0395AbuHilalCaskari/0395AbuHilalCaskari.JamharatAmthal/0395AbuHilalCaskari.JamharatAmthal.Shamela0006897-ara1.completed')
tail = am[len(am) - len(M) - len(J):]
if len(M) != 4756 or len(J) != 1966: bad.append(f'proverb counts {len(M)} / {len(J)}')
for (ch, pr, ex), e, S_ in [(a, b, S) for a, b in zip(tail[:len(M)], M)] + [(a, b, SJ) for a, b in zip(tail[len(M):], J)]:
    if (ch, pr, ex) != (e['chapter'], e['proverb'], e['explanation']): bad.append(f'amthal row differs from parsed: {pr[:30]}'); continue
    for t in (pr, ex):
        lt = letters(re.sub(r'﴿|﴾', '', t))
        if lt and lt not in S_: bad.append(f'proverb NOT in source: {t[:60]}')
print('proverbs checked:', len(M), '+', len(J))
# 2) the hadith of dreams
rh = json.load(open('content/ruyahadith.json', encoding='utf8'))['h']
SRC = {'صحيح البخاري': f'{OITI}/0275AH/data/0256Bukhari/0256Bukhari.Sahih/0256Bukhari.Sahih.Shamela0001681-ara1', 'صحيح مسلم': f'{OITI}/0275AH/data/0261Muslim/0261Muslim.Sahih/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown',
       'سنن الترمذي': f'{OITI}/0300AH/data/0279Tirmidhi/0279Tirmidhi.Sunan/0279Tirmidhi.Sunan.Shamela0001435-ara1', 'سنن ابن ماجه': f'{OITI}/0275AH/data/0273IbnMaja/0273IbnMaja.Sunan/0273IbnMaja.Sunan.Shamela0001198-ara1',
       'موطأ مالك': f'{OITI}/0200AH/data/0179MalikIbnAnas/0179MalikIbnAnas.Muwatta/0179MalikIbnAnas.Muwatta.Shamela0001699-ara1.completed'}
STREAMS = {k: stream(v).replace('', '') for k, v in SRC.items()}
import collections
cnt = collections.Counter(r[4] for r in rh)
if dict(cnt) != {'صحيح البخاري': 66, 'صحيح مسلم': 40, 'سنن الترمذي': 25, 'سنن ابن ماجه': 34, 'موطأ مالك': 5}: bad.append(f'hadith counts {dict(cnt)}')
for r in rh:
    t, src = r[1].split('\t'); lt = letters(re.sub(r'﴿|﴾', '', t)); st = STREAMS[r[4]]
    if lt not in st: bad.append(f'hadith NOT in source: {t[:60]}')
    if r[4] not in src: bad.append(f'book not named: {src}')
print('hadith checked:', len(rh))
# 3) the comparison
B = json.load(open('content/books.json', encoding='utf8'))['h']; byb = {}
for r in B: byb.setdefault(r[3], set()).add(r[1])
cm = json.load(open('content/muqaranat.json', encoding='utf8'))['h']; n = 0
for sym, text, *_ in cm:
    books = set()
    for line in text.split('\n'):
        t, b = line.split('\t'); books.add(b); n += 1
        if t not in byb.get(b, ()): bad.append(f'compare passage not an entry of {b}: {t[:50]}')
    if len(books) < 2: bad.append(f'symbol with one book: {sym}')
print('symbols:', len(cm), 'passages:', n)
if bad: print('\n'.join(bad[:30])); sys.exit(1)
print('OK')
