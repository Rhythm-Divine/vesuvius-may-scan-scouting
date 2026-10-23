#!/usr/bin/env bash
# E1 depth offsets: Hecate forward with its 16-layer input window moved by k = -2, -1, +1, +2 layers (9.604 um) on the
# text-block crop (k = 0 is pred_win_fwd.png), GPU through the guard; then per-offset AUCs and the -1..+1 and -2..+2
# ensembles under every transfer. Low priority ($RUN).
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; D="$R/data/e1"; H="$HECATE_DIR"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS NUMEXPR_NUM_THREADS=$THREADS \
       NUMBA_NUM_THREADS=$THREADS CUDA_VISIBLE_DEVICES=""
T="$RUN"
for k in -2 -1 1 2; do
  IN="$D/render_off_$k.npy"; OUT="$D/pred_off_$k.png"; rm -f "$OUT"
  $T "$PY" -c "
import numpy as np, sys
r = np.load('$D/render_fit_win.npy', mmap_mode='r'); z0 = r.shape[0] // 2 - 8 + ($k)
np.save('$IN', np.ascontiguousarray(r[z0:z0 + 16])); print('offset', $k, 'layers', z0, z0 + 15)" || exit 1
  echo "== $(date -u +%FT%TZ) hecate offset $k"
  $T "$PY" tools/gpu_guard.py $GUARD_ARGS --log "$D/pred_off_$k.guard.log" \
     --pidfile "$D/pred_off_$k.guard.pid" -- "$PY" "$H/hecate.py" --checkpoint "$H/hecate_9.6um.pth" \
     --input "$IN" --output "$OUT" --spacing-um 9.604 --device cuda --precision bf16 --batch-size 4
  echo "guard rc=$? for offset $k"; rm -f "$IN"
done
cp "$D/pred_win_fwd.png" "$D/pred_off_0.png"
echo "== $(date -u +%FT%TZ) score"
$T "$PY" e1/score4.py --e1 "$D" --report score_off5.json --tag off5_ \
   $(ls "$D"/pred_off_-2.png "$D"/pred_off_-1.png "$D"/pred_off_0.png "$D"/pred_off_1.png "$D"/pred_off_2.png 2>/dev/null) > /dev/null
$T "$PY" e1/score4.py --e1 "$D" --report score_off3.json --tag off3_ \
   $(ls "$D"/pred_off_-1.png "$D"/pred_off_0.png "$D"/pred_off_1.png 2>/dev/null) > /dev/null
echo "== $(date -u +%FT%TZ) E1-offsets DONE"
