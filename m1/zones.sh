#!/usr/bin/env bash
# M1: grow three windings per PHerc0175B zone, for zones given as "NAME Z Y X CENTRE_Y CENTRE_X" (level-0 voxels; the
# zone centre from data/e2/zoom/*/zoom.json and the scroll centre at that height). Per zone: the thin-sheet seed nearest
# the zone centre (m1/seed.py), one winding inward and one outward on its radial line (m1/seeds_radial.py), then
# m1/grow_more.sh (growth sharing one normal-grid cache, QC, render, resample, caches cleared). CPU only, at low
# priority ($RUN). Generalises m1/zones_bc.sh.
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"; O="$R/data/m1/PHerc0175B"
T8="$RUN"
for spec in "$@"; do
  read -r name z y x cy cx <<< "$spec"
  D="$O/zone_$name"; mkdir -p "$D"
  echo "== $(date -u +%FT%TZ) zone $name seeds"
  read -r SX SY SZ < <($T8 "$PY" m1/seed.py --z "$z" --y "$y" --x "$x" --centre-yx "$cy" "$cx" --out "$D") || continue
  mapfile -t NB < <($T8 "$PY" m1/seeds_radial.py --seed "$SX" "$SY" "$SZ" --centre-yx "$cy" "$cx" \
                     --inward 1 --outward 1 --out "$D")
  echo "zone $name: seed $SX $SY $SZ; neighbours ${NB[*]}"
  bash m1/grow_more.sh "$SX $SY $SZ" "${NB[@]}"
done
echo "== $(date -u +%FT%TZ) zones DONE"
