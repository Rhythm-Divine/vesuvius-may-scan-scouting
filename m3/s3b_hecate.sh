#!/usr/bin/env bash
# S3b: Hecate 9.6 um (bf16, batch 4, as in S1 and S3) on one surface's 9.604 um render at the nine sweep depths
# k = -9 -7 -5 -2 0 2 5 7 9 (16-layer windows, layers 13+k..28+k), over the box Y0:Y1, X0:X1 of its crop frame (plus a
# 64 px margin, trimmed afterwards). Writes data/m3b/<SAMPLE>/<MESH>/hecate/pred_<DIR>_<k>.png (box size).
# Usage: bash m3/s3b_hecate.sh SAMPLE MESH DIR GPU CPUS Y0 Y1 X0 X1
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; s=$1; m=$2; dr=$3; G=$4; CPUS=$5; BY0=$6; BY1=$7; BX0=$8; BX1=$9
H="$HECATE_DIR"; O=data/m3b/$s/$m; P=$O/hecate; IN9=data/m1/$s/render/${m}_9p6.npy; mkdir -p $P
[ -f $O/crop.json ] || cp data/m3/$s/$m/crop.json $O/crop.json
case $dr in fwd) EXTRA="";; rev) EXTRA="--reverse";; *) exit 2;; esac
echo "$BY0 $BY1 $BX0 $BX1" > $P/box_$dr.txt
for k in ${KS:--9 -7 -5 -2 0 2 5 7 9}; do
  OUT=$P/pred_${dr}_$k.png
  [ -s $OUT ] && continue
  WN=$P/win_${dr}_$k.npy; FULL=$P/full_${dr}_$k.png
  nice -n 10 taskset -c $CPUS "$PY" -c "
import json, numpy as np
r = np.load('$IN9', mmap_mode='r'); z0 = 13 + ($k); assert r.shape[0] == 43, r.shape
y0, _, x0, _ = json.load(open('$O/crop.json'))['crop']
ya, xa = max(0, y0 + $BY0 - 64), max(0, x0 + $BX0 - 64)
yb, xb = min(r.shape[1], y0 + $BY1 + 64), min(r.shape[2], x0 + $BX1 + 64)
np.save('$WN', np.ascontiguousarray(r[z0:z0 + 16, ya:yb, xa:xb]))
json.dump([ya - y0, xa - x0], open('$WN.json', 'w'))" || exit 1
  echo "== $(date -u +%FT%TZ) $s $m hecate $dr $k"
  CUDA_VISIBLE_DEVICES=$G OMP_NUM_THREADS=4 nice -n 10 taskset -c $CPUS "$PY" $H/hecate.py \
    --checkpoint $H/hecate_9.6um.pth --input $WN --output $FULL --spacing-um 9.604 --device cuda --precision bf16 \
    --batch-size 4 $EXTRA > $P/pred_${dr}_$k.log 2>&1 || { rm -f $FULL $WN; echo "hecate failed $k"; exit 1; }
  "$PY" -c "
import json, imagecodecs, numpy as np
from pathlib import Path
a = imagecodecs.png_decode(Path('$FULL').read_bytes()); oy, ox = json.load(open('$WN.json'))
out = np.zeros(($BY1 - $BY0, $BX1 - $BX0), a.dtype); ys, xs = $BY0 - oy, $BX0 - ox
blk = a[max(ys, 0):ys + out.shape[0], max(xs, 0):xs + out.shape[1]]
out[max(-ys, 0):max(-ys, 0) + blk.shape[0], max(-xs, 0):max(-xs, 0) + blk.shape[1]] = blk
Path('$OUT').write_bytes(imagecodecs.png_encode(out))" || exit 1
  rm -f $WN $WN.json $FULL
done
echo "== $(date -u +%FT%TZ) $s $m hecate sweep $dr done"
