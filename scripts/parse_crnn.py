"""Parse the line-recogniser output (data/ocr_crnn/NNNN.txt, see crnn_ocr.py) of the pages that are NOT verified by hand into entries.
The recogniser reads the printed hadith number of every entry-first line ("2864 - text ...") together with the text, so entries are cut at the lines
that start with a number.  Numbers are then checked against the running sequence (previous number + 1): a number that agrees is kept, an isolated
wrong number is replaced, and a number that cannot be trusted is left out (n = 0) instead of being invented.
usage: python3 -I scripts/parse_crnn.py CRNN_DIR VOCAB_JSON OUT_JSON MANUAL_PAGES_FILE"""
import re, sys, json, os, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jami_decode as J
crnn_dir, vocab_path, out, manual_file = sys.argv[1:5]
manual = set(int(x) for x in open(manual_file).read().split())
vocab = set(json.load(open(vocab_path)))
AR = 'ء-ي'
DIAC = re.compile('[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\u200e\u200f]')
def norm(s):
    s = DIAC.sub('', s)
    return re.sub('[إأآٱ]', 'ا', s).replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي').replace('ة', 'ه')
start_re = re.compile(r'^\s*((?:\d\s*){1,7}?)\s*[-–ـ]\s*(.*)$')
close_re = re.compile(r'\(\s*(?:صح|ح|ض)\s*\)\s*\.?\s*$')
entries, letter, mahla, cur = [], '', False, None
def flush():
    global cur
    if cur: entries.append(cur); cur = None
for pf in sorted(glob.glob(crnn_dir + '/*.txt')):
    page = int(os.path.basename(pf)[:4])
    if page < 7 or page > 591 or page in manual: continue          # pp.1-6: front matter, p.592: index
    first = True
    for raw in open(pf, encoding='utf8').read().split('\n'):
        line = raw.strip()
        if not re.search('[' + AR + ']', line): continue
        if page == 591 and (line.startswith('قال مؤلفه') or line.startswith('بعونه تعالى')): break          # colophon
        n = norm(line)
        if re.match(r'^حرف\s+\S{1,12}$', n) and len(line) < 30 and not start_re.match(line): flush(); letter = line; mahla = False; first = False; continue
        if n.startswith('فصل') and len(line) < 45 and not start_re.match(line): flush(); mahla = True; first = False; continue          # «فصل في المحلى بأل من هذا الحرف» (read with small typos)
        ms = start_re.match(line)
        if ms:
            flush(); cur = {'page': page, 'letter': letter, 'mahla': mahla, 'ocr_n': int(re.sub(r'\s+', '', ms.group(1))), 'lines': [ms.group(2).strip()]}
        elif cur and cur.get('closed') and not line.startswith('('):
            flush(); cur = {'page': page, 'letter': letter, 'mahla': mahla, 'ocr_n': None, 'lines': [line]}      # previous entry is complete: this line starts an entry whose number was not read
        elif cur: cur['lines'].append(line)
        else: cur = {'page': page, 'letter': letter, 'mahla': mahla, 'ocr_n': None, 'lines': [line], 'top': first}
        if cur and close_re.search(line): cur['closed'] = True
        first = False
flush()
merged = []
for e in entries:
    if merged and e['ocr_n'] is None and not merged[-1].get('closed') and e['page'] - merged[-1]['page'] <= 1 and not e.get('top'):
        merged[-1]['lines'] += e['lines']; merged[-1]['closed'] = merged[-1].get('closed') or e.get('closed'); continue
    merged.append(e)
print('merged unnumbered fragments:', len(entries) - len(merged)); entries = merged
quality = lambda toks: sum(1 for t in toks if t in vocab) / max(1, len(toks))
rows = []
for i, e in enumerate(entries):
    text = re.sub(r'\s+', ' ', ' '.join(e['lines'])).strip()
    matn, takhrij, syms, grade = J.decode_text(text)
    toks = re.findall('[' + AR + ']{2,}', norm(matn)); cov = quality(toks); flags = []
    if cov < 0.75: flags.append('low_vocab_coverage')
    if re.search(r'[A-Za-z]', matn): flags.append('latin_noise')
    if len(matn) < 12: flags.append('very_short')
    if not takhrij: flags.append('no_takhrij_detected')
    rows.append({'i': i, 'top': bool(e.get('top')), 'page': e['page'], 'letter': e['letter'], 'mahla': e['mahla'], 'ocr_n': e['ocr_n'], 't': matn, 'k': takhrij, 'sym': syms, 'g': grade, 'cov': round(cov, 2), 'flags': flags})
