"""Builds the list «أحاديث الرؤيا» of the «المزيد» menu (content/ruyahadith.json): the whole «كتاب التعبير» of Sahih al-Bukhari and the whole «كتاب الرؤيا» of Sahih Muslim,
word for word from the digital texts of OpenITI (Shamela 1681 and 1727), each hadith under its chapter heading with its number and the book named.
Nothing is added: only the page marks and the copy's «msNNN» marks are removed, and the Qur'anic braces become ﴿ ﴾.   usage: python3 -I scripts/build_ruya_hadith.py"""
import re, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
OITI = os.environ.get('OITI', '/home/user/openiti')
BUK = f'{OITI}/0275AH/data/0256Bukhari/0256Bukhari.Sahih/0256Bukhari.Sahih.Shamela0001681-ara1'
MUS = f'{OITI}/0275AH/data/0261Muslim/0261Muslim.Sahih/0261Muslim.Sahih.Shamela0001727-ara1.mARkdown'
def clean(t):
    t = re.sub(r'PageV\d+P\d+', ' ', t); t = re.sub(r'\bms\d+\b', ' ', t); t = re.sub(r'\[\s*ص\s*:?\s*\d+\s*\]', ' ', t); t = t.replace('{', '﴿').replace('}', '﴾')
    t = re.sub(r'\s+([،؛:.؟!)»])', r'\1', t); t = re.sub(r'\(\s+', '(', t); t = re.sub(r'«\s+', '«', t)
    return re.sub(r'\s+', ' ', t).strip()
def parse(path, start_re, end_re, num_re, book, kitab):
    L = open(path, encoding='utf8').read().split('\n')
    i0 = next(k for k, l in enumerate(L) if re.match(start_re, l)); i1 = next(k for k in range(i0 + 1, len(L)) if re.match(end_re, L[k]))
    rows = []; bab = ''; cur = None
    def flush():
        nonlocal cur
        if cur:
            t = clean(' '.join(' '.join(p) for p in cur['paras']))
            if len(t) > 15: rows.append([cur['bab'], t + '\t' + f"{book} — {kitab}" + (f" — حديث {cur['num']}" if cur['num'] else ''), '', '', book])
        cur = None
    for l in L[i0 + 1:i1]:
        if re.match(r'^# PageV', l) or re.match(r'^PageV', l): continue
        m = re.match(num_re, l)
        if m: flush(); cur = {'bab': bab, 'num': m.group(1), 'paras': []}; continue
        m = re.match(r'^### \| (باب.*)$', l)
        if m: flush(); bab = clean(m.group(1)); continue
        if cur is None: continue
        if l.startswith('# '): cur['paras'].append([l[2:]])
        elif l.startswith('~~') and cur['paras']: cur['paras'][-1].append(l[2:])
        elif l.startswith('### '): cur['paras'].append([l[5:]])
    flush(); return rows
def main():
    b = parse(BUK, r'^### \$ 91 - كتاب التعبير', r'^### \$ 92 - كتاب الفتن', r'^### \| (\d+) - ?$', 'صحيح البخاري', 'كتاب التعبير')
    for r in b: r[0] = r[0] or 'كتاب التعبير'
    m = parse(MUS, r'^### \| 42 - كتاب الرؤيا', r'^### \| 43 - كتاب الفضائل', r'^### \$ (\d+) -\s*$', 'صحيح مسلم', 'كتاب الرؤيا')
    for r in m: r[0] = r[0] or 'كتاب الرؤيا'
    for r in m: r[1] = re.sub(r' — حديث \d+(?=$)', '', r[1])         # Muslim's internal numbers repeat for the other chains of the same hadith: not shown
    rows = b + m
    CL.publish('ruyahadith', 'أحاديث الرؤيا', 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'rule', 'menu': 'أحاديث الرؤيا', 'placeholder': 'اكتب هنا',
               'hint': 'كتاب التعبير من صحيح البخاري وكتاب الرؤيا من صحيح مسلم، بنصهما.', 'unit': 'حديثاً', 'l1': 'الحديث', 'l2': '', 'sub': 'من صحيح البخاري وصحيح مسلم'})
    return rows
if __name__ == '__main__':
    rows = main(); print(len(rows), 'hadith: bukhari', sum(1 for r in rows if r[4] == 'صحيح البخاري'), 'muslim', sum(1 for r in rows if r[4] == 'صحيح مسلم'))
    for r in rows[:2] + rows[-2:]: print(r[0], '|', r[1][:200])
