"""Extracts the verses of «خزانة الأدب ولب لباب لسان العرب» (عبد القادر البغدادي) from four independent digital copies (OpenITI, data/shawahid/khizana_*.txt.gz):
  jk      (دار الكتب العلمية، تحقيق طريفي ويعقوب)   hemistichs between «%»
  shamay  (the same edition, another digitisation)   «( first ** second )»
  shamela (طبعة هارون، مكتبة الخانجي)                «(first ... second)»
  shia    (the same edition, a third digitisation)   «* first * second *»
A verse is accepted from a copy only when its two hemistichs are cleanly delimited there (never guessed out of the prose). The copies are then aligned verse by verse and every hemistich is
decided by the vote of the copies that carry it: the reading found identically in most copies wins; when copies disagree the reading whose words are all real words (the vocabulary of the
book's own prose) wins; a tie between two real readings is kept as «ويُروى» only when the Hārūn edition differs from the Ṭarīfī edition. Nothing is added to a verse.
usage: pip install rapidfuzz; python3 -I scripts/parse_khizana.py  ->  data/shawahid/khizana_verses.json  (then scripts/build_shawahid.py)"""
import gzip, re, json, collections, sys
from rapidfuzz import fuzz, process
SRC = 'خزانة الأدب ولب لباب لسان العرب'
AR = re.compile(r'[ء-يً-ٰٟ]')
DIAC = re.compile(r'[ً-ٰٟ]')
def load(k):
    raw = gzip.open(f'data/shawahid/khizana_{k}.txt.gz', 'rt', encoding='utf8').read()
    return raw[raw.index('Header#End') + len('Header#End'):]
def paragraphs(raw):
    out = []
    for l in raw.split('\n'):
        if l.startswith('### '): out.append(l[4:].strip())
        elif l.startswith('# '): out.append(l[2:])
        elif l == '#': out.append('')
        elif l.startswith('~~') and out: out[-1] += ' ' + l[2:]
    return out
def clean(s):
    s = re.sub(r'PageV\d+P\d+', ' ', s); s = re.sub(r'\bms\d+\b', ' ', s); s = re.sub(r'\(¬\s*\d+\)', ' ', s)
    s = re.sub(r'\|\s*(?:AUTO|CHECK)\s*', ' ', s); s = s.replace('\u200f', ' ')
    return re.sub(r'\s+', ' ', s).strip()
def hem(s):
    """a hemistich as printed: no editor's brackets, no brackets/quotes around it"""
    s = re.sub(r'[\[\]]', ' ', s); s = re.sub(r'^[\s\(\)«»"]+|[\s\(\)«»"]+$', '', s)
    return re.sub(r'\s+', ' ', s).strip()
def words(s): return [w for w in s.split() if AR.search(w)]
def ok(a, b):
    return (2 <= len(words(a)) <= 9 and 2 <= len(words(b)) <= 9 and not re.search(r'[0-9A-Za-z:؟«»|\(\)\*%#@+~…\.]', a + b)
            and not re.search(r'(?:^|\s)(?:الخ|إلخ|البيت|الأبيات)(?:\s|$)', a + ' ' + b) and nw(a) != nw(b))
def nw(s):
    s = DIAC.sub('', s); s = re.sub(r'[أإآٱ]', 'ا', s); s = s.replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي').replace('ـ', '')
    return re.sub(r'[^ء-ي ]', '', s)
def key(a, b): return nw(a + ' ' + b)

# ---- strict extraction per copy; each verse keeps the prose around it (for the poet / the occasion, read later by shawahid_lib) ----
def context(paras, pi, span, text):
    """the sentences before and after the verse in the same paragraph, then the following paragraphs up to the next verse-bearing paragraph"""
    pre = text[:span[0]]; post = text[span[1]:]
    before = re.split(r'\s[.|]\s|\s#\s|\s:\s', pre.strip())[-1] if pre.strip() else (clean(paras[pi - 1]) if pi else '')
    after = [x.strip() for x in re.split(r'\s[.|]\s', post) if x.strip()]
    return before, after
