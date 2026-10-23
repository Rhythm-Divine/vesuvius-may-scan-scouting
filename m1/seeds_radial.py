"""M1: seeds for the neighbouring windings of a traced sheet, on the radial line through its seed (level-0 voxels).

Fetches the m7 prediction along the line from the seed toward (inward) and away from (outward) the scroll centre, at
the seed's height, and lists the prediction runs (sheet crossings) along it. Each run that is thin (<= 8 voxels
along the line after the +-1 voxel bridging, i.e. a single sheet's recto band) and is not the seed's own run gives one
seed at its middle. Takes up to --inward runs toward the
centre and --outward runs away from it. Writes seeds.json; prints one "X Y Z" line per seed.

Usage: python seeds_radial.py --seed X Y Z --centre-yx CY CX --inward 4 --outward 2 --out DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2"))
from seed import PRED  # noqa: E402
from zoom import fetch_box  # noqa: E402


def runs(prof):
    """(start, stop) of True runs in a 1D bool array."""
    d = np.diff(np.r_[0, prof.astype(np.int8), 0])
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, nargs=3, required=True, metavar=("X", "Y", "Z"))
    ap.add_argument("--centre-yx", type=float, nargs=2, required=True)
    ap.add_argument("--inward", type=int, default=4)
    ap.add_argument("--outward", type=int, default=2)
    ap.add_argument("--reach", type=int, default=600, help="voxels along the line in each direction")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default=PRED, help="m7 prediction zarr prefix in the open-data bucket (default PHerc0175B)")
    a = ap.parse_args()
    sx, sy, sz = a.seed
    vy, vx = a.centre_yx[0] - sy, a.centre_yx[1] - sx
    n = float(np.hypot(vy, vx))
    uy, ux = vy / n, vx / n                       # unit vector toward the centre
    t = np.arange(-a.reach, a.reach + 1)
    py, px = np.rint(sy + t * uy).astype(int), np.rint(sx + t * ux).astype(int)
    y0, y1, x0, x1 = py.min() - 3, py.max() + 4, px.min() - 3, px.max() + 4
    crop = fetch_box(a.prefix, 0, sz - 1, sz + 2, y0, y1, x0, x1) > 0
    # profile along the line: a voxel counts if the prediction is set within +-1 voxel of it (bridges 1-px gaps)
    prof = np.zeros(len(t), bool)
    for dz in range(crop.shape[0]):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = py - y0 + dy, px - x0 + dx
                ok = (yy >= 0) & (yy < crop.shape[1]) & (xx >= 0) & (xx < crop.shape[2])
                prof[ok] |= crop[dz, yy[ok], xx[ok]]
    rs = runs(prof)
    centre_idx = a.reach                          # the seed's own position on the line
    own = next((r for r in rs if r[0] <= centre_idx < r[1]), None)
    seeds = []
    for direction, limit in (("inward", a.inward), ("outward", a.outward)):
        cand = [r for r in rs if r is not own and ((r[0] > centre_idx) if direction == "inward" else (r[1] <= centre_idx))]
        cand = sorted(cand, key=lambda r: abs((r[0] + r[1]) / 2 - centre_idx))
        k = 0
        for r in cand:
            if k >= limit:
                break
            if r[1] - r[0] > 8:                   # thick run: fused sheets or an oblique crossing; skip
                continue
            m = (r[0] + r[1] - 1) // 2
            seeds.append({"direction": direction, "rank": k + 1, "x": int(px[m]), "y": int(py[m]), "z": int(sz),
                          "along_line_vox": int(m - centre_idx), "run_thickness_vox": int(r[1] - r[0])})
            k += 1
    rep = {"seed": a.seed, "unit_to_centre_yx": [round(uy, 4), round(ux, 4)], "runs_on_line": len(rs),
           "own_run": [int(own[0] - centre_idx), int(own[1] - centre_idx)] if own else None,
           "spacing_vox_median": float(np.median(np.diff([(r[0] + r[1]) / 2 for r in rs]))) if len(rs) > 2 else None,
           "seeds": seeds}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "seeds.json").write_text(json.dumps(rep, indent=1))
    for s in seeds:
        print(s["x"], s["y"], s["z"])
    print(json.dumps({k: v for k, v in rep.items() if k != "seeds"}), file=sys.stderr)


if __name__ == "__main__":
    main()
