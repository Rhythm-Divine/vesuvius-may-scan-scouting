#!/usr/bin/env bash
# S3b, one target end to end (prereg/M1-survey-S3b.md). For an escalated row:
#   1. starts the longer regrowth from the row's seed (m3/grow_s3b.sh: 160 generations) on cores GROW_CPUS;
#   2. sweeps the row's own surface (reader-v2 at nine depths, Hecate at nine depths over the band and row box), then
#      runs the depth test and, for the record, the chain test on the S3 surface at the peak window;
#   3. reads the facing windings on each side with Hecate at the nine depths over the mapped row and band;
#   4. once the regrowth is rendered, reads it at the peak window only (with Hecate at the matching depth over the
#      mapped band) and runs the chain test on it.
# For the control (NAME=E1d) only step 2 runs, and the chain test is run on its own surface.
# Usage: bash m3/s3b_row.sh NAME GPU CPUS GROW_CPUS
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; name=$1; G=$2; CPUS=$3; GC=$4
A=""$PY" m3/s3b_analyse.py"
read -r s m dr seed < <("$PY" -c "
import json; t = json.load(open('data/m3b/targets.json'))['$name']; print(t['sample'], t['mesh'], t['dir'], *t['seed'])" \
  | awk '{print $1, $2, $3, $4" "$5" "$6}')
KOF="m20:-9 m15:-7 m10:-5 m5:-2 c:0 p5:2 p10:5 p15:7 p20:9"
kof () { for p in $KOF; do [ "${p%%:*}" = "$1" ] && echo "${p#*:}"; done; }
echo "== $(date -u +%FT%TZ) S3b $name: $s $m $dr seed $seed"
if [ "$name" != E1d ]; then
  VOL=$(awk -F'\t' -v s=$s '$2 == s {print $3; exit}' data/m3/s3_queue.tsv)
  ( W=b_$name SAMPLE=$s VOL=$VOL GROW_CPUS=$GC VC3D_CACHE=$R/cache/vc3d_s3b_$name SEEDMAP=$R/data/m3b/seeds_$name.tsv \
      bash m3/grow_s3b.sh "$seed" > logs/s3b_grow_$name.log 2>&1 ) &
  GROW=$!
fi
bash m3/s3b_sweep.sh $s $m $dr $G $CPUS $($A box $name) || exit 1
peak=$($A depth $name | "$PY" -c "import json, sys; print(json.load(sys.stdin)['peak'])") || exit 1
k=$(kof $peak); echo "== $(date -u +%FT%TZ) $name peak window $peak (Hecate k $k)"
$A chain $name $m $peak $k > /dev/null || exit 1
[ "$name" = E1d ] && { echo "== $(date -u +%FT%TZ) S3b $name done"; exit 0; }
for side in plus minus; do
  nb=$("$PY" -c "
import json; f = json.load(open('data/m3b/targets.json'))['$name']['facing']; print(f.get('$side', {}).get('mesh', ''))")
  [ -z "$nb" ] && continue
  bash m3/s3b_hecate.sh $s $nb $dr $G $CPUS $($A box $name $nb) || exit 1
  $A facing $name $side > /dev/null || exit 1
done
wait $GROW
new=$(awk -F'\t' '$2 != "-" {print $2}' data/m3b/seeds_$name.tsv | tail -n 1)
[ -n "$new" ] || { echo "regrowth failed: no mesh"; exit 1; }
echo "== $(date -u +%FT%TZ) $name regrown as $new"
mkdir -p data/m3b/$s/$new
"$PY" -c "
import json, numpy as np; r = np.load('data/m1/$s/render/${new}_9p6.npy', mmap_mode='r')
json.dump({'crop': [0, r.shape[1], 0, r.shape[2]]}, open('data/m3b/$s/$new/crop.json', 'w'))" || exit 1
TAGS=$peak KS=$k bash m3/s3b_sweep.sh $s $new $dr $G $CPUS $($A box $name $new) || exit 1
$A chain $name $new $peak $k > /dev/null || exit 1
echo "== $(date -u +%FT%TZ) S3b $name done"
