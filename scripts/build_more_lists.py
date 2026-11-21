"""Builds the two lists of the «المزيد» menu that are made out of the other lists of the app:
  «رؤى الأنبياء والصالحين»  (content/anbiya.json)   — the dreams of the Prophets, of the Prophet ﷺ and of his Companions, and the dreams the Prophet or a Companion interpreted:
        1) the Qur'an's own dreams (Yusuf, the two prisoners, the king of Egypt, Ibrahim, the Prophet ﷺ): the ayat word for word from content/quran.json, each with its number;
        2) the Prophet's dreams in al-Jami' al-Saghir (content/jami.json), with the printed symbols;
        3) the passages of «رؤى وتعبيرها» (content/ruaa.json, which is built from the books) whose dreamer or interpreter is the Prophet ﷺ, a Companion, or a Prophet.
  «المعبِّرون»              (content/muabbirun.json) — who the interpreters are: what the classical dictionaries say of them (data/muabbirun/excerpts.json, word for word,
        scripts/extract_muabbirun.py) and the number of their dreams in the list.
Nothing is written by hand except the choice of what to include; every text is copied from the source that is named under it.   usage: python3 -I scripts/build_more_lists.py"""
import json, re, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
Q = json.load(open('content/quran.json', encoding='utf8'))
VERSE = {(s, a): t for s, a, t in Q['a']}; SURAH = {s['n']: s['name'] for s in Q['surahs']}
JAMI = json.load(open('content/jami.json', encoding='utf8'))['h']
RUAA = json.load(open('content/ruaa.json', encoding='utf8'))['h']

# ---------------------------------------------------------------- 1) the Qur'an
MARKS = re.compile('[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u0640]')
def key(w): return re.sub('[ٱأإآ]', 'ا', MARKS.sub('', w)).replace('ى', 'ي').replace('ة', 'ه')
def after(s, a, word):
    """the position just after the first word of the ayah that is spelled `word` (the mushaf's marks left aside)"""
    return next(i for i, x in enumerate(VERSE[(s, a)].split()) if key(x) == key(word)) + 1
def ayah(s, a, words=None):
    t = VERSE[(s, a)]
    if words: t = ' '.join(t.split()[words[0]:words[1]])
    return f'﴿{t}﴾ [{SURAH[s]}: {a}]'
def ayat(s, rng, words=None): return ' '.join(ayah(s, a, words) for a in rng)
def src(s, nums): return f'القرآن الكريم — سورة {SURAH[s]}: ' + '، '.join(str(n) for n in nums)
QUR = []
# who = the dreamer, by = the interpreter, when the ayat name them
QUR.append(['', ayah(12, 4), ayat(12, (6, 100)), src(12, (4, 6, 100)), '', 'يوسف عليه السلام'])
QUR.append(['', ayah(12, 36), ayah(12, 41), src(12, (36, 41)), 'يوسف عليه السلام', 'صاحبا يوسف في السجن'])
QUR.append(['', ayah(12, 43), ayat(12, (47, 48, 49)), src(12, (43, 47, 48, 49)), 'يوسف عليه السلام', 'ملك مصر'])
QUR.append(['', ayah(37, 102), ayat(37, (103, 104, 105)), src(37, (102, 103, 104, 105)), '', 'إبراهيم عليه السلام'])
w = VERSE[(48, 27)].split(); k = after(48, 27, 'بالحق')
QUR.append(['', f'﴿{" ".join(w[:k])}﴾ [{SURAH[48]}: 27]', f'﴿{" ".join(w[k:])}﴾ [{SURAH[48]}: 27]', src(48, (27,)), '', 'النبي ﷺ'])
w = VERSE[(8, 43)].split(); k = after(8, 43, 'قليلا')
QUR.append(['', f'﴿{" ".join(w[:k])}﴾ [{SURAH[8]}: 43]', f'﴿{" ".join(w[k:])}﴾ [{SURAH[8]}: 43]', src(8, (43,)), '', 'النبي ﷺ'])

