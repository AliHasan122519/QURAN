"""Third pass over data/raw/jami_parsed.json: checks every entry against the digital text of the same book (see scripts/ref_fix.py).
 - the printed number is confirmed or repaired by the text itself;
 - misread words of machine-read entries are replaced by the digital text's words (hand-verified entries: only unreadable words);
 - the exact end of the hadith text is set: names left inside it move to the takhrij, words that fell into the takhrij move back.
usage: python3 -I scripts/refine_with_reference.py"""
import json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_fix as R, jami_decode as J
rows = json.load(open('data/raw/jami_parsed.json', encoding='utf8'))
ref = json.load(open('data/ref/jamic_saghir.json', encoding='utf8'))
F = R.RefFixer(ref, [r['t'] for r in rows if r.get('verified')])
def decode_k(k):
    syms, grade = [], ''
    for m in J.paren_re.finditer(k):
        toks = [J.SYM_FIX.get(t, t) for t in m.group(1).split()]
        if toks and all(t in J.SYMBOLS or t in ('4', '3') for t in toks) and not syms: syms = toks
    gm = re.search(r'\(\s*(صح|ح|ض)\s*\)\s*\.?\s*$', k)
    if gm: grade = gm.group(1)
    return syms, grade
import difflib
st = collections.Counter(); used = collections.Counter()
def apply(r, nn, toks, min_ratio):
    """correct entry r with the digital text of hadith nn; returns True when it was applied"""
    out = F.fix(toks, nn, policy='ref', visual=True, verified=bool(r.get('verified')))
    if out is None or out[2]['ratio'] < min_ratio: return False
    matn, tail, info = out
    st['checked'] += 1; used[nn] += 1
    old_t = r['t']; new_t = ' '.join(matn); new_k = ' '.join(toks[info['cut']:])
    if new_t != old_t or new_k != r['k']:
        if len(new_t.split()) != len(old_t.split()) or new_k != r['k']: st['boundary_moved'] += 1
        if info['changes']: st['words_changed_entries'] += 1; st['words_changed'] += len(info['changes'])
        r['t'], r['k'] = new_t, new_k; r['sym'], r['g'] = decode_k(new_k) if new_k else ([], '')
        r['flags'] = r.get('flags', []) + ['ref_checked']; st['entries_changed'] += 1
    r['ref_ratio'] = round(info['ratio'], 3); return True
# Numbers by a global alignment: the entries are in book order and so are the numbers of the digital text, so the entries are matched to the digital hadith
# by the best order-preserving assignment (dynamic programming over the whole book), not one at a time. This repairs numbers that drifted by many places.
import numpy as np
NR = 10031; BAND = 260; MIN_SIM = 0.30
rk = [set(R.L(t) for t in r['t'].split() if R.L(t)) for r in rows]
refk = {m: set(R.L(t) for t in toks if R.L(t)) for m, toks in F.ref.items()}
def dice(a, b):
    if not a or not b: return 0.0
    return 2 * len(a & b) / (len(a) + len(b))
NEG = -1e12; dp = np.full(NR + 1, NEG); dp[0] = 0.0; idx = np.arange(NR + 1)
matched = []                                                       # per row: {ref number: predecessor} for the cells where the row was matched
est = 0
for i, r in enumerate(rows):
    c = r.get('n') or (est + 1); est = c
    lo, hi = max(1, c - BAND), min(NR, c + BAND)
    pm = np.maximum.accumulate(dp); ai = np.maximum.accumulate(np.where(dp >= pm, idx, -1))
    new = dp.copy(); mt = {}
    if rk[i]:
        for j in range(lo, hi + 1):
            if j not in refk: continue
            sim = dice(rk[i], refk[j])
            if sim < MIN_SIM: continue
            v = pm[j - 1] + sim - 0.25
            if v > new[j]: new[j] = v; mt[j] = int(ai[j - 1])
    matched.append(mt); dp = new
state = int(np.argmax(dp)); assign = {}
for i in range(len(rows) - 1, -1, -1):
    if state in matched[i]: assign[i] = state; state = matched[i][state]
print('entries matched by the global alignment:', len(assign), 'of', len(rows))
def best_by_content(i, center, window=150):
    keys = [R.L(t) for t in (rows[i]['t'] + ' ' + rows[i]['k']).split()]; cands = sorted(((dice(rk[i], refk[m]), m) for m in range(max(1, center - window), min(NR, center + window) + 1) if m in refk), reverse=True)[:3]
    best, bs = None, 0.0
    for _, m in cands:
        sc = difflib.SequenceMatcher(None, keys, [R.L(t) for t in F.ref[m]], autojunk=False).ratio()
        if sc > bs: best, bs = m, sc
    return best, bs
