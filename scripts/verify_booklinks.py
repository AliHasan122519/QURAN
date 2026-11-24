"""Checks (needs the network) every fact of data/booklists/books.json that can be checked against its source:
  * each quoted passage («about») is really in the page / local text it names (diacritics, quotation marks and spacing are ignored);
  * each «قراءة» link answers 200;
  * each «تحميل» file is in the archive.org item (metadata) and archive.org's download URL answers with a redirect to it (not 404); its size is written to the data file.
usage: python3 -I scripts/verify_booklinks.py [--write]        (--write stores the file sizes)"""
import json, re, sys, html, subprocess, urllib.parse
WRITE = '--write' in sys.argv
def curl(u, head=False):
    a = ['curl', '-s', '-L', '--max-time', '90', '-A', 'Mozilla/5.0']
    if head: a = ['curl', '-s', '-I', '--max-time', '60', '-A', 'Mozilla/5.0', '-o', '/dev/null', '-w', '%{http_code} %{redirect_url}']
    r = subprocess.run(a + [u], capture_output=True); return r.stdout.decode('utf8', 'replace')
def loose(s): return re.sub(r'[^0-9ء-ي]', '', re.sub(r'[ً-ْٰـٓ-ٟ]', '', s)).replace('ى', 'ي').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه')
def shamela(u):
    t = curl(u)
    if re.search(r'/book/\d+/\d+$', u):                     # a page of a book: only the text of the page itself (without the menus and the «next page» links)
        m = re.search(r'<div[^>]*class="[^"]*nass[^"]*"[^>]*>(.*?)</div>\s*(?:<div class="[^"]*(?:hide|clear|row)|<script|<nav|<footer)', t, re.S)
        return re.sub(r'تحميل الصفحة (?:التالية|السابقة)', '', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))) if m else ''
    body = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', body))
def local(f):
    t = open(f, encoding='utf8').read(); t = re.sub(r'#META#.*\n', '', t); return re.sub(r'صفحة فارغة', ' ', re.sub(r'PageV\d+P\d+|ms\d+|~~|\|', '', t))
B = json.load(open('data/booklists/books.json', encoding='utf8')); bad = 0; cache = {}
def fail(m): global bad; bad += 1; print('  FAIL', m)
for b in B:
    print('==', b['key'])
    for a in b['about']:
        if a.get('nolive') or (not a.get('u') and not a.get('f')): print('  (not checkable against a source:', a['s'], ')'); continue
        srcs = []
        for u in ([a['u']] if isinstance(a.get('u'), str) else a.get('u', [])):
            if u not in cache: cache[u] = shamela(u)
            srcs.append(cache[u])
        if a.get('f'):
            f = a['f']
            if f.endswith('.json'): srcs.append(open(f, encoding='utf8').read())
            else: srcs.append(local(f))
        hay = loose(' '.join(srcs)); parts = a.get('parts') or [a['t']]
        for p in parts:
            if loose(p) not in hay: fail('quote not found in its source: ' + p[:70])
        print('  quote ok:', a['t'][:60])
    code = curl(b['read']['url'], head=True).split(' ')[0]
    print('  read', b['read']['url'], code)
    if code != '200': fail('read link ' + code)
    for d in b['dls']:
        m = json.loads(curl('https://archive.org/metadata/' + d['id']) or '{}'); files = {f['name']: f for f in m.get('files', [])}
        if d['name'] not in files: fail('file not in the item: ' + d['id'] + ' / ' + d['name'][:40]); continue
        f = files[d['name']]; d['size'] = int(f['size'])
        url = 'https://archive.org/download/%s/%s' % (d['id'], urllib.parse.quote(d['name']))
        h = curl(url, head=True); print('  dl', d['id'], round(d['size'] / 1e6, 1), 'MB', h[:60])
        if not h.startswith('302') and not h.startswith('200'): fail('download url ' + h[:40])
if WRITE and not bad: json.dump(B, open('data/booklists/books.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('FAILED' if bad else 'ALL OK', bad); sys.exit(1 if bad else 0)
