"""Builds the text of each book that the in-app reader shows, with its table of contents (فهرس): content/books/<key>.json.
Sources: the digital texts of OpenITI (data/books/*, and the texts of Madarij / Turuq / Zaydan fetched from OpenITI into data/booklists/src/ by scripts/fetch_book_sources.sh).
Only the digital artefacts are removed (page / line marks, editor tokens): the words of the book are untouched; the table of contents is made of the book's own headings
(the headings of the digital text), with the printed page marks kept as «ج ص». Books read from a machine reading of a scan (OCR) are flagged `ocr`.
The files are listed in content/manifest.json (`files`) with their SHA-256, so the app updates them like any other content.
usage: python3 -I scripts/build_bookreader.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
SRC = 'data/booklists/src/'
B = 'data/books/'
SPECS = [
 dict(key='manamat-ibn-abi-dunya', file=B + 'manamat.txt', toc='manamat'),
 dict(key='qadiri', file=B + 'qadiri.txt', toc='ocr-qadiri', ocr=True),
 dict(key='badr-munir', file=B + 'badr_munir.txt', toc='pipe'),
 dict(key='ibn-ghannam', file=B + 'ibn_ghannam.txt', toc='pipe'),
 dict(key='isharat', file=B + '0873IbnShahinZahiri.Isharat.Shamela0009968-ara1', toc='pipe'),
 dict(key='tatir-anam', file=B + 'tatir_anam.txt', toc='pipe'),
 dict(key='muntakhab', file=B + 'muntakhab.txt', toc='pipe'),
 dict(key='tabir-artemidorus', file=SRC + 'hunayn.txt', toc='ocr-hunayn', ocr=True),
 dict(key='ilm-firasa-hadith', file=SRC + 'zaydan.txt', toc='pipe'),
]
KEY_OF_SRC = {'المنامات (ابن أبي الدنيا)': 'manamat-ibn-abi-dunya', 'القادري في التعبير': 'qadiri', 'البدر المنير في علم التعبير': 'badr-munir', 'تعبير الرؤيا (ابن غنام المقدسي)': 'ibn-ghannam',
              'الإشارات في علم العبارات': 'isharat', 'تعطير الأنام في تعبير المنام': 'tatir-anam', 'منتخب الكلام في تفسير الأحلام': 'muntakhab'}
def corrections(key):
    """the plain misprints of the digital copy that were checked against the printed page (data/books/corrections.json, each with its reason): the same list «الكتب» uses"""
    return [c for c in json.load(open(B + 'corrections.json', encoding='utf8')) if KEY_OF_SRC.get(c['src']) == key]
def apply_corrections(key, paras, toc):
    for c in corrections(key):
        n = 0
        for i, p in enumerate(paras):
            if c['find'] in p: n += p.count(c['find']); paras[i] = p.replace(c['find'], c['replace'])
        for e in toc:
            if c['find'] in e[1]: e[1] = e[1].replace(c['find'], c['replace'])
        assert n == c.get('rcount', c['count']), f"reader {key}: correction «{c['find']}» matched {n} times, expected {c.get('rcount', c['count'])}"
def ar(n): return str(n)                                   # numbers are shown with the digits 0-9 (the owner's rule for everything the app writes itself)
PAGE = re.compile(r'PageV(\d+)P(\d+)')
BLANK = re.compile(r'\bصفحة فارغة\b')              # the digital copy's note for a printed page that holds only the editor's footnotes (it is not the book's words)
TOK = re.compile(r'-{3,}\s*NO PAGE NO\s*-{3,}|\bPARATEXT\b|\bphysiognomy\b|\bAUTO\b|\bms\d+\b|@[A-Za-z0-9]{1,5}@|%~%|\^|\\|¬|‏|‎|﻿|\bCHECK\b|\bEDITOR\b|\bPRE\b|\bPOST\b|\$|#')
def clean(t):
    t = BLANK.sub(' ', PAGE.sub(' ', t)); t = re.sub(r'\s%\s', ' … ', t); t = TOK.sub(' ', t); t = re.sub(r'\s*\|\s*', ' ', t)
    t = re.sub(r'\(\s*\)|\[\s*\]|«\s*»', ' ', t); t = re.sub(r'\s+([،؛:.؟!)\]»])', r'\1', t); t = re.sub(r'([(\[«])\s+', r'\1', t)
    return re.sub(r'\s+', ' ', t).strip()
def parse(path):
    """-> items [text, isHeading (None = a page mark alone), level, page mark], and the set of volumes seen"""
    raw = open(path, encoding='utf8').read().split('\n'); vols = set(); items = []; cur = None
    end = next((i for i, l in enumerate(raw) if l.startswith('#META#Header#End#')), None)
    if end is None: end = max((i for i, l in enumerate(raw[:80]) if l.startswith('#META')), default=-1)
    for l in raw[end + 1:]:
        pm = PAGE.search(l)
        if pm: vols.add(int(pm.group(1)))
        h = re.match(r'^#{1,3}\s*\|+\s*(.*)$', l); lvl = len(re.match(r'^#{1,3}\s*(\|+)', l).group(1)) if h else 0
        if not h:
            h = re.match(r'^###\s+(?:\$\s*\d+\s*-\s*)?(.*)$', l); lvl = 2 if h else 0
        if h:
            if cur is not None: items.append(cur); cur = None
            items.append([h.group(1), True, min(lvl, 3), pm.group(0) if pm else None]); continue
        if l.startswith('# ') or l == '#':
            if cur is not None: items.append(cur)
            cur = [l[2:], False, 0, pm.group(0) if pm else None]
        elif l.startswith('~~'):
            if cur is None: cur = ['', False, 0, None]
            cur[0] += ' ' + l[2:]
            if pm and not cur[3]: cur[3] = pm.group(0)
        elif PAGE.fullmatch(l.strip()):
            items.append(['', None, 0, l.strip()])                    # a mark alone: the next paragraph starts on this page
        elif l.strip() and not l.startswith('![') and not l.startswith('######') and not l.startswith('# ----'):
            if cur is None: cur = ['', False, 0, None]
            cur[0] += ' ' + l.strip()
    if cur is not None: items.append(cur)
    return items, vols
def label(pg, vols):
    m = PAGE.match(pg); v, p = int(m.group(1)), int(m.group(2))
    if p == 0: return ''                                         # the marks of the front matter («PageV00P000») name no printed page
    return (f'ج{ar(v)} ' if len(vols) > 1 and v else '') + f'ص{ar(p)}'
def split_long(t, limit=1400):
    """a paragraph longer than the limit (a book whose digital text marks no paragraphs) is cut at the entry marks « - ( » or at the end of a sentence, never inside a word"""
    if len(t) <= limit: return [t]
    out = []
    for seg in re.split(r'\s+-\s+(?=\()', t):
        if len(seg) <= limit: out.append(seg); continue
        buf = ''
        for sent in re.split(r'(?<=[.؟!؛])\s+', seg):
            if buf and len(buf) + len(sent) > 900: out.append(buf); buf = sent
            else: buf = (buf + ' ' + sent).strip()
        if buf: out.append(buf)
    return out
def shape(items, vols):
    paras = []; heads = []; pages = []; pend = None
    for t, is_h, lvl, pg in items:
        if is_h is None: pend = pg; continue
        t = clean(t)
        if pg: pend = pg
        if not t: continue
        if pend:
            lb = label(pend, vols)
            if lb: pages.append([len(paras), lb])
            pend = None
        for k, seg in enumerate(split_long(t) if not is_h else [t]):
            i = len(paras); paras.append(seg.strip()); heads.append((i, lvl) if is_h and k == 0 else None)
    return paras, heads, pages
LABEL = re.compile(r'^(الباب|الفصل|فصل|المقالة|باب)\s+\S+(\s+\S+){0,3}$')
def tidy_title(t):
    t = re.sub(r'\bAUTO\b|\*', ' ', t)
    t = re.sub(r'^\s*\[\s*(?:فصل|باب)\s*:\s*\d+\s*\]\s*', '', t)                       # «[فصل: 1] الفصل الأول» (the editor's number before the title)
    t = re.sub(r'^\s*\d+\s*-?\s*(?=[\(\[]?[\u0621-\u064A])', '', t)             # a number before the title
    t = re.sub(r'^\(([^()]{2,60})\)\s*(?=\S)', r'\1 — ', t)                       # «(الباب الأول) في تأويل…» -> «الباب الأول — في تأويل…»
    t = re.sub(r'\s*\[?\d+/\d+[آأب]?\]?\s*$', '', t)
    t = t.strip(); op = sum(t.count(c) for c in '(['); cl = sum(t.count(c) for c in ')]')
    if op > cl: t = re.sub(r'^[\(\[]\s*', '', t)
    if cl > op: t = re.sub(r'\s*[\)\]]$', '', t)
    if t.startswith('(') and t.endswith(')'): t = t[1:-1]
    if t.startswith('[') and t.endswith(']'): t = t[1:-1]
    return re.sub(r'\s+', ' ', t.strip(' -:،.'))
def toc_pipe(paras, heads):
    toc = []; last = None
    for i, h in enumerate(heads):
        if not h: continue
        t = tidy_title(paras[i])
        if not t: continue
        if toc and i - last == 1 and toc[-1][0] == h[1] and LABEL.match(toc[-1][1]) and not LABEL.match(t) and ' — ' not in toc[-1][1]:
            toc[-1][1] += ' — ' + t; last = i; continue                       # a label heading followed at once by its subject (الباب الأول — في رؤية الله…) is one title
        toc.append([h[1], t, i]); last = i
    return dedupe(toc)
def dedupe(toc):
    out = []; seen = set()
    for lv, t, i in toc:
        half = len(t) // 2
        if len(t) > 8 and ' — ' in t and t.split(' — ')[0] == t.split(' — ')[-1]: t = t.split(' — ')[0]
        if i in seen or (out and out[-1][1] == t): continue
        seen.add(i); out.append([lv, t, i])
    return sorted(out, key=lambda x: x[2])
def toc_manamat(paras, heads):
    toc = [[1, 'مقدمة الرواة والإسناد', 0]]
    for i, p in enumerate(paras):
        m = re.match(r'^(\d+) ', p)
        if m and (int(m.group(1)) - 1) % 50 == 0: toc.append([1, f'الروايات من {ar(m.group(1))}', i])
        if heads[i] and 'باب' in p: toc.append([1, tidy_title(p), i])
    return dedupe(toc)
OK_OCR = re.compile(r'^[ء-يً-ٟ\s\-—()٠-٩0-9:،]+$')
def toc_ocr(paras, heads, allow, strip=lambda t: t):
    toc = []; last = None
    for i, p in enumerate(paras):
        if not (heads[i] and re.match(allow, tidy_title(p))): continue
        t = strip(tidy_title(p))
        if not t or not OK_OCR.match(t) or len(t) < 5: continue
        if toc and i - last <= 2 and re.match(r'^(الفصل|المقالة|الباب)', toc[-1][1]) and not re.match(r'^(الفصل|المقالة|الباب)', t): toc[-1][1] += ' — ' + t
        else: toc.append([1, t, i])
        last = i
    return dedupe(toc)

def main():
    for sp in SPECS:
        items, vols = parse(sp['file']); paras, heads, pages = shape(items, vols)
        if sp['toc'] == 'pipe': toc = toc_pipe(paras, heads)
        elif sp['toc'] == 'manamat': toc = toc_manamat(paras, heads)
        elif sp['toc'] == 'ocr-qadiri': toc = toc_ocr(paras, heads, r'^(الفصل|المقالة|الباب|فصل)\s+\S+')
        else: toc = toc_ocr(paras, heads, r'^(\[\d+\]\s*)?(في\s+\S+|المقالة\s+\S+|الباب\s+\S+)', lambda t: re.sub(r'\s*\(\d*\)?\s*$', '', re.sub(r'^\[\d+\]\s*', '', t)).strip())
        apply_corrections(sp['key'], paras, toc)
        head_idx = {h[0] for h in toc}
        book = {'v': 1, 'key': sp['key'], 'ocr': bool(sp.get('ocr')), 'toc': toc, 'p': paras, 'pg': pages}
        CL.publish_file(f"books/{sp['key']}.json", book)
        print(sp['key'], 'paragraphs', len(paras), 'chars', sum(map(len, paras)), 'toc', len(toc), 'pages', len(pages))
def prune():
    CL.prune_files('books/', {f"books/{sp['key']}.json" for sp in SPECS})
if __name__ == '__main__': main(); prune()
