"""Reads, from the commentary of the four books around a verse, who said it and on what occasion — only what the books themselves state (no guess)."""
import re
STOPN = {'وبعده', 'وقبله', 'وأوله', 'وأولها', 'أوله', 'أولها', 'من', 'في', 'يخاطب', 'يهجو', 'يمدح', 'يرثي', 'وهو', 'وهي', 'قال', 'يصف', 'والبيت', 'وقيل', 'على', 'ويروى', 'يقول', 'رضي', 'الصحابي', 'الجاهلي', 'الإسلامي', 'المخضرم', 'الراجز', 'الشاعر', 'وصدره', 'وعجزه', 'صدره', 'عجزه', 'وتمامه', 'تمامه', 'ثم', 'يعني', 'أي', 'ولم', 'وقد', 'وفيه', 'وكان', 'كان', 'وأنشده', 'أنشده', 'وهذا', 'هذا', 'وروي', 'رواه', 'وإنما', 'والرواية', 'وبعد', 'بعده', 'قبله', 'وقال', 'والشاهد', 'الشاهد', 'ويقال', 'يقال', 'إذ', 'لما', 'حين', 'حيث', 'وقوله', 'قوله', 'واسمه', 'اسمه', 'وكنيته', 'ومطلعها', 'ومطلعه', 'مطلعها', 'مطلعه', 'وهما', 'وهن', 'وبعدهما', 'وقبلهما', 'ورواية', 'بيت', 'البيت', 'وبيته', 'والمصنف', 'المصنف', 'أيضا', 'وهو', 'ونسبه', 'نسبه', 'وليس', 'وليست', 'وأما', 'وأن', 'أن', 'إن', 'ولا', 'لا', 'بل', 'لكن', 'ولكن', 'أو', 'وإن', 'فإن', 'لأن', 'وذكر', 'ذكر', 'وفي', 'وعلى', 'ومن', 'إلى', 'عن', 'مع', 'ما'}
BADNAME = {'الشاعر', 'شاعر', 'الراجز', 'بعضهم', 'غيره', 'بعض', 'أحد', 'رجل', 'امرأة', 'المصنف', 'أبي', 'الله', 'النحويين', 'سيبويه', 'الكتاب', 'هذا', 'هذه', 'ذلك', 'مجهول', 'أحدهم', 'الأعشى'}      # «الأعشى» alone is ambiguous: kept only with a qualifier (see below)
HONOR = re.compile(r'\s+(?:رضي|رحمه|رحمهما|عليه|صلى|الجاهلي|الإسلامي|المخضرم|الصحابي|الراجز|الأموي|العباسي|الشاعر|الفارس|المشهور|المعروف|الأعور|الأسدي الجاهلي).*$')
def _name(tokens):
    out = []
    for t in tokens:
        t = t.strip('،,.:;()«»"')
        if not t or t in STOPN: break
        out.append(t)
        if len(out) >= 6: break
    if not out: return ''
    n = ' '.join(out); n = HONOR.sub('', n).strip()
    n = re.sub(r'^(?:ل|لـ)(?=ال)', '', n)
    if len(n) < 3 or n in BADNAME or re.search(r'[0-9]', n): return ''
    if any(w in ('البيت', 'القصيدة', 'الأبيات', 'الرجز', 'قصيدة', 'الكتاب') for w in n.split()): return ''
    return n
P1 = re.compile(r'(?:^|[\s،:])(?:و?هو|و?هذا|و?هذه|و?هما|و?البيت|و?الأبيات|و?الرجز)\s+(?:من\s+)?(?:أبيات|بيتين|قصيدة|قصيدته|رجز|أرجوزة|مقطوعة|كلمة|قصيدة طويلة|أبيات ثلاثة|أبيات لـ?|قصيدة له|أبيات له)?\s*(?:ل|لـ)(?!م\b)(\S+(?:\s+\S+){0,6})')
P2 = re.compile(r'(?:قائله|قائلها|قائلهما|ينسب\s+(?:هذا\s+)?(?:البيت\s+)?إلى|لقائله|والقائل|وقائله|وقائلها)\s*:?\s*(?:هو\s+)?(\S+(?:\s+\S+){0,6})')
P3 = re.compile(r'^(?:و?قال|و?أنشد|و?قول|و?وقال)\s+(.+?)\s*:\s*$')
P4 = re.compile(r'(?:^|[\s،:])(?:و?هو|و?هي|و?البيت|و?الأبيات)\s+(?:من\s+(?:أبيات|قصيدة)\s+)?(?:لل?)(\S+(?:\s+\S+){0,6})')
def poet_of(ctx):
    """the poet named by the books around the verse: the most frequent name among the quotations; '' when no book says"""
    names = []
    for c in ctx:
        cand = []
        if c['before']:
            m = P3.match(c['before'])
            if m: cand.append(_name(m.group(1).split()))
        for t in c['after'][:3]:
            for rx in (P2, P1):
                m = rx.search(t)
                if m: cand.append(_name(m.group(1).split()))
        names += [x for x in cand if x]
    if not names: return ''
    import collections
    return collections.Counter(names).most_common(1)[0][0]
