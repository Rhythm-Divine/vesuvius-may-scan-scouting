"""S3 looking aid: does a reader-v2 feature recur at the same 3D place on the neighbouring windings? (no number here
feeds a verdict; S1's row check, m1/cross_winding.py, on S3's maps)

Ink on one winding has no reason to recur on the next, which lies a whole turn away along the scroll; a crack or fold
through several layers does recur. For a feature at crop pixel (Y, X) of the reference surface, this finds the 3D point
under it and, on each other surface, the nearest grid vertex (distance in voxels) and the matching crop pixel. It prints
each surface's share of reader-v2 >= T2 in a 1 mm square there, and saves the maps side by side (reference first),
each a 2 x HALF square around the matching point (grids may be flipped or rotated relative to each other).
Usage: python m3/xwind_r3.py SAMPLE FAM DIR REF_MESH Y X HALF OUT.jpg OTHER_MESH [OTHER_MESH ...]
"""
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "m1"))
sys.path.insert(0, str(ROOT / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

T2 = 0.6275
PER_CELL = SRC_UM / DST_UM * CELL_PX
Q = 52  # half of a 1 mm square at 9.604 um


def grid(s, m):
    d = ROOT / "data/m1" / s / "meshes" / m
    return np.stack([tifffile.imread(d / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def origin(s, m):
    y0, _, x0, _ = json.loads((ROOT / f"data/m3/{s}/{m}/crop.json").read_text())["crop"]
    return y0, x0


def rmap(s, m, fam, dr):
    d = ROOT / f"data/m3/{s}/{m}"
    f = d / (f"pred_r3_{dr}.png" if fam == "near" else f"pred_r3_{dr}_{fam}.png")
    if not f.exists() and fam == "near":
        f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
    return imagecodecs.png_decode(f.read_bytes()).astype(np.float32) / 255


def window(a, y, x, half):
    out = np.zeros((2 * half, 2 * half), np.float32)
    ya, xa = max(0, y - half), max(0, x - half)
    blk = a[ya:max(0, y + half), xa:max(0, x + half)]
    out[ya - (y - half):ya - (y - half) + blk.shape[0], xa - (x - half):xa - (x - half) + blk.shape[1]] = blk
    return out


def main():
    s, fam, dr, ref = sys.argv[1:5]
    y, x, half, out = int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), Path(sys.argv[8])
    y0, x0 = origin(s, ref)
    g = grid(s, ref)
    r, c = int(round((y0 + y) / PER_CELL - 0.5)), int(round((x0 + x) / PER_CELL - 0.5))
    p = g[r, c]
    a = rmap(s, ref, fam, dr)
    q = window(a, y, x, Q)
    print(f"ref {ref} {fam} {dr} crop ({y}, {x}) -> cell ({r}, {c}) -> xyz {p.round(1).tolist()}; "
          f">= T2 in 1 mm square {(q >= T2).mean():.1%}")
    panels = [window(a, y, x, half)]
    for m in sys.argv[9:]:
        h = grid(s, m)
        ok = h[..., 0] != -1
        idx = np.argwhere(ok)
        dist, j = cKDTree(h[ok]).query(p)
        rr, cc = idx[j]
        oy0, ox0 = origin(s, m)
        yy, xx = int((rr + 0.5) * PER_CELL) - oy0, int((cc + 0.5) * PER_CELL) - ox0
        b = rmap(s, m, fam, dr)
        inside = 0 <= yy < b.shape[0] and 0 <= xx < b.shape[1]
        qb = window(b, yy, xx, Q)
        print(f"  {m}: nearest vertex {dist:.1f} vox at cell ({rr}, {cc}) -> crop ({yy}, {xx})"
              f"{'' if inside else ' (outside its map)'}; >= T2 in 1 mm square {(qb >= T2).mean():.1%}")
        panels.append(window(b, yy, xx, half))
    w = len(panels) * 2 * half + 8 * (len(panels) - 1)
    img = np.full((2 * half, w), 255, np.uint8)
    for i, pn in enumerate(panels):
        img[:, i * (2 * half + 8):i * (2 * half + 8) + 2 * half] = np.clip(pn * 230, 0, 230).astype(np.uint8)
    out.write_bytes(imagecodecs.jpeg8_encode(img, level=88))


if __name__ == "__main__":
    main()
