"""Builds the list «رؤى وتعبيرها» (the side menu of the app): the dreams that the books themselves narrate together with the interpretation the interpreter gave.
Input: content/books.json (the «الكتب» tab, which is not touched). A dream is taken only where a book tells a particular person's dream («جاء رجل إلى ابن سيرين فقال: رأيت كأني…»,
«رأى رجل كأن…», «وقال آخر: رأيت… قلت: …») AND gives the interpretation in the same passage; the rules of the dictionaries («ومن رأى كأنه… فإنه…») are not dreams and are left in the «الكتب» tab.
The passage is copied word for word from the book; the only things done are cutting it at the point where the interpretation begins (the dream / the interpretation) and naming the
interpreter when the passage itself says who he is. Each book keeps its own version of a story that several books tell.
usage: python3 -I scripts/build_ruaa.py   [--dry]  ->  content/ruaa.json"""
import json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROWS = json.load(open('content/books.json', encoding='utf8'))['h']

# ---- what tells a particular person's dream ----
AR = r'[ء-ي]'
NOT_GENERIC = r'(?<!' + AR + r')(?<!من )(?<!ومن )(?<!فمن )(?<!إن )(?<!وإن )(?<!فإن )(?<!إذا )(?<!وإذا )(?<!فإذا )(?<!لو )(?<!متى )(?<!ومتى )(?<!كل من )(?<!ولو )(?<!وكل من )(?<!أن )(?<!وأن )(?<!فلو )(?<!ثم )'
DS_FIRST = re.compile(r'(?:رأيت|رأيتني|رأينا)\s+(?:في\s+(?:المنام|النوم|منامي|نومي|الحلم)|فيما\s+يرى\s+النائم|(?:كأني|كأنني|كأنه|كأنها|كأن|أني|أنني|أنه|أنها|أن)(?!' + AR + r'))')
SUBJ = r'(?:(?!الرائي|النائم|الإنسان|الناظر|المريض|الحامل|الرجل|المرأة|المسافر|التاجر\b|الغني|الفقير|الملك\b)(?:رجل|رجلا|إنسان|إنسانا|شخص|شخصا|امرأة|امرأته|أعرابي|أعرابيا|غلام|غلاما|جارية|فلان|فلانا|فلانة|أحدهم|بعضهم|' + AR + r'+\s+بن\s+' + AR + r'+(?:\s+بن\s+' + AR + r'+)?|أبو\s+' + AR + r'+|أم\s+' + AR + r'+|[ء-ي]+))'
DS_THIRD = re.compile(NOT_GENERIC + r'(?:رأى|رأت)\s+' + SUBJ + r'\s+(?:في\s+(?:منامه|نومه|منامها|المنام|النوم)|كأن|أنه|أنها|أن(?!' + AR + r'))')
DS_THIRD2 = re.compile(NOT_GENERIC + r'(?:رأى|رأت)\s+(?:في\s+(?:منامه|نومه|منامها)|كأنه|كأنها)')
# ---- what tells the interpretation begins ----
IC_STRONG = re.compile(r'(?:(?:ف|و)?(?:قصها|قصصتها|قص\s+رؤياه|قصت\s+رؤياها|قصصت\s+رؤياي)\s+(?:على|عند|إلى)\s+[^:؛.]{2,60}?\s+(?:فقال|فقالت|وقال|قال)\b)|(?:\s(?:فقلت|قلت)\s*(?:له|لها)?\s*[:،])|(?:\s(?:فعبرها|عبرها|فعبرتها|فعبرته|فسرها|ففسرها|(?:ف|و)?أول(?:ها|ته|تها|تهما|تهم|وها|وه|ت|ه)|(?:ف|و)?عبر(?:ها|ته|تها|وها))(?!' + AR + r'))|(?:\s(?:فقيل|وقيل|فقالوا|وقالوا)\s+(?:له|لها|لي)\s)|(?:\s(?:فقال|فقالت|قال|قالت)\s*(?:له|لها|لي|ابن\s+\S+|\S+\s+\S+)?\s*[:،])|(?:\s(?:وقال|وقالت)\s+(?:له|لها)\s*[:،])')
IC_WEAK = re.compile(r'\s(?:فقال|فقالت|قال|قالت|فقالوا)\s+(?!إني\b|إنني\b)')
NAMED = re.compile(r'ابن\s+سيرين|ابن\s+سرين|جعفر|ابن\s+المسيب|معبر|المعبر|الكرماني|رسول\s+الله|النبي|أبي\s+بكر|أبو\s+بكر|مسروق|الحسن\s+البصري|دانيال|الفيلسوف|المقدسي')                 # «فقال ابن سيرين تطأ امرأة…» in a text without punctuation: may also be a sentence said inside the dream
INTERP_WORDS = re.compile(r'تأويل|تعبير|عبر|يدل|تدل|دليل|فإن|لأن|ينال|تنال|تصير|يصير|تكون|يكون|تصيب|يصيب|تلد|تموت|يموت|فكان كذلك|فكذلك|صدقت|ترزق|يرزق|تتزوج|يتزوج|تسافر|يسافر|يحصل|تحصل|يقع|تقع|يذهب|تذهب|تأخذ|يأخذ|تعلم|اتق|تطأ|تستغفر|استغفر|ولد|مال|رزق|خير|شر|امرأة|زوجة|سلطان|ملك|مرض|موت|قتل|حرب|سفر|دين|علم|فقه')
TIER1 = re.compile(r'(?:^|\s)(?:وحكي|ويحكى|حكي|يحكى|وروي|روي|ويروى|وقد\s+بلغنا|بلغنا|ومن\s+الرؤيا\s+المعبرة|ومن\s+الحكايات|ومن\s+المنامات|ومن\s+الرؤيا|نادرة|حكاية|ومما\s+حكي|ومما\s+روي|وقد\s+حكي|وقد\s+روي|وجاء|جاء|وأتى|أتى|أتت|وجاءت|جاءت|وسأل|سأل|دخل\s+رجل|وقال\s+آخر|وقالت\s+أخرى|وقال\s+لي|قال\s+لي|وقال\s+إنسان|قال\s+إنسان|وقال\s+رجل|قال\s+رجل|وقالت\s+امرأة|قالت\s+امرأة|قال\s+المصنف|وقال\s+شخص)(?=\s|:)')
TIER2 = re.compile(r'(?:^|\s)(?:قال|وقال|فقال|وقالت|قالت)(?=\s|:)')
STORY = re.compile(r'(?:^|\s)(?:\((?:و[\u0621-\u064A ]{1,24})\)|وحكي|ويحكى|وروي|ويروى|وقد\s+بلغنا|ومن\s+الرؤيا\s+المعبرة|ومن\s+الحكايات|ومن\s+المنامات|نادرة|حكاية|ومما\s+حكي|ومما\s+روي|وقد\s+حكي|وقد\s+روي|ورأى|ورأت|وأتاه|وجاءه|وأتته|وجاءته|وسأله|وقال\s+آخر|وقالت\s+أخرى|وقال\s+لي|وقال\s+إنسان|وقال\s+رجل|وقالت\s+امرأة|وقال\s+شخص)(?=\s|:|\))')
OPEN = TIER1
SENT_END = re.compile(r'[.؛؟]\s+|\)\s+')
GENERIC_RESTART = re.compile(r'\s(?:ومن\s+رأى|وإن\s+رأى|فإن\s+رأى|فمن\s+رأى|ومن\s+سمع|وأما\s+من\s+رأى|فإن\s+رأى)\s')
TAIL = re.compile(r'\s+(?:ومثله|ومنه|وكذلك|فافهمه|والله\s+أعلم|وقال|وقيل|ومن|وإن|وان|ثم|و|أو|فإن|وأما|وقد|وهو|وهي)\s*[.،:]?\s*$')
# the interpreters the passages name (canonical form <- the spellings found in the books)
WHO = [('ابن سيرين', r'(?:محمد\s+بن\s+)?ابن\s+سيرين|ابن\s+سرين|محمد\s+بن\s+سيرين'), ('جعفر الصادق', r'جعفر\s+(?:الصادق|بن\s+محمد[^\s]*)'), ('سعيد بن المسيب', r'(?:سعيد\s+بن\s+)?ابن\s+المسيب|سعيد\s+بن\s+المسيب'),
       ('أبو بكر الصديق', r'أب[يو]\s+بكر(?:\s+الصديق)?'), ('الكرماني', r'الكرماني'), ('دانيال', r'دانيال'), ('الحسن البصري', r'الحسن\s+البصري'), ('ابن عباس', r'(?:عبد\s+الله\s+بن\s+)?ابن\s+عباس'),
       ('مسروق', r'مسروق'), ('الشعبي', r'الشعبي'), ('قتادة', r'قتادة'), ('النبي ﷺ', r'(?:النبي|رسول\s+الله)(?:\s+صلى\s+الله\s+عليه\s+وسلم)?'), ('الأوزاعي', r'الأوزاعي'), ('ابن شبرمة', r'ابن\s+شبرمة'),
       ('سليمان بن داود عليهما السلام', r'سليمان\s+بن\s+داود'), ('الإمام الشافعي', r'الشافعي'), ('عمر بن الخطاب', r'عمر\s+بن\s+الخطاب')]
