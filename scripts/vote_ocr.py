"""Combine all available OCR readings of every page by word-level voting (scripts/ocr_lib.py) -> data/ocr_voted/NNNN.txt (tashkeel removed).
Primary reading (owner of the page layout): data/ocr_500. Others: data/ocr_best, data/ocr, data/ocr_b400, data/ocr_f600p4 (if present).
Measured on the hand-read reference pages (scripts/ocr_eval.py) the vote is clearly better than any single reading.  usage: python3 -I scripts/vote_ocr.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ocr_lib as L
OTHERS = [d for d in ('data/ocr_best', 'data/ocr', 'data/ocr_b400', 'data/ocr_f600p4') if os.path.isdir(d)]
os.makedirs('data/ocr_voted', exist_ok=True); n = 0
for p in range(1, 593):
    f = f'{p:04d}.txt'; prim = open(f'data/ocr_500/{f}', encoding='utf8').read()
    others = [open(f'{d}/{f}', encoding='utf8').read() for d in OTHERS if os.path.exists(f'{d}/{f}') and os.path.getsize(f'{d}/{f}') > 0]
    out = L.process(prim, others) if (prim.strip() and others) else (L.strip_tashkeel(prim) if prim.strip() else (open(f'data/ocr/{f}', encoding='utf8').read() if os.path.exists(f'data/ocr/{f}') else ''))
    open(f'data/ocr_voted/{f}', 'w', encoding='utf8').write(out); n += 1
print('voted pages:', n, '| readings combined:', ['data/ocr_500'] + OTHERS)
