"""Measures the digital-text correction on held-out pages: machine-read pages (the model never saw them) whose hand-verified text is known.
Word error rate of the hadith text before and after, per policy. usage: python3 -I scripts/validate_ref_fix.py"""
import sys, os, re, json, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_fix as R, takhrij_split as T, jami_decode as J
ref = json.load(open('data/ref/jamic_saghir.json', encoding='utf8'))
rows = json.load(open('content/jami.json', encoding='utf8'))['h']
def manual_full():
    out = {}
    for f in glob.glob('data/manual/p*.txt'):
        for l in open(f, encoding='utf8'):
            m = re.match(r'\s*(\d+)\s*\|\s*(.*)$', l)
            if m: out[int(m.group(1))] = m.group(2).split()
    return out
MF = manual_full(); gold = {}
pages = {int(os.path.basename(f)[:4]) for f in glob.glob('data/ref/crnn_heldout/*.txt')}
# the correction must not use the held-out pages' hand-verified text for its vocabulary (they are the answer key)
def page_of(n): return next((r[0] for r in rows if r[8] == n), None)
held_nums = {r[8] for r in rows if r[6] == 'v' and r[0] in pages}
book = [r[2] for r in rows if r[6] == 'v' and r[8] not in held_nums]
F = R.RefFixer(ref, book)
# the answer key: the hand-read words of each entry up to the end the digital text gives (names/narrators after it are the takhrij)
import difflib
for n, toks in MF.items():
    B = F.ref.get(n)
    if not B or n not in held_nums: continue
    sm = difflib.SequenceMatcher(None, [R.L(t) for t in toks], [R.L(t) for t in B], autojunk=False); last = None
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if j2 == len(B) and tag in ('equal', 'replace'): last = i2
    gold[n] = [R.strip_p(t) for t in toks[:last if last is not None else len(toks)]]
M = T.Model([(r[2], r[3]) for r in rows if r[5] is not None and r[4]], [(r[2] + ' ' + r[3]).strip() for r in rows])
def lev(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]
ents = []
for f in sorted(glob.glob('data/ref/crnn_heldout/*.txt')):
    cur = None
    for l in open(f, encoding='utf8').read().split('\n'):
        m = re.match(r'^\s*(\d+)\s*-\s*(.*)$', l)
        if m: cur = [int(m.group(1)), m.group(2).strip()]; ents.append(cur)
        elif cur and l.strip(): cur[1] += ' ' + l.strip()
ents = [(n, t) for n, t in ents if n in gold]
print('held-out entries with a hand-verified answer:', len(ents), 'pages', sorted(pages))
def baseline(n, text):
    matn, tak, sym, g = J.decode_text(text); full = (matn + ' ' + tak).strip(); toks = full.split(); b = M.boundary(full, len(matn.split())); return toks[:b]
tot = sum(len(gold[n]) for n, _ in ents); res = {}
res['OCR + old takhrij split'] = sum(lev(baseline(n, t), gold[n]) for n, t in ents)
for name, kw in [('ours', dict(policy='ours')), ('ref (take every digital word)', dict(policy='ref')), ('ref, visual misreadings only', dict(policy='ref', visual=True)),
                 ('ref, visual, inserts<=2', dict(policy='ref', visual=True, ins_max=2)), ('ref, visual, no inserts', dict(policy='ref', visual=True, ins_max=0)),
                 ('score, visual', dict(policy='score', visual=True)), ('score, visual, vmax=2.5', dict(policy='score', visual=True, vmax=2.5)),('ref, visual vmax=2.5', dict(policy='ref', visual=True, vmax=2.5))]:
    err = 0
    for n, t in ents:
        toks = t.split(); nn, sc = F.best_number(n, toks); out = F.fix(toks, nn, **kw)
        err += lev(out[0], gold[n]) if out else lev(baseline(n, t), gold[n])
    res['digital: ' + name] = err
for k, v in res.items(): print(f'{k:48s} word errors {v:5d} / {tot}  = {100 * v / tot:.2f}%')
