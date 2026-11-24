"""Builds the two lists of the «المزيد» menu that hold books to read: «كتب علم التعبير» (content/kutubtabir.json) and «كتب الفراسة» (content/kutubfiras.json).
Source: data/booklists/books.json — every passage quoted there is checked against the page or the text it names, and every link against the site, by
scripts/verify_booklinks.py (needs the network). These books are NOT references of the «الكتب» tab and are never indexed for the search (drawer tabs are not).
A row: [title, «label ⏎ value» lines (all that an app which does not know this list shows), '', sources, '', '', the details as JSON (the book card of the new app)].
usage: python3 -I scripts/build_booklists.py"""
import json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
B = json.load(open('data/booklists/books.json', encoding='utf8'))
KINDS = {'tabir': ('kutubtabir', 'كتب علم التعبير', 'علم التعبير', 'أهمّ كتب تأويل الرؤى قديماً: اختر كتاباً لتعرف عنه وتقرأه أو تحمّله.'),
         'firasa': ('kutubfiras', 'كتب الفراسة', 'الفراسة', 'كتب في معرفة طباع الناس وأنماط شخصياتهم وصفاتهم وأساليبهم من ظاهرهم وسلوكهم، قديماً وحديثاً. للقراءة فقط وليست من مراجع البحث في تبويب «الكتب».')}
PC = json.load(open('data/booklists/pagecounts.json', encoding='utf8')) if os.path.exists('data/booklists/pagecounts.json') else {}   # scripts/page_counts.py
def with_pages(b):
    """The «عدد الصفحات» row of every book: the pages of the scanned file(s) the book offers (archive.org page list = what the viewer shows).
    A count the book's own card gives (the printed edition) stays as it is, and the scan's count is added beside it.  A book that has no scan (no downloads) or
    that is printed in the margin of another (`pagesSkip`) has none."""
    info = [list(r) for r in b['info']]; rows = PC.get(b['key']) or []
    if b.get('pagesSkip') or not rows: return info
    label = {x['name']: x['label'] for x in b['dls']}
    printed = any(k.startswith('عدد الصفحات') for k, _ in info)
    if len(b['dls']) == 1: new = [['عدد صفحات الملف المصوَّر' if printed else 'عدد الصفحات (الملف المصوَّر)', str(rows[0][1])]]
    elif all(re.match(r'^(المجلد|الجزء)', label[n]) for n, _ in rows) and len(rows) == len(b['dls']):
        new = [['عدد صفحات الملف المصوَّر' if printed else 'عدد الصفحات (الملف المصوَّر)', '%d (%s)' % (sum(n for _, n in rows), ' + '.join(str(n) for _, n in rows))]]
    else: new = [['عدد صفحات ' + re.sub(r' \(PDF\)$', '', label[nm]), str(n)] for nm, n in rows]
    at = max([i for i, (k, _) in enumerate(info) if k.startswith('عدد الصفحات')] + [len(info) - 1]) + 1 if printed else len(info)
    return info[:at] + new + info[at:]
for _b in B: _b['info'] = with_pages(_b)
W = str.maketrans('٠١٢٣٤٥٦٧٨٩٫', '0123456789.')
def west(t): return t.translate(W) if isinstance(t, str) else t          # numbers the app writes itself use the digits 0-9 (quoted passages stay word for word)
def mb(n): return ('%.1f' % (n / 1e6)) + ' ميغابايت'
def card(b):
    cv = dict(b['cover']); img = f"data/booklists/covers/{b['key']}.jpg"
    if os.path.exists(img):                                                        # the cover of the printed edition (the first page of the scan the book's page offers): the app shows it instead of the drawn one
        cv['img'] = f"covers/{b['key']}.jpg"; CL.publish_bytes(cv['img'], open(img, 'rb').read())
    assert b['kind'] in KINDS and 0 <= b['cover']['p'] <= 9 and 0 <= b['cover']['m'] <= 7, b['key']
    assert b['read']['url'].startswith('https://') and b['about'] and b['title'] and b['author'], b['key']
    same = lambda i: sum(1 for y in b['dls'] if y['id'] == i) > 1                       # an item that holds several files (volumes) is opened by the name of the file in the viewer
    d = [dict({'label': x['label'], 'url': 'https://archive.org/download/%s/%s' % (x['id'], urllib.parse.quote(x['name'])), 'size': mb(x['size']), 'id': x['id']},
              **({'sub': urllib.parse.quote(os.path.splitext(x['name'])[0])} if same(x['id']) else {}), **({'view': False} if x.get('view') is False else {})) for x in b['dls']]
    for x in b['dls']: assert x.get('size'), b['key'] + ': run verify_booklinks.py --write'
    rd = b['reader']; assert rd['mode'] in ('text', 'embed'), b['key']
    if rd['mode'] == 'text':
        bk = json.load(open('content/' + rd['file'], encoding='utf8'))              # the table of contents of the reader's text (scripts/build_bookreader.py)
        toc = [[a, west(t), i] for a, t, i in bk['toc']]; reader = {'mode': 'text', 'file': rd['file'], 'src': rd['src'], 'ocr': bk['ocr'], 'scan': rd.get('scan', ''), 'count': len(bk['p'])}; tocSrc = 'عناوين الكتاب نفسه في نصه الرقمي' + (' (قراءة آلية، فقد تكثر فيها الأخطاء)' if bk['ocr'] else '')
    else:
        toc = [[a, west(t), i, p] for a, t, i, p in rd['toc']]; reader = {'mode': 'embed', 'id': rd['id'], 'src': rd['src'], **({'manuscript': True} if rd.get('manuscript') else {})}; tocSrc = rd['tocSrc']
    return {'reader': reader, 'toc': toc, 'tocSrc': tocSrc, 'kind': KINDS[b['kind']][2], 'era': b['era'], 'author': b['author'], 'authorFull': west(b['authorFull']), 'coverTitle': b['coverTitle'], 'cover': cv,
            'info': [[west(k), west(v)] for k, v in b['info']], 'infoSrc': b['infoSrc'], 'about': [{'t': a['t'], 's': a['s']} for a in b['about']], 'note': west(b.get('note', '')), 'inApp': b['inApp'],
            'read': b['read'], 'dls': d}
tabs = {}
for b in B:
    tid = KINDS[b['kind']][0]; c = card(b)
    text = '\n'.join(f'{k}\t{v}' for k, v in [('المؤلف', west(b['authorFull'])), ('العصر', b['era'])] + [[west(k), west(v)] for k, v in b['info']])
    src = ' · '.join(dict.fromkeys(a['s'].split(' (')[0].split(' — ')[0] for a in b['about']))
    tabs.setdefault(tid, []).append([b['title'], text, '', src, '', '', json.dumps(c, ensure_ascii=False, separators=(',', ':'))])   # the details are the 7th field: an app that does not know them shows the readable lines only
for kind, (tid, label, _, sub) in KINDS.items():
    rows = tabs[tid]
    CL.publish(tid, label, 'generic', {'h': rows}, len(rows), extra={'drawer': True, 'card': 'library', 'menu': label, 'sub': sub, 'placeholder': 'اكتب هنا', 'hint': sub})
CL.prune_files('covers/', {f"covers/{b['key']}.jpg" for b in B})
# the order of the side menu: the lists of books before «حول التطبيق»
p = 'content/manifest.json'; m = json.load(open(p, encoding='utf8'))
last = [t for t in m['tabs'] if t['id'] == 'about']; m['tabs'] = [t for t in m['tabs'] if t['id'] != 'about'] + last
json.dump(m, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1); open(p, 'a').write('\n')
print({k: len(v) for k, v in tabs.items()})
