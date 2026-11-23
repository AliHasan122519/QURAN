"""Independent check of «أصول التأويل» (content/taweel.json): every rule's evidence is word for word in its source (the Jami', the dream hadith, the Qur'an), and every anchor is word for word in its book of «الكتب».
It reads the raw content files, not the builder's code.   usage: python3 -I tests/taweel_check.py"""
import json, re
MARKS = re.compile('[ً-ٰٟۖ-ۭـ]')
def f(s, deep=False):
    s = MARKS.sub('', s).replace('ٰ', ''); s = re.sub('[أإآٱ]', 'ا', s).replace('ى', 'ي').replace('ئ', 'ي').replace('ؤ', 'و').replace('ة', 'ه'); s = re.sub(r'[^ء-ي ]', ' ', s); s = re.sub(r'\s+', ' ', s).strip()
    return s.replace('ء', '').replace('ا', '').replace(' ', '') if deep else s
def load(n): return json.load(open(f'content/{n}.json', encoding='utf8'))
J = [r[2] for r in load('jami')['h']]; R = [r[1] for r in load('ruyahadith')['h']]; Q = [r[2] for r in load('quran')['a']]; B = load('books')['h']
A = [r[1] for r in load('amthal')['h']]; Sh = [r[1] for r in load('shawahid')['h']]; Al = [r[3] + ' … ' + r[4] for r in load('alfiya')['h']]; QW = load('qawaid')['h']
SRC = {'حديث': J + R, 'آية': Q, 'مثل': A, 'بيت': Sh, 'ألفية': Al}
bad = []; n = 0
rows = load('taweel')['h']
spec = {r[0] for r in rows if r[4] == 'rule'}
import sys, os; sys.path.insert(0, 'data/taweel'); from rules import RULES, COMBOS
if spec != {r['id'] for r in RULES}: bad.append('the published rules differ from data/taweel/rules.py')
for r in rows:
    if r[4] != 'rule': continue
    o = json.loads(r[1]); n += 1
    if o['kind'] == 'head' and not o.get('verdict'): bad.append(o['id'] + ': no verdict')
    for e in o['ev'] + [x for a in o.get('alts', []) for x in a['ev']]:
        q = f(e['q'], e['t'] == 'آية')
        if not any(q in f(t, e['t'] == 'آية') for t in SRC[e['t']]): bad.append(o['id'] + ': evidence not in its source: ' + e['q'][:50])
    spec_r = next(x for x in RULES if x['id'] == o['id'])
    if not spec_r['anchors']: bad.append(o['id'] + ': no anchor')
    for a in spec_r['anchors']:
        if 'qawaid' in a:
            if not any(r[0] == a['qawaid'] and f(a['needle']) in f(r[1]) for r in QW): bad.append(o['id'] + ': method anchor not in qawaid: ' + a['needle'][:40])
        elif not any(a['book'] in (b[3] or '') and f(a['needle']) in f(b[1]) for b in B): bad.append(o['id'] + ': anchor not in ' + a['book'] + ': ' + a['needle'][:40])
for c in (json.loads(r[1]) for r in rows if r[4] == 'combo'):
    for e in c['ev']:
        if not any(f(e['q'], e['t'] == 'آية') in f(t, e['t'] == 'آية') for t in SRC[e['t']]): bad.append(c['id'] + ': evidence not in its source')
    sp = next(x for x in COMBOS if x['id'] == c['id'])
    for a in sp['anchors']:
        if 'qawaid' in a:
            if not any(r[0] == a['qawaid'] and f(a['needle']) in f(r[1]) for r in QW): bad.append(c['id'] + ': method anchor missing')
        elif not any(a['book'] in (b[3] or '') and f(a['needle']) in f(b[1]) for b in B): bad.append(c['id'] + ': anchor not in ' + a['book'])
    n += 1
fams = next(json.loads(r[1]) for r in rows if r[4] == 'fams')
for k, v in fams.items():
    for e in v['ev']:
        if not any(f(e['q'], True) in f(t, True) for t in Q): bad.append('باب ' + k + ': evidence not in the Qur\'an: ' + e['q'][:40])
used = {o_['family'] for o_ in (json.loads(r[1]) for r in rows if r[4] == 'rule') if o_['kind'] == 'head'}
print('families with a rule but without a maal:', sorted(x for x in used if x not in fams and x != 'رزق'))
print('rules checked:', n)
for b in bad: print('BAD', b)
print('OK' if not bad else 'FAILED'); raise SystemExit(1 if bad else 0)
