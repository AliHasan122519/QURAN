#!/usr/bin/env python3
"""Same as ocr_scans.py for a book that has only a PDF of page images (no viewer on archive.org): downloads the PDF of the first download of the book that has no scan viewer,
renders it at 300 dpi and reads each page twice with Tesseract.  usage: python3 -I scripts/ocr_pdf.py <OUT> <key>"""
import json, os, subprocess, sys, tempfile, urllib.parse, urllib.request, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ocr_scans_lib as L
OUT, KEY = sys.argv[1], sys.argv[2]
B = json.load(open(os.path.join(L.ROOT, 'data/booklists/books.json'), encoding='utf8')); b = next(x for x in B if x['key'] == KEY)
d = next(x for x in b['dls'] if x['id'] != b['reader']['id'])           # the printed edition (the reader shows the manuscript)
m = L.meta(d['id'])
tmp = tempfile.mkdtemp(); pdf = tmp + '/b.pdf'; data = None
for h in (m['d1'], m['d2']):                                              # the file is read from the item's own servers
    try: data = L.get(f"https://{h}{m['dir']}/{urllib.parse.quote(d['name'])}", 2); break
    except Exception as e: err = e
if data is None: raise err
open(pdf, 'wb').write(data); print('pdf', os.path.getsize(pdf), flush=True)
subprocess.run(['pdftoppm', '-r', '300', '-gray', '-png', pdf, tmp + '/pg'], check=True)
pages = sorted(glob.glob(tmp + '/pg-*.png')); print(len(pages), 'pages', flush=True)
from PIL import Image
for n, p in enumerate(pages):
    f = f'{OUT}/{KEY}/{n}.json'
    if os.path.exists(f): continue
    im = Image.open(p).convert('L'); w, h = im.size; im = im.point(lambda v: 255 if v > 150 else 0); im.save(p)
    rec = {'w': w, 'h': h, 'lines': L.lines_of(L.tess(p, True, True)), 'alt': L.tess(p, False, False)}
    os.makedirs(os.path.dirname(f), exist_ok=True); json.dump(rec, open(f, 'w', encoding='utf8'), ensure_ascii=False)
    if n % 10 == 0: print(n, flush=True)
print('finished', flush=True)