def interpreter(dream, interp):
    """who interprets, as the passage itself says: the one who speaks first after «فقال» («فقال ابن سيرين: …»), else the one the dreamer went to («أتى ابن سيرين»); «قلت» = the author of the book"""
    if re.match(r'\s*(?:ف)?قلت', interp): return 'مؤلف الكتاب'
    for canon, rx in WHO:
        if re.match(r'\s*(?:ف|و)?(?:قال|قالت)\s+(?:له\s+|لها\s+)?(?:' + rx + r')(?![ء-ي])', interp): return canon
    for canon, rx in WHO:
        if re.search(r'(?:على|إلى|عند|لـ?|أتى|أتته|أتت|أتاه|سأل|سألت|ل)\s+(?:' + rx + r')(?![ء-ي])', dream) or re.search(r'(?:^|\s)(?:' + rx + r')\s+(?:رجل|امرأة|أعرابي|شخص)\s', dream[:60]):
            if canon == 'النبي ﷺ' and re.search(r'(?:قال|فقال)\s+(?:رسول|النبي)', dream[:40]): continue          # «قال رسول الله: رأيت…»: it is his dream, not necessarily his interpretation
            return canon
    return ''

def clean_end(t):
    t = t.strip()
    while TAIL.search(t): t = TAIL.sub('', t).strip()
    return t

