#!/usr/bin/env python3
"""The scan of a book that the owner supplied himself as a file of page pictures (no copy of it on archive.org): its pages are stored as content files
(content/scans/<key>/NNN.jpg, opened on demand by the app's own page viewer), one PDF of the same pages (the download), and the first page as the cover.
Nothing is redrawn or re-compressed: the pictures are the ones of the owner's file, in the order the file shows them.
usage: python3 -I scripts/build_own_scans.py <key> <file.docx>   (only the Word file of a book of data/booklists/books.json with an `own` record)"""
import io, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_lib as CL
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KEY, DOCX = sys.argv[1], sys.argv[2]
B = json.load(open(os.path.join(ROOT, 'data/booklists/books.json'), encoding='utf8')); b = next(x for x in B if x['key'] == KEY); own = b['own']
z = zipfile.ZipFile(DOCX); doc = z.read('word/document.xml').decode('utf8'); rel = z.read('word/_rels/document.xml.rels').decode('utf8')
tg = {}
for m in re.finditer(r'<Relationship [^>]*>', rel):
    i = re.search(r'Id="([^"]+)"', m.group(0)); t = re.search(r'Target="([^"]+)"', m.group(0))
    if i and t: tg[i.group(1)] = t.group(1)
names = [tg[r] for r in re.findall(r'r:embed="([^"]+)"', doc)]
assert len(names) == own['pages'] and len(set(names)) == len(names), (len(names), own['pages'])
pics = [z.read('word/' + n) for n in names]
for n, raw in enumerate(pics):
    im = Image.open(io.BytesIO(raw)); assert im.format == 'JPEG' and im.size[0] > 300, (n, im.format, im.size)
    CL.publish_bytes(f"scans/{KEY}/{n:03d}.jpg", raw, bump=False)
ims = [Image.open(io.BytesIO(r)).convert('RGB') for r in pics]
buf = io.BytesIO(); ims[0].save(buf, 'PDF', save_all=True, append_images=ims[1:], resolution=100.0); pdf = buf.getvalue()
CL.publish_bytes(f"scans/{KEY}.pdf", pdf)
open(os.path.join(ROOT, f'data/booklists/covers/{KEY}.jpg'), 'wb').write(pics[0])
print(KEY, len(pics), 'pages', len(pdf), 'bytes pdf')
