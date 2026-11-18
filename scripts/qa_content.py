"""Static quality scan of every text in content/: reports anomalies by kind with counts and samples.  usage: python3 -I scripts/qa_content.py [--samples N]"""
import json, re, sys, collections
N = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 3
def load(n): return json.load(open(f'content/{n}.json', encoding='utf8'))
AR = r'ء-يً-ٰٟٱۖ-ۭ'
def scan(name, items):
    """items: [(id, field, text)]"""
    kinds = collections.defaultdict(list)
    for i, f, t in items:
        if not t: continue
        if re.search(r'[A-Za-z]', t): kinds['latin_letters'].append((i, f, t))
        if re.search(r'(?<![\d(])\d(?![\d)])', t) and f != 'takhrij': kinds['stray_digit'].append((i, f, t))
        if t.count('(') != t.count(')'): kinds['unbalanced_parens'].append((i, f, t))
        if t.count('«') != t.count('»'): kinds['unbalanced_guillemets'].append((i, f, t))
        if t.count('﴿') != t.count('﴾'): kinds['unbalanced_verse_marks'].append((i, f, t))
        if re.search(r'  ', t): kinds['double_space'].append((i, f, t))
        if re.search(r'[،,.؛:]\s*[،,.؛:]', t): kinds['double_punct'].append((i, f, t))
        if re.search(r'\s[،.؛:؟,]', t) and f == 'text': kinds['space_before_punct'].append((i, f, t))
        if re.search(r'[#@~|\\\[\]{}<>_^*=+%$&]', t): kinds['odd_symbols'].append((i, f, t))
        if re.search(r'(\b\S{3,}\b) \1\b', t): kinds['repeated_word'].append((i, f, t))
        if re.search(r'(.)\1\1\1', t): kinds['char_run'].append((i, f, t))
        if not re.search('[' + AR + ']', t): kinds['no_arabic'].append((i, f, t))
        if t != t.strip(): kinds['untrimmed'].append((i, f, t))
        if re.search(r'[ـ]', t): kinds['tatweel'].append((i, f, t))
        if re.search(r'[​-‏‪-‮﻿]', t): kinds['invisible'].append((i, f, t))
        if re.search(r'\bمحمد\s+صلى\b(?! الله)', t): kinds['salat_abbrev'].append((i, f, t))
    print(f'\n=== {name}: {len(items)} fields')
    for k, v in sorted(kinds.items(), key=lambda x: -len(x[1])):
        print(f'  {k}: {len(v)}')
        for i, f, t in v[:N]: print('      ', i, f, '|', t[:110].replace('\n', ' '))
q = load('quran'); scan('quran', [(f'{s}:{a}', 'text', t) for s, a, t in q['a']])
j = load('jami')['h']; scan('jami', [(r[-1], 'text', r[2]) for r in j] + [(r[-1], 'takhrij', r[3]) for r in j])
am = load('amthal')['h']; scan('amthal', [(i, 'text', r[1]) for i, r in enumerate(am)] + [(i, 'expl', r[2]) for i, r in enumerate(am)])
al = load('alfiya')['h']; scan('alfiya', [(r[0], 'text', r[3] + ' ' + r[4]) for r in al])
bk = load('books')['h']; scan('books', [(i, 'text', r[1]) for i, r in enumerate(bk)] + [(i, 'ref', r[0]) for i, r in enumerate(bk)] + [(i, 'expl', r[2]) for i, r in enumerate(bk)])