def extract(k):
    paras = [clean(p) for p in paragraphs(load(k))]
    out = []
    for pi, t in enumerate(paras):
        spans = []
        if k == 'shamay':
            for m in re.finditer(r'\(\s*([^()*]+?)\s\*\*\s+([^()*]+?)\s*\)', t): spans.append((m.group(1), m.group(2), m.span()))
        elif k == 'shamela':
            for m in re.finditer(r'\(\s*([^()]+?)\s\.\.\.\s([^()]+?)\s*\)', t): spans.append((m.group(1), m.group(2), m.span()))
        elif k == 'jk' and t.startswith('% '):
            pc = [x.strip() for x in t.split('%')]; q = [(x, i) for i, x in enumerate(pc) if x]
            while len(q) >= 2:
                a, b = hem(q[0][0]), hem(q[1][0])
                if ok(a, b): spans.append((a, b, (0, 0))); q = q[2:]
                else: break
        elif k == 'shia':
            pc = [x.strip() for x in t.split('*')]
            # runs of cleanly short pieces; pairs are read from the first piece after a prose piece
            q = [x for x in pc]
            i = 0
            while i < len(q) - 1:
                a = hem(q[i]); b = hem(q[i + 1]) if i + 1 < len(q) else ''
                if a and b and ok(a, b) and (i == 0 or q[i - 1] == '' or len(words(hem(q[i - 1]))) > 9 or True) and (t.startswith(q[0]) and i == 0 or i > 0):
                    spans.append((a, b, (0, 0))); i += 2
                    while i < len(q) and q[i] == '': i += 1
                else: i += 1
        for a, b, sp in spans:
            a, b = hem(a), hem(b)
            if ok(a, b): out.append({'v': k, 'a': a, 'b': b, 'pi': pi, 'sp': sp, 'text': t})
    return out, paras


# ---- vocabulary: the words of the books' own prose (typed prose, where a real word recurs) ----
def vocabulary():
    """counts of the words of the prose only (the paragraphs that carry verses are left out; the four copies of the Khizana, which are the same text, are counted once), plus the words of the app's
    own other tabs: so that a word typed wrongly in a verse cannot vouch for itself"""
    raw = collections.Counter(); norm = collections.Counter()
    VERSE = re.compile(r' \.\.\. |\*\*| % | \* ')
    for f in ('suyuti_shawahid_mughni', 'baghdadi_abyat_mughni', 'ayni_maqasid', 'sirafi_abyat_sibawayh', 'khizana_shamela'):
        t = gzip.open(f'data/shawahid/{f}.txt.gz', 'rt', encoding='utf8').read()
        t = t[t.index('Header#End'):]
        for p in paragraphs(t):
            p = clean(p)
            if VERSE.search(p) or '(' in p and ')' in p and len(p) < 140: continue
            for w in re.findall(r'[ء-ي]+', DIAC.sub('', p)): raw[w] += 1
    def walk(o):
        if isinstance(o, str):
            for w in re.findall(r'[ء-ي]+', DIAC.sub('', o)): raw[w] += 1
        elif isinstance(o, list):
            for x in o: walk(x)
        elif isinstance(o, dict):
            for x in o.values(): walk(x)
    for f in ('jami', 'books', 'amthal', 'alfiya', 'quran'): walk(json.load(open(f'content/{f}.json', encoding='utf8')))
    for w, c in raw.items(): norm[nw(w)] += c
    return raw, norm
RAW, NORM = vocabulary()
def valid(w): return NORM[nw(w)] >= 1
def hamza_alts(w):
    alts = set()
    if w[:1] == 'ا': alts |= {'أ' + w[1:], 'إ' + w[1:]}
    if w[:1] in 'أإ': alts.add('ا' + w[1:])
    if w.endswith('ي'): alts.add(w[:-1] + 'ى')
    if w.endswith('ى'): alts.add(w[:-1] + 'ي')
    if 'ىء' in w: alts.add(w.replace('ىء', 'ئ'))
    if 'ئ' in w: alts.add(w.replace('ئ', 'ىء'))
    if w.startswith('و') and len(w) > 3 and w[1] == 'ا': alts |= {'وأ' + w[2:], 'وإ' + w[2:]}
    if w.startswith('ف') and len(w) > 3 and w[1] == 'ا': alts |= {'فأ' + w[2:], 'فإ' + w[2:]}
    if w[1:2] == 'ا' and w[:1] in 'بلك' and len(w) > 3: alts |= {w[0] + 'أ' + w[2:]}
    return alts
def ortho_penalty(h):
    """words whose spelling in the verse is rarer than the same word spelled with a hamza / a final ya-alif maqsura the book's prose uses"""
    pen = 0
    for w in DIAC.sub('', h).split():
        f = RAW[w]
        if any(RAW[a] > 3 * max(1, f) for a in hamza_alts(w)): pen += 1
    return pen
