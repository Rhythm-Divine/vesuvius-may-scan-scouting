"""M1: pick a GrowPatch seed on the m7 recto prediction near a zone centre (level-0 voxels), from the open data.

Fetches a level-0 crop (64 x 384 x 384) of the prediction around (z, y, x) and returns the predicted voxel nearest
the centre that sits on a thin sheet: its run along the local radial direction (from the scroll centre given in
--centre-yx) is at most 4 voxels, so the seed is not on a fused blob. Prints "X Y Z" (the tool's order) and writes
seed.json.

Usage: python seed.py --z 7944 --y 2056 --x 5232 --centre-yx 4876 5232 --out DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2"))
from zoom import fetch_box  # noqa: E402

PRED = ("PHerc0175B/representations/predictions/surfaces/"
        "20250521125822-surface-20260413222639-surface-m7-L0-th0.2.zarr/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=int, required=True)
    ap.add_argument("--y", type=int, required=True)
    ap.add_argument("--x", type=int, required=True)
    ap.add_argument("--centre-yx", type=float, nargs=2, required=True, help="scroll centre at this height (level 0)")
    ap.add_argument("--prefix", default=PRED)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hz, hy = 32, 192
    crop = fetch_box(a.prefix, 0, a.z - hz, a.z + hz, a.y - hy, a.y + hy, a.x - hy, a.x + hy) > 0
    if not crop.any():
        raise SystemExit("no prediction in the crop")
    ry, rx = a.y - a.centre_yx[0], a.x - a.centre_yx[1]
    n = np.hypot(ry, rx)
    uy, ux = (ry / n, rx / n) if n > 0 else (1.0, 0.0)
    zz, yy, xx = np.nonzero(crop)
    order = np.argsort((zz - hz) ** 2 + (yy - hy) ** 2 + (xx - hy) ** 2)
    for i in order[:5000]:
        z, y, x = int(zz[i]), int(yy[i]), int(xx[i])
        run = 0
        for s in (1, -1):   # thickness along the radial direction
            t = 0
            while t < 12:
                py, px = int(round(y + s * (t + 1) * uy)), int(round(x + s * (t + 1) * ux))
                if not (0 <= py < crop.shape[1] and 0 <= px < crop.shape[2]) or not crop[z, py, px]:
                    break
                t += 1
            run += t
        if run + 1 <= 4:
            seed = {"x": a.x - hy + x, "y": a.y - hy + y, "z": a.z - hz + z, "radial_thickness_vox": run + 1,
                    "dist_from_centre_vox": round(float(np.sqrt((z - hz) ** 2 + (y - hy) ** 2 + (x - hy) ** 2)), 1),
                    "crop_pred_frac": round(float(crop.mean()), 4)}
            Path(a.out).mkdir(parents=True, exist_ok=True)
            (Path(a.out) / "seed.json").write_text(json.dumps(seed, indent=1))
            print(seed["x"], seed["y"], seed["z"])
            print(json.dumps(seed), file=sys.stderr)
            return
    raise SystemExit("no thin-sheet voxel near the centre")


if __name__ == "__main__":
    main()
