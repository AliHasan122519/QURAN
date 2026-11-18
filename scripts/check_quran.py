"""Compares the Qur'an text of the app (content/quran.json) with an independent Uthmani text (data/ref/quran-uthmani.txt, Tanzil-derived) verse by verse.
Level 1: the letters (rasm skeleton). Level 2: letters + vowel/recitation marks after unifying the Unicode conventions of the two files. Prints the differences."""
import json, re, sys, collections
q = json.load(open('content/quran.json', encoding='utf8'))
ref = open('data/ref/quran-uthmani.txt', encoding='utf8').read().split('\n')
ref = [l for l in ref if l.strip()]
BASM = 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِیمِ '
ours = q['a']; print('verses: ours', len(ours), 'ref lines', len(ref))
MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ⁠‌‍࣓-ࣿ]')
def unify(s):                                  # conventions of the two files: Persian ya/kaf, dagger alef spellings, maddah signs, tatweel, word joiner
    s = s.replace('ی', 'ي').replace('ک', 'ك').replace('ى', 'ي')
    s = s.replace('⁠', '').replace('ـ', '')
    return s
def skel(s):
    s = unify(s); s = MARKS.sub('', s); s = re.sub('[ٱإأآ]', 'ا', s); s = s.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    return re.sub(r'[^ء-ي]', '', s)
BASM_SK = 'بسماللهالرحمنالرحيم'
diff1 = []; refi = 0
for s_, a, t in ours:
    line = ref[refi]; refi += 1
    sk = skel(line)
    if a == 1 and s_ not in (1, 9):
        if not sk.startswith(BASM_SK): diff1.append((s_, a, t, line)); continue
        sk = sk[len(BASM_SK):]
    if skel(t) != sk: diff1.append((s_, a, t, line))
print('level 1 (letters) different verses:', len(diff1))
for s_, a, t, line in diff1[:40]: print(f'  {s_}:{a}\n    ours: {t}\n    ref : {line}')
json.dump([[s_, a, t, l] for s_, a, t, l in diff1], open('data/ref/quran_diff_letters.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)

# ---- level 2: marks, aligned letter by letter (the letters are identical, so each letter can be compared with its marks) ----
# The two files encode the same signs with different Unicode characters; they are mapped to one convention before comparing.
CONV = {'\u06E4': '\u0653', '\u06DF': '\u0652', '\u08F0': '\u0657', '\u08F1': '\u065E', '\u08F2': '\u0656'}
SEAT = {'أ': ('ا', '\u0654'), 'إ': ('ا', '\u0655'), 'آ': ('ا', '\u0653'), 'ؤ': ('و', '\u0654'), 'ئ': ('ي', '\u0654'), 'ٱ': ('ا', ''), 'ى': ('ي', '')}
def toks(s):
    s = unify(s); out = []
    for ch in s:
        if ch == ' ': out.append([' ', []]); continue
        if re.match('[\u0621-\u064A\u0671]', ch):
            b, m = SEAT.get(ch, (ch, '')); out.append([b, [m] if m else []])
        elif out and MARKS.match(ch): out[-1][1].append(CONV.get(ch, ch))
    for t in out: t[1] = ''.join(sorted(c for c in t[1] if c not in '\u0654\u0655'))     # hamza signs are carried by the letter in one file and by a sign in the other
    return out
pairs = collections.Counter(); where = collections.defaultdict(list); misaligned = []; refi = 0
for s_, a, t in ours:
    line = ref[refi]; refi += 1
    A = toks(t); B = toks(line)
    if a == 1 and s_ not in (1, 9):
        k = 0; words = 0
        while k < len(B) and words < 4:
            if B[k][0] == ' ': words += 1
            k += 1
        B = B[k:]
    if [x[0] for x in A] != [x[0] for x in B]: misaligned.append((s_, a)); continue
    for (la, ma), (lb, mb) in zip(A, B):
        if ma != mb: pairs[(ma, mb)] += 1; where[(ma, mb)].append((s_, a))
print('verses whose letter sequence is not identical:', len(misaligned), misaligned[:10])
print('mark differences after unifying the conventions (ours -> ref): distinct', len(pairs), 'total', sum(pairs.values()), 'in verses', len({v for l in where.values() for v in l}))
def show(m): return ' '.join(f'U+{ord(c):04X}' for c in m) or '(none)'
for (ma, mb), n in pairs.most_common(40): print(f'{n:6d}  ours [{show(ma)}]  ref [{show(mb)}]   e.g. {where[(ma, mb)][:4]}')
json.dump({f'{show(a)} => {show(b)}': where[(a, b)] for (a, b) in pairs}, open('data/ref/quran_diff_marks.json', 'w'), ensure_ascii=False)
