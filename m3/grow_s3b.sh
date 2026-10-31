#!/usr/bin/env bash
# S3b (prereg/M1-survey-S3b.md): m3/grow_s3.sh with 160 generations instead of 80 (a longer surface around a row): grow seeds, then census, render and resample each new mesh,
# with m1/grow_more.sh's settings unchanged (step 20, 80 generations, CPU; 48-layer native render; 9.604 um resample).
# Three changes let workers share a volume:
# - worker W grows into its own folder (data/m1/<SAMPLE>/meshes_w<W>) and moves each finished mesh into meshes/, so a
#   new mesh is never attributed to another worker's seed;
# - each worker has its own normal-grid cache (cache/ng/<SAMPLE>_w<W>), cleared after the job;
# - the native render (render/<mesh>.zarr, on the NVMe) is kept for reader-v2, which deletes it after reading.
# Appends one "X Y Z<TAB>mesh" line per seed to SEEDMAP ("-" when no mesh grew).
# Usage: W=1 SAMPLE=... VOL=... GROW_CPUS=0-6 VC3D_CACHE=DIR SEEDMAP=FILE bash m3/grow_s3.sh "X Y Z" ["X Y Z" ...]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"
W=${W:?}; SAMPLE=${SAMPLE:?}; VOL=${VOL:?}; SEEDMAP=${SEEDMAP:?}; C=${VC3D_CACHE:?}
B="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$SAMPLE/representations/predictions/surfaces"
PRED="$B/$VOL-surface-20260413222639-surface-m7-L0-th0.2.zarr"
NG_URL="$B/$VOL-surface-20260413222639-surface-m7-L0-th0.2.normal-grids"
O="$R/data/m1/$SAMPLE"; NG="$R/cache/ng/${SAMPLE}_w$W"; GD="$O/meshes_w$W"
mkdir -p "$O/meshes" "$GD" "$NG" "$C/config" "$C/remote" "$C/grow" "$R/cache/tmp" "$O/render"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=10 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" \
       VC3D_CONFIG_DIR="$C/config"
printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
printf '{"url": "%s"}\n' "$NG_URL" > "$NG/normal-grids-remote.json"
T="nice -n 19 taskset -c ${GROW_CPUS:?}"; V="$VC3D"
P="$O/grow_params_s3b_w$W.json"
cat > "$P" <<JSON
{"mode": "seed", "use_cuda": false, "thread_limit": 10, "voxelsize": 8.64, "step_size": 20, "generations": 160,
 "min_area_cm": 0.0, "normal_grid_path": "$NG", "cache_size": 2000000000, "cache_root": "$C/grow"}
JSON
NEW=()
for s in "$@"; do
  read -r SX SY SZ <<< "$s"
  before=$(ls "$GD")
  L="$O/grow_s3b_${SX}_${SY}_${SZ}"
  echo "== $(date -u +%FT%TZ) grow seed $SX $SY $SZ"
  /usr/bin/time -v $T "$V" vc_grow_seg_from_seed -v "$PRED" -t "$GD" -p "$P" -s "$SX" "$SY" "$SZ" > "$L.log" 2> "$L.err"
  echo "grow rc=$?"; grep -E "Elapsed|ERROR" "$L.err" | head -n 3
  m=$(comm -13 <(echo "$before") <(ls "$GD") | head -n 1)
  if [ -n "$m" ] && mv "$GD/$m" "$O/meshes/$m"; then
    NEW+=("$m"); printf '%s %s %s\t%s\n' "$SX" "$SY" "$SZ" "$m" >> "$SEEDMAP"; echo "new mesh $m"
  else
    printf '%s %s %s\t-\n' "$SX" "$SY" "$SZ" >> "$SEEDMAP"
  fi
done
rm -rf "$NG/xy" "$NG/xz" "$NG/yz"
CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$SAMPLE/volumes/$VOL-8.640um-1.2m-116keV-masked.zarr"
for m in "${NEW[@]}"; do
  M="$O/meshes/$m"
  $T "$V" vc_tifxyz_selfcross --surface "$M" -o "$O/render/${m}_selfcross.json" --threads 8 > "$O/render/${m}_selfcross.log" 2>&1
  $T "$V" vc_render_tifxyz -v "$CT" -g 0 --scale 1 -s "$M" -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote \
     --surface-interpolation smooth --zarr-output "$O/render/$m.zarr" --zarr-compressor none > "$O/render/${m}_render.log" 2>&1
  echo "render $m rc=$?"
  $T "$PY" m3/resample9.py "$O/render/$m.zarr" "$O/render/${m}_9p6.npy"
done
rm -rf "$C/remote"
echo "== $(date -u +%FT%TZ) grow_s3b job done: ${NEW[*]}"
