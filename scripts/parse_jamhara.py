"""Parses «جمهرة الأمثال» (أبو هلال العسكري ت بعد ٣٩٥هـ; the digital text of OpenITI, Shamela 6897, «completed» = proofread) into entries {chapter, proverb, explanation}
-> data/amthal/jamhara_parsed.json.  Every numbered proverb of the book's commentary («التفسير») becomes one entry; the explanation is the book's own paragraphs (with its chains of narrators, as printed).
Nothing is added: the page marks, the digital copy's «msNNN» marks and the editor's page numbers are removed.   usage: python3 -I scripts/parse_jamhara.py"""
import re, json, os, collections
OITI = os.environ.get('OITI', '/home/user/openiti')
P = f'{OITI}/0400AH/data/0395AbuHilalCaskari/0395AbuHilalCaskari.JamharatAmthal/0395AbuHilalCaskari.JamharatAmthal.Shamela0006897-ara1.completed'
L = open(P, encoding='utf8').read().split('\n')
def clean(t):
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\[\s*ص\s*:?\s*\d+\s*\]', ' ', t)
    t = t.replace('{', '﴿').replace('}', '﴾'); t = re.sub(r'\s+([،؛:.؟!)])', r'\1', t); t = re.sub(r'\(\s+', '(', t)
    return re.sub(r'\s+', ' ', t).strip()
LET = {'ألف أصلية أو مجتلبة': 'الألف', 'باء': 'الباء', 'التاء': 'التاء', 'ثاء': 'الثاء', 'الجيم': 'الجيم', 'الحاء': 'الحاء', 'خاء': 'الخاء', 'دال': 'الدال', 'ذال': 'الذال', 'راء': 'الراء', 'زاي': 'الزاي', 'سين': 'السين', 'شين': 'الشين',
       'صاد': 'الصاد', 'ضاد': 'الضاد', 'طاء': 'الطاء', 'ظاء': 'الظاء', 'عين': 'العين', 'غين': 'الغين', 'فاء': 'الفاء', 'قاف': 'القاف', 'كاف': 'الكاف', 'لام': 'اللام', 'ميم': 'الميم', 'نون': 'النون', 'واو': 'الواو', 'هاء': 'الهاء', 'لا': 'لا', 'ياء': 'الياء'}
def chapter(h):
    h = clean(h); m = re.search(r'في أوله\s+(.*)$', h)
    if not m: return None
    w = m.group(1).strip(' .,،:'); return 'حرف ' + LET[w] if w in LET else None
i0 = next(k for k, l in enumerate(L) if re.match(r'^### \|\| التفسير', l))
out = []; ch = 'حرف الألف'; cur = None            # the commentary of the first chapter (alif) begins before any other chapter heading
def flush():
    global cur
    if cur:
        paras = [clean(' '.join(p)) for p in cur['paras']]; paras = [p for p in paras if p]
        prov = re.sub(r'^(?:و?قولهم|و?قولهم\s*-)\s*', '', cur['title']).strip(' -.'); prov = re.sub(r'^-\s*', '', prov).strip()
        if prov: out.append({'chapter': cur['ch'], 'proverb': prov, 'explanation': ' '.join(paras)})
    cur = None
for l in L[i0:]:
    if l.startswith('# PageV'): continue
    m = re.match(r'^### \| (الباب\s.*)$', l)
    if m:
        c = chapter(m.group(1))
        if c: flush(); ch = c; continue
    m = re.match(r'^### \|\|\| \d+(?:\s*ms\d+)?\s*-\s*(.*)$', l)
    if m: flush(); cur = {'ch': ch, 'title': clean(m.group(1)), 'paras': []}; continue
    if cur is None: continue
    if l.startswith('### '):
        if re.match(r'^### \|\|? ', l): flush(); continue                   # an index or another section: the entry has ended
        cur['paras'].append([l[5:]]); continue
    if l.startswith('# '): cur['paras'].append([l[2:]])
    elif l.startswith('~~') and cur['paras']: cur['paras'][-1].append(l[2:])
flush()
json.dump(out, open('data/amthal/jamhara_parsed.json', 'w', encoding='utf8'), ensure_ascii=False)
print(len(out), 'proverbs;', dict(collections.Counter(e['chapter'] for e in out)))
print('without explanation:', sum(1 for e in out if not e['explanation']))
for e in out[:3] + out[1500:1502]: print(e['chapter'], '|', e['proverb'], '|', e['explanation'][:100])
