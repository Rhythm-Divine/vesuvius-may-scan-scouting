#!/usr/bin/env bash
# S3 Hecate check (prereg/M1-survey-S3.md) of one reader-v2 map: Hecate 9.6 um (bf16, batch 4, as in S1) on the
# surface's 9.604 um render, cropped to its readout window, with five 16-layer windows (layers 13+k..28+k) at the depth
# of the map: k = -2..+2 for near, +3..+7 for p6, -7..-3 for m6, in direction fwd or rev. Writes
# data/m3/<SAMPLE>/<MESH>/hecate/pred_<dir>_<k>.png; m3/readout_r3.py then fills in that map's agreement.
# Refuses to run on a survey surface unless the pre-registration is committed (the PHerc0343 control runs before it).
# Usage: bash m3/hecate_confirm.sh SAMPLE MESH FAMILY DIR GPU CPUS
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; s=$1; m=$2; fam=$3; dir=$4; G=$5; CPUS=$6
PRE=prereg/M1-survey-S3.md; H="$HECATE_DIR"
if [ "$s" != PHerc0343 ]; then
  git ls-files --error-unmatch $PRE > /dev/null 2>&1 && git diff --quiet HEAD -- $PRE || { echo "prereg not committed"; exit 3; }
fi
case $fam in near) K="-2 -1 0 1 2";; p6) K="3 4 5 6 7";; m6) K="-7 -6 -5 -4 -3";; *) echo "unknown family $fam"; exit 2;; esac
case $dir in fwd) EXTRA="";; rev) EXTRA="--reverse";; *) echo "unknown direction $dir"; exit 2;; esac
O=data/m3/$s/$m; P=$O/hecate; IN9=data/m1/$s/render/${m}_9p6.npy; mkdir -p $P
echo "prereg $PRE commit $(git log -1 --format=%h -- $PRE 2> /dev/null)" > $P/prereg_commit.txt
read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$O/crop.json'))['crop'])")
for k in $K; do
  OUT=$P/pred_${dir}_$k.png
  [ -s $OUT ] && continue
  WN=$P/win_${dir}_$k.npy
  nice -n 10 taskset -c $CPUS "$PY" -c "
import numpy as np
r = np.load('$IN9', mmap_mode='r'); z0 = 13 + ($k)
assert r.shape[0] == 43, r.shape
np.save('$WN', np.ascontiguousarray(r[z0:z0 + 16, $Y0:$Y1, $X0:$X1]))" || exit 1
  echo "== $(date -u +%FT%TZ) $s $m hecate $dir $k"
  CUDA_VISIBLE_DEVICES=$G OMP_NUM_THREADS=4 nice -n 10 taskset -c $CPUS "$PY" $H/hecate.py \
    --checkpoint $H/hecate_9.6um.pth --input $WN --output $OUT --spacing-um 9.604 --device cuda --precision bf16 \
    --batch-size 4 $EXTRA > $P/pred_${dir}_$k.log 2>&1 || { rm -f $OUT $WN; echo "hecate failed: $s $m $dir $k"; exit 1; }
  rm -f $WN
done
echo "== $(date -u +%FT%TZ) $s $m hecate $fam $dir done"
