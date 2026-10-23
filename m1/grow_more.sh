#!/usr/bin/env bash
# M1: grow the neighbouring windings of mesh 1 in the PHerc0175B outer zone (seeds from m1/seeds_radial.py), then QC,
# render and resample each, the same way as mesh 1 (m1/grow_job.sh, m1/render_job.sh). Growth shares one streamed
# normal-grid cache (deleted afterwards); renders share one CT cache (deleted afterwards). CPU only, at low priority
# ($RUN), $GROW_THREADS threads. Usage: bash grow_more.sh "X Y Z" ["X Y Z" ...]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"
SAMPLE="${SAMPLE:-PHerc0175B}"; VOL="${VOL:-20250521125822}"   # env overrides for other scrolls
B="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$SAMPLE/representations/predictions/surfaces"
PRED="$B/$VOL-surface-20260413222639-surface-m7-L0-th0.2.zarr"
NG_URL="$B/$VOL-surface-20260413222639-surface-m7-L0-th0.2.normal-grids"
O="$R/data/m1/$SAMPLE"; NG="$R/cache/ng/$SAMPLE"; C="$R/cache/vc3d"
mkdir -p "$O/meshes" "$NG" "$C/config" "$C/remote" "$C/grow" "$R/cache/tmp" "$O/render"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$GROW_THREADS OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" \
       VC3D_CONFIG_DIR="$C/config"
printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
printf '{"url": "%s"}\n' "$NG_URL" > "$NG/normal-grids-remote.json"
T="$RUN"; V="$VC3D"
cat > "$O/grow_params_more.json" <<JSON
{"mode": "seed", "use_cuda": false, "thread_limit": $GROW_THREADS, "voxelsize": 8.64, "step_size": 20, "generations": ${GENERATIONS:-80},
 "min_area_cm": 0.0, "normal_grid_path": "$NG", "cache_size": 2000000000, "cache_root": "$C/grow"}
JSON
NEW=()
for s in "$@"; do
  read -r SX SY SZ <<< "$s"
  before=$(ls "$O/meshes")
  echo "== $(date -u +%FT%TZ) grow seed $SX $SY $SZ"
  /usr/bin/time -v $T "$V" vc_grow_seg_from_seed -v "$PRED" -t "$O/meshes" -p "$O/grow_params_more.json" \
     -s "$SX" "$SY" "$SZ" > "$O/grow_${SY}.log" 2> "$O/grow_${SY}.err"; echo "grow rc=$?"
  tail -3 "$O/grow_${SY}.log" | cut -c1-200; grep -E "Elapsed|ERROR" "$O/grow_${SY}.err" | head -3
  m=$(comm -13 <(echo "$before") <(ls "$O/meshes") | head -1)
  [ -n "$m" ] && NEW+=("$m") && echo "new mesh $m (seed y $SY)"
  du -sh "$NG" | cut -f1
done
rm -rf "$NG/xy" "$NG/xz" "$NG/yz"; echo "normal-grid cache cleared; $(du -sh "$R" | cut -f1) used"
CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$SAMPLE/volumes/$VOL-8.640um-1.2m-116keV-masked.zarr"
for m in "${NEW[@]}"; do
  M="$O/meshes/$m"
  echo "== $(date -u +%FT%TZ) $m: area $("$PY" -c "import json; print(round(json.load(open('$M/meta.json'))['area_cm2'], 2))") cm2"
  $T "$V" vc_tifxyz_selfcross --surface "$M" -o "$O/render/${m}_selfcross.json" --threads 8 > "$O/render/${m}_selfcross.log" 2>&1
  tail -1 "$O/render/${m}_selfcross.log"
  $T "$V" vc_render_tifxyz -v "$CT" -g 0 --scale 1 -s "$M" -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote \
     --surface-interpolation smooth --zarr-output "$O/render/$m.zarr" --zarr-compressor none > "$O/render/${m}_render.log" 2>&1
  echo "render rc=$?"
  $T "$PY" - "$O/render/$m.zarr" "$O/render/${m}_9p6.npy" <<'PY'
import os, sys
from pathlib import Path
import numpy as np, zarr
sys.path.insert(0, str(Path(os.environ["VES_ROOT"]) / "e1"))
from prepare import resample_render
g = zarr.open(sys.argv[1], mode="r")
src = g["0"] if hasattr(g, "keys") and "0" in g else g
out = resample_render(src)
np.save(sys.argv[2], out)
print("9.604 um", out.shape, "valid frac", round(float((out[out.shape[0] // 2] > 0).mean()), 3))
PY
  rm -rf "$O/render/$m.zarr"
done
rm -rf "$C/remote"; echo "CT cache cleared; $(du -sh "$R" | cut -f1) used"
echo "== $(date -u +%FT%TZ) M1-grow-more DONE: ${NEW[*]}"
