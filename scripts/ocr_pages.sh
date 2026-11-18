#!/bin/bash
# OCR every page of the supplied PDF with Tesseract 5 (Arabic). One reading per invocation; run it three times:
#   scripts/ocr_pages.sh public/assets/al-jami-al-saghir.pdf data/ocr      300            # Ubuntu 'ara' model (apt: tesseract-ocr-ara)
#   scripts/ocr_pages.sh public/assets/al-jami-al-saghir.pdf data/ocr_500  500            # same model, upsampled page
#   scripts/ocr_pages.sh public/assets/al-jami-al-saghir.pdf data/ocr_best 300 /path/to/tessdata_best   # dir containing tessdata_best ara.traineddata
#   PSM=4 JOBS=3 scripts/ocr_pages.sh ... 600       # page-segmentation mode / parallel jobs via environment
# Requires: poppler-utils (pdftoppm), tesseract-ocr, tesseract-ocr-ara. Safe to re-run (finished pages are skipped).
# NEVER run two copies at once on the same output folder: they delete each other's temporary images (this produced empty pages once).
set -e
PDF="$1"; OUT="$2"; DPI="${3:-300}"; TD="$4"
N=$(pdfinfo "$PDF" | awk '/^Pages:/{print $2}')
mkdir -p "$OUT" "$OUT/.img"
PSM="${PSM:-6}"
one() {
  P=$1; n=$(printf "%04d" "$P")
  [ -s "$OUT/$n.txt" ] && return
  pdftoppm -f "$P" -l "$P" -r "$DPI" -gray -png "$PDF" "$OUT/.img/$n"
  f=$(ls "$OUT/.img/$n"*.png | head -1)
  env ${TD:+TESSDATA_PREFIX=$TD} OMP_THREAD_LIMIT=1 tesseract "$f" "$OUT/$n" -l ara --psm "$PSM" >/dev/null 2>&1
  rm -f "$f"
}
export -f one; export PDF OUT DPI TD PSM
seq 1 "$N" | xargs -P "${JOBS:-4}" -I{} bash -c 'one {}'
rmdir "$OUT/.img" 2>/dev/null || true
