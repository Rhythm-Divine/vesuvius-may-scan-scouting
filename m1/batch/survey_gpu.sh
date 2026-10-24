#!/usr/bin/env bash
# M1 survey S1, Hecate worker on GPU G (prereg/M1-survey-S1.md).
# - It takes the oldest queued surface. The move from ready to running is atomic, so no surface is read twice.
# - It reads the surface with m1/hecate_more.sh: windows -2..+2, both directions, through the guard on GPU G.
#   hecate_more.sh refuses to run unless the pre-registration is committed.
# - It then writes the triage row (m1/survey_triage.py).
# - A surface whose read or triage fails goes to failed/ instead of done/, so it can be retried.
# - It exits once all NT tracers (and stage-2 workers) are done and the queue is empty.
# Usage: bash m1/batch/survey_gpu.sh G CPUS [NT]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
G=$1; CPUS=$2; NT=${3:-5}; PRE=prereg/M1-survey-S1.md
Q=data/m1/survey_queue; mkdir -p $Q/ready $Q/running $Q/done $Q/failed
while true; do
  item=$(ls -tr $Q/ready 2> /dev/null | head -n 1)
  if [ -z "$item" ]; then
    [ "$(ls $Q/tracer_done_w* 2> /dev/null | wc -l)" -ge "$NT" ] && [ -z "$(ls $Q/ready)" ] && break
    sleep 30; continue
  fi
  mv $Q/ready/$item $Q/running/$item 2> /dev/null || continue
  s=${item%%__*}; m=${item#*__}
  echo "== $(date -u +%FT%TZ) GPU $G reads $s $m"
  if SAMPLE=$s PRE=$PRE GPU=$G CPUS=$CPUS bash m1/hecate_more.sh $m < /dev/null \
     && nice -n $NICE "$PY" m1/survey_triage.py $s $m; then
    echo "prereg $PRE" >> data/m1/$s/hecate/$m/prereg_commit.txt
    mv $Q/running/$item $Q/done/$item
  else
    echo "== $(date -u +%FT%TZ) GPU $G FAILED $s $m"
    mv $Q/running/$item $Q/failed/$item
  fi
done
echo "== $(date -u +%FT%TZ) GPU $G done"
