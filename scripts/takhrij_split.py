"""Split an entry into hadith text (matn) and takhrij (authors/books, narrators, symbols, grade).
The earlier split cut only at the first group of known symbols, so entries whose takhrij starts with an author/book name
("ابن عساكر عن أبي هريرة (ض)", "الحكيم عن ...") kept those names INSIDE the hadith text.
The tail is parsed from the END with two learned resources (learned from the book itself, nothing typed by hand):
  * NARR  - how likely a word is part of a takhrij (ratio of its occurrences inside takhrij segments of the entries that have a symbol group);
  * SRC   - author/book phrases: frequent 1-5 word phrases that stand right before «عن <narrator>» in the tails of the entries.
Tail grammar (from the end):  [(symbols) | (grade) | «عن» NARRATOR | SRC-phrase [في BOOK]] repeated.
A «عن» that is not followed by a narrator ("نهى عن النياحة") is hadith text and is never moved."""
import re, collections
def nt(t): return re.sub(r'[ً-ٰٟـ‎‏]', '', t)
def is_p(t): return t.startswith('(') or t.endswith(')') or t in '()'
SYMS = {'خد','تخ','حب','خ','م','ق','د','ت','ن','ه','4','3','٤','٣','حم','عم','ك','طب','طس','طص','ص','ش','عب','ع','قط','فر','حل','هب','هق','عد','عق','خط','طبس'}
PRE = ('ابن', 'وابن', 'أبو', 'وأبو', 'أبي', 'وأبي', 'بن', 'أبا', 'و', 'عبد', 'وعبد', 'الإمام')
AN = ('عن', 'وعن', 'وعنه', 'عنه')
# authors / books named in the takhrij of al-Jami' al-Saghir that the learned phrase list can miss (spelled as printed; matched after normalisation)
SEED = ['البزار', 'الحاكم', 'الحكيم', 'الحكم', 'الحرث', 'القضاعي', 'الطيالسي', 'الخرائطي', 'الشيرازي', 'المرهبي', 'السجزي', 'البغوي', 'البعوي', 'المرزبان',
        'النقاش', 'الخلال', 'الحلواني', 'الخليلي', 'البارودي', 'العطريف', 'الغطريف', 'السمان', 'الفراء', 'البرقي', 'الرافعي', 'هناد', 'سمويه', 'الروياني', 'المحاملي',
        'الطحاوي', 'العسكري', 'الدارمي', 'الإسماعيلي', 'الاسماعيلي', 'الأصبهاني', 'الهروي', 'الشافعي', 'البيهقي', 'الضياء', 'الدارقطني', 'الأزدي', 'تمام', 'المخلص',
        'الخطيب', 'السلمي', 'الرازي', 'الصابوني', 'الشحامي', 'الأبهري', 'الخليعي', 'البانياسي', 'القالي', 'الجرباذقاني', 'الطرسوسي', 'الاطرابلسي', 'المديني',
        'أبو الشيخ', 'أبو نعيم', 'ابن أبي الدنيا', 'أبي الدنيا', 'ابن السني', 'ابن السنى', 'ابن عساكر', 'ابن النجار', 'ابن لال', 'ابن قانع', 'ابن مردويه', 'ابن سعد',
        'ابن منده', 'ابن شاهين', 'ابن زنجويه', 'ابن المبارك', 'ابن عبد البر', 'ابن عدي', 'ابن خزيمة', 'ابن صصري', 'ابن حبان', 'ابن راهويه', 'ابن جرير', 'ابن الأعرابي',
        'الحسن بن سفيان', 'يعقوب بن سفيان', 'أبو بكر الشافعي', 'أبو الحسن بن صخر', 'أبو عروبة', 'عبد بن حميد', 'محمد بن نصر', 'الحرث بن أبي أسامة', 'النقاش', 'أبو سعيد النقاش', 'الزبير بن بكار', 'القاضي عبد الجبار', 'المرهبي', 'الانباري', 'الأنباري', 'ابن الأنباري']
