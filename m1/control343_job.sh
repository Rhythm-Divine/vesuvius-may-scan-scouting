#!/usr/bin/env bash
# E1d, the pipeline control: our own M1 chain (m1/seed.py -> GrowPatch on the m7 prediction with streamed normal grids
# -> self-crossing QC -> 48-layer render -> 9.604 um -> Hecate windows -2..+2, forward and reverse, through the guard ->
# m1/readout.py) on PHerc0343, at the centre of the text area of the October First Letters winner (seed from
# m1/n343_seed.py on their published mesh). Same settings as PHerc0175B meshes 2-4. Pass criterion: fixed before the run
# (results/E1d-PHerc0343-pipeline-control.md). CPU at low priority ($RUN); caches under $R/cache, deleted after use.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; H="$HECATE_DIR"
SB="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0343"
PREF="PHerc0343/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
PRED="$SB/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr"
NG_URL="$SB/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.normal-grids"
CT="$SB/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr"
O="$R/data/m1/PHerc0343"; NG="$R/cache/ng/PHerc0343"; C="$R/cache/vc3d"
mkdir -p "$O/meshes" "$O/render" "$NG" "$C/config" "$C/remote" "$C/grow" "$R/cache/tmp"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=$GROW_THREADS OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" \
       VC3D_CONFIG_DIR="$C/config"
printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
printf '{"url": "%s"}\n' "$NG_URL" > "$NG/normal-grids-remote.json"
T8="$RUN"; T="$RUN"; V="$VC3D"
echo "== $(date -u +%FT%TZ) seed"
read -r SX SY SZ < <($T8 "$PY" m1/seed.py --prefix "$PREF" --z 10467 --y 3909 --x 5880 \
                      --centre-yx 4494.5 5068.9 --out "$O") || exit 1
echo "seed $SX $SY $SZ"
cat > "$O/grow_params.json" <<JSON
{"mode": "seed", "use_cuda": false, "thread_limit": $GROW_THREADS, "voxelsize": 8.64, "step_size": 20, "generations": ${GENERATIONS:-80},
 "min_area_cm": 0.0, "normal_grid_path": "$NG", "cache_size": 2000000000, "cache_root": "$C/grow"}
JSON
echo "== $(date -u +%FT%TZ) grow"
$T8 "$V" vc_grow_seg_from_seed -v "$PRED" -t "$O/meshes" -p "$O/grow_params.json" -s "$SX" "$SY" "$SZ" \
   > "$O/grow.log" 2> "$O/grow.err"; echo "grow rc=$?"; tail -2 "$O/grow.log" | cut -c1-200
rm -rf "$NG/xy" "$NG/xz" "$NG/yz"
M_NAME=$(ls "$O/meshes" | head -1); M="$O/meshes/$M_NAME"; echo "mesh $M_NAME"
$T8 "$V" vc_tifxyz_selfcross --surface "$M" -o "$O/render/${M_NAME}_selfcross.json" --threads 8 > "$O/render/selfcross.log" 2>&1
tail -1 "$O/render/selfcross.log"
echo "== $(date -u +%FT%TZ) render"
$T8 "$V" vc_render_tifxyz -v "$CT" -g 0 --scale 1 -s "$M" -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote \
   --surface-interpolation smooth --zarr-output "$O/render/$M_NAME.zarr" --zarr-compressor none > "$O/render/render.log" 2>&1
echo "render rc=$?"
IN9="$O/render/${M_NAME}_9p6.npy"
$T8 "$PY" m1/resample_render.py "$O/render/$M_NAME.zarr" "$IN9" || exit 1
rm -rf "$O/render/$M_NAME.zarr" "$C/remote"; du -sh "$R" | cut -f1
P="$O/hecate/$M_NAME"; mkdir -p "$P"
$T "$PY" m1/readout_crop.py --mesh "$M" --render9 "$IN9" --selfcross "$O/render/${M_NAME}_selfcross.json" \
   --exclude-contacts 8 --out "$P/crop.json" || exit 1
read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$P/crop.json'))['crop'])")
export OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS
missing () { for k in -2 -1 0 1 2; do for dir in fwd rev; do [ -s "$P/pred_${dir}_$k.png" ] || echo "$dir $k"; done; done; }
DEADLINE=$(( $(date +%s) + 12 * 3600 ))
while [ -n "$(missing)" ]; do
  [ "$(date +%s)" -gt "$DEADLINE" ] && { echo "giving up; missing: $(missing | tr '\n' ',')"; exit 4; }
  if gpu_reserved; then sleep 60; continue; fi
  read -r dir k < <(missing | head -1)
  W="$P/win_$k.npy"
  [ -s "$W" ] || $T "$PY" m1/window.py "$IN9" "$k" "$Y0" "$Y1" "$X0" "$X1" "$W" || exit 1
  OUT="$P/pred_${dir}_$k.png"; rm -f "$OUT"; EXTRA=""; [ "$dir" = rev ] && EXTRA="--reverse"
  echo "== $(date -u +%FT%TZ) hecate $dir $k"
  $T "$PY" tools/gpu_guard.py $GUARD_ARGS --log "$P/pred_${dir}_$k.guard.log" \
     --pidfile "$P/pred_${dir}_$k.guard.pid" -- "$PY" "$H/hecate.py" --checkpoint "$H/hecate_9.6um.pth" \
     --input "$W" --output "$OUT" --spacing-um 9.604 --device cuda --precision bf16 --batch-size 4 $EXTRA
  rc=$?; echo "guard rc=$rc"
  if [ "$rc" -ne 0 ]; then rm -f "$OUT"; sleep 60; continue; fi
  [ -s "$P/pred_fwd_$k.png" ] && [ -s "$P/pred_rev_$k.png" ] && rm -f "$W"
done
rm -f "$P"/win_*.npy
$T "$PY" m1/readout.py --mesh "$M" --render9 "$IN9" --pred-dir "$P" --out "$P/readout.json" \
   --selfcross "$O/render/${M_NAME}_selfcross.json" --exclude-contacts 8 --crop "$Y0" "$Y1" "$X0" "$X1"
echo "== $(date -u +%FT%TZ) E1d DONE"