# ---------------------------------------------------------------- 2) al-Jami' al-Saghir
def jami(idx, dream_from=None, dream_to=None, interp_from=None):
    r = JAMI[idx]; t = r[2]; tak = r[3]
    assert t.startswith(JAMI[idx][2][:10])
    d = t[t.index(dream_from):] if dream_from else t
    if interp_from:
        k = d.index(interp_from); dream, interp = d[:k].strip(), d[k:].strip()
    else: dream, interp = d.strip(), ''
    return ['', dream, interp, f'الجامع الصغير للسيوطي — {tak}', 'النبي ﷺ' if interp else '', 'النبي ﷺ']
HAD = [jami(4387, interp_from='فتأولتها'), jami(3148, dream_from='وبينا أنا نائم')]
for h in HAD: assert h[1] and (h[1] in JAMI[4387][2] or h[1] in JAMI[3148][2])

# ---------------------------------------------------------------- 3) from the books
AR = r'[ء-ي]'
FIG = [('النبي ﷺ', r'(?:صلى\s+الله\s+عليه\s+وسلم|النبي|رسول\s+الله|الرسول)(?:\s+صلى\s+الله\s+عليه\s+وسلم|\s+عليه\s+(?:الصلاة\s+و)?السلام)?'), ('أبو بكر الصديق', r'(?:أبو|أبا)\s+بكر(?:\s+الصديق)?'),
       ('عمر بن الخطاب', r'عمر(?:\s+(?:بن|ابن)\s+الخطاب)?'), ('عائشة', r'عائشة'), ('أم الفضل', r'أم\s+الفضل(?=ل?رسول|\s)'), ('عبد الله بن عمر', r'عبد\s+الله\s+بن\s+عمر'),
       ('أبو موسى الأشعري', r'أبو\s+موسى(?:\s+الأشعري)?'), ('الحسن بن علي', r'الحسن\s+بن\s+(?:علي|على)'), ('الحسن البصري', r'الحسن\s+البصري'), ('سفيان بن عيينة', r'سفيان\s+بن\s+عيينة')]
LEAD = r'(?:^|\s)(?:و?قال(?:ت)?|و?روي\s+أن|و?حكي\s+أن|و?روى|و?حكاية\s+عن|و?أن|و?رأى)\s+(?:ال)?'
def dreamer(dream):
    d = dream[:220]
    for name, rx in FIG:
        if re.search(LEAD + r'(?:' + rx + r')(?![ء-ي])[^.]{0,60}?(?:رأيت|رأى|رأت|رؤيا)', d): return name
        if re.search(r'^\s*(?:' + rx + r')\s+(?:رأى|رأت)', d): return name
    return ''
PROPHET_OR_COMPANION_INTERP = {'النبي ﷺ', 'أبو بكر الصديق', 'عمر بن الخطاب', 'ابن عباس', 'سليمان بن داود عليهما السلام'}
BOOKS = []
for ref, dream, interp, source, by in RUAA:
    who = dreamer(dream)
    if who or by in PROPHET_OR_COMPANION_INTERP: BOOKS.append([ref, dream, interp, source, by, who])


# the Qur'anic phrases of the digital copy are marked «@QB@ … @QE@»: each is replaced by the mushaf's own words when it is found there word for word (also across two ayat)
WAQF = re.compile('[\u06D6-\u06DC]')
def key2(w): return re.sub('[ٱأإآ]', 'ا', MARKS.sub('', w)).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي').replace('ا', '')
SUR = collections.defaultdict(list)
for (sn, an), t in sorted(VERSE.items()):
    for w in t.split(): SUR[sn].append(w)
IDX = collections.defaultdict(list)
for sn, ws in SUR.items():
    for i, w in enumerate(ws): IDX[key2(w)].append((sn, i))
def official(phrase):
    ks = [key2(w) for w in phrase.split() if key2(w)]
    if len(ks) < 2: return None
    found = {}
    for sn, i in IDX.get(ks[0], []):
        ws = SUR[sn]
        if [key2(w) for w in ws[i:i + len(ks)]] == ks: found[WAQF.sub('', ' '.join(ws[i:i + len(ks)])).strip()] = 1
    return next(iter(found)) if len(found) == 1 else None
