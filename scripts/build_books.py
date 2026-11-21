"""Builds the «الكتب» tab: one entry per interpretation, [heading (the symbol), the book's words, the reason the book gives (or '')].
Input data/books/isharat_parsed.json (scripts/parse_book_isharat.py). Two things are done to the text, nothing is added to it:
 1) a Qur'anic phrase between ﴿ ﴾ is replaced by the same words of the official text (content/quran.json) when it is found there word for word;
 2) the reason the author himself gives (a verse/hadith he cites, or a «لأن…» clause) is copied to the third field, which the app shows under «وجه الشبه».
usage: python3 -I scripts/build_books.py"""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
E = json.load(open('data/books/isharat_parsed.json', encoding='utf8')) + json.load(open('data/books/more_parsed.json', encoding='utf8'))
Q = json.load(open('content/quran.json', encoding='utf8'))['a']
MARKS = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def key(w):
    w = MARKS.sub('', w); w = re.sub('[ٱأإآ]', 'ا', w).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')
    return w.replace('ا', '')
def loose(w): return re.sub('[اويىءؤئأإآٱ]', '', MARKS.sub('', w)).replace('ة', 'ه')
V = [t.split() for _, _, t in Q]; VK = [[key(w) for w in t] for t in V]; VL = [[loose(w) for w in t] for t in V]
IDX = {}; IDL = {}
for vi, ks in enumerate(VK):
    for p, k in enumerate(ks): IDX.setdefault(k, []).append((vi, p))
for vi, ks in enumerate(VL):
    for p, k in enumerate(ks): IDL.setdefault(k, []).append((vi, p))
stat = {'verses': 0, 'fixed': 0, 'same': 0, 'unmatched': 0}
def official(snip):
    toks = snip.split(); WAQF = re.compile('[\u06D6-\u06DC]')
    for fk, ID, VV, lo in ((key, IDX, VK, 0), (loose, IDL, VL, 1)):
        ks = [fk(t) for t in toks]; ks = [k for k in ks if k]
        if len(ks) < (3 if lo else 2): continue
        found = {}
        for vi, p in ID.get(ks[0], []):
            if VV[vi][p:p + len(ks)] == ks: found.setdefault(WAQF.sub('', ' '.join(V[vi][p:p + len(ks)])), ' '.join(V[vi][p:p + len(ks)]))
        if len(found) == 1: return WAQF.sub('', next(iter(found.values()))).strip()      # a pause sign at the end of a quoted phrase is not part of the phrase
    return None
def fix_verses(t):
    def rep(m):
        stat['verses'] += 1; o = official(m.group(1))
        if o is None: stat['unmatched'] += 1; return m.group(0)
        if o == m.group(1).strip(): stat['same'] += 1
        else: stat['fixed'] += 1
        return '﴿' + o + '﴾'
    return re.sub(r'﴿([^﴾]+)﴾', rep, t)
def paren_verses(t):
    # «قوله تعالى (إن الذين اتقوا…) الآية»: a verse the author gives between plain parentheses -> the official text in ﴿ ﴾ when found word for word
    def rep(m):
        o = official(m.group(2)); return m.group(1) + ('﴿' + o + '﴾' if o else '(' + m.group(2) + ')')
    return re.sub(r'(قوله\s+تعالى\s*:?\s*)\(([^()]{8,300})\)', rep, t)
TAIL = re.compile(r'\s+(?:وقال|وقيل|ومن|وإن|وان|ثم|و|أو|فإن|وأما|وقد)\s*$')
def tidy(t):
    t = t.strip()
    while TAIL.search(t): t = TAIL.sub('', t)
    return t.strip()
STOP = r'(?=\s(?:ومن رأى|ومن|وقيل|وقال|وإن|وان|وأما|فإن|\()|[.؛]|$)'
RQ = re.compile(r'(?:ل|بـ?)قوله\s+تعالى\s*:?\s*(﴿[^﴾]+﴾(?:\s*الآية)?|[^﴿﴾.؛(]{4,200}?' + STOP + ')')
RH = re.compile(r'ل?قوله\s+((?:صلى الله عليه وسلم|عليه السلام|عليه الصلاة والسلام)\s*:?\s*[^﴿﴾.؛(]{6,220}?' + STOP + ')')
RB2 = re.compile(r'لما\s+(?:في|فيه|فيها)\s+([^﴿﴾.؛(]{6,200}?' + STOP + ')')
RB = re.compile(r'لأن(ه|ها|هم|هن|ك|ي)?\s+([^﴿﴾.؛(]{6,260}?' + STOP + ')')
def why(t):
    out = []
    for m in RQ.finditer(t):
        q = m.group(1).strip().rstrip(' .'); q = re.sub(r'\s*الآية$', '', q)
        if not q.startswith('﴿') and len(q.split()) > 18: q = ' '.join(q.split()[:18])
        if not q.startswith('﴿'):
            o = official(q); q = '﴿' + o + '﴾' if o else q
        out.append('وجه الشبه مأخوذ من قوله تعالى: ' + q)
    for m in RH.finditer(t): out.append('وجه الشبه مأخوذ من قوله ' + m.group(1).strip().rstrip(' .'))
    for m in RB.finditer(t):
        pron = {'': 'أنّ', 'ه': 'أنّه', 'ها': 'أنّها', 'هم': 'أنّهم', 'هن': 'أنّهنّ', 'ك': 'أنّك', 'ي': 'أنّي'}[m.group(1) or '']
        r = tidy(m.group(2)).rstrip(' .')
        r = re.split(r'\s+(?:ل?قوله\s)', r)[0].strip()
        if len(r) >= 6: out.append('وجه الشبه: ' + pron + ' ' + r)
    for m in RB2.finditer(t):
        r = tidy(m.group(1)).rstrip(' .')
        if len(r) >= 6: out.append('وجه الشبه: ما في ' + r)
    return '. '.join(dict.fromkeys(out)) + ('.' if out else '')

