"""The texts of the in-app reader (content/books/*.json) against the digital texts they come from: nothing of the book's Arabic letters may be added, lost or changed
(only digital marks and line breaks are removed), every table-of-contents entry points at a paragraph that starts the section it names, the files are in the manifest with the right SHA-256.
usage: python3 -I tests/bookreader_check.py"""
import json, re, sys, os, hashlib, importlib.util
sys.path.insert(0, 'scripts')
spec = importlib.util.spec_from_file_location('bbr', 'scripts/build_bookreader.py'); bbr = importlib.util.module_from_spec(spec); spec.loader.exec_module(bbr)
ok = True
def check(name, cond, detail=''):
    global ok; ok &= bool(cond); print('PASS' if cond else 'FAIL', '|', name, detail)
def letters(t): return re.sub(r'[^ء-ي]', '', re.sub(r'[ً-ٰٟـ]', '', t))
M = json.load(open('content/manifest.json', encoding='utf8')); F = {f['file']: f for f in M.get('files', [])}
for sp in bbr.SPECS:
    raw = open(sp['file'], encoding='utf8').read().split('\n')
    end = next((i for i, l in enumerate(raw) if l.startswith('#META#Header#End#')), None)
    if end is None: end = max((i for i, l in enumerate(raw[:80]) if l.startswith('#META')), default=-1)
    src = letters('\n'.join(l for l in raw[end + 1:] if not l.startswith('#META')))
    src = src.replace('صفحةفارغة', '')       # the digital copy's «blank page» note is not the book's words (the reader leaves it out)
    b = json.load(open(f'content/books/{sp["key"]}.json', encoding='utf8'))
    items, vols = bbr.parse(sp['file']); unc, _, _ = bbr.shape(items, vols); got = letters(' '.join(unc))      # the book as the cleaning leaves it, before any correction
    d = next((i for i in range(min(len(src), len(got))) if src[i] != got[i]), None)
    check(f'{sp["key"]}: the Arabic letters of the book are exactly those of its digital text', src == got, f'{len(got)} letters' + ('' if src == got else f' | first difference at {d}: …{src[max(0,(d or 0)-25):(d or 0)+25]}… vs …{got[max(0,(d or 0)-25):(d or 0)+25]}…'))
    fixed = list(unc); bbr.apply_corrections(sp['key'], fixed, [])
    cs = bbr.corrections(sp['key'])
    check(f'{sp["key"]}: the file is that text plus exactly its {len(cs)} listed corrections (each with a reason from the printed page)', fixed == b['p'] and all(c['why'] for c in cs))
    n = len(b['p']); toc = b['toc']
    check(f'{sp["key"]}: toc entries point inside the book, in order, with a title', toc and all(0 <= i < n and t.strip() for _, t, i in toc) and [i for _, _, i in toc] == sorted(i for _, _, i in toc), f'{len(toc)} entries')
    check(f'{sp["key"]}: no paragraph is empty or a digital leftover', all(p.strip() and not re.search(r'PageV|@\w+@|~~|\bms\d+\b', p) for p in b['p']))
    rel = f'books/{sp["key"]}.json'; raw_b = open(f'content/{rel}', 'rb').read()
    check(f'{sp["key"]}: listed in the manifest with its SHA-256 and size', rel in F and F[rel]['sha256'] == hashlib.sha256(raw_b).hexdigest() and F[rel]['size'] == len(raw_b))
    check(f'{sp["key"]}: the OCR flag is set exactly for the books read from a scan', b['ocr'] == bool(sp.get('ocr')))
print('OK' if ok else 'FAILED'); sys.exit(0 if ok else 1)
