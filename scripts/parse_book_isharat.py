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
# interpretation starters: «(ومن رأى)» etc. in parentheses, a sentence beginning «من رأى», or an interpreter's name «وقال ابن سيرين:»
OPEN = re.compile(r'\((?:ومن|وإن|وان|وإذا|وقد|فإن|ومتى|وكل|وأما|ومن سمع)[^()]{0,24}\)|\((?:وقال|قال)[^()]{2,45}\)')
ATTR = re.compile(r'(?:(?<=\s)|^)(?:\(?وقال\)?|\(?قال\)?|\(?وعن\)?|\(?وفي\)?)\s+[^:()﴿﴾.]{2,45}:')
SENT = re.compile(r'(?<=[.؟])\s+(?=(?:ومن|من|وإن|ومن رأى|وكل)\s)|(?<=\S)\s+(?=ومن رأى\s)')
def split_clauses(t):
    cuts = {0}
    for rx in (OPEN, ATTR, SENT):
        for m in rx.finditer(t):
            s = m.start() if rx is not SENT else m.end()
            if s > 0: cuts.add(s)
    pos = sorted(cuts); parts = [t[a:b].strip() for a, b in zip(pos, pos[1:] + [len(t)])]
    out = []
    for p in parts:                                  # a fragment too short to stand alone is joined to the one before it
        if out and len(p) < 40: out[-1] += ' ' + p
        else: out.append(p)
    if len(out) > 1 and len(out[0]) < 40: out[1] = out[0] + ' ' + out[1]; out.pop(0)
    return out
def unparen(c):
    m = re.match(r'^\(((?:وقال|قال)[^()]{2,45})\)\s*', c)
    if m: c = m.group(1) + ': ' + c[m.end():]                     # «(وقال جعفر الصادق) من رأى…» -> «وقال جعفر الصادق: من رأى…»
    else: c = re.sub(r'^\(([^()]{1,30})\)', r'\1', c)           # «(ومن رأى)» -> «ومن رأى»
    while c.count(')') > c.count('('): c = re.sub(r'\)\s*$', '', c) if c.rstrip().endswith(')') else c.replace(')', '', 1)
    while c.count('(') > c.count(')'): c = c.replace('(', '', 1)
    return re.sub(r'\s+', ' ', c).strip(' ')
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
