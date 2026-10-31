#!/usr/bin/env bash
# M1 survey S3, reader-v2 worker on GPU G (prereg/M1-survey-S3.md). Takes surfaces from data/m3/queue/ready
# (<sample>__<mesh>; the move to running is atomic) and for each:
#   1. reads its native render (left on the NVMe by a tracer) with reader-v2, forward and reverse: a new surface with
#      windows c, p2, m2 (S2's read) and p6, m6 (the deeper read); an S1 surface, already read by S2, with p6 and m6;
#   2. combines the maps and aligns them to the 9.604 um grid and the readout window (m3/r3_combine.py);
#   3. writes the readout (m3/readout_r3.py) and the triage row (m3/triage_r3.py);
#   4. deletes the native render and the window maps. The 9.604 um render stays on the NVMe for a Hecate check.
# A surface that fails goes to failed/. Exits once NT tracers are done and the queue is empty. Refuses to run unless
# the pre-registration is committed and unmodified.
# Usage: bash m3/batch/s3_reader.sh G CPUS NT
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"; G=$1; CPUS=$2; NT=$3
PRE=prereg/M1-survey-S3.md; T2=0.6275
git ls-files --error-unmatch "$PRE" > /dev/null 2>&1 && git diff --quiet HEAD -- "$PRE" || { echo "prereg not committed"; exit 3; }
PY2=$R2_DIR/venv/bin/python
Q=data/m3/queue; mkdir -p $Q/ready $Q/running $Q/done $Q/failed
one () {   # SAMPLE MESH
  local s=$1 m=$2 O=data/m3/$1/$2 X=data/m1/$1/render W=$R/cache/s3_work/$1__$2 wins
  mkdir -p $O $W
  echo "prereg $PRE commit $(git log -1 --format=%h -- $PRE)" > $O/prereg_commit.txt
  if [ -s data/s2/$s/$m/pred_r2_fwd.png ]; then
    wins="p6 m6"; cp data/m1/$s/hecate/$m/crop.json $O/crop.json
  else
    wins="c p2 m2 p6 m6"; cp $X/${m}_clean.json $O/crop.json
  fi
  WINDOWS="$wins" bash m3/r2_infer_s3.sh $X/$m.zarr $W $G $CPUS || return 1
  local Y0 Y1 X0 X1
  read -r Y0 Y1 X0 X1 < <("$PY" -c "import json; print(*json.load(open('$O/crop.json'))['crop'])")
  nice -n 10 taskset -c $CPUS $PY2 m3/r3_combine.py $W $O $Y0 $Y1 $X0 $X1 > /dev/null || return 1
  nice -n 10 taskset -c $CPUS "$PY" m3/readout_r3.py --sample $s --mesh $m --t2 $T2 \
    > $O/readout_r3.log 2>&1 || return 1
  "$PY" m3/triage_r3.py $s $m || return 1
  rm -rf $W $X/$m.zarr $X/${m}.native.done
}
while true; do
  item=$(ls -tr $Q/ready 2> /dev/null | head -n 1)
  if [ -z "$item" ]; then
    [ "$(ls $Q/tracer_done_w* 2> /dev/null | wc -l)" -ge "$NT" ] && [ -z "$(ls $Q/ready)" ] && break
    sleep 30; continue
  fi
  mv $Q/ready/$item $Q/running/$item 2> /dev/null || continue
  echo "== $(date -u +%FT%TZ) GPU $G reads $item"
  if one ${item%%__*} ${item#*__} < /dev/null; then mv $Q/running/$item $Q/done/$item
  else echo "== $(date -u +%FT%TZ) GPU $G FAILED $item"; mv $Q/running/$item $Q/failed/$item; fi
done
echo "== $(date -u +%FT%TZ) GPU $G done"