# ---- numbers ----
# The recogniser reads each printed number, but single digits are sometimes wrong. A read number is accepted only if it equals the running sequence
# (previous number + 1), or is within two digit edits of it, or is 1-3 ahead of it and within one edit of that value (entries skipped).
# Otherwise the entry gets NO number (n = 0): a number is never invented.
last_manual = 0
for f in sorted(glob.glob('data/manual/p*.txt')):
    for l in open(f, encoding='utf8'):
        m = re.match(r'\s*(\d+)\s*\|', l)
        if m: last_manual = max(last_manual, int(m.group(1)))
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]
stat = collections.Counter()
def seq(rs, exp):
    for r in rs:
        n = r['ocr_n']; r['n'], r['n_status'] = 0, 'unsure'
        if exp and n:
            s_n, s_e = str(n), str(exp)
            if n == exp: r['n'], r['n_status'] = exp, 'ok'
            elif ed(s_n, s_e) <= 2 and abs(len(s_n) - len(s_e)) <= 2: r['n'], r['n_status'] = exp, 'ok_fuzzy'
            else:
                for k in (1, 2, 3, -1, -2):
                    if exp + k > 0 and len(s_n) >= 3 and ed(s_n, str(exp + k)) <= 1: r['n'], r['n_status'] = exp + k, 'resync'; r['flags'].append('numbers_skipped_before' if k > 0 else 'numbers_repeated'); break
        elif n and not exp: r['n'], r['n_status'] = n, 'ok'
        if r['n']: exp = r['n'] + 1
        elif exp: exp += 1
        stat[r['n_status']] += 1
    return exp
mx = max(manual or [0])
before = [r for r in rows if r['page'] <= mx]; after = [r for r in rows if r['page'] > mx]
if before: seq(before, None)
LAST_PRINTED = 10031          # the last hadith printed in the book (p.591, read from the page image)
def dp_numbers(rs, first_n, window=90, step=4, change_cost=3.0):
    """Viterbi over the offset o (number = first_n + position + o). Cost: digit-edit distance (capped at 2) between the number the recogniser read and the
    number the offset implies. The offset may change by at most `step` at a time (an entry missed or split) at a price. The first entry is anchored to first_n
    and the last to the last printed number of the book."""
    INF = 1e18; offs = list(range(-window, window + 1)); W = len(offs)
    cost = [INF] * W; back = []; cost[window] = 0.0
    for i, r in enumerate(rs):
        read = str(r['ocr_n']) if r['ocr_n'] else None
        new, bk = [INF] * W, [0] * W
        for k in range(W):
            if i == 0 and k != window: continue
            best, src = cost[k], k
            for dk in range(-step, step + 1):
                if dk == 0 or not (0 <= k + dk < W): continue
                c = cost[k + dk] + change_cost * abs(dk) ** 0.5
                if c < best: best, src = c, k + dk
            if best >= INF: continue
            d = 0.0 if read is None else min(2, ed(read, str(first_n + i + offs[k])))
            new[k], bk[k] = best + d, src
        cost = new; back.append(bk)
    end = [cost[k] + 0.7 * min(40, abs(first_n + len(rs) - 1 + offs[k] - LAST_PRINTED)) for k in range(W)]
    k = end.index(min(end)); path = []
    for i in range(len(rs) - 1, -1, -1): path.append(offs[k]); k = back[i][k]
    path.reverse()
    for i, (r, o) in enumerate(zip(rs, path)):
        r['n'] = first_n + i + o; r['n_status'] = 'sequence'
        if r['ocr_n'] and r['ocr_n'] == r['n']: r['n_status'] = 'ok'
        elif r['ocr_n'] and ed(str(r['ocr_n']), str(r['n'])) > 2: r['n_status'] = 'sequence_unsupported'
        if i and path[i] != path[i - 1]: r['flags'].append('numbers_skipped_before' if path[i] > path[i - 1] else 'numbers_repeated')
    return path
if after and last_manual: dp_numbers(after, last_manual + 1)
elif after: seq(after, None)
for r in after: stat[r['n_status']] += 1

# an entry whose number repeats the previous one is a fragment (a split inside one hadith): join it to the previous entry
out_rows = []
for r in rows:
    if out_rows and r['n'] and out_rows[-1]['n'] == r['n']:
        q = out_rows[-1]; raw = ' '.join(x for x in (q['t'], q['k'], r['t'], r['k']) if x)
        q['t'], q['k'], q['sym'], q['g'] = J.decode_text(raw)[0], J.decode_text(raw)[1], J.decode_text(raw)[2], J.decode_text(raw)[3]
        q['flags'] = sorted(set(q['flags'] + ['joined_fragment'])); continue
    out_rows.append(r)
print('fragments joined:', len(rows) - len(out_rows)); rows = out_rows
json.dump(rows, open(out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('entries', len(rows), 'number status', dict(stat), '| last read number', max([r['n'] for r in rows] or [0]))
print('flag counts', dict(collections.Counter(f for r in rows for f in r['flags'])), '| with symbols', sum(1 for r in rows if r['sym']), '| with grade', sum(1 for r in rows if r['g']))
