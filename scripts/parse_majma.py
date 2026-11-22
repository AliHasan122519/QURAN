"""Parses «مجمع الأمثال» (أبو الفضل أحمد بن محمد الميداني النيسابوري ت ٥١٨هـ; the digital text of OpenITI, Shamela 12929, tahqiq Muhammad Muhyi al-Din Abd al-Hamid)
into entries {chapter, proverb, explanation} -> data/amthal/majma_parsed.json.  Every numbered proverb of the book becomes one entry (4965).
Nothing is added: the page marks, the editor's page numbers «[ص: 9]» and the digital copy's «msNNN» marks are removed, the paragraphs of the explanation are joined, Qur'anic braces become ﴿ ﴾.
usage: python3 -I scripts/parse_majma.py  (OITI: the folder of the OpenITI 0525AH sparse clone)"""
import re, json, os
OITI = os.environ.get('OITI', '/home/user/openiti')
P = f'{OITI}/0525AH/data/0518IbnMuhammadMaydaniNaysaburi/0518IbnMuhammadMaydaniNaysaburi.MajmacAmthal/0518IbnMuhammadMaydaniNaysaburi.MajmacAmthal.Shamela0012929-ara1'
L = open(P, encoding='utf8').read().split('\n')
i0 = next(k for k, l in enumerate(L) if re.match(r'^### \| الباب الأول', l))
def clean(t):
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\[\s*ص\s*:?\s*\d+\s*\]', ' ', t)
    t = t.replace('{', '﴿').replace('}', '﴾'); t = re.sub(r'\s+([،؛:.؟!)])', r'\1', t); t = re.sub(r'\(\s+', '(', t)
    return re.sub(r'\s+', ' ', t).strip()
LETTER = {'همزة': 'الألف', 'ألف': 'الألف'}
def chapter(h):
    h = clean(h); m = re.search(r'فيما أوله\s+(.*)$', h)
    if not m: return None
    w = m.group(1).strip(' .,،:').replace('معجمة', '').replace('مهملة', '').strip()
    return 'حرف ' + LETTER.get(w, 'ال' + w)
out = []; ch = ''; cur = None
def flush():
    global cur
    if cur:
        paras = [clean(' '.join(p)) for p in cur['paras']]; paras = [p for p in paras if p]
        prov = cur['title']
        if not prov and paras: prov, paras = paras[0], paras[1:]
        prov = prov.strip().rstrip('.').strip() if prov else ''
        if prov: out.append({'chapter': cur['ch'], 'proverb': prov, 'explanation': ' '.join(paras)})
    cur = None
for l in L[i0:]:
    if re.match(r'^# PageV', l): continue
    m = re.match(r'^### [|$] (\d+)\s*-\s*(.*)$', l)
    if m:
        flush(); cur = {'ch': ch, 'title': clean(m.group(2)), 'paras': []}; continue
    m = re.match(r'^(?:### \||#) (?:- )?(الباب\s.*)$', l)
    if m:
        if re.match(r'الباب التاسع والعشرون', m.group(1)): break              # the names of the days of the Arabs, and the last chapter (sayings): not proverbs
        c = chapter(m.group(1))
        if c: flush(); ch = c; continue
    if cur is None: continue
    if l.startswith('### '):
        t = l[5:]
        if re.match(r'^\[\s*ص', t.strip()): continue
        cur['paras'].append([t]); continue
    if l.startswith('# '): cur['paras'].append([l[2:]])
    elif l.startswith('~~') and cur['paras']: cur['paras'][-1].append(l[2:])
flush()
json.dump(out, open('data/amthal/majma_parsed.json', 'w', encoding='utf8'), ensure_ascii=False)
import collections
print(len(out), 'proverbs;', 'chapters:', dict(collections.Counter(e['chapter'] for e in out)))
print('without explanation:', sum(1 for e in out if not e['explanation']))
for e in out[:3] + out[2000:2002]: print(e['chapter'], '|', e['proverb'], '|', e['explanation'][:120])
