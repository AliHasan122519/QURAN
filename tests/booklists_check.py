"""«كتب علم التعبير» و«كتب علم الفراسة»: فحص بلا شبكة لما نُشر في content/ مقابل data/booklists/books.json، وأن كتب الفراسة (وكل كتب القائمتين) ليست من مراجع تبويب «الكتب».
الفحص بالشبكة (الاقتباسات والروابط والملفات): python3 -I scripts/verify_booklinks.py
usage: python3 -I tests/booklists_check.py"""
import json, re, sys, urllib.parse
ok = True
def check(name, cond, detail=''):
    global ok; ok &= bool(cond); print('PASS' if cond else 'FAIL', '|', name, detail)
B = json.load(open('data/booklists/books.json', encoding='utf8')); M = {t['id']: t for t in json.load(open('content/manifest.json', encoding='utf8'))['tabs']}
for kind, tid in (('tabir', 'kutubtabir'), ('firasa', 'kutubfiras')):
    t = M[tid]; rows = json.load(open(f'content/{t["file"]}', encoding='utf8'))['h']; mine = [b for b in B if b['kind'] == kind]
    check(f'{tid}: drawer list with the library card, not a search tab', t.get('drawer') is True and t.get('card') == 'library' and t['count'] == len(rows) == len(mine), f'{len(rows)} books')
    for r, b in zip(rows, mine):
        c = json.loads(r[6])
        check(f'{b["key"]}: title/author/cover', r[0] == b['title'] and c['author'] == b['author'] and 0 <= c['cover']['p'] <= 9 and 0 <= c['cover']['m'] <= 7)
        check(f'{b["key"]}: no field an old app would show badly (explanation, by, who are empty; the text is «label ⏎ value» lines)', r[2] == '' and r[4] == '' and r[5] == '' and all(len(l.split('\t')) == 2 for l in r[1].split('\n')))
        check(f'{b["key"]}: the source link (kept for verification only; the app shows no external link) is on shamela.ws/archive.org (https)', re.match(r'^https://(shamela\.ws/book/\d+(/\d+)?|archive\.org/details/[\w.\-]+)$', c['read']['url']) is not None, c['read']['url'])
        rd = c['reader']
        if rd['mode'] == 'text':
            bk = json.load(open('content/' + rd['file'], encoding='utf8')); n = len(bk['p'])
            check(f'{b["key"]}: the reader file exists in the manifest, its table of contents is the one shown on the book page, every entry inside the text', rd['file'] in {f['file'] for f in json.load(open('content/manifest.json', encoding='utf8'))['files']} and [list(t) for t in c['toc']] == [[a, re.sub(r'[٠-٩]', lambda m: str(ord(m.group(0)) - 0x660), t), i] for a, t, i in bk['toc']] and all(0 <= t[2] < n for t in c['toc']) and rd['count'] == n and rd['ocr'] == bk['ocr'], f'{len(c["toc"])} entries, {n} paragraphs')
        else:
            check(f'{b["key"]}: scan viewer of archive.org with a table of contents (title, scan leaf or none, printed page)', re.match(r'^[\w.\-]+$', rd['id']) is not None and len(c['toc']) > 20 and all(len(t) == 4 and (t[2] is None or 0 <= t[2] < 400) for t in c['toc']), f'{len(c["toc"])} entries')
        check(f'{b["key"]}: numbers the app writes itself use the digits 0-9 (authorFull, info, toc titles, sizes)', not re.search(r'[٠-٩]', c['authorFull'] + ''.join(k + v for k, v in c['info']) + ''.join(t[1] for t in c['toc']) + ''.join(d['size'] for d in c['dls'])))
        check(f'{b["key"]}: every download is an archive.org/download link with a size', all(re.match(r'^https://archive\.org/download/[\w.\-]+/[^/\s]+\.pdf$', d['url'], re.I) and re.match(r'^\d+\.\d ميغابايت$', d['size']) and d['label'] for d in c['dls']), f'{len(c["dls"])} files')
        check(f'{b["key"]}: every quoted passage names its source', all(a['t'] and a['s'] for a in c['about']))
        if not c['dls']: check(f'{b["key"]}: a book with no PDF says why, and has a text to save', bool(c['note']) and c['reader']['mode'] == 'text')
# the books of both lists are not references of the «الكتب» tab
books = json.load(open('content/books.json', encoding='utf8'))['h']; names = {r[3] for r in books}
check('«الكتب» keeps its eight references only (none of the physiognomy books, none of the new lists)', len(names) == 8 and not any('الفراسة' in n or 'الطرق الحكمية' in n or 'مدارج' in n for n in names), '; '.join(sorted(names))[:120])
check('no physiognomy book title is a source of any row of «الكتب»/«رؤى وتعبيرها»/«مقارنة المعبِّرين»', all(not any(k in (r[3] if len(r) > 3 else '') for k in ('الفراسة', 'الطرق الحكمية', 'مدارج السالكين')) for f in ('books', 'ruaa', 'muqaranat') for r in json.load(open(f'content/{f}.json', encoding='utf8'))['h']))
check('the manifest keeps «حول التطبيق» last in the side menu', [t for t in M if M[t].get('drawer')][-1] == 'about')
print('OK' if ok else 'FAILED'); sys.exit(0 if ok else 1)
