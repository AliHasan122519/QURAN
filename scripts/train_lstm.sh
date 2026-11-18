#!/bin/bash
# Fine-tune Tesseract's 'ara' (tessdata_best) on the typeface of al-Jami' al-Saghir using the aligned line images (scripts/make_train_data.py).
# usage: scripts/train_lstm.sh TRAIN_DIR TESSDATA_BEST_DIR [MAX_ITERATIONS]     (TRAIN_DIR contains train/ and eval/ with NAME.png + NAME.gt.txt)
set -e
D="$1"; TD="$2"; ITER="${3:-2500}"
export TESSDATA_PREFIX="$TD"
mkdir -p "$D/model"
python3 -I - "$D" <<'PY'
import sys, glob
from PIL import Image
for sp in ('train', 'eval'):
    for g in glob.glob(f'{sys.argv[1]}/{sp}/*.gt.txt'):
        base = g[:-len('.gt.txt')]; w, h = Image.open(base + '.png').size; t = open(g, encoding='utf8').read().strip()
        open(base + '.box', 'w', encoding='utf8').write(f'WordStr 0 0 {w} {h} 0 #{t}\n\t {w} 0 {w+1} {h} 0\n')
PY
for sp in train eval; do
  ls "$D/$sp"/*.png | xargs -P 4 -I{} bash -c 'f={}; b=${f%.png}; tesseract "$f" "$b" --psm 13 --oem 1 -l ara lstm.train >/dev/null 2>&1'
  ls "$D/$sp"/*.lstmf > "$D/$sp.list"
done
wc -l "$D/train.list" "$D/eval.list"
combine_tessdata -e "$TD/ara.traineddata" "$D/model/ara.lstm" >/dev/null
lstmtraining --continue_from "$D/model/ara.lstm" --traineddata "$TD/ara.traineddata" --model_output "$D/model/ft" \
  --train_listfile "$D/train.list" --eval_listfile "$D/eval.list" --max_iterations "$ITER" --learning_rate 0.0002 --debug_interval 0 2>&1 | tail -n 25
lstmtraining --stop_training --continue_from "$D/model/ft_checkpoint" --traineddata "$TD/ara.traineddata" --model_output "$D/model/jami_ara.traineddata"
ls -la "$D/model/jami_ara.traineddata"
