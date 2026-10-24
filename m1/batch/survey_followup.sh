#!/usr/bin/env bash
# M1 survey S1 follow-up check (prereg/M1-survey-S1.md, deviation of 2026-10-24 01:50 UTC) for one surface with more than
# 9.4% of its readout area >= T. Grows, QCs and queues three more surfaces, read ahead of the rest of the queue:
#   <zone>_f_in, <zone>_f_out: the neighbouring windings (m1/seeds_radial.py --inward 1 --outward 1 through its seed);
#   <zone>_f_z200: a second seed on the same winding (m1/seed.py at the same y, x, 200 slices higher).
# Growth, QC and the queue are as in stage 1 (m1/batch/survey_trace.sh).
# Usage: bash m1/batch/survey_followup.sh CPUS SAMPLE ZONE
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
CPUS=$1; s=$2; zone=$3
T="nice -n $NICE taskset -c $CPUS"
Q=data/m1/survey_queue; LOG=data/m1/survey_qc.tsv; Z=data/m1/survey_zones.tsv
row () { ( flock 9; printf "%s\t%s\n" "$(date -u +%FT%TZ)" "$1" >> $LOG ) 9> $LOG.lock; }
v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' $Z)
O=data/m1/$s; F=$O/zone_${zone}_f
pref="$s/representations/predictions/surfaces/$v-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
read -r sx sy sz < <(awk -F'\t' -v s=$s -v zz=$zone '$2 == s && $3 == zz {print $4; exit}' $LOG)
read -r cy cx < <(awk -F'\t' -v s=$s -v zz=$zone '$1 == s && $3 == zz {print $7, $8}' $Z)
echo "== $(date -u +%FT%TZ) follow-up for $s $zone (seed $sx $sy $sz)"
$T "$PY" m1/seeds_radial.py --seed $sx $sy $sz --centre-yx $cy $cx --inward 1 --outward 1 --prefix "$pref" \
    --out $F > /dev/null 2>&1 < /dev/null
"$PY" -c "
import json
for d in json.load(open('$F/seeds.json'))['seeds']: print({'inward': 'in', 'outward': 'out'}[d['direction']], d['x'], d['y'], d['z'])
" > cache/tmp/f_$zone.txt
z2=$((sz + 200))
p=$($T "$PY" m1/seed.py --prefix "$pref" --z $z2 --y $sy --x $sx --centre-yx $cy $cx --out ${F}_z200 \
      2> /dev/null < /dev/null | tail -n 1)
[ -n "$p" ] && echo "z200 $p" >> cache/tmp/f_$zone.txt
cat cache/tmp/f_$zone.txt
while read -r tag fx fy fz; do
  zf=${zone}_f_$tag; sd="$fx $fy $fz"
  awk -F'\t' -v s=$s -v zz=$zf '$2 == s && $3 == zz {f = 1} END {exit !f}' $LOG && continue
  before=$(ls $O/meshes)
  SAMPLE=$s VOL=$v CPUS=$CPUS VC3D_CACHE=$R/cache/vc3d_f bash m1/grow_more.sh "$sd" >> logs/survey_followup.log 2>&1 < /dev/null
  m=$(comm -13 <(echo "$before") <(ls $O/meshes) | head -n 1)
  [ -z "$m" ] && { row "$s"$'\t'"$zf"$'\t'"$sd"$'\t-\t-\t-\t-\t-\tno_mesh'; continue; }
  $T "$PY" m1/readout_crop.py --mesh $O/meshes/$m --render9 $O/render/${m}_9p6.npy \
      --selfcross $O/render/${m}_selfcross.json --exclude-contacts 8 --out $O/render/${m}_clean.json \
      > /dev/null 2>&1 < /dev/null
  $T "$PY" m1/onpapyrus.py --sample $s --volume-id $v $m 2> /dev/null < /dev/null | tail -n 1 \
      > $O/render/${m}_onpapyrus.json
  qc=$("$PY" m1/survey_qc.py $O $m)
  row "$s"$'\t'"$zf"$'\t'"$sd"$'\t'"$m"$'\t'"$qc"
  echo "$zf $m $qc"
  if [ "${qc##*$'\t'}" = keep ]; then
    touch -d "2026-10-23 00:00:00" $Q/ready/${s}__$m   # oldest first, so the GPU workers take it next
  else
    rm -f $O/render/${m}_9p6.npy
  fi
done < cache/tmp/f_$zone.txt
echo "== $(date -u +%FT%TZ) follow-up for $s $zone done"
