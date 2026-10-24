#!/usr/bin/env bash
# M1 survey S1, stage 2 for tracer W's volumes (prereg/M1-survey-S1.md).
# - It waits until tracer W has finished stage 1 (data/m1/survey_queue/tracer_done_wW).
# - For each volume it takes the kept stage-1 zone with the most clean area, if that has >= 3 cm2.
# - m1/seeds_radial.py --inward 2 --outward 2 gives up to four seeds for the neighbouring windings, on the radial line
#   through that zone's seed.
# - Each seed is grown, QC'd and queued as in stage 1 (m1/batch/survey_trace.sh), as zone <zone>_w<i>.
# - It ends with tracer_done_w<W>s2, so GPU workers started with NT=12 also wait for stage 2.
# Zones already in the QC log are skipped, so a restart resumes.
# Usage: bash m1/batch/survey_stage2.sh W CPUS SAMPLE [SAMPLE ...]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
W=$1; CPUS=$2; shift 2
T="nice -n $NICE taskset -c $CPUS"
Q=data/m1/survey_queue; LOG=data/m1/survey_qc.tsv; Z=data/m1/survey_zones.tsv
row () { ( flock 9; printf "%s\t%s\n" "$(date -u +%FT%TZ)" "$1" >> $LOG ) 9> $LOG.lock; }
until [ -e $Q/tracer_done_w$W ]; do sleep 60; done
echo "== $(date -u +%FT%TZ) stage 2 for tracer $W"
for s in "$@"; do
  v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' $Z)
  [ -z "$v" ] && continue
  O=data/m1/$s
  pref="$s/representations/predictions/surfaces/$v-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
  best=$(awk -F'\t' -v s=$s '$2 == s && $10 == "keep" && $8 + 0 >= 3 && $3 !~ /_w[0-9]+$/ {print $8 "\t" $3 "\t" $4}' $LOG \
         | sort -t$'\t' -k1,1gr | head -n 1)
  if [ -z "$best" ]; then echo "$s: no kept zone with >= 3 cm2 clean, so no stage 2"; continue; fi
  IFS=$'\t' read -r clean zone seed <<< "$best"
  read -r cy cx < <(awk -F'\t' -v s=$s -v zz=$zone '$1 == s && $3 == zz {print $7, $8}' $Z)
  echo "$s: stage 2 around $zone ($clean cm2 clean, seed $seed)"
  $T "$PY" m1/seeds_radial.py --seed $seed --centre-yx $cy $cx --inward 2 --outward 2 --prefix "$pref" \
      --out $O/zone_${zone}_s2 2> /dev/null < /dev/null | grep -E '^[0-9]+ [0-9]+ [0-9]+$' > cache/tmp/s2_w$W.txt
  i=0
  while read -r sx sy sz; do
    i=$((i + 1)); zw=${zone}_w$i; sd="$sx $sy $sz"
    awk -F'\t' -v s=$s -v zz=$zw '$2 == s && $3 == zz {f = 1} END {exit !f}' $LOG && continue
    before=$(ls $O/meshes)
    SAMPLE=$s VOL=$v CPUS=$CPUS VC3D_CACHE=$R/cache/vc3d_w$W bash m1/grow_more.sh "$sd" \
        >> logs/survey_trace_w$W.log 2>&1 < /dev/null
    m=$(comm -13 <(echo "$before") <(ls $O/meshes) | head -n 1)
    [ -z "$m" ] && { row "$s"$'\t'"$zw"$'\t'"$sd"$'\t-\t-\t-\t-\t-\tno_mesh'; continue; }
    $T "$PY" m1/readout_crop.py --mesh $O/meshes/$m --render9 $O/render/${m}_9p6.npy \
        --selfcross $O/render/${m}_selfcross.json --exclude-contacts 8 --out $O/render/${m}_clean.json \
        > /dev/null 2>&1 < /dev/null
    $T "$PY" m1/onpapyrus.py --sample $s --volume-id $v $m 2> /dev/null < /dev/null | tail -n 1 \
        > $O/render/${m}_onpapyrus.json
    qc=$("$PY" m1/survey_qc.py $O $m)
    row "$s"$'\t'"$zw"$'\t'"$sd"$'\t'"$m"$'\t'"$qc"
    if [ "${qc##*$'\t'}" = keep ]; then touch $Q/ready/${s}__$m; else rm -f $O/render/${m}_9p6.npy; fi
  done < cache/tmp/s2_w$W.txt
done
touch $Q/tracer_done_w${W}s2
echo "== $(date -u +%FT%TZ) stage 2 for tracer $W done"
