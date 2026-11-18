"""Parses the other dream-interpretation books of the «الكتب» tab (digital texts from OpenITI, kept in data/books/*.txt) into entries
{ref (the heading / symbol, '' when the book has none), text (the book's words, cut at its own separators)}  ->  data/books/more_parsed.json
Nothing is added to a text; page/footnote markers are removed.   usage: python3 -I scripts/parse_books_more.py"""
import re, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from book_lib import split_clauses, unparen, split_long
B = 'data/books/'
def body(fn):
    L = open(B + fn, encoding='utf8').read().split('\n')
    i = next((k for k, l in enumerate(L) if 'Header#End' in l), -1) + 1
    return L[i:]
def clean(t):
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t)
    t = re.sub(r'\[\s*ص\s*\d+\s*\]', ' ', t); t = re.sub(r'@\s*\d+\s*/\s*[أب]\s*@', ' ', t); t = re.sub(r'\[\s*\d+\s*/\s*[أب]\s*\]', ' ', t)
    t = t.replace('%~%', ' ').replace('٭', ' ')
    t = re.sub(r'!\[image filename\]\([^)]*\)', ' ', t)
    t = re.sub(r'\{((?:ومن|وإن|وان|وقال|قال|وإذا|فإن)[^{}]{0,30})\}', r'(\1)', t)
    t = t.replace('{', '﴿').replace('}', '﴾')
    t = re.sub(r'\(\s+', '(', t); t = re.sub(r'\s+\)', ')', t)
    t = re.sub(r'\[\s*\d+\s*\]\s*', ' ', t)                                # paragraph numbers «[142]»
    return re.sub(r'\s+', ' ', t).strip()
ORD = r'(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي|الثاني|الثالث|عشر|عشرة|والعشرون|العشرون|والثلاثون|الثلاثون|والأربعون|الأربعون|والخمسون|الخمسون|الستون|والستون|السبعون|والسبعون|الثمانون|والثمانون|والتسعون|التسعون|المائة|الثذى|الثاذى|\d+)'
def heading_title(h):
    h = re.sub(r'\bms\d+\b', ' ', h); h = re.sub(r'\[[^\]]*\]', ' ', h); h = re.sub(r'[()\[\]|]', ' ', h)
    h = re.sub(r'\s+', ' ', h).strip()
    if re.fullmatch(r'(?:ال?باب|ال?فصل|الفص)?\s*(?:' + ORD + r'\s*)*', h): return None            # «الباب الثالث عشر» alone: the title is on the next heading line
    h = re.sub(r'^(?:ال?باب|ال?فصل)\s+(?:' + ORD + r'\s*)+', '', h).strip()
    h = re.sub(r'^(?:فصل|باب)\s*:?\s*', '', h); h = re.sub(r'^في\s+(?:تأويل\s+)?', '', h)
    return h.strip(' .:') or None
def paragraphs(fn, headings=True):
    """[(ref, text)] in book order; a heading sets the ref of the paragraphs after it"""
    out = []; ref = ''; buf = []
    def flush():
        nonlocal buf
        t = ' '.join(buf).strip()
        if t: out.append((ref, t))
        buf = []
    for l in body(fn):
        if l.startswith('### ') and headings:
            flush(); h = heading_title(l[3:])
            if h: ref = h
        elif l.startswith('# ') or l == '#': flush(); buf.append(l[2:])
        elif l.startswith('~~'): buf.append(l[2:])
    flush(); return out
entries = []
def add(src, ref, text):
    for c in split_clauses(clean(text)):
        c = unparen(c)
        for p in split_long(c):
            if len(p) >= 25: entries.append({'src': src, 'ref': ref, 'text': p})
# 1) books with headings
for src, fn in (('muntakhab', 'muntakhab.txt'), ('qadiri', 'qadiri.txt'), ('badr', 'badr_munir.txt')):
    for ref, t in paragraphs(fn): add(src, ref, t)
# 2) the alphabetical dictionary: every entry opens with «- ( الرمز )»; «- ( ومن رأى )» continues the symbol before it
T = ' '.join(l[2:] if l.startswith('# ') else l[2:] if l.startswith('~~') else '' for l in body('tatir_anam.txt'))
T = clean(T)
CONT = re.compile(r'^(?:ف?إن|و?من|وإن|وإذا|فمن|وان|فإذا|وكذلك|ومن سمع)\b')
parts = re.split(r'\s-\s\(([^()]{1,40})\)\s', ' ' + T)
sym = ''; i = 1
for k in range(1, len(parts), 2):
    m, rest = parts[k].strip(), parts[k + 1]
    if CONT.match(m): add('tatir', sym, m + ' ' + rest)
    else: sym = m; add('tatir', sym, rest)
# 3) books without headings
for ref, t in paragraphs('ibn_ghannam.txt', headings=False): add('ghannam', '', t)
S = ' '.join(l[2:] if l.startswith('# ') else l[2:] if l.startswith('~~') else '' for l in body('isharah_salimi.txt'))
for piece in clean(S).split(' | '): add('salimi', '', piece)
for ref, t in paragraphs('manamat.txt'): add('manamat', ref, t)
json.dump(entries, open(B + 'more_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
import collections; c = collections.Counter(e['src'] for e in entries); print(c, len(entries))