def start_of(t, ds, floor, first):
    """where the story that holds the dream statement at ds begins (the nearest narrative opener before it, else the speech verb, else the statement itself)"""
    lo = max(floor, ds - 75); region = t[lo:ds]
    cuts = [m.end() for m in SENT_END.finditer(region)]
    base = lo + (cuts[-1] if cuts else 0)
    om = TIER1.search(t[base:ds])
    if om: return base + om.start() + (1 if t[base + om.start()].isspace() else 0)
    lo2 = max(floor, ds - 60); tm = list(TIER2.finditer(t[lo2:ds]))
    if tm and first: return lo2 + tm[-1].start() + (1 if t[lo2 + tm[-1].start()].isspace() else 0)
    return 0 if ds <= 3 else ds
CUELESS = re.compile(r'\s(?:وإنما\s+دل|وإنما\s+عبر|وذلك\s+أن|فعرض\s+(?:له|لها)|فكان\s+(?:كذلك|ذلك|كما))(?=\s)')
def anecdotes(t):
    """[(start, end, split_at)] of every dream+interpretation passage in the text of one row (split_at = -1 when the cut between the dream and the interpretation is uncertain)"""
    cand = sorted({m.start() for rx in (DS_FIRST, DS_THIRD, DS_THIRD2) for m in rx.finditer(t)})
    out = []; last_end = 0
    for ds in cand:
        if ds < last_end: continue
        first = DS_FIRST.match(t, ds) is not None
        if first and ds > 3 and not re.search(r'(?:قال|فقال|وقال|قالت|فقالت|قال\s+لي|:)\s*(?:\S+\s+){0,5}(?:إني\s+|إنني\s+|ال?ليلة\s+)?$', t[max(last_end, ds - 70):ds]) and not re.search(r'(?:^|\s)قلت\s*:\s*$', t[max(0, ds - 12):ds]):
            if not TIER1.search(t[max(last_end, ds - 75):ds]): continue           # «رأيت» of the author's own speech, not a dream told by someone
        start = start_of(t, ds, last_end, first)
        # the interpretation must come before the next story (the next narrated dream, or the next story opener of the book)
        bound = len(t)
        for c in cand:
            if c > ds + 12: bound = min(bound, start_of(t, c, ds + 12, DS_FIRST.match(t, c) is not None) if start_of(t, c, ds + 12, DS_FIRST.match(t, c) is not None) > ds + 12 else c); break
        sm = STORY.search(t, ds + 12)
        if sm: bound = min(bound, sm.start())
        im = next((m for m in IC_STRONG.finditer(t, ds + 6, bound) if m.start() - ds >= 12), None); strong = im is not None
        if not im:
            im = next((m for m in IC_WEAK.finditer(t, ds + 6, bound) if m.start() - ds >= 12), None)
            if im and NAMED.search(t[start:im.start()]): strong = True            # «أتى ابن سيرين رجل فقال رأيت… فقال…»: the interpreter is named in the passage
        if not im:
            cm = next((m for m in CUELESS.finditer(t, ds + 6, bound)), None)       # «…فحبلت وولدت؛ وإنما دل الفراش على المرأة»: the interpretation follows without «فقال»
            if cm: im = cm; strong = False
        if not im: continue
        end = bound
        g = GENERIC_RESTART.search(t, im.end() + 25)
        if g: end = min(end, g.start())
        cut = re.search(r'\s(?:ومثله|ومنه|وأعط|فافهمه|ونحو\s+ذلك\s+فقس|ومثل\s+ذلك)(?=\s|$)', t[im.end():end])
        if cut: end = im.end() + cut.start()
        seg = clean_end(t[start:end])
        if len(seg) < 40: continue
        dream, interp = seg[:im.start() - start], seg[im.start() - start:]
        body = re.sub(r'^[\s،:]*(?:فقلت|قلت|فقال|قال|فقالت|وقال)[\s،:]*(?:له|لها|لي)?[\s،:]*', '', interp).strip(' .،:؛/')
        if len(body) < (5 if re.match(r'\s*(?:ف)?قلت', interp) else (12 if strong else 20)): continue             # the passage ends where the interpretation should begin, or what follows is only a word
        if not strong and not INTERP_WORDS.search(interp): continue
        if not strong and re.search(r'(?:قالت|يقول|قائلا|فقال|قال)\s', dream[len(dream) // 3:]): sp = -1
        else: sp = im.start() - start
        out.append((start, start + len(seg), sp)); last_end = start + len(seg)
    return out

def main():
    rows = []; stat = collections.Counter(); bysrc = collections.defaultdict(list)
    for ref, text, expl, src in ROWS: bysrc[src].append((ref, text))
    seen = set()
    for src, lst in bysrc.items():
        for i, (ref, text) in enumerate(lst):
            t = text; prefix = ''
            if i and re.match(r'\s*(?:ف|و)?(?:قال|قالت)\s*:', t) and len(lst[i - 1][1]) < 700:
                prefix = lst[i - 1][1][-300:] + ' '                                          # the book's own cut fell between «جاء رجل إلى ابن سيرين» and «فقال: رأيت…»
            if i + 1 < len(lst) and re.search(r'(?:قلت|فقلت|قال|فقال|قالت)\s*[:،]?\s*$', t) and len(t) < 600: t = t + ' ' + lst[i + 1][1][:400]
            full = prefix + t
            res = anecdotes(full)
            nxt = lst[i + 1][1] if i + 1 < len(lst) else ''
            if (not res or (res and res[-1][1] >= len(full) - 2 and len(full[res[-1][0] + res[-1][2]:]) < 40 if res and res[-1][2] > 0 else False)) and nxt and re.search(r'(?:رأى|رأت|رأيت|رؤيا)', full) and re.match(r'\s*(?:ف|و)?(?:قال|قالت|قلت|فقلت|قيل)\b', nxt) and len(full) < 900:
                full2 = full + ' ' + nxt[:420]; res2 = anecdotes(full2)
                if len(res2) >= len(res): full, res = full2, res2
            for a, b, sp in res:
                if prefix and b <= len(prefix): continue
                seg = full[a:b]
                k = (src, re.sub(r'\W', '', seg)[:80])
                if k in seen: continue
                seen.add(k)
                dream, interp = (seg[:sp].strip(), seg[sp:].strip()) if sp > 0 else (seg.strip(), '')
                if src.startswith('المنامات') and not re.match(r'\s*(?:ف|و)?(?:قال\s+\S+\s+)?(?:أول|عبر|فسر)', interp[:60]) and not re.search(r'(?:ف|و)?(?:أول|عبر|فسر)(?:ها|ته|تها|ه|وها)\b', interp[:90]): continue      # «المنامات»: dreams of the dead told with their dialogue; only where someone interprets
                rows.append({'ref': ref, 'dream': dream, 'interp': interp, 'src': src, 'full': seg}); stat[src] += 1
    return rows, stat

def publish(rows):
    import content_lib as CL
    out = []
    for r in rows:
        by = interpreter(r['dream'], r['interp'])
        out.append(['', r['dream'], r['interp'], r['src'], by])
    CL.publish('ruaa', 'رؤى وتعبيرها', 'generic', {'h': out}, len(out), extra={'drawer': True, 'card': 'dream', 'placeholder': 'اكتب هنا', 'hint': 'رؤى ذكرها أصحاب الكتب المرجعية مع تعبيرها.'})
    return out
if __name__ == '__main__':
    rows, stat = main()
    print(len(rows), dict(stat), 'unsplit', sum(1 for r in rows if not r['interp']))
    if '--dry' not in sys.argv:
        out = publish(rows); print(collections.Counter(o[4] for o in out).most_common(14)); sys.exit(0)
    import random
    random.seed(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1)
    pool = [r for r in rows if 'البدر' not in r['src']] if len(sys.argv) > 2 else rows
    for r in random.sample(pool, min(24, len(pool))):
        print(f"[{r['src'][:16]}] {r['ref'][:30]}\n  الرؤيا: {r['dream'][:300]}\n  التعبير: {r['interp'][:260]}\n")
