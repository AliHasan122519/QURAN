"""Build the tab «النظم» (id alfiya): «الألفية الوردية في تعبير الرؤيا» (ابن الوردي) from the hand-read pages data/alfiya/pNNN.txt,
plus «العبير في التعبير» (النابلسي) from data/nazm/abir.txt (verses 1-103 of the Shamela edition; see NAZM_NOTES.md).
Each page file: lines  `N|first hemistich|second hemistich`  (N = the verse number printed in the book) and `#heading` lines (chapter titles).
Consecutive heading lines form one chapter title. Output: content/alfiya.json  {h: [[number, page, chapter, hemistich1, hemistich2], ...]}
Checks: verse numbers are FIRST..N without gaps or repeats, every verse has two hemistichs."""
import glob, json, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
ALF, ABIR, ABIR_BASE = 'الألفية الوردية', 'العبير في التعبير', 2000   # row ids: alfiya:N (N = printed verse number); العبير: alfiya:2000+verse (ids must stay unique and stable)
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
        rows.append([n, page, chap, a, b, ALF, n]); prev = n
n_alf = len(rows)
# العبير في التعبير: lines  N|first|second  and #chapter headings (verses 1-103 only — the rest of the poem is not available as text, see NAZM_NOTES.md)
chap, prev = '', 0
for l in open('data/nazm/abir.txt', encoding='utf8').read().split('\n'):
    l = l.strip()
    if not l: continue
    if l.startswith('#'): chap = l[1:].strip(); continue
    n, a, b = l.split('|'); n = int(n)
    if n != prev + 1: sys.exit(f'abir verse number gap/repeat at {n}')
    a, b = re.sub(r'\s+', ' ', a).strip(), re.sub(r'\s+', ' ', b).strip()
    if not a or not b or '?' in a + b: sys.exit(f'bad hemistich in abir verse {n}')
    rows.append([ABIR_BASE + n, 0, chap, a, b, ABIR, n]); prev = n
CL.publish('alfiya', 'النظم', 'poem', {'h': rows}, len(rows))
m = json.load(open('data/meta.json')); m['alfiya_verses'] = n_alf; m['alfiya_pages'] = [rows[0][1], rows[n_alf - 1][1]]; m['abir_verses'] = len(rows) - n_alf
json.dump(m, open('data/meta.json', 'w'), ensure_ascii=False)
print('nazm rows', len(rows), '(alfiya', n_alf, '+ abir', len(rows) - n_alf, ') chapters', len({r[2] for r in rows}), 'pages', rows[0][1], '-', rows[n_alf - 1][1])
