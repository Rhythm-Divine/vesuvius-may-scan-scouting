#!/usr/bin/env bash
# E2b: coarse scouting of the least-searched May 8.64 um First Letters volumes (one shallow public pass each), plus
# PHerc0490B again for comparison (from its local level-3 zarrs). Level 3 (69 um voxels), CT + m7 prediction from the
# open-data bucket; only overview.json and PNGs are kept (no local zarrs). CPU: Low priority ($RUN).
set -u
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"; . "$R/config.sh"
export TMPDIR="$R/cache/tmp" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
       NUMBA_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=""
T="$RUN"
run () {  # sample volume-id out-dir
  echo "== $(date -u +%FT%TZ) $1"
  $T "$PY" e2/overview.py --scout --sample "$1" --volume-id "$2" --level 3 --out "$3" > "$3.log" 2>&1
  echo "rc=$? for $1"; free -g | sed -n 2p; df -h "$HOME" | tail -1
}
mkdir -p "$R/data/e2/scout"
run PHerc0490B 20250521151215 "$R/data/e2/PHerc0490B_L3"
for sv in PHerc0490A:20250521151210 PHerc0483A:20250521140913 PHerc0175B:20250521125822 PHerc1218:20250521120456; do
  s="${sv%%:*}"; v="${sv##*:}"; mkdir -p "$R/data/e2/scout/${s}_L3"
  run "$s" "$v" "$R/data/e2/scout/${s}_L3"
done
"$PY" - <<'PY'
import json, os
from pathlib import Path
R = Path(os.environ["VES_ROOT"]) / "data/e2"
rows = [R / "PHerc0490B_L3/overview.json"] + sorted((R / "scout").glob("*_L3/overview.json"))
keys = ["phantom_fraction", "rough_recto_area_cm2_inside_ct", "crossing_spacing_um_median",
        "crossing_spacing_cv_median", "thick_run_fraction"]
summary = {}
for p in rows:
    if not p.exists():
        continue
    r = json.loads(p.read_text())
    summary[r["sample"]] = {k: r.get(k) for k in keys} | {"crossings_by_height": {h: v["crossings_median"]
                            for h, v in r.get("inside_ct_by_height", {}).items()}}
    print(r["sample"], json.dumps(summary[r["sample"]]))
(R / "scout/scout_summary.json").write_text(json.dumps(summary, indent=1))
PY
echo "== $(date -u +%FT%TZ) E2b DONE"
