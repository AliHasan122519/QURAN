"""Checks the lists of the «المزيد» menu against their sources (run after scripts/build_ruaa.py / build_more_lists.py):  python3 -I tests/lists_check.py
  - every ayah of «رؤى الأنبياء والصالحين» is the mushaf's own text (content/quran.json) with the right number;
  - every hadith of it is inside content/jami.json with the printed symbols; every passage taken from the books is in «رؤى وتعبيرها» word for word;
  - every report of «المنامات» is whole and none repeats;  the biographical excerpts of «المعبِّرون» are found word for word in the dictionaries when those are present (OITI=…);
  - no typing residue (page marks, footnote numbers glued to words, ASCII «?», empty brackets, unbalanced brackets) in any of the three lists."""
import json, re, sys, os, collections
J = lambda f: json.load(open(f'content/{f}.json', encoding='utf8'))['h']
Q = json.load(open('content/quran.json', encoding='utf8'))
VERSE = {(s, a): t for s, a, t in Q['a']}; SURAH = {s['n']: s['name'] for s in Q['surahs']}; SNUM = {v: k for k, v in SURAH.items()}
ruaa, anb, mua, jami = J('ruaa'), J('anbiya'), J('muabbirun'), J('jami')
bad = []; ok = collections.Counter()
def check(c, msg):
    if c: ok['checks'] += 1
    else: bad.append(msg)
MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۨ-ۭـ]')
def nk(t): return re.sub(r'\s+', ' ', MARKS.sub('', t)).strip()
ruaa_set = {(r[1], r[2], r[3]) for r in ruaa}
for r in anb:
    ref, dream, interp, source, by, who = r
    if source.startswith('القرآن'):
        for m in re.finditer(r'﴿([^﴾]*)﴾ \[([^:\]]+): (\d+)\]', dream + ' ' + interp):
            s = SNUM[m.group(2)]; a = int(m.group(3)); check(m.group(1) in VERSE[(s, a)], f'ayah text differs: {m.group(2)} {a}')
        check(source.split('سورة ')[1].split(':')[0] in SNUM, f'surah name: {source}')
    elif source.startswith('الجامع'):
        sym = source.split(' — ', 1)[1]
        check(any(dream in h[2] and sym == h[3] and (not interp or interp in h[2]) for h in jami), f'hadith not found in al-Jami: {dream[:40]}')
    elif source.startswith('المنامات'):
        check(ref == 'رواية' and not interp and len(dream) > 60, f'report: {dream[:40]}')
    else:
        check((dream, interp, source) in ruaa_set, f'passage not in the ruaa list: {dream[:40]}')
reps = [r[1] for r in anb if r[3].startswith('المنامات')]
check(len(set(reps)) == len(reps) and len(reps) > 150, 'the reports of al-Manamat repeat or are too few')
for name, rows in (('ruaa', ruaa), ('anbiya', anb), ('muabbirun', mua)):
    for r in rows:
        t = ' '.join(x for x in r if isinstance(x, str))
        check(not re.search(r'PageV|\bms\d+\b|@|\^|\\|\|', t), f'{name}: residue marks: {t[:50]}')
        check(not re.search(r'[ء-ي]\d', t), f'{name}: digit glued to a word: {t[:50]}')
        check('?' not in t.replace('؟?', ''), f'{name}: ASCII question mark: {t[:50]}')
        check(not re.search(r'\(\s*\)', t), f'{name}: empty brackets: {t[:50]}')
        for o, c in (('(', ')'), ('﴿', '﴾'), ('«', '»')): check(t.count(o) == t.count(c), f'{name}: unbalanced {o}: {t[:50]}')
OITI = os.environ.get('OITI', '/tmp/claude-0/oiti')
src_files = [f'{OITI}/0750AH/data/0748Dhahabi/0748Dhahabi.SiyarAclamNubala/0748Dhahabi.SiyarAclamNubala.Shamela0010906-ara1.mARkdown', f'{OITI}/1400AH/data/1396KhayrDinZirikli/1396KhayrDinZirikli.Aclam/1396KhayrDinZirikli.Aclam.Shamela0012286-ara1.mARkdown']
if all(os.path.exists(f) for f in src_files):
    def clean(t):
        t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\(\d+\)', ' ', t)
        t = re.sub(r'^(?:#|~~)\s?', '', t, flags=re.M)
        return re.sub(r'\s+([.،؛:؟])', r'\1', re.sub(r'\s+', ' ', t)).strip()
    corpus = [re.sub(r'\s+', ' ', clean(open(f, encoding='utf8', errors='ignore').read())) for f in src_files]
    ex = json.load(open('data/muabbirun/excerpts.json', encoding='utf8'))
    for pp in ex:
        for x in pp['parts']:
            parts = [x['text']]
            for t in parts:
                check(any(t in c for c in corpus), f"excerpt not found in the dictionary: {pp['name']}: {t[:50]}")
    ok['excerpts verified'] = sum(len(p['parts']) for p in ex)
else: print('(the dictionaries are not present: the excerpts were not compared with them)')
for r in mua:
    check(r[1].count('\t') >= 1 or r[0].startswith('يوسف'), f'person without a source: {r[0]}')
print('checks passed:', ok['checks'], '| excerpts compared with the dictionaries:', ok.get('excerpts verified', 0))
if bad: print('PROBLEMS:'); [print('  ', b) for b in bad[:40]]; sys.exit(1)
print('OK')
