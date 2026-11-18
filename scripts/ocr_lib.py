"""OCR post-processing for al-Jami' al-Saghir: (1) tashkeel removal, (2) word-level voting between three OCR readings (ROVER-style),
(3) dictionary-based correction of words that are not valid Arabic words, (4) OCR comma repair. Layout (lines, numbers, dashes) is preserved."""
import re, json, difflib, collections
DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ‎‏]')
AR = 'ء-يٱ'
LETTERS = re.compile('[' + AR + ']+')
def unify(w):
    return re.sub('[إأآٱ]', 'ا', w).replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي').replace('ة', 'ه')
def strip_tashkeel(t): return DIAC.sub('', t).replace('ٱ', 'ا')
_lex = None
def lex():
    global _lex
    if _lex is None: _lex = json.load(open('data/raw/lexicon.json', encoding='utf8'))
    return _lex
ALPHA = 'ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي'
def neighbors(w):
    s = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    out = set()
    for a, b in s:
        if b: out.add(a + b[1:])                                  # deletion
        for c in ALPHA:
            out.add(a + c + b)                                    # insertion
            if b: out.add(a + c + b[1:])                          # substitution
        if len(b) > 1: out.add(a + b[1] + b[0] + b[2:])           # transposition
    out.discard(w); return out
def split_tokens(text):
    """-> lines, list of (line_idx, token_idx, prefix, letters, suffix) for tokens that contain Arabic letters"""
    lines = text.split('\n'); toks = []; words_by_line = []
    for li, line in enumerate(lines):
        ws = line.split(' '); words_by_line.append(ws)
        for ti, w in enumerate(ws):
            m = LETTERS.search(strip_tashkeel(w))
            if m:
                clean = strip_tashkeel(w); a = LETTERS.search(clean); b = None
                # core = maximal letter run; keep surrounding punctuation as is
                toks.append((li, ti, clean[:a.start()], a.group(0), clean[a.end():]))
    return words_by_line, toks
def vote(A, others):
    """A: token list of the primary reading (layout owner); others: token lists of the other readings.
    Plurality vote per word position among all readings (spelling variants compared after unification); ties go to the primary reading."""
    la = [t[3] for t in A]; ua = [unify(w) for w in la]
    maps = []
    for X in others:
        lx = [t[3] for t in X]; m = {}
        sm = difflib.SequenceMatcher(None, ua, [unify(w) for w in lx], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal' or (tag == 'replace' and (i2 - i1) == (j2 - j1)):
                for k in range(i2 - i1): m[i1 + k] = lx[j1 + k]
        maps.append(m)
    L = lex(); out = []
    for i, a in enumerate(la):
        cands = [a] + [m[i] for m in maps if i in m]
        cnt = collections.Counter(unify(c) for c in cands)
        top = max(cnt.values()); leaders = [k for k, v in cnt.items() if v == top]
        if unify(a) in leaders and (len(leaders) == 1 or True): out.append(a); continue
        key = max(leaders, key=lambda k: max(L.get(c, 0) for c in cands if unify(c) == k))
        out.append(max((c for c in cands if unify(c) == key), key=lambda c: L.get(c, 0)))
    return out
def correct_word(w, min_count=25):
    L = lex()
    if len(w) < 3 or w in L: return w
    if w.endswith('ء') and w[:-1] in L and len(w) > 3: return w[:-1] + '،'     # the OCR reads the Arabic comma as a trailing hamza
    best, bc = None, 0
    for n in neighbors(w):
        c = L.get(n, 0)
        if c > bc: best, bc = n, c
    return best if best and bc >= min_count else w
def process(textA, others=(), do_correct=False, min_count=25):
    wa, A = split_tokens(textA)
    letters = vote(A, [split_tokens(t)[1] for t in others]) if others else [t[3] for t in A]
    if do_correct: letters = [correct_word(w, min_count) for w in letters]
    for (li, ti, pre, _, suf), new in zip(A, letters): wa[li][ti] = pre + new + suf
    return '\n'.join(' '.join(ws) for ws in wa)
