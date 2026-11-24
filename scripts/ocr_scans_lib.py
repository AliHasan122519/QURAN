"""helpers shared by ocr_scans.py and ocr_pdf.py"""
import io, json, os, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BEST = os.environ.get('BEST', '/tmp/claude-0/aud/tessbest/tessdata')
def get(url, tries=4):
    err = None
    for k in range(tries):
        try: return urllib.request.urlopen(url, timeout=120).read()
        except Exception as e: err = e; time.sleep(2 + k * 3)
    raise err
def meta(i): return json.loads(get('https://archive.org/metadata/' + i))
def page_image(m, i, zname, n):
    base = zname[:-8]
    q = urllib.parse.urlencode({'zip': f"{m['dir']}/{zname}", 'file': f"{base}_jp2/{base}_{n:04d}.jp2", 'id': i, 'scale': 1, 'rotate': 0})
    err = None
    for k in range(3):
        for h in (m['d1'], m['d2']):
            try: return urllib.request.urlopen(f"https://{h}/BookReader/BookReaderImages.php?{q}", timeout=120).read()
            except Exception as e: err = e
        time.sleep(3)
    raise err
def tess(path, best, tsv):
    env = {**os.environ, 'OMP_THREAD_LIMIT': '1'}
    if best: env['TESSDATA_PREFIX'] = BEST
    return subprocess.run(['tesseract', path, '-', '-l', 'ara', '--psm', '6'] + (['tsv'] if tsv else []), capture_output=True, text=True, env=env).stdout
def lines_of(tsv):
    rows = {}
    for l in tsv.splitlines()[1:]:
        c = l.split('\t')
        if len(c) < 12 or not c[11].strip(): continue
        k = tuple(c[2:5]); x, y, w, h = map(int, c[6:10]); r = rows.setdefault(k, {'w': [], 'l': 10**9, 't': 10**9, 'r': 0, 'b': 0, 'c': []})
        r['w'].append((x, c[11])); r['l'] = min(r['l'], x); r['t'] = min(r['t'], y); r['r'] = max(r['r'], x + w); r['b'] = max(r['b'], y + h); r['c'].append(float(c[10]))
    out = []
    for k in sorted(rows, key=lambda k: (int(k[0]), int(k[1]), int(k[2]))):
        r = rows[k]; ws = [w for _, w in sorted(r['w'], key=lambda z: -z[0])]            # right to left
        out.append({'b': [r['l'], r['t'], r['r'], r['b']], 't': ' '.join(ws), 'c': round(sum(r['c']) / len(r['c']), 1)})
    return out
