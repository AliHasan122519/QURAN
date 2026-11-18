"""Shared by the book parsers: cutting a text into one entry per interpretation at the author's own separators."""
import re
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

def split_long(c, limit=900):
    """a clause that is still very long is cut at sentence ends (full stop) so that every entry stays readable"""
    if len(c) <= limit: return [c]
    out, cur = [], ''
    for sent in re.split(r'(?<=[.؟])\s+', c):
        if cur and len(cur) + len(sent) > limit: out.append(cur.strip()); cur = ''
        cur += sent + ' '
    if cur.strip(): out.append(cur.strip())
    return out
