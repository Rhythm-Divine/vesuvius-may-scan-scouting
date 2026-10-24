#!/usr/bin/env bash
# M1 survey S2, worker on GPU G (prereg/M1-survey-S2.md). Takes surfaces from data/s2/queue/ready (one per kept S1
# surface, <sample>__<mesh>; the move to running is atomic) and for each:
#   1. renders it natively (48 layers, 8.64 um) exactly as S1 did before resampling, into $S2_SCRATCH (default
#      cache/s2work);
#   2. reads it with reader-v2, forward and reverse, three depth windows each (m2/r2_infer.sh);
#   3. averages, resamples to S1's 9.604 um grid and crops to S1's window (m2/r2_combine.py);
#   4. writes the readout (m2/readout_r2.py) and the triage row (m2/triage_r2.py);
#   5. deletes the native volume and window maps; the 9.604 um maps and readout stay in data/s2/<sample>/<mesh>/.
# A surface that fails goes to failed/. Refuses to run unless the pre-registration is committed and unmodified.
# Usage: bash m2/batch/s2_worker.sh G CPUS
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
G=$1; CPUS=$2
PRE=prereg/M1-survey-S2.md; T2=0.6275; BG2=0.0155
git ls-files --error-unmatch "$PRE" > /dev/null 2>&1 && git diff --quiet HEAD -- "$PRE" || { echo "prereg not committed"; exit 3; }
N=${S2_SCRATCH:-$R/cache/s2work}; PY2=$R2_DIR/venv/bin/python
Q=data/s2/queue; mkdir -p $Q/ready $Q/running $Q/done $Q/failed
C=$R/cache/vc3d_s2_g$G; mkdir -p $C/config $C/remote
printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
one () {   # SAMPLE MESH
  local s=$1 m=$2 W=$N/$1__$2 O=data/s2/$1/$2 H=data/m1/$1/hecate/$2
  local v; v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' data/m1/survey_zones.tsv)
  local CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$s/volumes/$v-8.640um-1.2m-116keV-masked.zarr"
  mkdir -p $W $O
  echo "prereg $PRE commit $(git log -1 --format=%h -- $PRE)" > $O/prereg_commit.txt
  if [ ! -e $W/native.done ]; then
    VC3D_CONFIG_DIR=$C/config OMP_NUM_THREADS=$GROW_THREADS nice -n $NICE taskset -c $CPUS "$VC3D" vc_render_tifxyz \
      -v "$CT" -g 0 --scale 1 -s data/m1/$s/meshes/$m -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote \
      --surface-interpolation smooth --zarr-output $W/native.zarr --zarr-compressor none > $W/render.log 2>&1 < /dev/null \
      || return 1
    rm -rf $C/remote/*; touch $W/native.done
  fi
  bash m2/r2_infer.sh $W/native.zarr $W $G $CPUS || return 1
  local Y0 Y1 X0 X1
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$H/crop.json'))['crop'])")
  nice -n $NICE taskset -c $CPUS $PY2 m2/r2_combine.py $W $O $Y0 $Y1 $X0 $X1 > /dev/null || return 1
  nice -n $NICE taskset -c $CPUS "$PY" m2/readout_r2.py --mesh data/m1/$s/meshes/$m \
    --render9 data/m1/$s/render/${m}_9p6.npy --hecate-dir $H --pred-dir $O --t2 $T2 --bg $BG2 \
    --selfcross data/m1/$s/render/${m}_selfcross.json --crop $Y0 $Y1 $X0 $X1 > $O/readout_r2.log 2>&1 || return 1
  "$PY" m2/triage_r2.py $s $m || return 1
  rm -rf $W
}
while true; do
  item=$(ls $Q/ready 2> /dev/null | head -n 1)
  [ -z "$item" ] && break
  mv $Q/ready/$item $Q/running/$item 2> /dev/null || continue
  echo "== $(date -u +%FT%TZ) GPU $G reads $item"
  if one ${item%%__*} ${item#*__}; then mv $Q/running/$item $Q/done/$item
  else echo "== $(date -u +%FT%TZ) GPU $G FAILED $item"; mv $Q/running/$item $Q/failed/$item; fi
done
echo "== $(date -u +%FT%TZ) GPU $G done"
