"""Corrects the reading of al-Jami' al-Saghir with the independent digital text of the same book (data/ref/jamic_saghir.json, numbered 1..10031 like the print).
For each entry: (1) the printed number is confirmed or repaired by the text itself, (2) misread words are replaced by the digital text's words, (3) the exact end of the hadith
text is found (the digital text has no authors/narrators), so names that were left inside the text move to the takhrij and words that fell into the takhrij move back.
Everything is decided word by word with a vocabulary and bigram support learned from the book itself; the printed spelling of the book is kept (e.g. شيء)."""
import re, json, math, collections, difflib
DI = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ‎‏]')
def L(w):
    """loose key of a word: no marks, one form of alef/ya/ta marbuta/hamza seats and no hamza itself, so شيء/شئ/شي and يجيء/يجي are one key"""
    w = DI.sub('', w); w = re.sub('[إأآٱ]', 'ا', w).replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    return re.sub(r'[^ء-ي0-9]', '', w)
def L3(w):
    """even looser: the hamza-carrying letters are dropped (ادرؤوا = ادرأوا), used only to tell a spelling variant from a different word"""
    return re.sub('[أإآؤئء]', '', DI.sub('', w)).replace('ى', 'ي').replace('ة', 'ه').replace('ٱ', 'ا')
PUNCT = '،؛.:؟!,;'
CLASSES = ['بتثنيئى', 'جحخ', 'دذ', 'رز', 'سش', 'صض', 'طظ', 'عغ', 'فق', 'هة', 'ولاك', 'مه', 'ذك', 'نق']
CLS = {}
for i, c in enumerate(CLASSES):
    for ch in c: CLS.setdefault(ch, set()).add(i)
def vdist(a, b):
    """edit distance of two words where swapping letters that look alike in print costs half (the typical misreadings of a scanned page)"""
    d = [float(j) for j in range(len(b) + 1)]
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], float(i)
        for j, y in enumerate(b, 1):
            sub = 0.0 if x == y else (0.5 if CLS.get(x, set()) & CLS.get(y, set()) else 1.0)
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + sub)
    return d[-1]
def strip_p(w): return w.strip(PUNCT) or w
def clean_ref(text):
    t = re.sub(r'\(\s*\d+\s*\)', ' ', text); t = t.replace('"', ' ').replace('«', ' ').replace('»', ' ')
    t = re.sub(r'\s+(حرف\s+\S+|فصل\s+في\s+(\S+\s+){0,7}\S+)$', '', t)                     # the chapter heading that follows the last hadith of a chapter is not part of it
    return [strip_p(w) for w in t.split() if strip_p(w).strip(PUNCT)]
