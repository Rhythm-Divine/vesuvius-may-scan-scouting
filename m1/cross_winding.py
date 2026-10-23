"""Does a readout feature repeat on the neighbouring windings? (looking only; not a verdict rule)

Ink on one winding has no reason to recur at the same place on the next one, which lies a whole turn away along the
scroll. A crack or fold running through several layers does recur. For a feature at crop pixel (y, x) of a reference
mesh, this finds the 3D point under it, the nearest vertex of each other mesh (distance in voxels), and that mesh's
forward and reverse ensembles in a 200 px (1.9 mm) square there. It saves 800 px squares (ref fwd | each other fwd | rev).

Usage: python m1/cross_winding.py SAMPLE OUTDIR REF_MESH Y X OTHER_MESH [OTHER_MESH ...]
"""
import os
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import CELL_PX, T  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL, HALF, Q = SRC_UM / DST_UM * CELL_PX, 400, 100


def mesh_xyz(root, m):
    return np.stack([tifffile.imread(root / "meshes" / m / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def ens(root, m, d):
    h = root / "hecate" / m
    return np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                    for k in (-2, -1, 0, 1, 2)], axis=0)


def crop_origin(root, m):
    y0, _, x0, _ = json.loads((root / "hecate" / m / "crop.json").read_text())["crop"]
    return y0, x0


def window(a, y, x, half):
    out = np.zeros((2 * half, 2 * half), a.dtype)
    ys, xs = slice(max(0, y - half), y + half), slice(max(0, x - half), x + half)
    blk = a[ys, xs]
    out[ys.start - (y - half):ys.start - (y - half) + blk.shape[0], xs.start - (x - half):xs.start - (x - half) + blk.shape[1]] = blk
    return out


def main():
    root, out, ref = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    y, x = int(sys.argv[4]), int(sys.argv[5])
    out.mkdir(parents=True, exist_ok=True)
    y0, x0 = crop_origin(root, ref)
    g = mesh_xyz(root, ref)
    r, c = int((y + y0) / PER_CELL), int((x + x0) / PER_CELL)
    p = g[r, c]
    print(f"ref {ref} crop ({y}, {x}) -> cell ({r}, {c}) -> xyz {p.round(1).tolist()}")
    panels = [np.clip(window(ens(root, ref, "fwd"), y, x, HALF) * 230, 0, 230).astype(np.uint8)]
    for m in sys.argv[6:]:
        h = mesh_xyz(root, m)
        ok = h[..., 0] != -1
        idx = np.argwhere(ok)
        dist, j = cKDTree(h[ok]).query(p)
        rr, cc = idx[j]
        oy0, ox0 = crop_origin(root, m)
        yy, xx = int(rr * PER_CELL + PER_CELL / 2) - oy0, int(cc * PER_CELL + PER_CELL / 2) - ox0
        row = f"  {m}: nearest vertex {dist:.1f} vox away at cell ({rr}, {cc}) -> crop ({yy}, {xx})"
        for d in ("fwd", "rev"):
            e = ens(root, m, d)
            q = window(e, yy, xx, Q)
            row += f"; {d} mean {q.mean():.3f} area >= T {(q >= T).mean():.1%}"
            panels.append(np.clip(window(e, yy, xx, HALF) * 230, 0, 230).astype(np.uint8))
        print(row)
    w = sum(pn.shape[1] for pn in panels) + 12 * (len(panels) - 1)
    img = np.full((2 * HALF, w), 255, np.uint8)
    xo = 0
    for pn in panels:
        img[:, xo:xo + pn.shape[1]] = pn
        xo += pn.shape[1] + 12
    (out / f"xwind_{ref[-9:]}_{y}_{x}.png").write_bytes(imagecodecs.png_encode(img[::2, ::2].copy()))


if __name__ == "__main__":
    main()
