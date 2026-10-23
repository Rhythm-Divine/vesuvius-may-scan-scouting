#!/usr/bin/env bash
# E1b: the PHerc0009B positive control on the open-data same-mesh labels. CT-only registration (CPU), then Hecate
# forward with its 16-layer window at offsets -2..+2 on the supervision window of render.npy (GPU via the guard,
# bf16, batch 4), then AUCs, nulls, T and the depth ensembles. Low priority ($RUN).
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; D="$R/data/e1b"; H="$HECATE_DIR"; mkdir -p "$D"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS NUMEXPR_NUM_THREADS=$THREADS \
       NUMBA_NUM_THREADS=$THREADS CUDA_VISIBLE_DEVICES=""
T="$RUN"
echo "== $(date -u +%FT%TZ) register"
$T "$PY" e1b/register.py --out "$D" || exit 1
# one Hecate job on the shared GPU at a time: wait for the E1 offset runs to finish
P=$(cat "$R/logs/e1off.pid" 2>/dev/null); while [ -n "$P" ] && kill -0 "$P" 2>/dev/null; do sleep 10; done
for k in -2 -1 0 1 2; do
  IN="$D/render_off_$k.npy"; OUT="$D/pred_off_$k.png"; rm -f "$OUT"
  $T "$PY" -c "
import json, numpy as np
y0, y1, x0, x1 = json.load(open('$D/register.json'))['window']
r = np.load('$R/data/e1/render.npy', mmap_mode='r'); z0 = r.shape[0] // 2 - 8 + ($k)
np.save('$IN', np.ascontiguousarray(r[z0:z0 + 16, y0:y1, x0:x1])); print('offset', $k, 'layers', z0, z0 + 15)" || exit 1
  echo "== $(date -u +%FT%TZ) hecate offset $k"
  $T "$PY" tools/gpu_guard.py $GUARD_ARGS --log "$D/pred_off_$k.guard.log" \
     --pidfile "$D/pred_off_$k.guard.pid" -- "$PY" "$H/hecate.py" --checkpoint "$H/hecate_9.6um.pth" \
     --input "$IN" --output "$OUT" --spacing-um 9.604 --device cuda --precision bf16 --batch-size 4
  echo "guard rc=$? for offset $k"; rm -f "$IN"
done
echo "== $(date -u +%FT%TZ) score"
$T "$PY" e1b/score.py --out "$D" $(ls "$D"/pred_off_*.png 2>/dev/null)
echo "== $(date -u +%FT%TZ) E1b DONE"