class RefFixer:
    def __init__(self, ref, book_texts, extra_texts=()):
        self.ref = {int(k): clean_ref(v) for k, v in ref.items()}
        self.freq = collections.Counter(); self.bg = collections.Counter(); self.spell = collections.defaultdict(collections.Counter)
        for toks in self.ref.values():
            ks = [L(t) for t in toks]; self.freq.update(k for k in ks if k)
            self.bg.update(zip(ks, ks[1:]))
        for tx in list(book_texts) + list(extra_texts):
            for w in tx.split():
                k = L(w)
                if k: self.freq[k] += 1; self.spell[k][w] += 1
        for tx in book_texts:                                   # the book's own spelling (hand-verified pages) decides how a word is written
            pass
        self.book_spell = {k: c.most_common(1)[0][0] for k, c in self.spell.items()}
        self.exact = collections.Counter(w for tx in book_texts for w in tx.split())
    # ----- number -----
    def best_number(self, n, toks, window=8):
        keys = [L(t) for t in toks]
        def score(m):
            r = self.ref.get(m)
            if not r: return 0.0
            return difflib.SequenceMatcher(None, keys, [L(t) for t in r], autojunk=False).ratio()
        cur = score(n) if n else 0.0
        if cur >= 0.8: return n, cur
        best, bs = n, cur
        for m in range(max(1, (n or 1) - window), (n or 1) + window + 1):
            s = score(m)
            if s > bs + 0.05: best, bs = m, s
        if not n:                                                 # no number was read: look in the whole neighbourhood given by the caller
            pass
        return best, bs
    # ----- words -----
    def surface(self, ref_tok):
        """how the book writes the word: as the digital text has it if the book spells it so, else the book's usual spelling of that word"""
        if self.exact[ref_tok] >= 2: return ref_tok
        return self.book_spell.get(L(ref_tok), ref_tok)
    def fix(self, toks, n, policy='score', verified=False, ins_max=6, visual=False, vmax=1.5):
        """toks: all words of the entry (hadith text + takhrij) as read. Returns (matn_tokens, tail_tokens, info)"""
        B = self.ref.get(n)
        if not B: return None
        A = [strip_p(t) for t in toks]; ka = [L(t) for t in A]; kb = [L(t) for t in B]
        sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False); ops = sm.get_opcodes()
        ratio = sm.ratio()
        # own bigrams of this entry are removed from the corpus counts, so the reference text cannot vote for itself
        own = collections.Counter(zip(kb, kb[1:]))
        def sup(prev, w, nxt):
            c = 0
            if prev is not None: c += max(0, self.bg[(prev, w)] - own[(prev, w)])
            if nxt is not None: c += max(0, self.bg[(w, nxt)] - own[(w, nxt)])
            return c
        out = []; end_a = 0; changes = []
        def choose(x, y, prev, nxt, j):
            kx, ky = L(x), L(y)
            if kx == ky:                                                  # the same word: the spelling that the book uses (ى/ي, hamza seats…)
                if x == y: return x
                if verified: return x
                if self.exact[x] >= 1 and self.exact[x] > self.exact[y]: return x
                return y if self.exact[y] >= 1 or self.exact[x] == 0 else x
            if L3(x) == L3(y):                                            # hamza seat variants (ادرؤوا / ادرأوا): the one the book prints more; the reading of the scan decides a tie
                return y if (not verified) and self.exact[y] > self.exact[x] else x
            fx, fy = self.freq[kx], max(0, self.freq[ky] - 1)
            if verified: return self.surface(y) if fx < 2 and fy >= 1 else x
            if visual and fx >= 2 and vdist(kx, ky) > vmax: return x             # a known word that does not look like a misreading of the other: a different wording of the printing
            if policy == 'ref': return self.surface(y)
            if policy == 'ours': return x
            sx = math.log(1 + fx) + 2 * math.log(1 + sup(prev, kx, nxt)); sy = math.log(1 + fy) + 2 * math.log(1 + sup(prev, ky, nxt))
            return self.surface(y) if sy > sx + 0.5 else x
        for tag, i1, i2, j1, j2 in ops:
            prev = kb[j1 - 1] if j1 > 0 else None; nxt = kb[j2] if j2 < len(kb) else None
            if tag == 'equal':
                for d in range(i2 - i1):
                    x, y = A[i1 + d], B[j1 + d]
                    w = choose(x, y, kb[j1 + d - 1] if j1 + d else None, kb[j1 + d + 1] if j1 + d + 1 < len(kb) else None, j1 + d) if x != y else x
                    if w != x: changes.append((x, w))
                    out.append(w)
                end_a = i2
            elif tag == 'replace':
                if i2 - i1 == j2 - j1:
                    for d in range(i2 - i1):
                        w = choose(A[i1 + d], B[j1 + d], kb[j1 + d - 1] if j1 + d else None, kb[j1 + d + 1] if j1 + d + 1 < len(kb) else None, j1 + d)
                        if w != A[i1 + d]: changes.append((A[i1 + d], w))
                        out.append(w)
                else:
                    ours = A[i1:i2]; refb = B[j1:j2]
                    if ''.join(ka[i1:i2]) == ''.join(kb[j1:j2]):          # one word split in two (or two joined): the form that is a real word
                        a_ok = all(self.freq[k] >= 3 for k in ka[i1:i2]); r_ok = all(self.freq[k] >= 3 for k in kb[j1:j2])
                        pick = refb if (r_ok and not a_ok) or (policy == 'ref' and not verified) else ours
                    else:
                        a_known = sum(1 for k in ka[i1:i2] if self.freq[k] >= 2); pick = refb if (policy == 'ref' or (not verified and a_known < len(ours)) or (verified and a_known == 0)) else ours
                        if policy == 'ours': pick = ours
                    if pick is refb: changes.append((' '.join(ours), ' '.join(refb))); out += [self.surface(t) for t in refb]
                    else: out += ours
                end_a = i2
            elif tag == 'delete':                                         # our words that the book text does not have
                dele = A[i1:i2]
                if j1 >= len(kb):                                          # after the last word of the hadith: the takhrij
                    continue
                if verified or policy == 'ours' or any(self.freq[k] >= 2 for k in ka[i1:i2]): out += dele; end_a = i2
                else: changes.append((' '.join(dele), ''))                 # unreadable noise inside the text
            elif tag == 'insert':                                          # words only the book text has: dropped by the reading
                ins = B[j1:j2]
                if verified or policy == 'ours' or len(ins) > ins_max: continue
                changes.append(('', ' '.join(ins))); out += [self.surface(t) for t in ins]
        # end of the hadith text = the position in A aligned with the last word of the book text
        last = None
        for tag, i1, i2, j1, j2 in ops:
            if j2 == len(kb) and tag in ('equal', 'replace'): last = i2
        if last is None:
            for tag, i1, i2, j1, j2 in ops:
                if tag == 'insert' and j2 == len(kb): last = i1
        if last is None: last = end_a
        return out, A[last:], {'ratio': ratio, 'changes': changes, 'cut': last}
