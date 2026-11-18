"""Measure OCR variants against the hand-read reference pages (data/ground_truth/pNNN.txt). usage: python3 -I scripts/ocr_eval.py [ext_dir]"""
import re, glob, os, difflib, sys, itertools
sys.path.insert(0, 'scripts'); import ocr_lib as L
EXT = sys.argv[1] if len(sys.argv) > 1 else None
def toks(t): return L.LETTERS.findall(L.strip_tashkeel(t))
def acc(gt, ocr, norm):
    f = L.unify if norm else (lambda x: x)
    sm = difflib.SequenceMatcher(None, [f(w) for w in gt], [f(w) for w in ocr], autojunk=False); return sum(b.size for b in sm.get_matching_blocks()), len(gt)
pages = {int(re.search(r'p(\d+)', f).group(1)): open(f, encoding='utf8').read() for f in glob.glob('data/manual/p*.txt')}   # the hand-verified pages are the reference
pages = {p: '\n'.join(l for l in t.split('\n') if '|' in l and not l.startswith('+')) for p, t in pages.items()}
def rd(folder, p): return open(f'{folder}/{p:04d}.txt', encoding='utf8').read()
SRC = {'ocr500': 'data/ocr_500', 'best300': 'data/ocr_best', 'fast300': 'data/ocr', 'b400': 'data/ocr_b400', 'f600p4': 'data/ocr_f600p4'}
if EXT:
    for d in sorted(glob.glob(EXT + '/*/')): SRC[os.path.basename(d.rstrip('/'))] = d.rstrip('/')
def score(names, primary):
    tot = {False: [0, 0], True: [0, 0]}
    for p, g in pages.items():
        gt = toks(' '.join(l.split('|', 1)[1] for l in g.strip().split('\n')))
        txt = L.process(rd(SRC[primary], p), [rd(SRC[n], p) for n in names if n != primary])
        for norm in (False, True):
            h, n = acc(gt, toks(txt), norm); tot[norm][0] += h; tot[norm][1] += n
    return tot[False][0] / tot[False][1], tot[True][0] / tot[True][1], tot[True][1]
if __name__ == '__main__':
    print('reference pages:', len(pages), 'words:', score(['ocr500'], 'ocr500')[2])
    for n in SRC: e, sr, _ = score([n], n); print(f'single {n:9} exact {e:.3f}  search {sr:.3f}')
    allr = list(SRC); e, sr, _ = score(allr, 'ocr500'); print(f'vote of {len(allr)} readings   exact {e:.3f}  search {sr:.3f}')
    import json; json.dump({'pages': len(pages), 'words': score(['ocr500'], 'ocr500')[2], 'single': {n: dict(zip(('exact', 'search'), score([n], n)[:2])) for n in SRC}, 'vote_all': {'exact': e, 'search': sr}}, open('data/ocr_eval_result.json', 'w'), indent=1)
