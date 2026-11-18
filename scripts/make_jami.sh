#!/bin/bash
# Rebuild the al-Jami' al-Saghir data from the line-recogniser output (data/ocr_crnn, produced by scripts/crnn_ocr.py) and the hand-verified pages (data/manual):
# parse the machine-read pages, merge the hand-verified pages over them, build the app data.
set -e
cd "$(dirname "$0")/.."
ls data/manual/p*.txt 2>/dev/null | sed -E 's/.*p0*([0-9]+)\.txt/\1/' | sort -n > data/manual_pages.txt || true
python3 -I scripts/parse_crnn.py data/ocr_crnn data/raw/_vocab.json data/raw/jami_ocr_parsed.json data/manual_pages.txt
python3 -I scripts/merge_manual.py
python3 -I scripts/refine_takhrij.py
python3 -I scripts/refine_with_reference.py
python3 -I scripts/build_data.py
python3 -I scripts/build_alfiya.py