CUES = [('يمدح', 'مدح'), ('مدح', 'مدح'), ('يهجو', 'هجاء'), ('هجا', 'هجاء'), ('يرثي', 'رثاء'), ('رثى', 'رثاء'), ('يخاطب', 'مخاطبة'), ('خاطب', 'مخاطبة'), ('يعتذر', 'الاعتذار إلى'), ('يعاتب', 'عتاب'), ('يتغزل', 'التغزل'), ('يشكو', 'الشكوى'), ('يتوعد', 'الوعيد'), ('يحرض', 'التحريض'), ('يخاطبها', 'مخاطبة'), ('يخاطبه', 'مخاطبة'), ('يصف', 'وصف'), ('وصف', 'وصف'), ('يفتخر', ''), ('يفخر', '')]
NOUN_FIRST = {'يفتخر': 'الفخر', 'يفخر': 'الفخر'}
OBJ_STOP = {'وبعده', 'وقبله', 'وأوله', 'وأولها', 'ثم', 'وقد', 'وكان', 'وهو', 'وهي', 'من', 'أنه', 'بأنه', 'وبعدها', 'فقال', 'فيقول', 'يقول', 'وقال', 'وقوله', 'إذ', 'حين', 'لما', 'لأن', 'ويروى', 'وفيه', 'وهذا', 'قال', 'ويقال', 'وروي', 'والذي', 'الذي', 'التي', 'وأنشد', 'حيث', 'وذلك', 'وإنما', 'وهما', 'فيها', 'فيه', 'وأولهما', 'وفي'}
NAMES = set()                                                                        # filled by the builder with the poets' names found in the books
def occasion_of(ctx):
    """«يقال عند … / في …»: the occasion as the books word it. Only the strong cues: «يمدح/يهجو/يرثي/يخاطب/يعاتب/يعتذر إلى X», «يفتخر», and «قالها لما/حين …»"""
    for c in ctx:
        for t in c['after'][:4]:
            m = re.search(r'(?:قاله|قالها|قالهما|قال هذا|قال ذلك|أنشدها|أنشده)\s+(?:الشاعر\s+)?(لما|حين|عندما|حينما)\s+(\S+(?:\s+\S+){0,8})', t)
            if m:
                tail = _trim(m.group(2).split())
                if tail and len(tail.split()) >= 2 and not re.search(r'[؟?]|آخره|الى آخر|إلى آخر', tail): return f'عندما {tail}'
            for cue, noun in CUES:
                if noun in ('وصف', 'التغزل', 'الشكوى', 'الوعيد', 'التحريض', 'مخاطبة') and cue not in ('يخاطب', 'خاطب'): continue
                m = re.search(r'(?:^|[\s،:])' + cue + r'(?:\s+(?:بها|بهذا|بهما|به|لها|له))?(?:\s+(\S+(?:\s+\S+){0,5}))?', t)
                if not m: continue
                if cue in NOUN_FIRST: return f'في {NOUN_FIRST[cue]}'
                obj = _trim((m.group(1) or '').split())
                if not obj or re.search(r'[؟?]|آخره|الى آخر|إلى آخر', obj) or obj.split()[0].startswith('و'): continue
                if not (re.search(r'\b(?:بن|ابن|أبي|أبو|ذي|ذو)\b', obj) or obj in NAMES): continue      # only a named person: «عند مدح عمر بن عبد العزيز», not «عند مخاطبة الواحد…»
                return f'عند {noun} {obj}'
    return ''
def _trim(ws):
    out = []
    for w in ws:
        w2 = w.strip('،,.:;()«»"')
        if not w2 or w2 in OBJ_STOP or w.endswith('،') and out and len(out) >= 1: 
            if w2 and w2 not in OBJ_STOP and out is not None: out.append(w2)
            break
        out.append(w2)
        if w.endswith(('.', ':', '؛')): break
    if out and len(out[0]) >= 4 and out[0].endswith('ا') and out[0] not in ('أبا', 'أخا', 'حتى', 'إذا', 'عليا', 'ملكا') and len(out) == 1: out[0] = out[0][:-1]   # «جريرا» → «جرير» (accusative alif of a lone name)
    r = re.sub(r'\s*[-–—].*$', '', ' '.join(out[:7])); return re.sub(r'\s+(?:رضي|رحمه|عليه|صلى)\b.*$', '', r).strip()

