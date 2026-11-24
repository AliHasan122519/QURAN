#!/usr/bin/env python3
"""Stage 1 of the text versions of the scanned books: reads every page image of a book's scan (archive.org) with Tesseract twice
(the accurate «tessdata_best» Arabic model, and the standard one), after binarising the page.  One JSON per page in <OUT>/<key>/<leaf>.json:
{"w","h","lines":[{"b":[l,t,r,b],"t":text,"c":mean confidence}],"alt":text of the standard model}.  Resumable.  The results are working files (not in the repository).
usage: python3 -I scripts/ocr_scans.py <OUT> [key …]       env: BEST=<dir holding ara.traineddata of tessdata_best>"""
import io, json, os, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = sys.argv[1]; ONLY = set(sys.argv[2:])
B = json.load(open(os.path.join(ROOT, 'data/booklists/books.json'), encoding='utf8'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_scans_lib import get, meta, page_image, tess, lines_of
def work(job):
    key, i, m, zname, n = job
    f = f'{OUT}/{key}/{n}.json'
    if os.path.exists(f): return
    try:
        im = Image.open(io.BytesIO(page_image(m, i, zname, n))).convert('L'); w, h = im.size
        im = im.point(lambda v: 255 if v > 150 else 0); d = tempfile.mkdtemp(); p = d + '/p.png'; im.save(p)
        rec = {'w': w, 'h': h, 'lines': lines_of(tess(p, True, True)), 'alt': tess(p, False, False)}
        os.remove(p); os.rmdir(d)
    except Exception as e:
        rec = {'err': str(e)[:200]}
    os.makedirs(os.path.dirname(f), exist_ok=True); json.dump(rec, open(f + '.tmp', 'w', encoding='utf8'), ensure_ascii=False); os.replace(f + '.tmp', f)
jobs = []
for b in B:
    if b['reader']['mode'] != 'embed' or (ONLY and b['key'] not in ONLY): continue
    d0 = next(x for x in b['dls'] if x['id'] == b['reader']['id'])
    m = meta(d0['id']); stem = os.path.splitext(d0['name'])[0]
    z = next((f['name'] for f in m['files'] if f['name'] == stem + '_jp2.zip'), None) or next((f['name'] for f in m['files'] if f['name'].endswith('_jp2.zip')), None)
    if not z: print('no image zip', b['key']); continue
    cnt = sum(1 for f in m['files'] if f['name'] == z[:-8] + '_page_numbers.json')
    pc = json.load(open(os.path.join(ROOT, 'data/booklists/pagecounts.json'), encoding='utf8')).get(b['key'], [[None, 0]])[0][1]
    print(b['key'], d0['id'], z[:40], 'pages', pc, flush=True)
    jobs += [(b['key'], d0['id'], m, z, n) for n in range(pc)]
print(len(jobs), 'pages to read', flush=True)
t0 = time.time(); done = 0
with ThreadPoolExecutor(4) as ex:
    for _ in ex.map(work, jobs):
        done += 1
        if done % 100 == 0: print(done, 'of', len(jobs), round(time.time() - t0), 's', flush=True)
print('finished', flush=True)
