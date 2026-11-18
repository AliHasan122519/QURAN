"""Build line-level training data for fine-tuning Tesseract on the typeface of al-Jami' al-Saghir, from the hand-verified pages (data/manual).
For every verified page: OCR it once (word boxes), align the OCR words with my transcription (anchors = identical words), and for each physical line
crop the image between its first and last anchored word; the label is my transcription between the same two words. Tashkeel is NOT in the labels,
so the fine-tuned model learns to ignore it.  usage: python3 -I scripts/make_train_data.py OUT_DIR PAGES_RENDER_DIR [held-out pages comma list] [shard i/n]"""
import sys, os, re, glob, subprocess, difflib, csv, io
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ocr_lib as L
out, rend = sys.argv[1], sys.argv[2]; held = set(int(x) for x in (sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else []))
shard = tuple(int(x) for x in sys.argv[4].split('/')) if len(sys.argv) > 4 else (0, 1)
PDF = 'public/assets/al-jami-al-saghir.pdf'
os.makedirs(out + '/train', exist_ok=True); os.makedirs(out + '/eval', exist_ok=True)
def gt_tokens(page):
    """tokens of the verified page text + {token index of an entry's first word: entry number}"""
    toks, starts = [], {}
    for line in open(f'data/manual/p{page:03d}.txt', encoding='utf8').read().split('\n'):
        if not line.strip() or line.startswith('#') or '|' not in line: continue
        head, body = line.split('|', 1)
        if head.strip().isdigit(): starts[len(toks)] = int(head.strip())
        toks += body.split()
    return toks, starts
key = lambda w: L.unify(''.join(L.LETTERS.findall(L.strip_tashkeel(w))))
n_lines = {'train': 0, 'eval': 0}
for f in sorted(glob.glob('data/manual/p*.txt')):
    page = int(re.search(r'p(\d+)', f).group(1)); split = 'eval' if page in held else 'train'
    if page % shard[1] != shard[0] or page < int(os.environ.get('MINPAGE', '0')): continue
    img_path = f'{rend}/n{page}-{page:03d}.png'
    if not os.path.exists(img_path): subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '300', '-gray', '-png', PDF, f'{rend}/n{page}'])
    if not os.path.exists(img_path): continue
    tsv = subprocess.run(['tesseract', img_path, '-', '-l', 'ara', '--psm', '6', 'tsv'], capture_output=True, text=True).stdout
    rows = list(csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE))
    words = [r for r in rows if r['level'] == '5' and key(r['text'])]
    G, STARTS = gt_tokens(page); gk = [key(t) for t in G]; ok = [key(r['text']) for r in words]
    sm = difflib.SequenceMatcher(None, gk, ok, autojunk=False); anchor = {}          # ocr word idx -> gt idx
    for a, b, size in sm.get_matching_blocks():
        for k in range(size): anchor[b + k] = a + k
    im = Image.open(img_path).convert('L'); lines = {}
    for i, r in enumerate(words): lines.setdefault((r['block_num'], r['par_num'], r['line_num']), []).append(i)
    for li, idxs in enumerate(lines.values()):
        anc = [i for i in idxs if i in anchor]
        if len(anc) < 3: continue
        x1 = min(int(words[i]['left']) for i in anc); x2 = max(int(words[i]['left']) + int(words[i]['width']) for i in anc)
        y1 = min(int(words[i]['top']) for i in idxs); y2 = max(int(words[i]['top']) + int(words[i]['height']) for i in idxs)
        g0, g1 = min(anchor[i] for i in anc), max(anchor[i] for i in anc)
        text = ' '.join(G[g0:g1 + 1])
        if g1 - g0 + 1 > 2 * len(anc) + 2: continue                      # alignment looks inconsistent
        if g0 in STARTS: text = f'{STARTS[g0]} - ' + text               # entry-first line: the printed number is part of the line image and of the label
        elif any((g0 - k) in STARTS for k in (1, 2, 3)): continue        # the number is on this line but its words were not anchored: ambiguous, skip
        pad = 10; RPAD = 150      # the crop always extends 150 px to the right so that the entry number (printed at the right margin) is inside it
        crop = im.crop((max(0, x1 - pad), max(0, y1 - pad), min(im.width, x2 + RPAD), min(im.height, y2 + pad)))
        if crop.width < 120 or len(text) < 8: continue
        base = f'{out}/{split}/p{page:03d}_l{li:02d}'; crop.save(base + '.png')
        open(base + '.gt.txt', 'w', encoding='utf8').write(text + '\n'); n_lines[split] += 1
print('lines:', n_lines, 'held-out pages:', sorted(held))
