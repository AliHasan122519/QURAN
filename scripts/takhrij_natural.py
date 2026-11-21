"""Writes the takhrij of al-Jami' al-Saghir in plain words instead of the printed symbols («(ق 4) عن عمر بن الخطاب» → «رواه البخاري ومسلم وأبو داود… عن عمر بن الخطاب»).
The meaning of every symbol is the author's own key (the khutba of the book, printed pages 5 and 6 of the copy in `public/assets/al-jami-al-saghir.pdf`): nothing is added to it.
Where the key says «الحاكم فإن كان في مستدركه أطلق» (ك), «الدارقطني فإذا كان في السنن أطلق» (قط), «الخطيب فإذا كان في التاريخ أطلق» (خط), the bare symbol is the book named in the key; when the author
writes the book after the symbol («(حل قط) في غرائب مالك») his words are kept and no default book is added.
The grade symbols (صح، ح، ض) are the publisher's and stay in their own field (shown as «حكم السيوطي»).  Used by scripts/build_data.py; usage as a check: python3 -I scripts/takhrij_natural.py"""
import re, json
FULL = {'خد': 'البخاري في الأدب', 'تخ': 'البخاري في التاريخ', 'حب': 'ابن حبان في صحيحه', 'خ': 'البخاري', 'م': 'مسلم', 'ق': 'البخاري ومسلم', 'د': 'أبو داود', 'ت': 'الترمذي', 'ن': 'النسائي', 'ه': 'ابن ماجه',
        '4': 'أبو داود والنسائي والترمذي وابن ماجه', '3': 'أبو داود والنسائي والترمذي', 'حم': 'أحمد في مسنده', 'عم': 'عبد الله بن أحمد في زوائده', 'ك': 'الحاكم في المستدرك', 'طب': 'الطبراني في الكبير',
        'طس': 'الطبراني في الأوسط', 'طص': 'الطبراني في الصغير', 'ص': 'سعيد بن منصور في سننه', 'ش': 'ابن أبي شيبة', 'عب': 'عبد الرزاق في الجامع', 'ع': 'أبو يعلى في مسنده', 'قط': 'الدارقطني في السنن',
        'فر': 'الديلمي في مسند الفردوس', 'حل': 'أبو نعيم في الحلية', 'هب': 'البيهقي في شعب الإيمان', 'هق': 'البيهقي في السنن', 'عد': 'ابن عدي في الكامل', 'عق': 'العقيلي في الضعفاء', 'خط': 'الخطيب في التاريخ'}
BARE = {'ك': 'الحاكم', 'قط': 'الدارقطني', 'خط': 'الخطيب', 'حم': 'أحمد', 'حب': 'ابن حبان', 'خد': 'البخاري', 'تخ': 'البخاري', 'عم': 'عبد الله بن أحمد', 'طب': 'الطبراني', 'طس': 'الطبراني', 'طص': 'الطبراني',
        'ص': 'سعيد بن منصور', 'عب': 'عبد الرزاق', 'ع': 'أبو يعلى', 'فر': 'الديلمي', 'حل': 'أبو نعيم', 'هب': 'البيهقي', 'هق': 'البيهقي', 'عد': 'ابن عدي', 'عق': 'العقيلي'}
GRADES = {'صح', 'ح', 'ض'}
ALIAS = {'طبس': 'طس', 'نخ': 'تخ'}      # «طبس» is the print of «طس»; «نخ» (not in the key) is «تخ» (al-Bukhari in the History): both agreed by the recogniser and al-Munawi
UNCLEAR = '؟'                # a symbol the printed copy itself does not make out (a letter the print lost, or one that is not in the author's key): written «؟» in the raw takhrij
UNCLEAR_TEXT = '(رمز لم يتضح في الطبعة)'
DIG = str.maketrans('٣٤', '34')
def segment(tok):
    """a token of the print that the reader may have glued («دن» = «د ن», «خدم» = «خد م»): the symbols it is made of, or None"""
    tok = tok.translate(DIG)
    if tok in FULL: return [tok]
    best = None
    def go(s, acc):
        nonlocal best
        if not s:
            if best is None or len(acc) < len(best): best = list(acc)
            return
        for k in range(min(2, len(s)), 0, -1):
            if s[:k] in FULL: go(s[k:], acc + [s[:k]])
    go(tok, [])
    return best
def join(items):
    return items[0] if len(items) == 1 else (' و'.join(items) if len(items) == 2 else '، '.join([items[0]] + ['و' + x for x in items[1:]]))
def names(symbols, specified):
    items = []
    for s in symbols:
        n = UNCLEAR_TEXT if s == UNCLEAR else (BARE.get(s) if specified and s in BARE else FULL[s])
        if n not in items: items.append(n)
    return join(items)
