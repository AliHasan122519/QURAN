"""Parses «الأمثال العامية» (أحمد تيمور باشا; OpenITI/Hindawi digital text in data/amthal/) into entries
{chapter, proverb, explanation} -> data/amthal/amthal_parsed.json. The text of the book is copied as it is (only the page markers of the digital file are removed).
Checks printed at the end: entries per chapter, proverbs whose first letter does not match the chapter, suspicious headlines."""
import re, json, collections, sys
F = 'data/amthal/1348AhmadTaymurBasha.AmthalCammiyya.Hindawi075241938-ara1'
t = open(F, encoding='utf8').read().split('#META#Header#End#', 1)[1]
t = re.sub(r'\bms\d+\b|PageV\d+P\d+', ' ', t); t = t.replace('‏', '')
def clean_line(l): return re.sub(r'\s+', ' ', re.sub(r'^(# \|? ?|# |~~)', '', l)).strip()
blocks = [[clean_line(l) for l in b.split('\n') if clean_line(l)] for b in re.split(r'\n\s*\n', t) if b.strip()]
blocks = [b for b in blocks if not (len(b) == 1 and re.fullmatch(r'\d{1,3}', b[0]))]      # footnote numbers stand alone in the digital file
TITLES = {'سحر العيون', 'المستطرف'}                                                            # titles of books quoted at the end of a note, not proverbs
CH = re.compile(r'^حرف (\S+)$')
def headline_len(b):
    """number of trailing lines that form ONE complete quoted proverb («…» with nothing before it), or 0"""
    for k in range(1, min(4, len(b)) + 1):
        s = ' '.join(b[-k:])
        if not s.startswith('«'): continue
        if s.count('«') != 1 or s.count('»') != 1 or not s.endswith('»'): continue
        if s[1:-1] in TITLES: return 0
        if s.endswith('.»') or s.endswith('،»'): return 0                     # a quotation inside an explanation, ending like a sentence
        if k < len(b) and re.search(r'(:|قولهم|قوله|قالوا|وانظر|انظر|ويروى|وفي|كقولهم|مثل|وقولهم|و)$', b[-k - 1]): return 0     # «…» introduced by a lead-in = a cross-reference
        return k
    return 0
entries, cur, chapter, started = [], None, '', False
for b in blocks:
    if not started:
        if b == ['أحمد تيمور باشا']: started = True            # the title page ends here; the table of contents above it is skipped
        continue
    if len(b) == 1 and CH.match(b[0]): chapter = b[0]; continue
    k = headline_len(b)
    if k == len(b):                                    # a block that is only a headline: a new proverb
        cur = {'chapter': chapter, 'proverb': ' '.join(b)[1:-1].strip(), 'exp': []}; entries.append(cur); continue
    expl = b[:len(b) - k] if k else b
    if cur is not None: cur['exp'].append(' '.join(expl))
    if k: cur = {'chapter': chapter, 'proverb': ' '.join(b[-k:])[1:-1].strip(), 'exp': []}; entries.append(cur)
for e in entries: e['explanation'] = re.sub(r'\s+', ' ', ' '.join(e.pop('exp'))).strip()
json.dump(entries, open('data/amthal/amthal_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print('entries', len(entries))
c = collections.Counter(e['chapter'] for e in entries); print(dict(c))
DI = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
def norm(s): return re.sub('[إأآٱ]', 'ا', DI.sub('', s))
def first(s): m = re.search('[\u0621-\u064A]', norm(s)); return m.group(0) if m else ''
def chap_letter(c): n = c.replace('حرف ', ''); return 'ا' if n == 'الألف' else n[2:3] if n.startswith('ال') else n[:1]
def ok_letter(e):
    p = re.sub('^[^\u0621-\u064A]*', '', norm(e['proverb'])); cl = chap_letter(e['chapter']); c = {first(p)}
    if p.startswith('ال'): c.add(first(p[2:]))
    if p.startswith('وال'): c.add(first(p[3:]))
    return cl in c
bad = [e for e in entries if not ok_letter(e)]
print('proverbs whose first letter does not match the chapter (articles ignored):', len(bad), '| distinct proverbs', len({e['proverb'] for e in entries}))
for e in bad[:12]: print('  ', e['chapter'], '|', e['proverb'][:70])
print('long headlines (>110)', sum(1 for e in entries if len(e['proverb']) > 110), '| no explanation', sum(1 for e in entries if not e['explanation']))
