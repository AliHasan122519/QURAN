"""Builds the «أبيات الاستشهاد» tab: [heading, «first hemistich … second hemistich», «occasion ⏎ poet ⏎ another transmission», source(s)].
Input data/shawahid/verses_parsed.json (scripts/parse_shawahid.py). What is added to a verse is only what the books state around it (scripts/shawahid_lib.py): the poet, and the
occasion when a book names one. The verses quoted by several books are compared: a reading that is a misprint (a word nobody else uses, where another book has a real word) is
dropped; a different transmission of a real word is kept as «ويُروى».   usage: python3 -I scripts/build_shawahid.py"""
import json, os, sys, re, gzip, collections, difflib
from rapidfuzz import fuzz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL, shawahid_lib as S
V = json.load(open('data/shawahid/verses_parsed.json', encoding='utf8'))
KH = json.load(open('data/shawahid/khizana_verses.json', encoding='utf8'))          # scripts/parse_khizana.py: the verses of «خزانة الأدب», each decided by the vote of four copies
for e in KH: e.pop('copies', None)
V += KH
AR = re.compile(r'[^ء-ي ]')
def nw(s): return AR.sub('', re.sub(r'[ً-ٰٟ]', '', s))
# vocabulary: every word of the four books' own prose (typed, so a real word recurs)
FREQ = collections.Counter()
for f in ('suyuti_shawahid_mughni', 'baghdadi_abyat_mughni', 'ayni_maqasid', 'sirafi_abyat_sibawayh', 'khizana_jk'):
    for w in nw(gzip.open(f'data/shawahid/{f}.txt.gz', 'rt', encoding='utf8').read()).split(): FREQ[w] += 1
def valid(w): return FREQ[w] >= 3
# 1) compare the verses quoted twice with small differences
def full(e): return nw(e['a'] + ' ' + e['b'])
groups = collections.defaultdict(list)
for i, e in enumerate(V): groups[nw(e['b']).split()[-1] if e['b'].split() else ''].append(i)
parent = list(range(len(V)))
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for k, ids in groups.items():
    if len(ids) < 2 or len(ids) > 600: continue
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            a, b = full(V[ids[x]]), full(V[ids[y]])
            if abs(len(a) - len(b)) <= 6 and fuzz.ratio(a, b) >= 88: parent[find(ids[x])] = find(ids[y])
clusters = collections.defaultdict(list)
for i in range(len(V)): clusters[find(i)].append(i)
drop = set(); variant = {}; stat = collections.Counter()
SRC_ORDER = ['شرح شواهد المغني', 'المقاصد النحوية في شرح شواهد شروح الألفية', 'شرح أبيات مغني اللبيب', 'شرح أبيات سيبويه', 'خزانة الأدب ولب لباب لسان العرب']
for root, ids in clusters.items():
    if len(ids) < 2: continue
    ids.sort(key=lambda i: (-len(V[i]['srcs']), min(SRC_ORDER.index(s) for s in V[i]['srcs'])))
    prim = ids[0]
    for o in ids[1:]:
        ta, tb = full(V[prim]).split(), full(V[o]).split()
        if ta == tb: drop.add(o); stat['same words, other spelling'] += 1; V[prim]['srcs'] = sorted(set(V[prim]['srcs'] + V[o]['srcs']), key=SRC_ORDER.index); V[prim]['ctx'] += V[o]['ctx']; continue
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        bad_o = bad_p = other = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal': continue
            pa, ob = ta[i1:i2], tb[j1:j2]
            if ob and all(not valid(w) for w in ob) and (not pa or all(valid(w) for w in pa)): bad_o += 1
            elif pa and all(not valid(w) for w in pa) and (not ob or all(valid(w) for w in ob)): bad_p += 1
            else: other += 1
        if bad_o and not bad_p and not other:   drop.add(o); stat['misprint dropped'] += 1; V[prim]['srcs'] = sorted(set(V[prim]['srcs'] + V[o]['srcs']), key=SRC_ORDER.index); V[prim]['ctx'] += V[o]['ctx']
        elif bad_p and not bad_o and not other: drop.add(prim); stat['misprint replaced'] += 1; V[o]['srcs'] = sorted(set(V[o]['srcs'] + V[prim]['srcs']), key=SRC_ORDER.index); V[o]['ctx'] += V[prim]['ctx']; prim = o
        else:
            if prim not in variant: variant[prim] = []
            variant[prim].append(o); drop.add(o); stat['other transmission kept as «ويُروى»'] += 1
            V[prim]['ctx'] += V[o]['ctx']
# 2) poet and occasion from the books' own words
keep = [i for i in range(len(V)) if i not in drop]
poets = S.poets([V[i]['ctx'] for i in keep]); S.NAMES.update(p for p in poets if p)
rows = []
for n, i in enumerate(keep):
    e = V[i]; ref = e['ref']
    if re.match(r'^(?:و?أنشد|وأنشد|الكتاب|الشاهد|الباب|فصل)', ref) or len(ref) > 70: ref = ''
    ref = re.sub(r'\s+', ' ', ref).strip()
    occ = S.occasion_of(e['ctx']); poet = poets[n]
    if occ and poet and S.same_person(occ, poet): occ = ''                                  # «عند رثاء أبو ذؤيب نشبة…»: the poet himself is the one the book names as the subject, not the object
    alt = ''
    if i in variant:
        for vi in variant[i]:
            o = V[vi]
            if '?' in o['a'] + o['b']: continue                                    # a «?» in a word is an unreadable letter of the digital copy, not a transmission
            if full(o) != full(e): alt = f"{o['a']} … {o['b']}"; break           # a variant that differs only in the way a hamza / alif maqsura is written is the same line
    stat['poet'] += bool(poet); stat['occasion'] += bool(occ)
    rows.append([ref, f"{e['a']} … {e['b']}", '\n'.join([occ, poet, alt]) if (occ or poet or alt) else '', ' · '.join(e['srcs'])])
CL.publish('shawahid', 'أبيات الإستشهاد', 'generic', {'h': rows}, len(rows), extra={'card': 'verse', 'smart': 'full', 'placeholder': 'اكتب هنا',
    'hint': 'اكتب الكلمة ويفهم التطبيق مرادفاتها وما يقابلها بالعامية، وتظهر الأبيات التي ورد فيها المعنى.'})
print(dict(stat), 'entries', len(rows))