QSTAT = collections.Counter()
def quran_marks(t):
    def rep(m):
        o = official(m.group(1)); QSTAT['replaced' if o else 'kept as typed'] += 1
        return '﴿' + (o or m.group(1).strip()) + '﴾'
    return re.sub(r'@QB@(.*?)@QE@', rep, t)

# ---------------------------------------------------------------- 4) «المنامات» of Ibn Abi al-Dunya: the dreams of the righteous, each numbered report whole (with its chain of narrators)
def manamat():
    L = open('data/books/manamat.txt', encoding='utf8').read().split('\n')
    i0 = next(k for k, l in enumerate(L) if 'Header#End' in l) + 1
    paras = []; cur = None; head = ''
    for l in L[i0:]:
        if l.startswith('### '):
            h = re.sub(r'^###\s*\|*\s*', '', l).strip()
            if h: head = h
            continue
        if l.startswith('# ') or l == '#': cur = [l[2:]]; paras.append([head, cur])
        elif l.startswith('~~') and cur is not None: cur.append(l[2:])
    def clean(t):
        t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\[\s*\d+\s*\]|\(\s*\d+\s*\)', ' ', t)
        t = quran_marks(t); t = t.replace('%~%', ' ').replace('٭', ' ').replace('{', '﴿').replace('}', '﴾')
        return re.sub(r'\s+', ' ', t).strip()
    reps = []
    for h, c in paras:
        t = clean(' '.join(c))
        if not t: continue
        m = re.match(r'^(\d+)\s+(.*)$', t)
        if m: reps.append({'n': int(m.group(1)), 'head': h, 't': m.group(2)})
        elif reps: reps[-1]['t'] += ' ' + t
    out = []
    for r in reps:
        t = r['t']
        if not (re.search(r'رأيت|رأى|رئي|رؤي|رؤيا|أري|رأينا|يرى|ترى|رآه|رأته', t) and re.search(r'المنام|النوم|منامي|منامه|الرؤيا|رؤيا|منامها|منامهم', t)): continue
        out.append(['رواية', t, '', 'المنامات (ابن أبي الدنيا)', '', ''])        # the numbers printed in the digital copy repeat and jump (301, 202, 303, 204…): they are not shown
    return out
MAN = manamat()

def main():
    rows = QUR + HAD + BOOKS + MAN
    for r in rows[:0]: pass
    CL.publish('anbiya', 'رؤى الأنبياء والصالحين', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'dream', 'menu': 'رؤى الأنبياء والصالحين', 'placeholder': 'اكتب هنا',
               'hint': 'رؤى الأنبياء والنبي ﷺ وأصحابه، ورؤى عبّرها النبي ﷺ أو أحد الصحابة، من القرآن والسنة وكتب التعبير.'})
    # ---- the interpreters
    ex = json.load(open('data/muabbirun/excerpts.json', encoding='utf8'))
    count = collections.Counter(r[4] for r in RUAA)
    people = []
    for pp in ex:
        parts = '\n'.join(f"{x['text']}\t{x['src']} — {x['loc']}" for x in pp['parts'])
        people.append([pp['name'], parts, '', '', pp['key']])
    # Yusuf: the ayat that say he was taught the interpretation (word for word from the mushaf)
    yus = '\n'.join(f"﴿{VERSE[(12, a)]}﴾\tالقرآن الكريم — سورة يوسف: {a}" for a in (6, 21, 101))
    people.insert(0, ['يوسف عليه السلام', yus, '', '', 'يوسف عليه السلام'])
    CL.publish('muabbirun', 'المعبِّرون', 'generic', {'h': people}, len(people), extra={'drawer': True, 'card': 'person', 'menu': 'المعبِّرون', 'placeholder': 'اكتب هنا',
               'hint': 'من هم المعبِّرون الذين ورد ذكرهم في الكتب، وما قالته عنهم كتب التراجم.'})
    return rows, people, count
if __name__ == '__main__':
    rows, people, count = main()
    print(len(rows), 'anbiya: qur', len(QUR), 'jami', len(HAD), 'books', len(BOOKS), 'manamat', len(MAN)); print(len(people), 'people')
