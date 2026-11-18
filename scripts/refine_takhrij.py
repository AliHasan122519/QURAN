"""Second pass over data/raw/jami_parsed.json: move author/narrator names that were left INSIDE the hadith text into the takhrij, and split two hadith that were
joined into one entry.  See scripts/takhrij_split.py for how the takhrij is recognised.  usage: python3 -I scripts/refine_takhrij.py"""
import json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import takhrij_split as T, jami_decode as J
rows = json.load(open('data/raw/jami_parsed.json', encoding='utf8'))
texts = [(r['t'] + ' ' + r['k']).strip() for r in rows]
M = T.Model([(r['t'], r['k']) for r in rows if r['sym']], texts)
GRADE = re.compile(r'\(\s*(?:صح|ح|ض)\s*\)$')
def decode_k(k):
    syms, grade = [], ''
    for m in J.paren_re.finditer(k):
        toks = [J.SYM_FIX.get(t, t) for t in m.group(1).split()]
        if toks and all(t in J.SYMBOLS or t in ('4', '3') for t in toks) and not syms: syms = toks
    gm = re.search(r'\(\s*(صح|ح|ض)\s*\)\s*\.?\s*$', k)
    if gm: grade = gm.group(1)
    return syms, grade
stats = collections.Counter(); out = []
used = {r['n'] for r in rows if r.get('n')}
for r, tx in zip(rows, texts):
    toks = tx.split(); old = len(r['t'].split()); new = M.boundary(tx, old)
    parts = [(toks, r)]
    # joined hadith: a complete takhrij (closing grade) followed by more hadith text
    cut = None
    for k in range(len(toks) - 1):
        if GRADE.search(toks[k]) and len(toks) - k - 1 >= 4:
            rest = ' '.join(toks[k + 1:]); b = M.boundary(rest)
            if b >= 4 and not r.get('verified'): cut = k + 1; break
    items = [(toks[:cut], r)] if cut else [(toks, r)]
    if cut:
        stats['split_joined'] += 1
        r2 = dict(r); r2['flags'] = list(r['flags']) + ['split_from_joined']; r2['n'] = (r['n'] + 1) if r.get('n') and (r['n'] + 1) not in used else None
        if r2['n']: used.add(r2['n'])
        items.append((toks[cut:], r2))
    for tk, rr in items:
        tx2 = ' '.join(tk); n_old = old if not cut or rr is r else 0
        b = M.boundary(tx2, old if (rr is r and not cut) else None)
        if rr.get('sym') and rr is r and not cut: b = min(b, old) if b else b           # a symbol group was found: never move the cut later than it
        if b < 2: b = len(tk) if not rr.get('sym') else min(old, len(tk))                # keep at least a couple of words of hadith text
        matn = ' '.join(tk[:b]); k = ' '.join(tk[b:])
        if matn != rr['t']: stats['moved_into_takhrij'] += 1
        rr = dict(rr); rr['t'], rr['k'] = matn, k; rr['sym'], rr['g'] = decode_k(k) if k else ([], ''); out.append(rr)
json.dump(out, open('data/raw/jami_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(dict(stats), '| entries', len(rows), '->', len(out), '| with takhrij', sum(1 for r in out if r['k']), '| with symbols', sum(1 for r in out if r['sym']), '| with grade', sum(1 for r in out if r['g']))
