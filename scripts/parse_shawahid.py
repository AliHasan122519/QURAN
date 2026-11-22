"""Extracts the verses quoted as evidence (أبيات الاستشهاد) from four mother books of the shawahid (OpenITI digital texts, data/shawahid/*.txt.gz):
شرح شواهد المغني (السيوطي) · شرح أبيات مغني اللبيب (البغدادي) · المقاصد النحوية (العيني) · شرح أبيات سيبويه (السيرافي).
In these texts a verse is a paragraph of its own with the two hemistichs joined by « ... ». Nothing is changed in a verse except the removal of page marks, footnote marks and the
brackets that open/close a quotation.   usage: python3 -I scripts/parse_shawahid.py  ->  data/shawahid/verses_parsed.json"""
import gzip, re, json, collections
BOOKS = [('suyuti_shawahid_mughni', 'شرح شواهد المغني'), ('baghdadi_abyat_mughni', 'شرح أبيات مغني اللبيب'), ('ayni_maqasid', 'المقاصد النحوية في شرح شواهد شروح الألفية'), ('sirafi_abyat_sibawayh', 'شرح أبيات سيبويه')]
AR = re.compile(r'[ء-يً-ٰٟ]')
START_BAD = re.compile(r'^(?:و?قوله|و?قال|أي|يعني|و?يروى|ويروى|الشاهد|من قصيدة|و?أنشد|وأنشده|انظر|وفي رواية|و?رواه|و?روي|إلى أن قال|ومنها|و?منها)\b')
def clean(l):
    l = re.sub(r'\(¬\s*\d+\)', ' ', l); l = re.sub(r'\bms\d+\b', ' ', l); l = re.sub(r'PageV\d+P\d+', ' ', l)
    l = l.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', l).strip()
def words(s): return [w for w in s.split() if AR.search(w)]
out = []; stats = collections.Counter()
for key, title in BOOKS:
    raw = gzip.open(f'data/shawahid/{key}.txt.gz', 'rt', encoding='utf8').read()
    raw = re.sub(r'PageV\d+P\d+\s*#\s', '\n# ', raw)                           # a page break in the middle of a paragraph
    lines = raw.split('\n'); i0 = next(k for k, l in enumerate(lines) if 'Header#End' in l) + 1
    ref = ''
    paras = []; cur = None
    for l in lines[i0:]:
        if l.startswith('### '):
            h = re.sub(r'^###\s*\|*\s*(?:AUTO|CHECK)?\s*', '', l).strip(); h = re.sub(r'[\[\]]', '', h); h = re.sub(r'\bms\d+\b|PageV\d+P\d+', ' ', h); h = re.sub(r'\s+', ' ', h).strip()
            if h and not h.startswith('فائدة'): ref = h
            cur = None; continue
        if l.startswith('# '): cur = [l[2:]]; paras.append((ref, cur))
        elif l.startswith('~~') and cur is not None: cur.append(l[2:])
    texts = [(ref_, clean(' '.join(parts_))) for ref_, parts_ in paras]
    for pi, (ref, parts) in enumerate(paras):
        t = clean(' '.join(parts))
        t = re.sub(r'^\(\s*', '', t); t = re.sub(r'\s*\)\s*$', '', t)             # «( … )» around a quoted verse
        if t.count(' ... ') != 1 or len(parts) > 2: continue
        a, b = [x.strip() for x in t.split(' ... ')]
        a = re.sub(r'^[\(\)\s«»"]+', '', a); b = re.sub(r'[\(\)\s«»"]+$', '', b)
        wa, wb = words(a), words(b)
        stats['seen'] += 1
        if not (2 <= len(wa) <= 9 and 2 <= len(wb) <= 9): stats['len'] += 1; continue
        if START_BAD.match(a) or re.search(r'[0-9A-Za-z:؟«»]|\.\.\.|…', a + b): stats['bad'] += 1; continue
        if re.search(r'إلى آخر|البيت|انتهى|الأبيات|\.\s*\.|الشاهد', a + ' ' + b): stats['cut'] += 1; continue
        if '(' in a or ')' in a or '(' in b or ')' in b: stats['paren'] += 1; continue
        before = texts[pi - 1][1] if pi > 0 and texts[pi - 1][0] == ref else ''
        after = []
        for rr, tt in texts[pi + 1: pi + 40]:
            if rr != ref or re.match(r'^\d+ - ', tt) or tt.startswith('(الشاهد') : break
            if rr != ref: break
            if ' ... ' in tt: continue                                           # the other verses of the same poem
            after.append(tt)
        out.append({'ref': ref, 'a': a, 'b': b, 'src': title, 'before': before, 'after': after})
# the same verse quoted by several books: one entry, all the books
def key(e): return re.sub(r'[^ء-ي]', '', e['a'] + e['b'])
by = collections.OrderedDict()
for e in out:
    k = key(e)
    if k in by:
        if e['src'] not in by[k]['srcs']: by[k]['srcs'].append(e['src'])
        by[k]['ctx'].append({'before': e['before'], 'after': e['after']})
    else: by[k] = {'ref': e['ref'], 'a': e['a'], 'b': e['b'], 'srcs': [e['src']], 'ctx': [{'before': e['before'], 'after': e['after']}]}
res = list(by.values())
json.dump(res, open('data/shawahid/verses_parsed.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print(dict(stats), 'verses', len(out), 'unique', len(res), collections.Counter(len(e['srcs']) for e in res))
