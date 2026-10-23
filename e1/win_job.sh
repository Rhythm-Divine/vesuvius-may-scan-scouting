#!/usr/bin/env bash
# E1 on the labelled text block: crop render_fit.npy to align3's window (+128 px), then in parallel
#   CPU: align4 (depth search + tile displacement field), and
#   GPU: Hecate forward + reverse on the crop through the guard (bf16, batch 4);
# then score4 under each transfer against displaced-label nulls. Low priority ($RUN); GPU only via the guard.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; D="$R/data/e1"; H="$HECATE_DIR"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS NUMEXPR_NUM_THREADS=$THREADS \
       NUMBA_NUM_THREADS=$THREADS CUDA_VISIBLE_DEVICES=""
T="$RUN"
echo "== $(date -u +%FT%TZ) crop"
$T "$PY" - "$D" <<'PY' || exit 1
import json, sys
from pathlib import Path
import numpy as np
d = Path(sys.argv[1])
y0, y1, x0, x1 = json.loads((d / "align2.json").read_text())["local"]["window"]
r = np.load(d / "render_fit.npy", mmap_mode="r")
m = 128
Y0, Y1, X0, X1 = max(0, y0 - m), min(r.shape[1], y1 + m), max(0, x0 - m), min(r.shape[2], x1 + m)
np.save(d / "render_fit_win.npy", np.ascontiguousarray(r[:, Y0:Y1, X0:X1]))
(d / "render_fit_win.json").write_text(json.dumps({"crop": [Y0, Y1, X0, X1], "shape": [r.shape[0], Y1 - Y0, X1 - X0]}))
print("crop", [Y0, Y1, X0, X1])
PY
echo "== $(date -u +%FT%TZ) align4 (background)"
$T "$PY" e1/align4.py --e1 "$D" > "$D/align4.log" 2>&1 &
AL=$!
for dir in fwd rev; do
  OUT="$D/pred_win_$dir.png"; rm -f "$OUT"
  EXTRA=""; [ "$dir" = rev ] && EXTRA="--reverse"
  echo "== $(date -u +%FT%TZ) hecate $dir"
  $T "$PY" tools/gpu_guard.py $GUARD_ARGS --log "$D/pred_win_$dir.guard.log" \
     --pidfile "$D/pred_win_$dir.guard.pid" -- "$PY" "$H/hecate.py" --checkpoint "$H/hecate_9.6um.pth" \
     --input "$D/render_fit_win.npy" --output "$OUT" --spacing-um 9.604 --device cuda --precision bf16 --batch-size 4 $EXTRA
  echo "guard rc=$? for $dir"; tail -2 "$D/pred_win_$dir.guard.log"
done
wait "$AL"; echo "align4 rc=$?"; tail -6 "$D/align4.log"
echo "== $(date -u +%FT%TZ) score4"
$T "$PY" e1/score4.py --e1 "$D" $(ls "$D"/pred_win_fwd.png "$D"/pred_win_rev.png 2>/dev/null)
echo "== $(date -u +%FT%TZ) E1-win DONE"