PROPHET = 'عن النبي ﷺ'
def with_prophet(v):
    """«عن أنس» → «عن أنس عن النبي ﷺ»: the author names the Companion (or the Successor, with «مرسلا») who narrates from the Prophet, so the chain ends with these two names.
    Only a clean clause is touched: one «عن» followed by at most five words, no book name («في …»), no second «عن», no «موقوفا/مقطوعا» (those are sayings of the Companion or the Successor, not of the Prophet), no «عنه»."""
    ms = list(re.finditer(r'(?:^|\s)عن\s+', v))
    if not ms: return v
    pre, tail = v[:ms[0].start()], v[ms[0].end():]
    # only the first to hear it from the Prophet is named (the owner's request): «X عن أبيه عن جده» is X's grandfather, «X عن أبيه Y» is Y, «X عن أبيه» is X's father («والد X»)
    m = re.fullmatch(r'(?P<x>.+?)\s+عن\s+أبيه\s+عن\s+جده', tail) or re.fullmatch(r'(?P<x>.+?)\s+عن\s+أبيه\s+(?P<n>.+)', tail) or re.fullmatch(r'(?P<x>.+?)\s+عن\s+أبيه', tail)
    if m and ' عن ' not in ' ' + m.group('x') + ' ' and not re.search(r'\sفي\s|وعن|عنه|\d|[()]|مرسلا|موقوف|مقطوع|معضلا|رحمهم|قال', tail) and not re.match(r'عن\s', m.groupdict().get('n') or '') and len(m.group('x').split()) <= 8:
        g = m.groupdict(); who = ('جدّ ' + g['x']) if m.re.pattern.endswith('جده') else (g['n'] if g.get('n') else 'والد ' + g['x'])
        return (pre + (' ' if pre else '') + 'عن ' + who + ' ' + PROPHET).strip()
    if len(ms) != 1: return v
    q = re.search(r'\s+(مرسلا|معضلا)$', tail); qual = ''
    if q: qual = ' ' + q.group(1); tail = tail[:q.start()]
    if not tail or tail in ('أبيه', 'جده') or len(tail.split()) > 5 or re.search(r'\sفي\s|^في\s|موقوف|مقطوع|مرفوع|زاد|\d|عنه|وعن|مسلا|[()]', tail): return v
    return (pre + (' ' if pre else '') + 'عن ' + tail + ' ' + PROPHET + qual).strip()
def natural(raw, none=False):
    """(natural text, problems): the takhrij in words; problems = the tokens that are not symbols of the key.
    none=True: the printed entry has no source at all (only its grade, or nothing): the natural text is empty"""
    s = raw.strip(); problems = []
    parts = re.split(r'(\([^()]*\))', s); items = []
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            toks = p[1:-1].split()
            if toks and all(t in GRADES for t in toks): continue                      # the grade has its own field
            if len(toks) > 1: toks = [UNCLEAR if t == 'ح' else t for t in toks if t not in ('صح', 'ض')]   # a grade inside a group of sources stays in the grade field; a lone «ح» among sources is not a symbol of the key
            syms = []
            for t in toks:
                t = ALIAS.get(t, t)
                if t == UNCLEAR: syms.append(t); continue
                if t.startswith('و') and len(t) > 1 and segment(t[1:]): t = t[1:]; syms.append('+')
                seg = segment(t)
                if seg is None: problems.append(t)
                else: syms += seg
            syms = [x for x in syms if x != '+']
            if not syms: problems.append('empty brackets')
            items.append(('g', syms))
        elif p.strip(): items.append(('t', p.strip()))
    while len(items) > 1 and items[-1][0] == 'g' and items[-2][0] == 't' and re.search(r'(?:^|\s)عن\s', items[-2][1]) and set(items[-1][1]) <= {'خ', 'ص', 'ن'}:
        items.pop()                  # «(د هب) عن جابر (خ)»: every source is followed by its narrator, so a last bracket after the narrator is the grade as printed (a dotted «ح»), not al-Bukhari
    if problems: return raw, problems
    if not items: return ('', []) if none else (raw, ['nothing but a grade, or nothing'])
    res = ''; an = False
    for idx, (k, v) in enumerate(items):
        if k == 'g':
            nxt = items[idx + 1][1] if idx + 1 < len(items) and items[idx + 1][0] == 't' else ''
            nm = names(v, bool(re.match(r'في\s', nxt)))
            if not res: res = 'رواه ' + nm
            elif re.search(r'(?:^|\s)زاد$', res): res += ' ' + nm
            elif an: res += '، ورواه ' + nm; an = False
            else: res += ' و' + nm
        else:
            v = with_prophet(v)
            if not res: res = v if v.startswith('عن ') else 'رواه ' + v      # the print itself names no source before «عن»
            else: res += ' ' + v
            if re.search(r'(?:^|\s)عن\s', v): an = True
    return re.sub(r'\s+', ' ', res).strip(), []
if __name__ == '__main__':
    d = json.load(open('content/jami.json', encoding='utf8'))['h']; bad = []
    for i, r in enumerate(d):
        n, pr = natural(r[3])
        if pr: bad.append((i, r[6], r[3], pr))
    print(len(d), 'entries;', len(bad), 'with something that is not a symbol of the key:')
    for b in bad: print('  ', b)
    for i in (0, 1, 5, 80, 135, 274, 6000):
        print(d[i][3], '→', natural(d[i][3])[0])
