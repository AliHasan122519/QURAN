#!/usr/bin/env python3
"""Count the pages of every scanned file listed in data/booklists/books.json (from archive.org: the file's
«_page_numbers.json» / «_scandata.xml», i.e. the pages the in-app viewer shows).  Writes data/booklists/pagecounts.json
({key: [[file name, pages], …]}); build_booklists.py puts them in the «عدد الصفحات» row of each book.
usage: python3 -I scripts/page_counts.py [key …]   (no keys = every book that has no count yet)"""
import json, os, re, sys, time, urllib.parse, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BOOKS = os.path.join(ROOT, 'data/booklists/books.json'); OUT = os.path.join(ROOT, 'data/booklists/pagecounts.json')
books = json.load(open(BOOKS, encoding='utf8'))
have = json.load(open(OUT, encoding='utf8')) if os.path.exists(OUT) else {}
def get(url, tries=4):
    err = None
    for k in range(tries):
        try: return urllib.request.urlopen(url, timeout=90).read()
        except Exception as e: err = e; time.sleep(2)
    raise err
def meta(i):
    return json.loads(get('https://archive.org/metadata/' + i))
def count(m, name):
    stem = re.sub(r'\.[A-Za-z0-9]+$', '', name)
    files = {f['name']: f for f in m['files']}
    for suf in ('_page_numbers.json', '_scandata.xml'):
        fn = stem + suf
        if fn in files:
            for h in (m['d1'], m['d2']):
                try: raw = get(f"https://{h}{m['dir']}/{urllib.parse.quote(fn)}", 2); break
                except Exception: raw = None
            if raw is None: continue
            if suf.endswith('.json'): return len(json.loads(raw)['pages'])
            return len(re.findall(rb'<page ', raw))
    return None
only = set(sys.argv[1:])
for b in books:
    if only and b['key'] not in only: continue
    if not only and b['key'] in have: continue
    rows = []; cache = {}
    for d in b['dls']:
        if d['id'] not in cache: cache[d['id']] = meta(d['id'])
        n = count(cache[d['id']], d['name'])
        if n: rows.append([d['name'], n])
    have[b['key']] = rows
    print(b['key'], rows)
json.dump(have, open(OUT, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
