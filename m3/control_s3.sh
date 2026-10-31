#!/usr/bin/env bash
# S3 controls for reader-v2's windows on this restart, run before prereg/M1-survey-S3.md is committed and before any
# S3 output on a survey surface exists.
#   E1b: the organisers' native PHerc0009B surface volume, windows c, p2, m2, p6 and m6, forward and reverse (GPU 0).
#        The near map (S2's read, repeated) and the p6 and m6 maps are scored against the same-mesh labels:
#        e1b/score.py gives AUC and each map's own T; m3/bg_t2.py gives the share of non-ink pixels >= T2, which is the
#        triage background of each window family.
#   E1d: our own PHerc0343 mesh, rendered natively again and read with the same windows (GPU 1), then Hecate at the p6
#        and m6 depths, forward (GPUs 2 and 3), and the S3 readout: the by-eye check that the October text line shows,
#        and the deeper maps' agreement on known text.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; N=$R/cache/s3; PY2=$R2_DIR/venv/bin/python
V="$VC3D"; T2=0.6275
mkdir -p $N/ctrl data/m3/e1b
e1b () {
  echo "== $(date -u +%FT%TZ) E1b reader-v2, S3 windows"
  Z=$(ls -d data/PHerc0009B/segments/*/surface-volumes/*.zarr | head -n 1)
  WINDOWS="c p2 m2 p6 m6" bash m3/r2_infer_s3.sh "$Z" $N/ctrl/e1b 0 0-11 || return 1
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('data/e1b/register.json'))['window'])")
  $PY2 m3/r3_combine.py $N/ctrl/e1b data/m3/e1b $Y0 $Y1 $X0 $X1
  cp data/e1b/register.json data/m3/e1b/
  P=(data/m3/e1b/pred_r3_fwd.png data/m3/e1b/pred_r3_rev.png data/m3/e1b/pred_r3_fwd_p6.png
     data/m3/e1b/pred_r3_rev_p6.png data/m3/e1b/pred_r3_fwd_m6.png data/m3/e1b/pred_r3_rev_m6.png)
  "$PY" e1b/score.py --out data/m3/e1b "${P[@]}"
  "$PY" m3/bg_t2.py --out data/m3/e1b --t2 $T2 "${P[@]}"
  echo "== $(date -u +%FT%TZ) E1b DONE"
}
e1d () {
  local S=PHerc0343 M_NAME=auto_grown_20261023221723612 C=$R/cache/vc3d_s3ctl
  local M=data/m1/$S/meshes/$M_NAME X=data/m1/$S/render O=data/m3/$S/$M_NAME
  local CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$S/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr"
  mkdir -p $C/config $C/remote $O $X
  printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > "$C/config/VC3D.ini"
  echo "== $(date -u +%FT%TZ) E1d native render"
  if [ ! -e $X/${M_NAME}.native.done ]; then
    VC3D_CONFIG_DIR=$C/config OMP_NUM_THREADS=8 nice -n 10 taskset -c 12-23 "$V" vc_render_tifxyz -v "$CT" -g 0 --scale 1 \
      -s "$M" -n 48 --slice-step 1 --cache-gb 4 --prefetch-remote --surface-interpolation smooth \
      --zarr-output $X/$M_NAME.zarr --zarr-compressor none > $N/ctrl/e1d_render.log 2>&1 && touch $X/${M_NAME}.native.done
  fi
  rm -rf $C/remote
  [ -s $X/${M_NAME}_selfcross.json ] || nice -n 10 taskset -c 12-23 "$V" vc_tifxyz_selfcross --surface "$M" \
    -o $X/${M_NAME}_selfcross.json --threads 8 > $X/${M_NAME}_selfcross.log 2>&1
  [ -s $X/${M_NAME}_9p6.npy ] || nice -n 10 taskset -c 12-23 "$PY" m3/resample9.py $X/$M_NAME.zarr $X/${M_NAME}_9p6.npy
  echo "== $(date -u +%FT%TZ) E1d reader-v2, S3 windows"
  WINDOWS="c p2 m2 p6 m6" bash m3/r2_infer_s3.sh $X/$M_NAME.zarr $N/ctrl/e1d 1 12-23 || return 1
  cp data/m1/$S/hecate/$M_NAME/crop.json $O/crop.json
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$O/crop.json'))['crop'])")
  $PY2 m3/r3_combine.py $N/ctrl/e1d $O $Y0 $Y1 $X0 $X1
  echo "== $(date -u +%FT%TZ) E1d Hecate at the p6 and m6 depths, forward"
  bash m3/hecate_confirm.sh $S $M_NAME p6 fwd 2 24-35 &
  bash m3/hecate_confirm.sh $S $M_NAME m6 fwd 3 36-47 &
  wait
  "$PY" m3/readout_r3.py --sample $S --mesh $M_NAME --t2 $T2 --kind new --hecate-dir data/m1/$S/hecate/$M_NAME
  echo "== $(date -u +%FT%TZ) E1d DONE"
}
e1b > logs/s3_ctrl_e1b.log 2>&1 &
e1d > logs/s3_ctrl_e1d.log 2>&1 &
wait
echo "== $(date -u +%FT%TZ) S3 CONTROLS DONE"
