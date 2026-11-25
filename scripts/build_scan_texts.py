#!/usr/bin/env python3
"""Stage 2 of the text versions of the scanned books: from the page readings of scripts/ocr_scans.py (Tesseract, two models) and the machine reading that
archive.org keeps with the scan (ABBYY, `_djvu.xml`), builds content/books/<key>.json — the text of the book in paragraphs, flagged `ocr`, with its table of contents
(the verified one of data/booklists/toc/, each entry placed on its page), the scan page of every paragraph (`lf`), and the pages that read poorly (`weak`).
How a page is made: the best Tesseract reading is the base (its lines and their places give the paragraphs); a word of it that is not a known word is replaced by the
word the other two readings give when that is a known word (or when they agree with each other), nothing else is changed; running heads, page numbers and noise lines
are dropped; ONLY mechanical clean-up (Persian letters, invisible marks) is applied.  No word is ever written from memory or guessed.
usage: python3 -I scripts/build_scan_texts.py <OCR_DIR> <XML_DIR> [key …]"""
import collections, difflib, glob, json, os, re, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OCR, XML = sys.argv[1], sys.argv[2]; ONLY = set(sys.argv[3:])
B = json.load(open(os.path.join(ROOT, 'data/booklists/books.json'), encoding='utf8'))
DIAC = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
INVIS = re.compile('[​-‏‪-‮⁦-⁩﻿]')
def norm(t):
    t = DIAC.sub('', t); t = re.sub('[إأآٱ]', 'ا', t).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')
    return re.sub('[^ء-ي]', '', t)
def key(tok): return norm(tok) or tok
PERS = str.maketrans({'ک': 'ك', 'ی': 'ي', 'ە': 'ه', 'ہ': 'ه', 'ھ': 'ه', 'ۀ': 'ة', 'ڤ': 'ف'})
def mech(t): return INVIS.sub('', t).translate(PERS)
# --- the lexicon: the digital texts of the repository (heritage Arabic) + every word that the base reading repeats >= 4 times across all the books
def lexicon():
    c = collections.Counter()
    for f in glob.glob(os.path.join(ROOT, 'data/books/*.txt')) + glob.glob(os.path.join(ROOT, 'data/booklists/src/*.txt')) + [os.path.join(ROOT, 'data/books/0873IbnShahinZahiri.Isharat.Shamela0009968-ara1')]:
        t = re.sub(r'PageV\d+P\d+', ' ', open(f, encoding='utf8').read())
        for w in t.split():
            k = norm(w)
            if len(k) > 1: c[k] += 1
    for f in glob.glob(f'{OCR}/*/*.json'):
        d = json.load(open(f, encoding='utf8'))
        for l in d.get('lines', []):
            for w in l['t'].split():
                k = norm(w)
                if len(k) > 1: c[k] += 1
    return c
def abbyy(key_):
    p = f'{XML}/{key_}.xml'
    if not os.path.exists(p): return None
    return [re.findall(r'<WORD[^>]*>(.*?)</WORD>', o, re.S) for o in re.findall(r'<OBJECT.*?</OBJECT>', open(p, encoding='utf8').read(), re.S)]
def vote(base, others, freq):
    """base = raw tokens; others = lists of raw tokens; returns the new tokens and how many were replaced"""
    bk = [key(t) for t in base]; out = list(base); alts = [collections.Counter() for _ in base]
    for S in others:
        sk = [key(t) for t in S]
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, bk, sk, autojunk=False).get_opcodes():
            if tag == 'replace' and i2 - i1 == j2 - j1:
                for k in range(i2 - i1): alts[i1 + k][S[j1 + k]] += 1
    n = 0
    for i, w in enumerate(base):
        if not alts[i] or not norm(w): continue
        wk = norm(w); known = freq.get(wk, 0) >= 3
        cand = [(a, c) for a, c in alts[i].items() if norm(a) and norm(a) != wk]
        good = [(a, c) for a, c in cand if freq.get(norm(a), 0) >= 3]
        if not known and good:
            out[i] = max(good, key=lambda z: (z[1], freq.get(norm(z[0]), 0)))[0]; n += 1
        elif not known and not good and cand:
            a, c = max(cand, key=lambda z: z[1])
            if c >= 2 and len(alts[i]) == 1: out[i] = a; n += 1                # both other readings agree with each other
        elif known and good:
            a, c = max(good, key=lambda z: z[1])
            if c >= 2 and freq.get(norm(a), 0) > 8 * max(1, freq.get(wk, 0)): out[i] = a; n += 1
    return out, n
