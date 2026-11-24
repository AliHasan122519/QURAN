#!/usr/bin/env python3
"""Put the tables of contents of the scan-only books into data/booklists/books.json.
Each data/booklists/toc/<key>.json was transcribed by eye from the printed contents page of the scan (or, where
the printed book has none, from the chapter headings printed on its pages) and is NOT generated text.
Formats of the "items":
  offset   : [level, title, printed page]      leaf = printed + offset   (constant difference in the scan)
  leafmode : [level, title, leaf]              no printed page shown
  full     : [level, title, leaf, printed|null]
leaf = the zero-based image index the archive.org viewer uses (#page/n<leaf>)."""
import json, glob, os, sys, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BOOKS = os.path.join(ROOT, 'data/booklists/books.json')
books = json.load(open(BOOKS, encoding='utf8'))
by = {b['key']: b for b in books}
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'data/booklists/toc/*.json'))):
    key = os.path.basename(f)[:-5]
    spec = json.load(open(f, encoding='utf8'))
    b = by[key]; r = b['reader']
    assert r.get('mode') == 'embed', key
    toc = []
    for it in spec['items']:
        if spec.get('full'): lv, t, leaf, pr = it
        elif spec.get('leafmode'): lv, t, leaf = it; pr = None
        else: lv, t, pr = it; leaf = pr + spec['offset']
        assert leaf >= 0 and lv in (1, 2) and t.strip(), (key, it)
        t = re.sub(r'[٠-٩]', lambda m: str(ord(m.group(0)) - 0x660), t)      # the app writes digits 0-9
        toc.append([lv, t, leaf, pr])
    r['toc'] = toc; r['tocSrc'] = spec.get('tocSrc', '')
    n += 1
open(BOOKS, 'w', encoding='utf8').write(json.dumps(books, ensure_ascii=False, indent=1) + '\n')
print('tocs applied:', n)