for i, r in enumerate(rows):
    toks = (r['t'] + ' ' + r['k']).split(); n_old = r.get('n')
    if not toks: continue
    if r.get('verified') and n_old:                                  # a hand-verified page: its printed number is certain; only unreadable words and the end of the text are checked
        if not apply(r, n_old, toks, 0.3): st['verified_no_match'] += 1
    elif i in assign and (not n_old or abs(assign[i] - n_old) <= 3):
        nn = assign[i]                                              # the number follows the digital text: the printed sequence had drifted by a place or two
        if nn != n_old: st['number_set' if not n_old else 'number_repaired'] += 1; r['flags'] = r.get('flags', []) + ['number_from_reference']; r['n'] = nn
        apply(r, nn, toks, 0.0)
    elif n_old:                                                     # the digital text has this part in another order: keep the printed number, match the words by content
        m, sc = best_by_content(i, n_old)
        if m is not None and sc >= 0.45 and apply(r, m, toks, 0.0): st['matched_other_order'] += 1; r['flags'] = r.get('flags', []) + ['reference_other_order']
        else: st['no_match'] += 1; r['flags'] = r.get('flags', []) + ['not_in_reference']
    else: st['no_match'] += 1; r['flags'] = r.get('flags', []) + ['not_in_reference']
# a hadith that the page reading split in two entries (the second half starts a new line): the two halves together match the digital text better than the first alone
def ratio_of(tokens, m):
    return difflib.SequenceMatcher(None, [R.L(t) for t in tokens], [R.L(t) for t in F.ref[m]], autojunk=False).ratio()
merged = 0
for i in range(len(rows) - 1):
    a, b = rows[i], rows[i + 1]
    if a.get('_gone') or b.get('_gone') or not a.get('n') or a['n'] not in F.ref or a.get('verified') or b.get('verified'): continue
    if not ('not_in_reference' in b.get('flags', []) or b.get('n') == a['n']): continue
    ta = (a['t'] + ' ' + a['k']).split(); tb = (b['t'] + ' ' + b['k']).split()
    if not tb or len(tb) > 40: continue
    base = ratio_of(a['t'].split(), a['n']); both = ratio_of((a['t'] + ' ' + b['t']).split(), a['n'])
    if both >= base + 0.04 and both >= 0.6:
        a['t'] = a['t'] + ' ' + b['t']; a['k'] = (b['k'] if b['k'] else a['k']); a['sym'], a['g'] = decode_k(a['k']) if a['k'] else ([], '')
        toks = (a['t'] + ' ' + a['k']).split(); apply(a, a['n'], toks, 0.0)
        a['flags'] = a.get('flags', []) + ['joined_halves']; b['_gone'] = True; merged += 1
rows = [r for r in rows if not r.get('_gone')]
print('entries that were the second half of a hadith and are joined to the first:', merged)
# entries that match nothing and look like noise (a chapter heading or a smear read as text) are not hadith
AR_WORD = re.compile(r'^[\u0621-\u064A\u064B-\u065F\u0670]{2,}[،,.؛:؟!»«"()\-]*$')
for r in rows:
    if r.get('verified') or 'not_in_reference' not in r.get('flags', []): continue
    tk = r['t'].split(); good = sum(1 for t in tk if AR_WORD.match(t))
    if not r['k'] and (len(tk) <= 3 or (tk and good / len(tk) < 0.7) or r.get('cov', 1) < 0.6 or re.search(r'حر[فق]\s', r['t']) and len(tk) <= 5): r['flags'].append('noise_by_reference'); st['noise'] += 1
# two entries with one number: the better match keeps it, the other takes the free neighbouring number
by = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r.get('n') and 'noise_by_reference' not in r['flags']: by[r['n']].append(i)
used_n = {r['n'] for r in rows if r.get('n') and 'noise_by_reference' not in r['flags']}
for n, idxs in sorted(by.items()):
    if len(idxs) < 2: continue
    idxs.sort(key=lambda i: -rows[i].get('ref_ratio', 0)); keep = idxs[0]
    for i in idxs[1:]:
        cand = n - 1 if i < keep else n + 1
        prevn = max([rows[j]['n'] for j in range(i) if rows[j].get('n') and 'noise_by_reference' not in rows[j]['flags']] or [0])
        nextn = min([rows[j]['n'] for j in range(i + 1, len(rows)) if rows[j].get('n') and 'noise_by_reference' not in rows[j]['flags']] or [10032])
        if not rows[i].get('verified') and cand not in used_n and prevn < cand < nextn:
            rows[i]['n'] = cand; used_n.add(cand); rows[i]['flags'] = rows[i].get('flags', []) + ['number_from_sequence']; st['dedup'] += 1
# the numbers of the entries must increase with the book: a repeated or backward number is repaired from its neighbours
fixed_seq = 0; last = 0
for i, r in enumerate(rows):
    n = r.get('n')
    if not n: continue
    if n <= last:
        nxt = next((rows[j]['n'] for j in range(i + 1, len(rows)) if rows[j].get('n')), 10032)
        if last + 1 < nxt and not r.get('verified'): r['n'] = last + 1; r['flags'] = r.get('flags', []) + ['number_from_sequence']; fixed_seq += 1
    last = max(last, r.get('n') or 0)
