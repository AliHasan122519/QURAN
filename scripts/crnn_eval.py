"""Measure the line recogniser (and the Tesseract readings it replaces) on HELD-OUT hand-verified pages: pages that were never used for training.
For every held-out page: word accuracy against the hand-verified text (exact spelling and search-normalised spelling), and how well the printed
hadith numbers / entry starts were read.   usage: python3 -I scripts/crnn_eval.py CRNN_OUT_DIR  (a folder with NNNN.txt for the held-out pages)
Writes data/crnn_eval_result.json."""
import re, sys, glob, os, json, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ocr_lib as L
d = sys.argv[1]
pages = sorted(int(re.search(r'(\d+)\.txt', f).group(1)) for f in glob.glob(d + '/*.txt'))
def toks(t): return L.LETTERS.findall(L.strip_tashkeel(t))
def match(gt, hyp, norm):
    f = L.unify if norm else (lambda x: x)
    sm = difflib.SequenceMatcher(None, [f(w) for w in gt], [f(w) for w in hyp], autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks())
SRC = {'ocr500': 'data/ocr_500', 'best300': 'data/ocr_best', 'fast300': 'data/ocr', 'b400': 'data/ocr_b400', 'f600p4': 'data/ocr_f600p4'}
tot = {k: [0, 0, 0] for k in ('crnn', 'vote5', *SRC)}
num_ok = num_tot = ent_ok = ent_tot = 0
start_re = re.compile(r'^\s*(\d{1,5})\s*[-–ـ]\s*(.*)$')
for p in pages:
    man = open(f'data/manual/p{p:03d}.txt', encoding='utf8').read().split('\n')
    gt_text = ' '.join(l.split('|', 1)[1] for l in man if '|' in l and not l.startswith('+'))
    gt = toks(gt_text); gnums = [int(l.split('|')[0]) for l in man if re.match(r'\s*\d+\s*\|', l)]
    texts = {'crnn': open(f'{d}/{p:04d}.txt', encoding='utf8').read()}
    for k, folder in SRC.items():
        if os.path.exists(f'{folder}/{p:04d}.txt'): texts[k] = open(f'{folder}/{p:04d}.txt', encoding='utf8').read()
    texts['vote5'] = L.process(texts['ocr500'], [texts[k] for k in SRC if k != 'ocr500' and k in texts])
    for k, t in texts.items():
        h = toks(re.sub(r'^\s*\d+\s*[-–ـ]\s*', '', t, flags=re.M)) if k == 'crnn' else toks(t)
        tot[k][0] += match(gt, h, False); tot[k][1] += match(gt, h, True); tot[k][2] += len(gt)
    read = [int(m.group(1)) for m in (start_re.match(l) for l in texts['crnn'].split('\n')) if m]
    num_tot += len(gnums); num_ok += sum(1 for a, b in zip(read, gnums) if a == b) if len(read) == len(gnums) else len(set(read) & set(gnums))
    ent_tot += 1; ent_ok += (len(read) == len(gnums))
res = {'pages': pages, 'words': tot['crnn'][2], 'exact': {k: round(v[0] / v[2], 4) for k, v in tot.items()}, 'search': {k: round(v[1] / v[2], 4) for k, v in tot.items()},
       'numbers': {'printed': num_tot, 'read_correctly': num_ok}, 'pages_with_correct_entry_count': [ent_ok, ent_tot]}
json.dump(res, open('data/crnn_eval_result.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