class Model:
    def __init__(self, pairs, texts):
        tk, mt = collections.Counter(), collections.Counter()
        for matn, k in pairs:
            for t in k.split(): tk[nt(t)] += 1
            for t in matn.split(): mt[nt(t)] += 1
        self.tk, self.mt = tk, mt
        # source phrases: frequent phrases right before a narrator clause in tails
        cnt = collections.Counter()
        for tx in texts:
            w = [nt(t) for t in tx.split()]
            for j in range(1, len(w)):
                if w[j] in AN and j + 1 < len(w) and self.is_narr_start(w, j + 1) and len(w) - j <= 12:
                    seen = set()
                    for e in range(j, max(0, j - 5), -1):                      # the phrase ends right before «عن» or up to 4 words earlier («أبو الشيخ في التوبيخ عن»)
                        if any(is_p(x) for x in w[e:j]): break
                        for n in range(1, 5):
                            if e - n >= 0 and not any(is_p(x) for x in w[e - n:e]): seen.add(' '.join(w[e - n:e]))
                    for g in seen: cnt[g] += 1
        cands = {k for k, v in cnt.items() if v >= 3}
        occ = collections.Counter()
        for tx in texts:
            w = [nt(t) for t in tx.split()]
            for n in range(1, 6):
                for j in range(0, len(w) - n + 1):
                    g = ' '.join(w[j:j + n])
                    if g in cands:
                        if (j > 0 and w[j - 1] in AN) or (j + n < len(w) and w[j + n] in ('بن', 'ابن')): continue          # used as part of a narrator's name
                        occ[g] += 1
        # purity: how often the phrase really is an author/book name (stands right before a narrator clause) among all its occurrences
        tot = collections.Counter(nt(t) for tx in texts for t in tx.split())
        def ok(k):
            if occ[k] == 0 or cnt[k] / occ[k] < (0.4 if ' ' not in k else 0.5): return False
            if ' ' not in k and tot[k] >= 150 and cnt[k] / occ[k] < 0.85: return False              # very common words (الله، الجنة، يوم...) are hadith text, never an author name
            return True
        src = {k for k in cands if ok(k)} | {nt(x) for x in SEED}
        # a phrase that begins with a very common hadith word (القيامة، الله، الجنة…) is hadith text + a name: keep only names whose first word is rare or a name particle
        src = {k for k in src if not (k.startswith('في ') and (tot[k.split()[1]] >= 150 or k.split()[1] == 'تمام'))}
        seed = {nt(x) for x in SEED}
        after_an = collections.Counter()                                  # words that follow «عن» are narrators (أنس، جابر، عائشة), not authors
        for tx in texts:
            w = [nt(t) for t in tx.split()]
            for j in range(len(w) - 1):
                if w[j] in AN: after_an[w[j + 1]] += 1
        # a learned one-word «author» is kept only if it looks like a name (nisba «…ي», e.g. البيهقي) or is practically never hadith text; words like «الغضب» (a book title in «ذم الغضب») are not authors
        src = {k for k in src if ' ' in k or k in seed or (k.endswith('ي') and len(k) > 4) or (k.startswith('و') and k[1:] in seed) or (after_an[k] < 5 and self.tk.get(k, 0) >= 5 and self.tk.get(k, 0) / max(1, self.tk.get(k, 0) + self.mt.get(k, 0)) >= 0.7)}
        self.TH = {k.split()[1] for k in src if k.startswith('في ') and len(k.split()) >= 2 and tot[k.split()[1]] < 150}
        self.src = {k for k in src if ' ' not in k or k.split(' ', 1)[0] in PRE or k.split(' ', 1)[0] == 'في' or tot[k.split(' ', 1)[0]] < 150}
    def ratio(self, w):
        a, b = self.tk.get(w, 0), self.mt.get(w, 0)
        return a / (a + b) if a + b >= 2 else 0.0
    def is_narr_start(self, w, i):
        return i < len(w) and (is_p(w[i]) or self.ratio(w[i]) >= 0.5 or w[i] in ('أبي', 'ابن', 'أم', 'بنت', 'عبد', 'أبو'))
    def boundary(self, text, hint=None):
        raw = text.split(); toks, pos = [], []                       # a parenthesised group of symbols is ONE token
        k = 0
        while k < len(raw):
            t = raw[k]
            if t.startswith('(') and not t.endswith(')'):
                j = k
                while j + 1 < len(raw) and j - k < 8 and not raw[j].endswith(')'): j += 1
                if raw[j].endswith(')'): toks.append(' '.join(raw[k:j + 1])); pos.append(k); k = j + 1; continue
            toks.append(t); pos.append(k); k += 1
        w = [nt(t) for t in toks]; i = len(toks)
        def phrase_end(i):
            if i > 0 and w[i - 1].startswith('و') and len(w[i - 1]) > 4 and w[i - 1][1:] in self.src and not is_p(toks[i - 1]):
                i -= 1; return i, True
            for n in range(5, 0, -1):
                if i - n >= 0 and ' '.join(w[i - n:i]) in self.src and not any(is_p(x) for x in toks[i - n:i]):
                    i -= n
                    while i > 0 and w[i - 1] in PRE and not is_p(toks[i - 1]): i -= 1
                    return i, True
            return i, False
        while i > 0:
            moved = False
            while i > 0 and is_p(toks[i - 1]): i -= 1; moved = True                    # symbol groups and grade
            for k in range(i - 1, max(-1, i - 11), -1):
                if is_p(toks[k]): break
                if w[k] in AN and (self.is_narr_start(w, k + 1) or pos[k] == hint or (i - k <= 8 and phrase_end(k)[1])) and k + 1 < i:
                    i = k; moved = True
                    i, _ = phrase_end(i)                                                 # author/book phrase right before it
                    while True:                                                           # lists of authors sharing one «عن»
                        j, ok = phrase_end(i)
                        if not ok and i > 0 and w[i - 1] == 'في': j, ok = phrase_end(i - 1)         # «ابن السني في عمل يوم وليلة»: the title's «في» is takhrij only when an author stands before it
                        if not ok:                                                            # «البيهقي في شعب الإيمان / في الدعوات»: a known author, then «في» + a title of up to 4 words
                            for f in range(i - 2, max(-1, i - 6), -1):
                                if f < 0 or is_p(toks[f]): break
                                if w[f] == 'في':
                                    j2, ok2 = phrase_end(f)
                                    if ok2: j, ok = j2, True
                                    break
                        if not ok: break
                        i = j
                    break
            if not moved: break
        # the first group of known symbols is certainly takhrij: everything from it on is takhrij, plus the author names standing right before it
        q = next((k for k, t in enumerate(toks) if t.startswith('(') and (lambda g: g and all(x in SYMS for x in g))(re.findall(r'[^\s()]+', nt(t)))), None)
        if q is not None and q < i:
            i = q
        if q is not None:                                                      # «ابن سعد عن ابن عوف (م) عن محمد»: an author + «عن» narrator standing right before the first symbols
            for k in range(i - 2, max(-1, i - 7), -1):
                if k < 0 or is_p(toks[k]): break
                if w[k] in AN and k + 1 < i:
                    j, ok = phrase_end(k)
                    if ok: i = j
                    break
        while True:
            j, ok = phrase_end(i)
            if not ok and i > 0 and w[i - 1] == 'في': j, ok = phrase_end(i - 1)
            if not ok: break
            i = j
        # an unknown author standing before a known book title («X بن Y في جزئه عن ...»): take the name chain that precedes the title
        TITLE = self.TH | {'كتاب', 'تاريخ', 'فضل', 'فضائل', 'ذم', 'ذكر', 'أدب', 'مناقب', 'أحبار', 'أخبار', 'علوم', 'فوائد', 'امالي', 'معجم', 'مشيخه', 'جزء', 'جزءه', 'مسند'}
        if i + 1 < len(toks) and w[i] == 'في' and w[i + 1] in TITLE:
            steps = 0; i0 = i
            while i > 0 and steps < 6:
                t = w[i - 1]; left = w[i - 2] if i >= 2 else ''
                nisba = t.startswith('ال') and t.endswith('ي') and len(t) > 4
                if is_p(toks[i - 1]): break
                if t in PRE or t == 'بن' or nisba or left in ('بن', 'ابن') or left in PRE or (i < len(w) and w[i] == 'بن'): i -= 1; steps += 1
                else: break
        # a title of a book that is not in the learned list («في تاريخ قزوين», «في أدب الإملاء»): «في» + a known title-opening word, right before the tail
        if i > 0 and not (i < len(w) and w[i] == 'في'):
            for f in range(i - 1, max(-1, i - 6), -1):
                if is_p(toks[f]): break
                if w[f] == 'في' and f + 1 < i and (w[f + 1] in self.TH or w[f + 1] in ('كتاب', 'تاريخ', 'فضل', 'فضائل', 'ذم', 'أدب', 'مناقب')) and f > 0:
                    i0 = i; i = f; steps = 0
                    while i > 0 and steps < 6:
                        t = w[i - 1]; left = w[i - 2] if i >= 2 else ''; nisba = t.startswith('ال') and t.endswith('ي') and len(t) > 4
                        if is_p(toks[i - 1]): break
                        if t in PRE or t == 'بن' or nisba or left in ('بن', 'ابن') or left in PRE or w[i] == 'بن': i -= 1; steps += 1
                        else: break
                    if steps == 0: i = i0                                   # no author stands before the title: it is hadith text
                    break
        # a list of authors: «وكيع في الغرر وابن مردويه في التفسير (خط)» — the tail opens with «و+author»; an earlier «NAME في TITLE» in the same list is takhrij too
        if 0 < i < len(w) and w[i].startswith('و') and len(w[i]) > 3 and (w[i][1:] in self.src or w[i] in ('وابن', 'وأبو', 'وأبي', 'وعبد')):
            for f in range(i - 2, max(0, i - 5), -1):
                if is_p(toks[f]): break
                if w[f] == 'في' and f >= 1 and not is_p(toks[f - 1]) and not (w[f - 1] in AN) and w[f - 1] not in ('الله', 'قال', 'وقال'):
                    g = f - 1
                    while g > 0 and w[g - 1] in PRE and not is_p(toks[g - 1]): g -= 1
                    if g > 0 and f - g <= 3: i = g
                    break
        while i > 0 and w[i - 1] in ('رواه', 'ورواه', 'وأورده', 'اخرجه'): i -= 1
        return pos[i] if i < len(pos) else len(raw)
