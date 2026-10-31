#!/usr/bin/env bash
# M1 survey S3, tracing worker W (prereg/M1-survey-S3.md).
# - With OLD=1 it first prepares the S1 surfaces for the deeper read: each item of data/m3/oldq/ready is rendered
#   natively again (renders lived on the NVMe, which the stop wiped), resampled to 9.604 um, and its self-crossing
#   census redone, then queued for reader-v2 (data/m3/queue/ready).
# - Then it takes growth jobs from data/m3/jobs/ready in their pre-registered order (the move to running is atomic):
#   one job is one zone's new windings, or one new zone's test surface. It grows them (m3/grow_s3.sh), then for each
#   new mesh runs S1's QC (clean area, papyrus share) and, for a kept surface, the duplicate check (m3/distinct.py)
#   under the QC-log lock. A kept, distinct surface is queued for reader-v2; other renders are deleted.
# - No growth job starts at or after the stop time, 2026-10-24 22:30 UTC.
# Refuses to run unless the pre-registration is committed and unmodified.
# Usage: bash m3/batch/s3_trace.sh W CPUS [OLD]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
W=$1; CPUS=$2; OLD=${3:-0}
PRE=prereg/M1-survey-S3.md
git ls-files --error-unmatch $PRE > /dev/null 2>&1 && git diff --quiet HEAD -- $PRE || { echo "prereg not committed"; exit 3; }
STOP=1792881000   # 2026-10-24 22:30:00 UTC
T="nice -n 10 taskset -c $CPUS"; V="$VC3D"; C=$PWD/cache/vc3d_s3_w$W
J=data/m3/jobs; Q=data/m3/queue; OQ=data/m3/oldq; LOG=data/m3/s3_qc.tsv; Z=data/m1/survey_zones.tsv
mkdir -p $J/running $J/done $Q/ready $OQ/running $OQ/done $OQ/failed cache/tmp logs
( flock 9; [ -s $LOG ] || printf "time\tsample\tsurface\tseed\tmesh\tgrown_cm2\tcontacts\tclean_cm2\ton_papyrus\tdecision\tdistinct\n" > $LOG ) 9> $LOG.lock
old_one () {   # SAMPLE MESH: an S1 surface, prepared again for reader-v2
  local s=$1 m=$2 O=data/m1/$1 v
  v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' $Z)
  local CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$s/volumes/$v-8.640um-1.2m-116keV-masked.zarr"
  mkdir -p $C/config $C/remote $O/render/
  printf '[viewer]\nremote_cache_dir=%s\n' "$C/remote" > $C/config/VC3D.ini
  [ -s $O/render/${m}_selfcross.json ] || OMP_NUM_THREADS=8 $T $V vc_tifxyz_selfcross --surface $O/meshes/$m \
    -o $O/render/${m}_selfcross.json --threads 8 > $O/render/${m}_selfcross.log 2>&1 < /dev/null || return 1
  if [ ! -e $O/render/${m}.native.done ]; then
    rm -rf $O/render/$m.zarr
    VC3D_CONFIG_DIR=$C/config OMP_NUM_THREADS=8 $T $V vc_render_tifxyz -v "$CT" -g 0 --scale 1 -s $O/meshes/$m -n 48 \
      --slice-step 1 --cache-gb 4 --prefetch-remote --surface-interpolation smooth --zarr-output $O/render/$m.zarr \
      --zarr-compressor none > $O/render/${m}_render.log 2>&1 < /dev/null || return 1
    touch $O/render/${m}.native.done
  fi
  [ -s $O/render/${m}_9p6.npy ] || $T "$PY" m3/resample9.py $O/render/$m.zarr $O/render/${m}_9p6.npy \
    > /dev/null 2>&1 < /dev/null || return 1
  rm -rf $C/remote/*
  touch $Q/ready/${s}__$m
}
job_one () {   # JOB FILE: lines SAMPLE VOLUME SURFACE "X Y Z"
  local f=$1 s v SM=cache/tmp/seedmap_w$W.tsv
  s=$(head -n 1 $f | cut -f1); v=$(head -n 1 $f | cut -f2)
  local O=data/m1/$s
  : > $SM
  mapfile -t seeds < <(cut -f4 $f)
  W=$W SAMPLE=$s VOL=$v GROW_CPUS=$CPUS VC3D_CACHE=$C SEEDMAP=$PWD/$SM bash m3/grow_s3.sh "${seeds[@]}" \
    >> logs/s3_trace_w$W.log 2>&1 < /dev/null
  while IFS=$'\t' read -r _ _ surf seed; do
    m=$(awk -F'\t' -v sd="$seed" '$1 == sd {print $2; exit}' $SM)
    if [ -z "$m" ] || [ "$m" = - ]; then
      ( flock 9; printf "%s\t%s\t%s\t%s\t-\t-\t-\t-\t-\tno_mesh\t-\n" "$(date -u +%FT%TZ)" "$s" "$surf" "$seed" >> $LOG ) 9> $LOG.lock
      continue
    fi
    $T "$PY" m1/readout_crop.py --mesh $O/meshes/$m --render9 $O/render/${m}_9p6.npy \
      --selfcross $O/render/${m}_selfcross.json --exclude-contacts 8 --out $O/render/${m}_clean.json > /dev/null 2>&1 < /dev/null
    $T "$PY" m1/onpapyrus.py --sample $s --volume-id $v $m 2> /dev/null < /dev/null | tail -n 1 \
      > $O/render/${m}_onpapyrus.json
    qc=$("$PY" m1/survey_qc.py $O $m < /dev/null)
    (
      flock 9
      dist=-
      [ "${qc##*$'\t'}" = keep ] && dist=$("$PY" m3/distinct.py $s $m 2> /dev/null < /dev/null)
      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$(date -u +%FT%TZ)" "$s" "$surf" "$seed" "$m" "$qc" "${dist:-failed}" >> $LOG
      if [ "${qc##*$'\t'}" = keep ] && [ "${dist%% *}" = distinct ]; then touch $Q/ready/${s}__$m
      else rm -rf $O/render/$m.zarr $O/render/${m}_9p6.npy; fi
    ) 9> $LOG.lock
  done < $f
}
if [ "$OLD" = 1 ]; then
  while true; do
    item=$(ls $OQ/ready 2> /dev/null | head -n 1)
    [ -z "$item" ] && break
    mv $OQ/ready/$item $OQ/running/$item 2> /dev/null || continue
    echo "== $(date -u +%FT%TZ) tracer $W prepares S1 surface $item"
    if old_one ${item%%__*} ${item#*__}; then mv $OQ/running/$item $OQ/done/$item
    else echo "== $(date -u +%FT%TZ) FAILED $item"; mv $OQ/running/$item $OQ/failed/$item; fi
  done
fi
while true; do
  [ "$(date +%s)" -ge "$STOP" ] && { echo "== $(date -u +%FT%TZ) stop time reached"; break; }
  item=$(ls $J/ready 2> /dev/null | sort | head -n 1)
  [ -z "$item" ] && break
  mv $J/ready/$item $J/running/$item 2> /dev/null || continue
  echo "== $(date -u +%FT%TZ) tracer $W job $item"
  job_one $J/running/$item
  mv $J/running/$item $J/done/$item
done
touch $Q/tracer_done_w$W
echo "== $(date -u +%FT%TZ) tracer $W done"
