"""Copies, word for word, the passages in which the books of dream interpretation themselves state the RULES of interpretation
(the sources of ta'wil: the name, the derivation, the meaning, the saying, the poem, the opposite, the reversal …; and what changes the interpretation: the dreamer, his religion, his
craft, his language, the time …; and the manners of the interpreter) -> data/qawaid/excerpts.json  (read by scripts/build_qawaid.py).
Nothing is written by hand: every passage is the text of the book between a first-words anchor and a last-words anchor, both of which must be found (the script stops otherwise);
only the digital copy's printing marks are removed (page marks, footnote numbers, editorial «msNNN»), the Qur'anic phrases are given the mushaf's own words when they match it word for word,
and the plain misprints listed with their reason in data/qawaid/typos.json are mended.   usage: python3 -I scripts/extract_qawaid.py"""
import re, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
B = 'data/books/'
FILES = {'badr': 'badr_munir.txt', 'muntakhab': 'muntakhab.txt', 'tatir': 'tatir_anam.txt', 'isharat': '0873IbnShahinZahiri.Isharat.Shamela0009968-ara1',
         'ghannam': 'ibn_ghannam.txt', 'salimi': 'isharah_salimi.txt', 'qadiri': 'qadiri.txt'}
NAMES = {'badr': 'البدر المنير في علم التعبير', 'muntakhab': 'منتخب الكلام في تفسير الأحلام', 'tatir': 'تعطير الأنام في تعبير المنام', 'isharat': 'الإشارات في علم العبارات',
         'ghannam': 'تعبير الرؤيا (ابن غنام المقدسي)', 'salimi': 'الإشارة إلى علم العبارة', 'qadiri': 'القادري في التعبير'}

def clean(t):
    t = re.sub(r'!\[image filename\]\([^)]*\)', ' ', t)
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t)
    t = re.sub(r'\[\s*ص\s*\d+\s*\]', ' ', t); t = re.sub(r'@\s*\d+\s*/?\s*[أب]\s*@', ' ', t); t = re.sub(r'\[\s*\d+\s*/\s*[أب]\s*\]', ' ', t)
    t = t.replace('%~%', ' ').replace('٭', ' ')
    t = re.sub(r'@QB@\s*(.*?)\s*@QE@', r'﴿\1﴾', t)                                         # Qur'anic phrase of the digital copy
    t = re.sub(r'\^\s*\(\s*(.*?)\s*\)\s*\^', r'﴿\1﴾', t)                                    # «^ ( … ) ^»
    t = re.sub(r'\(\s*\^\s*([^()]*?)\s*\)', r'﴿\1﴾', t)                                     # «( ^ … )»
    t = t.replace('{', '﴿').replace('}', '﴾')
    t = re.sub(r'(?<=\s)\|(?=\s)', ' ', t); t = re.sub(r'(?<=\s)\.(?:\s\.)+(?=\s)', ' ', t)    # line marks of the digital copy
    t = re.sub(r'\[\s*\d+\s*\]\s*', ' ', t)                                                # paragraph numbers «[142]»
    t = re.sub(r'\[[^\]]*؟؟\s*\]', ' ', t)                                                # the editor's doubtful-reading notes «[…؟؟]»
    t = re.sub(r'\(\s*\d{1,3}\s*\)', ' ', t)                                              # footnote numbers «(3)»
    t = re.sub(r'(?<=\s)/(?=\s)', ' ', t)
    t = re.sub(r'\(\s+', '(', t); t = re.sub(r'\s+\)', ')', t); t = re.sub(r'\s+([،؛:.؟!])', r'\1', t)
    return re.sub(r'\s+', ' ', t).strip()
def body(key):
    L = open(B + FILES[key], encoding='utf8').read().split('\n')
    i = next((k for k, l in enumerate(L) if 'Header#End' in l), -1) + 1
    out = []
    for l in L[i:]:
        if l.startswith('### '): out.append(' ##H## ')             # a heading breaks any passage
        elif l.startswith('# ') or l.startswith('~~'): out.append(l[2:])
    t = clean(' '.join(out))
    if key in ('tatir', 'ghannam'): t = re.sub(r"'\s*([^']{1,600}?)\s*'", r'«\1»', t)          # the hadith quotes ' … ' of these two copies
    return t
TEXT = {k: body(k) for k in FILES}

