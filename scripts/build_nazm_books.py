"""Builds the two reader texts of the poems of «نظم علم التعبير»: content/books/alfiya-wardiyya.json and content/books/abir.json.
They are made from the rows of the tab «النظم» (content/alfiya.json, built by scripts/build_alfiya.py) — nothing is typed here: every verse is «number - first hemistich ... second hemistich»,
each chapter heading is a table-of-contents entry, and for the Alfiya each verse's printed page is a page mark. Run build_alfiya.py first.
usage: python3 -I scripts/build_nazm_books.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
rows = json.load(open('content/alfiya.json', encoding='utf8'))['h']
SPEC = {'الألفية الوردية': ('alfiya-wardiyya', 'الملف المقدَّم من صاحب المشروع (صور صفحات الطبعة المحققة)، مقروءاً صفحةً صفحة وبقي أثر قراءته في ملاحظة الكتاب'),
        'العبير في التعبير': ('abir', 'نسخة المكتبة الشاملة (الكتاب رقم 102770)، الأبيات 1–103')}
for poem, (key, src) in SPEC.items():
    mine = [r for r in rows if r[5] == poem]; assert mine, poem
    p, toc, pg, last, lastpg = [], [], [], None, None
    for n, page, chap, a, b, _, shown in mine:
        if chap != last: toc.append([1, chap, len(p)]); last = chap
        if page and page != lastpg: pg.append([len(p), f'ص{page}']); lastpg = page
        p.append(f'{shown} - {a} ... {b}')
    assert len(toc) >= 3
    CL.publish_file(f'books/{key}.json', {'v': 1, 'key': key, 'ocr': False, 'src': src, 'toc': toc, 'p': p, 'pg': pg})
    print(key, len(p), 'verses', len(toc), 'chapters', len(pg), 'page marks')
