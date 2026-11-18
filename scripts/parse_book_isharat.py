"""Splits the digital text of «الإشارات في علم العبارات» (data/books/…Shamela0009968-ara1, OpenITI) into one entry per interpretation:
{ref: the section heading (the symbol being interpreted), text: the interpretation as the book words it, why: the reason the book itself gives (verse/hadith/«لأن…»), if any}.
Nothing is added to the text: it is cut at the book's own separators «(ومن رأى)», «وقال فلان:» and cleaned of page/footnote markers.
usage: python3 -I scripts/parse_book_isharat.py   ->  data/books/isharat_parsed.json"""
import re, json, sys
SRC = 'data/books/0873IbnShahinZahiri.Isharat.Shamela0009968-ara1'
lines = open(SRC, encoding='utf8').read().split('\n')
i = next(k for k, l in enumerate(lines) if l.startswith('#META#Header#End#')) + 1
bab = ''; fasl = ''; buf = []; paras = []     # paras: (bab, fasl, text)
def flush():
    global buf
    t = ' '.join(buf).strip()
    if t: paras.append((bab, fasl, t))
    buf = []
expect_title = False
for l in lines[i:]:
    if l.startswith('# PageV') or not l.strip(): continue
    m = re.match(r'^### [|$] ?(?:\d+ - )?\((.*)\)\s*$', l)
    if m or l.startswith('### '):
        flush(); h = (m.group(1) if m else l[4:]).strip()
        if re.match(r'^الباب\b', h): bab_no = h; expect_title = True; fasl = ''; bab = h
        elif expect_title and h.startswith('في'): bab = h; expect_title = False; fasl = ''
        else: fasl = h; expect_title = False
        continue
    if l.startswith('# ') or l.startswith('~~'):
        if l.startswith('# '): flush()
        buf.append(l[2:] if l.startswith('# ') else l[2:])
flush()
def clean(t):
    t = re.sub(r'\bms\d+\b', ' ', t)
    t = re.sub(r'\{((?:ومن|وإن|وان|وقال|قال|وإذا|فإن)[^{}]{0,30})\}', r'(\1)', t)       # the book sometimes brackets its «ومن رأى» separator with braces: not a verse
    t = t.replace('{', '﴿').replace('}', '﴾')
    t = re.sub(r'\s+', ' ', t).strip(); return t
def title(h):
    h = re.sub(r'\bms\d+\b', ' ', h); h = re.sub(r'^[\s$|]*\d*\s*-?\s*\(?', '', h.strip()).rstrip(') ')
    h = re.sub(r'^(فصل\s+)?(في\s+)?', '', h.strip()).strip(' .'); return re.sub(r'\s+', ' ', h)
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from book_lib import split_clauses, unparen
REASON = [
    (re.compile(r'(ل?قوله\s+تعالى\s*:?\s*﴿[^﴾]+﴾(?:\s*الآية)?)'), 'quran'),
    (re.compile(r'(ل?قوله\s+(?:صلى الله عليه وسلم|عليه السلام|عليه الصلاة والسلام)[^﴿﴾]{0,200})'), 'hadith'),
    (re.compile(r'(لأن\S*\s[^.؛]{6,260})'), 'because'),
    (re.compile(r'(لما\s+(?:ورد|روي)\s[^.؛]{6,200})'), 'because'),
]
entries = []
for b, f, t in paras:
    ref = title(f or b); t = clean(t)
    for c in split_clauses(t):
        c = unparen(c)
        if len(c) < 25 or not ref: continue                     # (the author's preface has no heading and no interpretation)
        entries.append({'ref': ref, 'bab': title(b), 'text': c})
json.dump(entries, open('data/books/isharat_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
import statistics
L = [len(e['text']) for e in entries]
print('entries', len(entries), 'median len', statistics.median(L), 'max', max(L), '>700:', sum(1 for x in L if x > 700), '<60:', sum(1 for x in L if x < 60))