GAP = r'[\s()\[\]،؛:.؟!"\'«»-]*'
def rx(anchor): return GAP.join(re.escape(w) for w in re.sub(r'[()\[\]،؛:.؟!"\'«»-]', ' ', anchor).split())
def cut(book, start, end, nth=0):
    T = TEXT[book]; ms = [m for m in re.finditer(rx(start), T)]
    if not ms: raise KeyError(f'START not found [{book}]: {start}')
    if len(ms) > 1 and nth == 0 and False: raise SystemExit(f'START not unique [{book}]: {start}')
    m = ms[nth]; e = re.search(rx(end), T[m.start():])
    if not e: raise KeyError(f'END not found [{book}]: {end}  (after: {start})')
    a, b = m.start(), m.start() + e.end(); s = T[a:b]
    for _ in range(3):                                                   # a closing mark that belongs to a mark opened inside the passage
        rest = T[b:b + 3].lstrip(); c = rest[:1]
        if c == '﴾' and s.count('﴿') > s.count('﴾') or c == ')' and s.count('(') > s.count(')') or c == '»' and s.count('«') > s.count('»') or c == '"' and s.count('"') % 2 == 1:
            b = b + (T[b:b + 3].index(c)) + 1; s = T[a:b]
    if s.count(')') > s.count('(') and T[:a].rstrip().endswith('('): a = T[:a].rstrip().rfind('('); s = T[a:b]
    if s.count('"') % 2 == 1: s = s.replace('"', '')                      # a stray quotation mark of the digital copy
    if '##H##' in s: raise KeyError(f'passage crosses a heading [{book}]: {start} … {end}')
    return s

# the Qur'anic phrases (mushaf's own words when the phrase is found there word for word)
Q = json.load(open('content/quran.json', encoding='utf8'))
import collections
MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۨ-ۭـ]'); WAQF = re.compile('[ۖ-ۜ]')
def key2(w): return re.sub('[ٱأإآ]', 'ا', MARKS.sub('', w)).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي').replace('ا', '').replace('ي', '')
SUR = collections.defaultdict(list)
for s, a, t in Q['a']:
    for w in t.split(): SUR[s].append(w)
IDX = collections.defaultdict(list)
for s, ws in SUR.items():
    for i, w in enumerate(ws): IDX[key2(w)].append((s, i))
def official(phrase):
    ks = [key2(w) for w in phrase.split() if key2(w)]
    if len(ks) < 2: return None
    found = {}
    for s, i in IDX.get(ks[0], []):
        ws = SUR[s]
        if [key2(w) for w in ws[i:i + len(ks)]] == ks: found[WAQF.sub('', ' '.join(ws[i:i + len(ks)])).strip()] = 1
    return next(iter(found)) if len(found) == 1 else None
QS = collections.Counter()
def quran(t):
    def rep(m):
        o = official(m.group(1)); QS['mushaf' if o else 'as typed'] += 1
        return '﴿' + (o or m.group(1).strip()) + '﴾'
    return re.sub(r'﴿([^﴾]*)﴾', rep, t)
TYPOS = json.load(open('data/qawaid/typos.json', encoding='utf8')) if os.path.exists('data/qawaid/typos.json') else []
USED = collections.Counter()
def mend(book, t):
    for c in TYPOS:
        if c['book'] == book and c['find'] in t:
            USED[c['find']] += t.count(c['find']); t = t.replace(c['find'], c['replace'])
    return t

def P(book, start, end, nth=0): return {'book': book, 'start': start, 'end': end, 'nth': nth}
exec(open('data/qawaid/spec.py', encoding='utf8').read())          # defines ENTRIES = [ {title, group, rule:[P…], ex:[P…]} … ]

out = []; FAIL = []
for e in ENTRIES:
    d = {'title': e['title'], 'group': e['group'], 'rule': [], 'ex': []}
    for kind in ('rule', 'ex'):
        for p in e.get(kind, []):
            try: t = mend(p['book'], cut(p['book'], p['start'], p['end'], p['nth'])); t = quran(t)
            except KeyError as ex: FAIL.append(str(ex)); continue
            d[kind].append({'book': NAMES[p['book']], 'key': p['book'], 'text': t})
    out.append(d)
if FAIL: print('\n'.join(FAIL)); raise SystemExit(f'{len(FAIL)} anchors failed')
for c in TYPOS: assert USED[c['find']] == c['count'], f"typo «{c['find']}» matched {USED[c['find']]} times, expected {c['count']}"
json.dump(out, open('data/qawaid/excerpts.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(len(out), 'entries;', sum(len(d['rule']) + len(d['ex']) for d in out), 'passages;', 'quran phrases:', dict(QS))
