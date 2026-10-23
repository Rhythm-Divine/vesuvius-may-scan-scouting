#!/usr/bin/env bash
# M1: Hecate on further meshes exactly as pre-registered (PRE, default prereg/PHerc0175B-m1-b.md): crop each render to its
# readout-area bbox + 128 px, windows k = -2..+2 (layers 13+k..28+k), forward and reverse, bf16, batch 4, GPU only
# through the guard and never while $GPU_RESERVE_FILE exists (refused or yielded runs retry); then the readout
# with --exclude-contacts 8. Refuses to run unless the prereg is committed. Low priority ($RUN). Gives up after 12 h.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; H="$HECATE_DIR"; O="$R/data/m1/${SAMPLE:-PHerc0175B}"   # SAMPLE: env override
PRE="${PRE:-prereg/PHerc0175B-m1-b.md}"   # the prereg these meshes were registered under (env override)
git ls-files --error-unmatch "$PRE" > /dev/null 2>&1 && git diff --quiet HEAD -- "$PRE" || { echo "prereg not committed"; exit 3; }
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS NUMEXPR_NUM_THREADS=$THREADS \
       NUMBA_NUM_THREADS=$THREADS CUDA_VISIBLE_DEVICES=""
T="$RUN"; DEADLINE=$(( $(date +%s) + 12 * 3600 ))
for MESH_NAME in "$@"; do
  IN9="$O/render/${MESH_NAME}_9p6.npy"; P="$O/hecate/$MESH_NAME"; mkdir -p "$P"
  echo "prereg commit $(git log -1 --format=%h -- "$PRE")" > "$P/prereg_commit.txt"
  if [ ! -s "$P/crop.json" ]; then
    $T "$PY" - "$O/meshes/$MESH_NAME" "$IN9" "$O/render/${MESH_NAME}_selfcross.json" "$P" <<'PY' || exit 1
import json, os, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(os.environ["VES_ROOT"]) / "m1"))
from readout import interior_mask
mesh, in9, sc, p = sys.argv[1:5]
r = np.load(in9, mmap_mode="r")
valid = (np.asarray(r[21]) > 0) & interior_mask(mesh, r.shape[1:], sc, 8)
ys, xs = np.nonzero(valid)
H, W = r.shape[1:]
crop = [max(0, int(ys.min()) - 128), min(H, int(ys.max()) + 129), max(0, int(xs.min()) - 128), min(W, int(xs.max()) + 129)]
Path(p, "crop.json").write_text(json.dumps({"crop": crop, "valid_cm2": round(float(valid.sum()) * (9.604e-4) ** 2, 3)}))
print("crop", crop)
PY
  fi
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$P/crop.json'))['crop'])")
  missing () { for k in -2 -1 0 1 2; do for dir in fwd rev; do [ -s "$P/pred_${dir}_$k.png" ] || echo "$dir $k"; done; done; }
  while [ -n "$(missing)" ]; do
    [ "$(date +%s)" -gt "$DEADLINE" ] && { echo "== $(date -u +%FT%TZ) giving up; $MESH_NAME missing: $(missing | tr '\n' ',')"; exit 4; }
    if gpu_reserved; then sleep 60; continue; fi
    read -r dir k < <(missing | head -1)
    W="$P/win_$k.npy"
    [ -s "$W" ] || $T "$PY" -c "
import numpy as np
r = np.load('$IN9', mmap_mode='r'); z0 = 13 + ($k)
assert r.shape[0] == 43, r.shape
np.save('$W', np.ascontiguousarray(r[z0:z0 + 16, $Y0:$Y1, $X0:$X1])); print('window', $k, 'layers', z0, z0 + 15)" || exit 1
    OUT="$P/pred_${dir}_$k.png"; rm -f "$OUT"; EXTRA=""; [ "$dir" = rev ] && EXTRA="--reverse"
    echo "== $(date -u +%FT%TZ) $MESH_NAME hecate $dir $k"
    $T "$PY" tools/gpu_guard.py $GUARD_ARGS --log "$P/pred_${dir}_$k.guard.log" \
       --pidfile "$P/pred_${dir}_$k.guard.pid" -- "$PY" "$H/hecate.py" --checkpoint "$H/hecate_9.6um.pth" \
       --input "$W" --output "$OUT" --spacing-um 9.604 --device cuda --precision bf16 --batch-size 4 $EXTRA
    rc=$?; echo "guard rc=$rc"
    if [ "$rc" -ne 0 ]; then rm -f "$OUT"; sleep 60; continue; fi
    [ -s "$P/pred_fwd_$k.png" ] && [ -s "$P/pred_rev_$k.png" ] && rm -f "$W"
  done
  rm -f "$P"/win_*.npy
  echo "== $(date -u +%FT%TZ) $MESH_NAME readout"
  $T "$PY" m1/readout.py --mesh "$O/meshes/$MESH_NAME" --render9 "$IN9" --pred-dir "$P" --out "$P/readout.json" \
     --selfcross "$O/render/${MESH_NAME}_selfcross.json" --exclude-contacts 8 --crop "$Y0" "$Y1" "$X0" "$X1"
done
echo "== $(date -u +%FT%TZ) M1-hecate-more DONE"