NOTE = re.compile(r'\[[^\]]*(?:لعله|لعل |دار الحديث|فليراجع|هكذا|في الأصل|في المخطوط|في المطبوع|سقط|ساقط|كذا في|النسخة|ظ:)[^\]]*\]')
def balance(t):
    """removes the brackets that have no partner (a quotation cut by the book's page break, an editor's stray mark)"""
    for o, c in (('(', ')'), ('«', '»'), ('﴿', '﴾'), ('[', ']')):
        st = []; bad = set()
        for k, ch in enumerate(t):
            if ch == o: st.append(k)
            elif ch == c:
                if st: st.pop()
                else: bad.add(k)
        bad |= set(st)
        if bad: t = ''.join(ch for k, ch in enumerate(t) if k not in bad)
    return t
def finalize(t):
    t = re.sub(r'[\u200B-\u200F\u202A-\u202E\uFEFF]', '', t)
    t = re.sub(r'PageV\d+P\d+|@QB@|@QE@|@\w{1,4}@', ' ', t)
    t = NOTE.sub(' ', t)
    t = re.sub(r'@\s*\d+\s*[أب]?\s*@', ' ', t); t = t.replace('^', ' ').replace('\\', ' ').replace('_', ' ').replace('|', ' '); t = re.sub(r'\s%\s', ' ... ', t); t = re.sub(r'\s\*\s', ' ', t)
    t = re.sub(r'(?<=[\u0621-\u064A])\d{1,3}(?=[\s.،:)؛])', '', t); t = re.sub(r'\s,\s?', '، ', t)
    t = re.sub(r'\[([^\[\]]{1,60})\]', r'\1', t)                  # an editor's supplement «[عليهما السلام]» keeps its words
    t = re.sub(r'\(\s*\d{1,3}\s*\)', ' ', t); t = re.sub(r'(?<=[\u0621-\u064A])\d{1,3}\)', ')', t)      # footnote numbers
    parts = re.split(r'(﴿[^﴾]*﴾)', t)
    t = ''.join(p if p.startswith('﴿') else p.replace('\u0640', '') for p in parts)     # tatweel is kept only inside the Qur'an text
    t = re.sub(r'\s+([،؛:.؟!)])', r'\1', t); t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'([،؛:؟])(?=[\u0621-\u064A])', r'\1 ', t); t = re.sub(r'\.{4,}', '...', t)
    t = balance(t)
    t = re.sub(r'^[)﴾»\]\s]+', '', t); t = re.sub(r'[(﴿«\[\s]+$', '', t)
    # typing residue of the digital texts (never part of the author's words): footnote numbers glued to a word, ASCII «?», empty brackets, the line/page mark « / »
    parts = re.split(r'(﴿[^﴾]*﴾)', t)
    def tidy_plain(p):
        p = re.sub(r'(?<=[\u0621-\u064A])\d{1,3}(?=[\s.،:؛)؟?!]|$)', '', p); p = re.sub(r'(?:(?<=\s)|^)\d{1,3}(?=[\u0621-\u064A])', '', p)
        p = re.sub(r'(?<=[\u0621-\u064A\s])\s?\?', '؟', p); p = re.sub(r'(?<=[!])\?', '؟', p); p = re.sub(r'\(\s*\)|«\s*»|\[\s*\]', ' ', p)
        p = re.sub(r'\s/(?=\s|$)', ' ', p); p = re.sub(r'^/\s', '', p)
        return p
    t = ''.join(p if p.startswith('﴿') else tidy_plain(p) for p in parts)
    t = re.sub(r'\s+([،؛:.؟!)])', r'\1', t)
    return re.sub(r'\s+', ' ', t).strip()
SOURCES = {'isharat': 'الإشارات في علم العبارات', 'tatir': 'تعطير الأنام في تعبير المنام', 'qadiri': 'القادري في التعبير', 'ghannam': 'تعبير الرؤيا (ابن غنام المقدسي)',
           'muntakhab': 'منتخب الكلام في تفسير الأحلام', 'badr': 'البدر المنير في علم التعبير', 'manamat': 'المنامات (ابن أبي الدنيا)', 'salimi': 'الإشارة إلى علم العبارة'}
rows = []
for e in E:
    t = finalize(tidy(re.sub(r'﴿((?:و?من|و?إن) رأى)﴾', r'\1', re.sub(r':\s*:', ':', paren_verses(fix_verses(e['text']))))))
    if len(t) < 25: continue
    ref = '' if e['ref'] == 'PARATEXT' else finalize(e['ref'])
    rows.append([ref, t, finalize(why(t)), SOURCES[e.get('src', 'isharat')]])
# typing mistakes of the digital copies that are plain misprints (a missing letter, a doubled one): each is listed with the reason in data/books/corrections.json and must match exactly as many times as stated
CORR = json.load(open('data/books/corrections.json', encoding='utf8'))
for c in CORR:
    n = 0
    for r in rows:
        if r[3] == c['src'] and c['find'] in r[1]: n += r[1].count(c['find']); r[1] = r[1].replace(c['find'], c['replace'])
    assert n == c['count'], f"correction «{c['find']}» matched {n} times, expected {c['count']}"
CL.publish('books', 'الكتب', 'generic', {'h': rows}, len(rows), extra={'card': 'meaning', 'smart': 'dialect', 'placeholder': 'اكتب هنا', 'hint': 'اكتب اسم الرمز لتعرف ما ورد في معناه، ثم اضغط «وجه الشبه» لبيان سببه.'})
print(stat, 'with reason:', sum(1 for r in rows if r[2]), 'of', len(rows))