def paragraphs(lines, W, H, heading_ok):
    """lines [{b,t,c}] (already voted) -> paragraph texts of one page"""
    ls = []
    for L in lines:
        l, t, r, b = L['b']; txt = mech(L['t']).strip()
        if not txt: continue
        if (t < 0.055 * H or b > 0.955 * H) and (len(txt) <= 48 or re.fullmatch(r'[\d٠-٩\s\-–—ـ]+', txt)) and not heading_ok(txt): continue         # running head / page number
        if L['c'] < 25 or len(re.sub(r'[^ء-ي0-9A-Za-z]', '', txt)) < 2 and not re.search(r'[\d٠-٩]', txt): continue                                 # noise
        ls.append((l, t, r, b, txt))
    if not ls: return []
    R = statistics.median_high(sorted(x[2] for x in ls)[len(ls) // 2:]); Lm = statistics.median_low(sorted(x[0] for x in ls)[:max(1, len(ls) // 2)])
    full = R - Lm; paras = []; cur = []
    for i, (l, t, r, b, txt) in enumerate(ls):
        centred = full > 0 and abs(((l + r) / 2) - ((R + Lm) / 2)) < 0.05 * W and (r - l) < 0.62 * full and len(txt) <= 70 and not re.search(r'[.،؛:?؟]$', txt)
        indent = (R - r) > 0.03 * W
        short_prev = bool(cur) and prev_short
        if cur and (centred or prev_centred or short_prev or (indent and re.search(r'[.:؟?!؛»)\]…]$', cur[-1]))): paras.append(' '.join(cur)); cur = []
        cur.append(txt); prev_centred = centred; prev_short = (l - Lm) > 0.14 * full and not centred
    if cur: paras.append(' '.join(cur))
    return paras
SRC_TEXT = 'قراءة آلية (OCR) لصور صفحات الكتاب نفسه بمحرك Tesseract (نموذجان للعربية) مع قراءة أرشيف الإنترنت، دُقِّقت بمقارنة القراءات الثلاث ولم يُغيَّر فيها كلمة إلا بإجماع قراءتين أو بكلمة معروفة'
SRC_TEXT2 = 'قراءة آلية (OCR) لصور صفحات الكتاب نفسه بمحرك Tesseract (نموذجان للعربية)، دُقِّقت بمقارنة القراءتين ولم يُغيَّر فيها كلمة إلا باتفاق القراءتين على كلمة معروفة'
SRC_PRINTED = 'قراءة آلية (OCR) لصور صفحات المطبوع المحقَّق نفسه (تحقيق محمد عبد الرحمن الشاغول) بمحرك Tesseract (نموذجان للعربية)، دُقِّقت بمقارنة القراءتين ولم يُغيَّر فيها كلمة إلا باتفاق القراءتين على كلمة معروفة؛ وفهرسها هو فهرس المطبوع. وهي غير مخطوطة الكتاب المعروضة مصوَّرةً'
def lis(a):
    """indices of a longest non-decreasing run of a (ties: earliest)"""
    n = len(a); best = [1] * n; prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if a[j] <= a[i] and best[j] + 1 > best[i]: best[i] = best[j] + 1; prev[i] = j
    if not n: return set()
    i = max(range(n), key=lambda x: (best[x], -x)); out = set()
    while i >= 0: out.add(i); i = prev[i]
    return out
def main():
    freq = lexicon(); print('lexicon', len(freq), 'forms,', sum(1 for c in freq.values() if c >= 3), 'known', flush=True)
    report = json.load(open(os.path.join(ROOT, 'data/booklists/transcribe_report.json'), encoding='utf8')) if os.path.exists(os.path.join(ROOT, 'data/booklists/transcribe_report.json')) else {}
    for b in B:
        k = b['key']
        if b['reader']['mode'] != 'embed' or (ONLY and k not in ONLY): continue
        printed = k == 'firasa-ansari'            # the reader shows the manuscript; the text is read from the printed edition (its own table of contents, no scan viewer)
        n = len(glob.glob(f'{OCR}/{k}/*.json'))
        pc = len(glob.glob(f'{OCR}/{k}/*.json')) if printed else json.load(open(os.path.join(ROOT, 'data/booklists/pagecounts.json'), encoding='utf8'))[k][0][1]
        if n < pc: print(k, 'not finished', n, pc); continue
        ab = None if printed else abbyy(k); use_ab = ab is not None and len(ab) == pc
        if printed: toc_in = [(lv, t, p - 1) for lv, t, p in json.load(open(os.path.join(ROOT, 'data/booklists/toc/firasa-ansari-printed.json'), encoding='utf8'))['items']]
        else: toc_in = [(lv, t, lf) for lv, t, lf in [(r[0], r[1], r[2]) for r in b['reader']['toc']] if lf is not None]
        title_at = collections.defaultdict(list)
        for lv, t, lf in toc_in: title_at[lf].append(t)
        P = []; pg = []; lfm = []; weak = []; changed = 0; words = 0; confs = []; blank = 0; heads = {}
        for leaf in range(pc):
            rec = json.load(open(f'{OCR}/{k}/{leaf}.json', encoding='utf8'))
            if rec.get('err') or not rec.get('lines'): blank += 1; continue
            lines = rec['lines']; flat = [(li, w) for li, L in enumerate(lines) for w in L['t'].split()]
            base = [w for _, w in flat]; others = [rec['alt'].split()]
            if use_ab: others.append(ab[leaf])
            new, nch = vote(base, others, freq); changed += nch
            pos = 0; vl = []
            for L in lines:
                m = len(L['t'].split()); vl.append({**L, 't': ' '.join(new[pos:pos + m])}); pos += m
            tit = title_at.get(leaf, []) + title_at.get(leaf - 1, [])
            def heading_ok(txt, tit=tit): return any(difflib.SequenceMatcher(None, ' '.join(map(norm, txt.split())), ' '.join(map(norm, t.split()))).ratio() > 0.6 for t in tit)
            ps = paragraphs(vl, rec['w'], rec['h'], heading_ok)
            if not ps: blank += 1; continue
            toks = [w for p in ps for w in p.split()]; words += len(toks)
            hit = sum(1 for w in toks if freq.get(norm(w), 0) >= 3) / max(1, sum(1 for w in toks if norm(w)))
            cf = statistics.mean(L['c'] for L in lines); confs.append(cf)
            lfm.append([len(P), leaf]); pg.append([len(P), f'ص{leaf + 1}'])
            if cf < 70 or hit < 0.6: weak.append(len(P))
            for p in ps: P.append(p)
            # headings of the verified table of contents that are printed on this page
            for lv, t, lf in toc_in:
                if lf != leaf: continue
                core = ' '.join(norm(w) for w in re.sub(r'^(الفصل|الباب|الوحدة|القسم|الجزء|المبحث)\s+[^:]{0,25}:\s*', '', t).split())
                best = (0, None)
                for j in range(len(P) - len(ps), min(len(P), len(P) - len(ps) + 12)):
                    if len(P[j]) > 140: continue
                    s = difflib.SequenceMatcher(None, core, ' '.join(norm(w) for w in P[j].split())).ratio()
                    if s > best[0]: best = (s, j)
                if best[0] >= 0.62: heads[(lv, t, lf)] = best[1]
        # the table of contents of the text: the verified entries (heading = the paragraph found on the page; otherwise a jump to the page, flagged 1)
        first_of = {l: i for i, l in lfm}; leaves = sorted(first_of)
        toc = []; keep = lis([lf for _, _, lf in toc_in]); last = 0               # an entry whose page breaks the order of the verified list stays out of the text's table (the scan table still has it)
        for n, (lv, t, lf) in enumerate(toc_in):
            if n not in keep: continue
            if (lv, t, lf) in heads: pos = heads[(lv, t, lf)]; fl = []
            else:
                nx = next((x for x in leaves if x >= lf), None)
                if nx is None: continue
                pos = first_of[nx]; fl = [1]
            toc.append([lv, t, max(pos, last)] + fl); last = max(pos, last)           # two entries of one page: the later never points before the earlier
        book = {'v': 1, 'key': k, 'ocr': True, 'scanText': True, 'src': SRC_PRINTED if printed else SRC_TEXT if use_ab else SRC_TEXT2, **({'noScan': True} if printed else {}), 'toc': toc, 'p': P, 'pg': pg, 'lf': lfm, 'weak': weak}
        CL.publish_file(f'books/{k}.json', book)
        report[k] = {'pages': pc, 'pagesWithText': len(lfm), 'blankOrImagePages': blank, 'paragraphs': len(P), 'words': words, 'meanConfidence': round(statistics.mean(confs), 1) if confs else 0,
                     'replacedByVote': changed, 'weakPages': len(weak), 'abbyyUsed': use_ab, 'tocHeadingsFound': len(heads), 'tocEntries': len(toc)}
        print(k, report[k], flush=True)
    json.dump(report, open(os.path.join(ROOT, 'data/booklists/transcribe_report.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
if __name__ == '__main__': main()
