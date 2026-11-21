"""al-Jami' al-Saghir: the takhrij is in words (index 3) and the printed one is kept (index 9); every symbol of the print is a symbol of the author's key.
usage: python3 -I tests/takhrij_check.py"""
import json, re, sys
sys.path.insert(0, 'scripts')
import takhrij_natural as TN
d = json.load(open('content/jami.json', encoding='utf8'))['h']
fx = json.load(open('data/jami_takhrij_fixes.json', encoding='utf8'))['fixes']
bad = []
def check(c, m):
    if not c: bad.append(m)
check(len(d) == 10031, 'entries')
none = {n for n, f in fx.items() if f.get('none')}
for r in d:
    check(len(r) == 10, f'row {r[8]} has no printed takhrij (index 9)')
    nat, raw = r[3], r[9]
    if str(r[8]) in none: check(nat == '', f'{r[8]}: no source printed, the words must be empty'); continue
    check(bool(nat), f'{r[8]}: empty takhrij in words')
    check(not re.search(r'\(|\)|\b\d\b', nat) or 'رمز لم يتضح' in nat, f'{r[8]}: a bracket or number left in the words: {nat[:60]}')
    check(TN.natural(raw, none=str(r[8]) in none)[1] == [] or str(r[8]) in fx, f'{r[8]}: symbol not in the key: {raw[:60]}')
for n, f in fx.items():
    row = next(r for r in d if r[8] == int(n)); check(row[0] == f['page'], f'fix {n} is on another page')
    check(row[9] == f['k'], f'fix {n}: the printed takhrij was not applied')
print('entries checked:', len(d), '| fixes read from the printed pages:', len(fx), '| unclear symbols kept honest:', sum(1 for r in d if 'رمز لم يتضح' in r[3]))
print('OK' if not bad else 'PROBLEMS:\n   ' + '\n   '.join(bad[:30])); sys.exit(1 if bad else 0)
