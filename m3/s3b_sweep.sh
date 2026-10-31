#!/usr/bin/env bash
# S3b depth sweep of one surface (prereg/M1-survey-S3b.md), in one direction:
# 1. renders the surface natively again (48 layers, 8.64 um, as m3/grow_s3.sh) if its native render is gone;
# 2. reader-v2 in nine 17-layer windows shifted by -10, -7.5, -5, -2.5, 0, +2.5, +5, +7.5, +10 layers (the model takes the
#    central 17 layers of what it is given, so trimming 2s layers from one end shifts the window by s);
# 3. resamples each map to the 9.604 um grid and crops it to the surface's crop.json window (m3/s3b_combine.py);
# 4. Hecate at k = -9, -7, -5, -2, 0, 2, 5, 7, 9 (16-layer windows of the 9.604 um render, layers 13+k..28+k) over the
#    box Y0:Y1, X0:X1 of the crop frame (m3/s3b_hecate.sh).
# Outputs go to data/m3b/<SAMPLE>/<MESH>/. Refuses to run unless the S3b pre-registration is committed and unmodified.
# TAGS and KS (environment) restrict the windows, as for the regrown surfaces (the row's peak window only).
# Usage: [TAGS="p10" KS="9"] bash m3/s3b_sweep.sh SAMPLE MESH DIR GPU CPUS Y0 Y1 X0 X1
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; s=$1; m=$2; dr=$3; G=$4; CPUS=$5; BY0=$6; BY1=$7; BX0=$8; BX1=$9
PRE=prereg/M1-survey-S3b.md
git ls-files --error-unmatch $PRE > /dev/null 2>&1 && git diff --quiet HEAD -- $PRE || { echo "prereg not committed"; exit 3; }
X=data/m1/$s/render; O=data/m3b/$s/$m; W=$R/cache/s3b_work/${s}__${m}_$dr
mkdir -p $O $W
echo "prereg $PRE commit $(git log -1 --format=%h -- $PRE)" > $O/prereg_commit.txt
if [ ! -d $X/$m.zarr ]; then
  VOL=$(awk -F'\t' -v s=$s '$2 == s {print $3; exit}' data/m3/s3_queue.tsv)
  CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$s/volumes/$VOL-8.640um-1.2m-116keV-masked.zarr"
  echo "== $(date -u +%FT%TZ) render $s $m"
  nice -n 5 taskset -c $CPUS "$VC3D" vc_render_tifxyz -v "$CT" -g 0 --scale 1 \
    -s data/m1/$s/meshes/$m -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote --surface-interpolation smooth \
    --zarr-output $X/$m.zarr --zarr-compressor none > $O/render.log 2>&1 || { echo "render failed"; exit 1; }
fi
[ -f $X/${m}_9p6.npy ] || nice -n 5 taskset -c $CPUS "$PY" m3/resample9.py $X/$m.zarr $X/${m}_9p6.npy
if [ ! -f $O/crop.json ]; then   # an S3 surface keeps its S3 crop; a regrown one is read over its whole 9.604 um canvas
  cp data/m3/$s/$m/crop.json $O/crop.json 2> /dev/null || "$PY" -c "
import json, numpy as np; r = np.load('$X/${m}_9p6.npy', mmap_mode='r')
json.dump({'crop': [0, r.shape[1], 0, r.shape[2]]}, open('$O/crop.json', 'w'))"
fi
N=$R2_DIR; PY=$N/venv/bin/python; CK=$N/models/reader-v2-step040000.pth
D=$($PY -c "import zarr; g = zarr.open('$X/$m.zarr', mode='r'); print((g['0'] if hasattr(g, 'keys') else g).shape[0])")
d=$([ $dr = fwd ] && echo forward || echo reverse)
for t in ${TAGS:-m20 m15 m10 m5 c p5 p10 p15 p20}; do
  case $t in c) A="";; p*) A="--layer-start ${t#p}";; m*) A="--layer-end $((D - ${t#m}))";; esac
  out=$W/r2_${d}_$t.tif
  [ -s $out ] && continue
  echo "== $(date -u +%FT%TZ) reader-v2 $s $m $dr $t"
  CUDA_VISIBLE_DEVICES=$G OMP_NUM_THREADS=4 nice -n 5 taskset -c $CPUS $PY -m koine_machines.inference.infer \
    $X/$m.zarr $CK $out --overlap 0.5 --blend-mode hann --direction $d --batch-size 32 --num-workers 4 --no-compile $A \
    > $W/r2_${d}_$t.log 2>&1 < /dev/null || { echo "reader-v2 failed $t"; exit 1; }
done
read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$O/crop.json'))['crop'])")
nice -n 5 taskset -c $CPUS $PY m3/s3b_combine.py $W $O $Y0 $Y1 $X0 $X1 $dr || exit 1
bash m3/s3b_hecate.sh $s $m $dr $G $CPUS $BY0 $BY1 $BX0 $BX1 || exit 1
echo "== $(date -u +%FT%TZ) sweep $s $m $dr done"
