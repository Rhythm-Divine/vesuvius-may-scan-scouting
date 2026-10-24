#!/usr/bin/env bash
# S2 controls for reader-v2 (run before prereg/M1-survey-S2.md was committed, and before any survey surface was read).
#   E1b: the organisers' native PHerc0009B surface volume (fetched by e1/fetch_control.py), scored against their
#        same-mesh labels (e1b/fetch_labels.sh) with e1b/score.py on E1b's window and registration (data/e1b/register.json
#        from e1b/job.sh), plus the control background (m2/r2_bg.py). Forward and reverse. GPU 0.
#   E1d: the PHerc0343 mesh grown by m1/control343_job.sh, rendered natively (48 layers, 8.64 um) and read the S2 way,
#        on the S1 readout window, for the by-eye check that the October text line shows. GPU 1.
# Note: reader-v2's training includes 14 PHerc0009B and 6 PHerc0343 segments, so these are pipeline checks.
# Usage: bash m2/control_job.sh [E1D_MESH_NAME]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"
N=$R/cache/s2ctrl; mkdir -p $N data/s2/e1b; PY2=$R2_DIR/venv/bin/python
e1b () {
  echo "== $(date -u +%FT%TZ) E1b reader-v2"
  Z=$(ls -d data/PHerc0009B/segments/*/surface-volumes/*.zarr | head -n 1)
  bash m2/r2_infer.sh "$Z" $N/e1b 0 || return 1
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('data/e1b/register.json'))['window'])")
  $PY2 m2/r2_combine.py $N/e1b data/s2/e1b $Y0 $Y1 $X0 $X1
  cp data/e1b/register.json data/s2/e1b/
  "$PY" e1b/score.py --out data/s2/e1b data/s2/e1b/pred_r2_fwd.png data/s2/e1b/pred_r2_rev.png
  "$PY" m2/r2_bg.py --out data/s2/e1b data/s2/e1b/pred_r2_fwd.png data/s2/e1b/pred_r2_rev.png
  echo "== $(date -u +%FT%TZ) E1b DONE"
}
e1d () {
  echo "== $(date -u +%FT%TZ) E1d native render"
  M_NAME=${1:-$(ls data/m1/PHerc0343/meshes | head -n 1)}; M=data/m1/PHerc0343/meshes/$M_NAME; C=$R/cache/vc3d_s2ctl
  CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr"
  mkdir -p $C/config $C/remote
  printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
  [ -d $N/e1d/native.zarr ] || VC3D_CONFIG_DIR=$C/config OMP_NUM_THREADS=$GROW_THREADS $RUN "$VC3D" vc_render_tifxyz \
    -v "$CT" -g 0 --scale 1 -s "$M" -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote --surface-interpolation smooth \
    --zarr-output $N/e1d/native.zarr --zarr-compressor none > $N/e1d_render.log 2>&1
  echo "render rc=$?"; rm -rf $C/remote
  echo "== $(date -u +%FT%TZ) E1d reader-v2"
  bash m2/r2_infer.sh $N/e1d/native.zarr $N/e1d 1 || return 1
  P=data/m1/PHerc0343/hecate/$M_NAME; Q=data/s2/PHerc0343/$M_NAME
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$P/crop.json'))['crop'])")
  $PY2 m2/r2_combine.py $N/e1d $Q $Y0 $Y1 $X0 $X1
  "$PY" m2/readout_r2.py --mesh $M --render9 data/m1/PHerc0343/render/${M_NAME}_9p6.npy --hecate-dir $P --pred-dir $Q \
    --t2 0.6275 --bg 0.0155 --selfcross data/m1/PHerc0343/render/${M_NAME}_selfcross.json --crop $Y0 $Y1 $X0 $X1
  echo "== $(date -u +%FT%TZ) E1d DONE"
}
e1b > logs/s2_ctrl_e1b.log 2>&1 &
e1d "${1:-}" > logs/s2_ctrl_e1d.log 2>&1 &
wait
echo "== $(date -u +%FT%TZ) S2 CONTROLS DONE"
