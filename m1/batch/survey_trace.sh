#!/usr/bin/env bash
# M1 survey S1, tracing worker W (prereg/M1-survey-S1.md). For each zone of its volumes in data/m1/survey_zones.tsv:
#   1. seed (m1/seed.py at the crop centre);
#   2. grow, self-crossing census and render (m1/grow_more.sh, with its own VC3D cache);
#   3. QC: clean readout area (m1/readout_crop.py) and papyrus share (m1/onpapyrus.py).
# The QC row goes to data/m1/survey_qc.tsv first. A surface with >= 2 cm2 clean and >= 0.8 on papyrus is then queued
# for Hecate (data/m1/survey_queue/ready). A dropped surface keeps its mesh, but its render is deleted.
# Renders go to $RENDER_SCRATCH/<sample> when RENDER_SCRATCH is set (e.g. a fast local disk), else data/m1/<sample>/render.
# Zones already in the QC log are skipped, so a restart resumes.
# Usage: bash m1/batch/survey_trace.sh W CPUS SAMPLE [SAMPLE ...]
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"; cd "$R"; . "$R/config.sh"
W=$1; CPUS=$2; shift 2
T="nice -n $NICE taskset -c $CPUS"
Q=data/m1/survey_queue; LOG=data/m1/survey_qc.tsv; Z=data/m1/survey_zones.tsv
mkdir -p $Q/ready $Q/running $Q/done cache/tmp logs
( flock 9; [ -s $LOG ] || printf "time\tsample\tzone\tseed\tmesh\tgrown_cm2\tcontacts\tclean_cm2\ton_papyrus\tdecision\n" > $LOG ) 9> $LOG.lock
row () { ( flock 9; printf "%s\t%s\n" "$(date -u +%FT%TZ)" "$1" >> $LOG ) 9> $LOG.lock; }
for s in "$@"; do
  v=$(awk -F'\t' -v s=$s '$1 == s {print $2; exit}' $Z)
  [ -z "$v" ] && continue
  O=data/m1/$s
  mkdir -p $O/meshes
  if [ -n "${RENDER_SCRATCH:-}" ]; then mkdir -p "$RENDER_SCRATCH/$s"; [ -e $O/render ] || ln -s "$RENDER_SCRATCH/$s" $O/render; fi
  mkdir -p $O/render
  pref="$s/representations/predictions/surfaces/$v-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
  awk -F'\t' -v s=$s 'NR > 1 && $1 == s' $Z > cache/tmp/zones_w$W.tsv
  while IFS=$'\t' read -r _ _ zone z y x cy cx _ _ _; do
    awk -F'\t' -v s=$s -v zz=$zone '$2 == s && $3 == zz {f = 1} END {exit !f}' $LOG && continue
    seed=$($T "$PY" m1/seed.py --prefix "$pref" --z $z --y $y --x $x --centre-yx $cy $cx \
             --out $O/zone_$zone 2> /dev/null < /dev/null | tail -n 1)
    [ -z "$seed" ] && { row "$s"$'\t'"$zone"$'\t-\t-\t-\t-\t-\t-\tno_seed'; continue; }
    before=$(ls $O/meshes)
    SAMPLE=$s VOL=$v CPUS=$CPUS VC3D_CACHE=$R/cache/vc3d_w$W bash m1/grow_more.sh "$seed" \
        >> logs/survey_trace_w$W.log 2>&1 < /dev/null
    m=$(comm -13 <(echo "$before") <(ls $O/meshes) | head -n 1)
    [ -z "$m" ] && { row "$s"$'\t'"$zone"$'\t'"$seed"$'\t-\t-\t-\t-\t-\tno_mesh'; continue; }
    $T "$PY" m1/readout_crop.py --mesh $O/meshes/$m --render9 $O/render/${m}_9p6.npy \
        --selfcross $O/render/${m}_selfcross.json --exclude-contacts 8 --out $O/render/${m}_clean.json \
        > /dev/null 2>&1 < /dev/null
    $T "$PY" m1/onpapyrus.py --sample $s --volume-id $v $m 2> /dev/null < /dev/null | tail -n 1 \
        > $O/render/${m}_onpapyrus.json
    qc=$("$PY" m1/survey_qc.py $O $m)
    row "$s"$'\t'"$zone"$'\t'"$seed"$'\t'"$m"$'\t'"$qc"
    if [ "${qc##*$'\t'}" = keep ]; then touch $Q/ready/${s}__$m; else rm -f $O/render/${m}_9p6.npy; fi
  done < cache/tmp/zones_w$W.tsv
done
touch $Q/tracer_done_w$W
echo "== $(date -u +%FT%TZ) tracer $W done"
