"""Remove tashkeel ink from a page image before OCR. Connected components that are small and NOT compact solid blobs (dots are compact and solid;
fatha/kasra are thin slanted dashes, damma/sukun/shadda are rings or loops) are erased. Large components (letters/words) are untouched."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
def clean(img, dot_max_area=140, dot_fill=0.72, dot_aspect=(0.55, 1.8), max_h=19, max_w=34):
    a = np.array(img.convert('L')) < 128                      # ink = True
    lab, n = ndi.label(a, structure=np.ones((3, 3)))
    objs = ndi.find_objects(lab); areas = ndi.sum(a, lab, range(1, n + 1))
    keep = np.ones(n + 1, bool); keep[0] = False; removed = 0
    for i, sl in enumerate(objs, 1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start; ar = areas[i - 1]
        if h > max_h or w > max_w: continue                      # letters / words keep their full size
        fill = ar / max(1, w * h); asp = w / max(1, h)
        is_dot = ar <= dot_max_area and fill >= dot_fill and dot_aspect[0] <= asp <= dot_aspect[1] and min(w, h) >= 3
        if not is_dot: keep[i] = False; removed += 1
    out = np.where(keep[lab], 0, 255).astype(np.uint8)
    return Image.fromarray(out), removed
if __name__ == '__main__':
    im = Image.open(sys.argv[1]); o, r = clean(im); o.save(sys.argv[2]); print('removed components', r)
