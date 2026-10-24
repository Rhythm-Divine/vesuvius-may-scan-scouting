"""Seed points for the S1 row-candidate check (prereg/M1-survey-S1.md, deviation of 2026-10-24 04:10 UTC).

For a row on a read mesh, given as crop pixels (Y X pairs) along it:
- mid: the 3D point under the row point nearest the row's median (level-0 voxels);
- s2:  a second seed on the same sheet, the mesh vertex nearest in (x, y) to mid among the vertices within 10 slices of
       mid's height + DZ (default 400 slices, 3.5 mm; tried at -DZ if the mesh does not reach +DZ).
Prints "mid X Y Z" and "s2 X Y Z".
Usage: python m1/rowcheck_seeds.py SAMPLE MESH [--dz 400] Y X [Y X ...]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import tifffile

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL = SRC_UM / DST_UM * CELL_PX


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("mesh")
    ap.add_argument("--dz", type=int, default=400)
    ap.add_argument("yx", type=int, nargs="+")
    a = ap.parse_args()
    root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / a.sample
    y0, _, x0, _ = json.loads((root / "hecate" / a.mesh / "crop.json").read_text())["crop"]
    g = np.stack([tifffile.imread(root / "meshes" / a.mesh / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)
    pts = np.array(a.yx).reshape(-1, 2)
    med = np.median(pts, axis=0)
    py, px = pts[np.argmin(((pts - med) ** 2).sum(1))]
    mid = g[int((py + y0) / PER_CELL), int((px + x0) / PER_CELL)]
    if mid[0] == -1:
        sys.exit("row middle falls on an invalid mesh cell")
    v = g[g[..., 0] != -1]
    for dz in (a.dz, -a.dz):
        near = v[np.abs(v[:, 2] - (mid[2] + dz)) <= 10]
        if len(near):
            s2 = near[np.argmin(np.hypot(near[:, 0] - mid[0], near[:, 1] - mid[1]))]
            break
    else:
        sys.exit("mesh does not reach +-dz from the row")
    print("mid", *np.rint(mid).astype(int))
    print("s2", *np.rint(s2).astype(int))


if __name__ == "__main__":
    main()
