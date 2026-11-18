"""Build the data of «الألفية الوردية في تعبير الرؤيا» (ابن الوردي) from the hand-read pages data/alfiya/pNNN.txt.
Each page file: lines  `N|first hemistich|second hemistich`  (N = the verse number printed in the book) and `#heading` lines (chapter titles).
Consecutive heading lines form one chapter title. Output: content/alfiya.json  {h: [[number, page, chapter, hemistich1, hemistich2], ...]}
Checks: verse numbers are FIRST..N without gaps or repeats, every verse has two hemistichs."""
import glob, json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
FIRST = 20            # first verse of the content: «الباب الأول: باب آداب المعبر»
rows, chap, pend, prev = [], '', [], FIRST - 1
def flush():
    global chap, pend
    if pend: chap = ' — '.join(pend); pend = []
for f in sorted(glob.glob('data/alfiya/p*.txt')):
    page = int(re.search(r'p(\d+)\.txt', f).group(1))
    for l in open(f, encoding='utf8').read().split('\n'):
        l = l.strip()
        if not l: continue
        if l.startswith('#'):
            if page == 32: continue            # the invocation line before the first verse is not a chapter title
            pend.append(l[1:].strip()); continue
        flush()
        n, a, b = l.split('|'); n = int(n)
        if n < FIRST: pend = []; continue            # the author's introduction (verses 1-19) is not part of the book's content and is not included
        if n >= 1003 and n <= 1008: chap = 'خاتمة المنظومة'
        chap = chap.replace('وهذا الباب المترجم له مرتب على حروف المعجم — ', '')
        if n != prev + 1: sys.exit(f'verse number gap/repeat at {n} after {prev} ({f})')
        a, b = re.sub(r'\s+', ' ', a).strip(), re.sub(r'\s+', ' ', b).strip()
        if not a or not b: sys.exit(f'empty hemistich in verse {n}')
        rows.append([n, page, chap, a, b]); prev = n
CL.publish('alfiya', 'الألفية الوردية', 'poem', {'h': rows}, len(rows))
m = json.load(open('data/meta.json')); m['alfiya_verses'] = len(rows); m['alfiya_pages'] = [rows[0][1], rows[-1][1]]
json.dump(m, open('data/meta.json', 'w'), ensure_ascii=False)
print('alfiya verses', len(rows), 'chapters', len({r[2] for r in rows}), 'pages', rows[0][1], '-', rows[-1][1])
