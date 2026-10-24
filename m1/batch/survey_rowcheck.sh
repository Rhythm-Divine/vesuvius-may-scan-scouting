#!/usr/bin/env bash
# M1 survey S1 row-candidate check (prereg/M1-survey-S1.md, deviation of 2026-10-24 04:10 UTC) for one surface that
# shows a row of blobs along the text direction. Grows, QCs and queues three more surfaces, read ahead of the rest:
#   <zone>_r_s2:  a second seed on the same sheet, 400 slices (3.5 mm) from the row (m1/rowcheck_seeds.py), snapped to
#                 the m7 prediction by m1/seed.py;
#   <zone>_r_in, <zone>_r_out: the neighbouring windings (m1/seeds_radial.py --inward 1 --outward 1 through the row).
# Growth, QC and the queue are as in stage 1 (m1/batch/survey_trace.sh).
# Usage: bash m1/batch/survey_rowcheck.sh CPUS SAMPLE ZONE MESH Y X [Y X ...]   (Y X: crop pixels along the row)
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
CPUS=$1; s=$2; zone=$3; mesh=$4; shift 4
T="nice -n $NICE taskset -c $CPUS"
Q=data/m1/survey_queue; LOG=data/m1/survey_qc.tsv; Z=data/m1/survey_zones.tsv
row () { ( flock 9; printf "%s\t%s\n" "$(date -u +%FT%TZ)" "$1" >> $LOG ) 9> $LOG.lock; }
v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' $Z)
O=data/m1/$s; F=$O/zone_${zone}_r; mkdir -p $F
pref="$s/representations/predictions/surfaces/$v-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
read -r cy cx < <(awk -F'\t' -v s=$s -v zz=$zone '$1 == s && $3 == zz {print $7, $8}' $Z)
"$PY" m1/rowcheck_seeds.py $s $mesh "$@" | tee $F/rowcheck_seeds.txt
read -r _ mx my mz < <(grep '^mid' $F/rowcheck_seeds.txt)
read -r _ ax ay az < <(grep '^s2' $F/rowcheck_seeds.txt)
echo "== $(date -u +%FT%TZ) row check for $s $zone (row middle $mx $my $mz)"
: > cache/tmp/r_$zone.txt
p=$($T "$PY" m1/seed.py --prefix "$pref" --z $az --y $ay --x $ax --centre-yx $cy $cx --out ${F}_s2 \
      2> /dev/null < /dev/null | tail -n 1)
[ -n "$p" ] && echo "s2 $p" >> cache/tmp/r_$zone.txt
$T "$PY" m1/seeds_radial.py --seed $mx $my $mz --centre-yx $cy $cx --inward 1 --outward 1 --prefix "$pref" \
    --out $F > /dev/null 2>&1 < /dev/null
"$PY" -c "
import json
for d in json.load(open('$F/seeds.json'))['seeds']: print({'inward': 'in', 'outward': 'out'}[d['direction']], d['x'], d['y'], d['z'])
" >> cache/tmp/r_$zone.txt
cat cache/tmp/r_$zone.txt
while read -r tag fx fy fz; do
  zf=${zone}_r_$tag; sd="$fx $fy $fz"
  awk -F'\t' -v s=$s -v zz=$zf '$2 == s && $3 == zz {f = 1} END {exit !f}' $LOG && continue
  before=$(ls $O/meshes)
  SAMPLE=$s VOL=$v CPUS=$CPUS VC3D_CACHE=$R/cache/vc3d_r bash m1/grow_more.sh "$sd" >> logs/survey_rowcheck.log 2>&1 < /dev/null
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
done < cache/tmp/r_$zone.txt
echo "== $(date -u +%FT%TZ) row check for $s $zone done"
