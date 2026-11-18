"""Verifies the Qur'an text of the app against the official digital text of the King Fahd Complex (KFGQPC Hafs v18, data/ref/hafsData_v18.json).
Every verse is compared character by character (the tatweel carrier, a font convention, is ignored). With --apply the verses that differ are replaced by the official text.
usage: python3 -I scripts/check_quran_kfgqpc.py [--apply]"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
q = json.load(open('content/quran.json', encoding='utf8')); rows = q['a']
k = json.load(open('data/ref/hafsData_v18.json', encoding='utf8'))
K = {(r['sora'], r['aya_no']): re.sub('[ ‏ ]*[٠-٩]+\\s*$', '', r['aya_text']).strip() for r in k}
assert len(K) == 6236 and all((s, a) in K for s, a, _ in rows), 'verse numbering differs'
n = lambda s: s.replace('ـ', '')
diff = [(i, s, a) for i, (s, a, t) in enumerate(rows) if n(t) != n(K[(s, a)])]
print('verses:', len(rows), '| identical to the official text:', len(rows) - len(diff), '| different:', len(diff))
for i, s, a in diff[:5]: print(f'  {s}:{a}\n    app : {rows[i][2]}\n    kfg : {K[(s, a)]}')
if '--apply' in sys.argv and diff:
    for i, s, a in diff: rows[i][2] = K[(s, a)]
    CL.publish('quran', 'القرآن الكريم', 'quran', q, len(rows)); print('replaced', len(diff), 'verses by the official text')