SCHOLARS = {'ابن جني', 'أبو حيان', 'المبرد', 'القالي', 'ابن قتيبة', 'سيبويه', 'الأخفش', 'الفراء', 'الزجاجي', 'الجوهري', 'ابن الشجري', 'ابن هشام', 'الأعلم', 'ابن يعيش', 'الزمخشري', 'السيوطي', 'الشنتمري', 'الأصمعي', 'أبو عبيدة', 'أبو زيد', 'ابن دريد', 'ثعلب', 'ابن الأنباري', 'ابن السكيت', 'الجرجاني', 'ابن السيرافي', 'أبو علي', 'الفارسي', 'السيرافي', 'ابن مالك', 'الكسائي', 'ابن الأعرابي', 'أبو عمرو', 'أبو العباس', 'ابن عصفور', 'البغدادي', 'العيني', 'الخليل', 'يونس', 'الرضي', 'ابن الحاجب', 'ابن خلف', 'ابن بري', 'ابن السراج', 'الزجاج', 'ابن ولاد', 'الأزهري', 'الصاغاني', 'السهيلي', 'التبريزي', 'ابن جماعة', 'ابن الصائغ', 'ابن عقيل', 'الدماميني', 'الشمني', 'الأشموني', 'الفراء', 'ابن عباس', 'ابن عمر', 'ابن مسعود', 'ابن سيده', 'ابن فارس', 'ابن منظور', 'الأسود', 'ابن قتيبه', 'الآخر', 'آخر', 'أبو حنيفة', 'أبو بكر', 'الأخفش الأصغر', 'السيد المرتضى', 'المرتضى', 'الأشموني', 'ابن الحاجب', 'الكوفيين', 'البصريين', 'الراوي', 'الأصمعي'}
JUNK = re.compile(r'بعض|وأورده|وساق|خاطب|كذا|فتح|يقرض|الساعة|وصلناك|يعقل|يزل|الذي|مساجد|سميت|أبياتا|فتزوج|قالت|فمن|الناهدة|بفتح|بكسر|بضم|فيه|وقيل|ويقال|وفي|معاني|أمير المؤمنين|مرة|الثديين|وقد')
def clean_poet(n):
    n = re.sub(r'\s*[-–—].*$', '', n).strip(); n = re.sub(r'\s+(?:قالها|قاله|خاطب بها|خاطب)$', '', n).strip()
    if not n or JUNK.search(n) or n in SCHOLARS or len(n.split()) > 5: return ''
    return n
def resolve_lam(n, known):
    """«لفرزدق» (from «للفرزدق»): the lam of the preposition swallowed the alif of the article; chosen by what the books write elsewhere"""
    if n.startswith('ل') and not n.startswith('لل') and len(n) > 3:
        alt = 'ا' + n
        if known.get(alt, 0) > known.get(n, 0): return alt
        if n[1] in 'أإآ' and known.get(n, 0) <= 1: return alt                           # «لأعشى» → «الأعشى»
    return n
def poets(rows):
    """rows: list of ctx lists. -> list of poet names (or '')"""
    import collections
    raw = [_poet_raw(c) for c in rows]
    known = collections.Counter(n for r in raw for n in r if n)
    out = []
    for r in raw:
        r = [clean_poet(resolve_lam(n, known)) for n in r if n]
        r = [n for n in r if n]
        out.append(collections.Counter(r).most_common(1)[0][0] if r else '')
    cnt = collections.Counter(n for n in out if n)
    # a name seen once, with no «بن/أبو/ذو» in it, is accepted only if it is one word of a well-known shape (the books name him alone)
    return [n if n and (cnt[n] >= 2 or re.search(r'\b(?:بن|ابن|أبو|أبي|ذو|ذي)\b', n)) else '' for n in out]
def _poet_raw(ctx):
    names = []
    for c in ctx:
        if c['before']:
            m = P3.match(c['before'])
            if m: names.append(_name(m.group(1).split()))
        for t in c['after'][:3]:
            for rx in (P2, P1):
                m = rx.search(t)
                if m: names.append(_name(m.group(1).split()))
    return [x for x in names if x]
