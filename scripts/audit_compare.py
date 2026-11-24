"""(AUDIT TOOL — needs the per-page OCR XML of the scan from archive.org, `*_djvu.xml`, downloaded by hand; see AUDIT_NOTES.md)
Compare a book's typed text (content/books/<key>.json, the in-app reader copy) with the
page-ordered OCR text of its scan.  Per typed page: where it sits in the OCR (diagonal vote on
word bigrams), what fraction of its words are found in order in that OCR window (difflib on
words), and the same on letters for the pages that look poor.
usage: python3 -I scripts/audit_compare.py key out.json scan1_djvu.xml [scan2_djvu.xml ...]"""
import sys, json, re, collections, difflib, unicodedata

DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def norm(s):
    s = DIAC.sub('', s)
    s = re.sub('[إأآٱ]', 'ا', s).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')
    s = re.sub(r'[^ء-ي ]', ' ', s)
    return s.split()

def pages_of(key, chunk=260):
    d = json.load(open(f'/home/user/quran/content/books/{key}.json', encoding='utf8'))
    p, pg = d['p'], d['pg']
    units = []
    if len(pg) >= 60:
        idx = [i for i, _ in pg] + [len(p)]
        cur_label, cur = None, []
        for k, (i, lab) in enumerate(pg):
            toks = norm(' '.join(p[i:idx[k + 1]]))
            units.append((lab, toks))
        # the text before the first marker
        if pg[0][0] > 0:
            units.insert(0, ('قبل ' + pg[0][1], norm(' '.join(p[:pg[0][0]]))))
        # merge tiny pages into the next so a 10-word page is not judged alone
        out, buf, blab = [], [], None
        for lab, t in units:
            if blab is None: blab = lab
            buf += t
            if len(buf) >= 40:
                out.append((blab if blab == lab else blab + '…' + lab, buf)); buf, blab = [], None
        if buf: out.append((blab, buf))
        return out
    toks = norm(' '.join(p))
    return [(f'مقطع {n // chunk + 1}', toks[n:n + chunk]) for n in range(0, len(toks), chunk)]

def main():
    key, out, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    ocr = []; leaf = []   # leaf[i] = (file number, leaf index) of token i
    for fn, f in enumerate(files):
        x = open(f, encoding='utf8').read()
        for li, ob in enumerate(re.findall(r'<OBJECT.*?</OBJECT>', x, re.S)):
            ws = re.findall(r'<WORD[^>]*>(.*?)</WORD>', ob, re.S)
            tk = norm(' '.join(ws)); ocr += tk; leaf += [(fn, li)] * len(tk)
    index = collections.defaultdict(list)
    for i in range(len(ocr) - 1): index[(ocr[i], ocr[i + 1])].append(i)
    res, prev = [], 0
    pages = pages_of(key)
    # letters-only view of the OCR (words in it may be glued or split): 6-gram index
    OS = ''.join(ocr); G = 6
    gidx = collections.defaultdict(list)
    for i in range(len(OS) - G + 1): gidx[OS[i:i + G]].append(i)
    for lab, t in pages:
        votes = collections.Counter()
        for i in range(len(t) - 1):
            ps = index.get((t[i], t[i + 1]))
            if ps and len(ps) <= 6:
                for q in ps: votes[(q - i) // 25] += 1
        P = ''.join(t)
        gv = collections.Counter()
        for i in range(0, len(P) - G + 1):
            ps = gidx.get(P[i:i + G])
            if ps and len(ps) <= 8:
                for q in ps: gv[(q - i) // 120] += 1
        g6 = 0.0; gat = None
        if gv:
            gb, _ = gv.most_common(1)[0]
            lo_c = max(0, gb * 120 - 300); hi_c = min(len(OS), gb * 120 + len(P) + 420)
            win_c = OS[lo_c:hi_c]
            ws = {win_c[i:i + G] for i in range(len(win_c) - G + 1)}
            tot = max(1, len(P) - G + 1)
            g6 = round(sum(P[i:i + G] in ws for i in range(tot)) / tot, 3); gat = lo_c
        if not votes:
            res.append(dict(label=lab, n=len(t), at=None, cov=0.0, votes=0, g6=g6, gat=gat, first=' '.join(t[:8]))); continue
        b, v = votes.most_common(1)[0]
        v += votes.get(b - 1, 0) + votes.get(b + 1, 0)
        lo = max(0, b * 25 - 40); hi = min(len(ocr), b * 25 + len(t) + 65)
        win = ocr[lo:hi]
        sm = difflib.SequenceMatcher(None, t, win, autojunk=False)
        m = sum(x.size for x in sm.get_matching_blocks())
        blocks = [x for x in sm.get_matching_blocks() if x.size]
        at = lo + (blocks[0].b if blocks else 0)
        lf = leaf[min(at, len(leaf) - 1)]
        res.append(dict(label=lab, n=len(t), at=at, leaf=lf, cov=round(m / len(t), 3), votes=v, g6=g6, gat=gat,
                        first=' '.join(t[:8]), ocr=' '.join(win[blocks[0].b:blocks[0].b + 8]) if blocks else ''))
    json.dump(dict(key=key, ocrtokens=len(ocr), pages=res), open(out, 'w'), ensure_ascii=False)
    cov = sorted(r['cov'] for r in res)
    q = lambda f: cov[int(f * (len(cov) - 1))]
    g = sorted(r['g6'] for r in res); qg = lambda f: g[int(f * (len(g) - 1))]
    print(f'   g6 quantiles 5%={qg(.05)} 25%={qg(.25)} 50%={qg(.5)}  <0.3: {sum(c < .3 for c in g)}  <0.5: {sum(c < .5 for c in g)}')
    print(f'{key}: pages {len(res)}  cov quantiles 5%={q(.05)} 25%={q(.25)} 50%={q(.5)} 75%={q(.75)}  <0.3: {sum(c < .3 for c in cov)}  <0.5: {sum(c < .5 for c in cov)}')

main()