print('numbers repaired from the sequence:', fixed_seq)
# last resolution for a number that two entries still share: (1) both are halves of one hadith -> joined and corrected by the digital text;
# (2) otherwise a second entry that has no takhrij of its own (nothing but a smear or a stray fragment) is dropped
grp = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r.get('n') and 'noise_by_reference' not in r.get('flags', []): grp[r['n']].append(i)
joined2 = dropped2 = 0
for n, ix in sorted(grp.items()):
    if len(ix) != 2 or n not in F.ref: continue
    a, b = rows[ix[0]], rows[ix[1]]
    if a.get('verified') or b.get('verified'): continue
    both_toks = (a['t'] + ' ' + a['k'] + ' ' + b['t'] + ' ' + b['k']).split()
    out = F.fix(both_toks, n, policy='ref', visual=True)
    one = F.fix((a['t'] + ' ' + a['k']).split(), n, policy='ref', visual=True)
    if out and out[2]['ratio'] >= 0.5 and (one is None or out[2]['ratio'] > one[2]['ratio'] + 0.15):
        if apply(a, n, both_toks, 0.0): a['flags'] = a.get('flags', []) + ['joined_halves']; b['flags'] = b.get('flags', []) + ['noise_by_reference']; joined2 += 1; continue
    weak = b if len(re.findall(r'[\u0621-\u064A]', b['k'])) < 3 else None
    if weak is not None: weak['flags'] = weak.get('flags', []) + ['noise_by_reference']; dropped2 += 1
# one hadith (4533) that the page reading broke in two with a garbled middle: the digital text has it whole, so the matn is taken from it and the takhrij from the second half
for i, r in enumerate(rows):
    if r.get('n') == 4533 and 'noise_by_reference' not in r.get('flags', []) and not r.get('verified') and r['k'].startswith('باب'):
        j = next((x for x in range(i + 1, min(i + 3, len(rows))) if rows[x].get('n') == 4533), None)
        if j is not None and F.ref.get(4533):
            r['t'] = ' '.join(F.ref[4533]); r['k'] = rows[j]['k']; r['sym'], r['g'] = rows[j]['sym'], rows[j]['g']
            r['flags'] = r.get('flags', []) + ['text_from_reference']; rows[j]['flags'] = rows[j].get('flags', []) + ['noise_by_reference']; joined2 += 1
print('numbers shared by two entries: joined', joined2, ', second dropped', dropped2)
# entries the machine reading missed or merged: read by eye from the printed pages (data/jami_manual_fixes.json)
fx = json.load(open('data/jami_manual_fixes.json', encoding='utf8')); fixed_groups = 0
for grp_ in fx['groups']:
    rep = set(grp_['replace']); idx = [i for i, r in enumerate(rows) if r.get('n') in rep and 'noise_by_reference' not in r.get('flags', []) and not r.get('verified')]
    if len(idx) != len(rep): print('manual fix skipped, rows not found for', sorted(rep)); continue
    first = grp_['entries'][0]['n']
    pos = min(idx) if idx else next((i for i, r in enumerate(rows) if (r.get('n') or 0) > first), len(rows))
    base = rows[idx[0]] if idx else rows[max(pos - 1, 0)]
    new = []
    for e in grp_['entries']:
        sy, gr = decode_k(e['k'])
        new.append({'i': base.get('i'), 'top': False, 'page': e['page'], 'letter': base.get('letter', ''), 'mahla': base.get('mahla', True), 'ocr_n': None, 't': e['t'], 'k': e['k'], 'sym': sy, 'g': gr, 'cov': 1.0, 'flags': ['manual_from_image'], 'n': e['n'], 'verified': True})
    rows = [r for i, r in enumerate(rows) if i not in set(idx) and i != pos] if False else rows
    keep = [r for i, r in enumerate(rows) if i not in set(idx)]
    ins = pos - sum(1 for i in idx if i < pos)
    rows = keep[:ins] + new + keep[ins:]; fixed_groups += 1
for n_, k_ in fx['takhrij_only'].items():
    for r in rows:
        if r.get('n') == int(n_) and not r['k']: r['k'] = k_; r['sym'], r['g'] = decode_k(k_); r['flags'] = r.get('flags', []) + ['takhrij_from_image']
for r in rows:
    if not r.get('n') and not r.get('verified'): r['flags'] = r.get('flags', []) + ['noise_by_reference']   # unnumbered and matching nothing
for r in rows:
    if (r.get('n') or 0) > 10031 and not r.get('verified'): r['flags'] = r.get('flags', []) + ['noise_by_reference']   # the author's closing note, not a hadith
print('manual groups applied:', fixed_groups, 'of', len(fx['groups']))
dups = [n for n, c in collections.Counter(r['n'] for r in rows if r.get('n')).items() if c > 1]
print(dict(st)); print('numbers used by more than one entry:', len(dups), dups[:15])
have = {r['n'] for r in rows if r.get('n')}; miss = [n for n in range(1, 10032) if n not in have]
print('hadith numbers 1..10031 without an entry:', len(miss), miss[:30])
json.dump(rows, open('data/raw/jami_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
