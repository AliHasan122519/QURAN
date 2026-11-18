"""Read pages of the PDF with the trained line recogniser (scripts/crnn.py). For every page: render at 300 dpi, get the line boxes from Tesseract's layout
analysis (tsv), recognise each line with the CRNN, write data/ocr_crnn/NNNN.txt (one recognised line per physical line, no tashkeel, no numbers/dashes).
usage: python3 -I scripts/crnn_ocr.py MODEL.pt FIRST_PAGE LAST_PAGE [shard i/n]"""
import sys, os, subprocess, csv, io, glob, tempfile, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from PIL import Image
import crnn as C
torch.set_num_threads(1)
mp, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); shard = tuple(int(x) for x in sys.argv[4].split('/')) if len(sys.argv) > 4 else (0, 1)
ck = torch.load(mp); chars = ck['chars']; net = C.Net(len(chars)); net.load_state_dict(ck['state']); net.eval()
PDF = 'public/assets/al-jami-al-saghir.pdf'; OUT = os.environ.get('CRNN_OUT', 'data/ocr_crnn'); os.makedirs(OUT, exist_ok=True)
tmp = tempfile.mkdtemp(prefix='crnnocr_'); env = dict(os.environ, OMP_THREAD_LIMIT='1')
RPAD = int(os.environ.get('CRNN_RPAD', '150'))
def line_image(im, x, y, w, h, pad=10, rpad=None):
    rpad = RPAD if rpad is None else rpad
    return im.crop((max(0, x - pad), max(0, y - pad), min(im.width, x + w + rpad), min(im.height, y + h + pad)))
for page in range(first, last + 1):
    if page % shard[1] != shard[0]: continue
    outp = f'{OUT}/{page:04d}.txt'
    if os.path.exists(outp): continue
    png = f'{tmp}/p{page}.png'
    subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '300', '-gray', '-png', '-singlefile', PDF, png[:-4]], check=True)
    tsv = subprocess.run(['tesseract', png, '-', '-l', 'ara', '--psm', os.environ.get('CRNN_PSM', '6'), 'tsv'], capture_output=True, text=True, env=env).stdout
    rows = list(csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE))
    lines = [r for r in rows if r['level'] == '4' and int(r['width']) > 80]
    im = Image.open(png).convert('L'); texts = []
    with torch.no_grad():
        for i in range(0, len(lines), 8):
            chunk = lines[i:i + 8]; crops = []
            for r in chunk:
                p = f'{tmp}/l.png'; line_image(im, int(r['left']), int(r['top']), int(r['width']), int(r['height'])).save(p); crops.append(C.load_img(p))
            x, _ = C.batchify(crops); texts += C.decode(net(x), chars)
    open(outp, 'w', encoding='utf8').write('\n'.join(texts) + '\n'); os.remove(png)
print('done', first, last, shard)