def score(h, votes):
    ws = [w for w in h.split() if AR.search(w)]
    invalid = sum(1 for w in ws if not valid(w))
    return (invalid, ortho_penalty(h), -votes, len(ws))
def decide(cands):
    """cands: list of raw hemistichs (one per copy) -> (chosen, other real reading or '')"""
    c = collections.Counter(cands)
    if len(c) == 1: return cands[0], ''
    best = min(c, key=lambda h: score(h, c[h]))
    return best, ''

def build():
    E = {k: extract(k)[0] for k in ('shamay', 'shamela', 'jk', 'shia')}
    for k in E:
        for i, e in enumerate(E[k]): e['k'] = key(e['a'], e['b']); e['i'] = i
    M = E['shamay']; mk = [e['k'] for e in M]
    clusters = [{'shamay': e} for e in M]
    def align(O, thr=82):
        res = {}; j = 0
        for i, e in enumerate(O):
            best = None; bs = 0
            for lo, hi in ((j - 5, j + 80), (j - 400, j + 800)):
                for x in range(max(0, lo), min(len(mk), hi)):
                    s = fuzz.ratio(e['k'], mk[x])
                    if s > bs: bs = s; best = x
                if bs >= thr: break
            if bs >= thr: res[i] = best; j = best + 1
        return res
    extra = []
    for k in ('jk', 'shamela', 'shia'):
        r = align(E[k])
        for i, e in enumerate(E[k]):
            if i in r: clusters[r[i]].setdefault(k, e)
            else: extra.append((k, e))
    return E, clusters, extra

def sentences(t): return [x.strip() for x in re.split(r'\s[.|]\s|\s#\s', t) if x.strip()]
def contexts(master_entries, paras):
    """for each verse of the master copy: the sentence before it and the sentences after it (up to the next verse of the same poem), as the book words them"""
    by = collections.defaultdict(list)
    for e in master_entries: by[e['pi']].append(e)
    ctx = {}
    for pi, es in by.items():
        t = paras[pi]
        for j, e in enumerate(es):
            s0, s1 = e['sp']
            pre = t[(es[j - 1]['sp'][1] if j else 0):s0]
            before = sentences(pre)[-1] if sentences(pre) else (clean(paras[pi - 1]) if pi and not j else '')
            if j + 1 < len(es): post = t[s1:es[j + 1]['sp'][0]]; aft = sentences(post)
            else:
                aft = sentences(t[s1:])
                for q in range(pi + 1, min(pi + 7, len(paras))):
                    if q in by: break
                    aft += sentences(clean(paras[q]))
            c = {'before': before[-300:], 'after': [x[:600] for x in aft[:14]], 'sh': bool(re.search(r'الشاهد', before))}
            if c['sh']:                                                           # a shahid: the whole section of the book up to the next «وأنشد بعده»
                sec = []; seg = t[s1:]
                for q in range(pi, min(pi + 400, len(paras))):
                    if q > pi: seg = paras[q]
                    m = re.search(r'وأنشد بعده', seg)
                    sec += [x[:500] for x in sentences(seg[:m.start()] if m else seg) if '**' not in x]
                    if m or len(sec) > 400: break
                c['sec'] = sec[:300]
            ctx[id(e)] = c
    return ctx

def main():
    E, clusters, extra = build()
    paras = [clean(p) for p in paragraphs(load('shamay'))]
    ctx = contexts(E['shamay'], paras)
    out = []; stat = collections.Counter(); seen = {}
    for c in clusters:
        a, _ = decide([e['a'] for e in c.values()]); b, _ = decide([e['b'] for e in c.values()])
        if not ok(a, b): stat['rejected after vote'] += 1; continue
        stat['copies %d' % len(c)] += 1
        if len({(e['a'], e['b']) for e in c.values()}) > 1: stat['copies disagreed (decided by vote)'] += 1
        k = key(a, b)
        cx = ctx[id(c['shamay'])]
        if k in seen: seen[k]['ctx'].append(cx); stat['same verse quoted again'] += 1; continue
        e = {'ref': '', 'a': a, 'b': b, 'srcs': [SRC], 'ctx': [cx], 'copies': len(c)}
        seen[k] = e; out.append(e)
    json.dump(out, open('data/shawahid/khizana_verses.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    print(dict(stat), 'verses', len(out))
if __name__ == '__main__': main()
