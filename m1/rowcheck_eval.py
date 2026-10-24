"""Row-candidate check, the comparison (prereg/M1-survey-S1.md, deviation of 2026-10-24 04:10 UTC). Looking aid.

Maps each row point (crop pixels on the reference mesh) to 3D, then to the nearest vertex of another mesh. For each
point it prints the 3D distance (voxels) and that mesh's forward and reverse share >= T within 0.3 mm (31 px) of the
mapped point, next to the mesh's own background share. It saves the reference ensemble (the direction given) around the
row, then the other mesh's forward and reverse ensembles around the mapped row, 1000 px (9.6 mm) squares. Mapped row
points are marked with small grey crosses.
Usage: python m1/rowcheck_eval.py SAMPLE REF_MESH REF_DIR OTHER_MESH OUT.png Y X [Y X ...]
"""
import json
import os
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX, T  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL, HALF, R = SRC_UM / DST_UM * CELL_PX, 500, 31


def xyz(root, m):
    return np.stack([tifffile.imread(root / "meshes" / m / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def ens(root, m, d):
    h = root / "hecate" / m
    return np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                    for k in (-2, -1, 0, 1, 2)], axis=0)


def origin(root, m):
    y0, _, x0, _ = json.loads((root / "hecate" / m / "crop.json").read_text())["crop"]
    return y0, x0


def window(a, y, x, half):
    out = np.zeros((2 * half, 2 * half), np.float32)
    ys0, xs0 = max(0, y - half), max(0, x - half)
    ys1, xs1 = min(a.shape[0], y + half), min(a.shape[1], x + half)
    if ys1 > ys0 and xs1 > xs0:
        out[ys0 - (y - half):ys1 - (y - half), xs0 - (x - half):xs1 - (x - half)] = a[ys0:ys1, xs0:xs1]
    return out


def main():
    s, ref, rdir, other, out = sys.argv[1:6]
    pts = np.array(list(map(int, sys.argv[6:]))).reshape(-1, 2)
    root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / s
    ry0, rx0 = origin(root, ref)
    oy0, ox0 = origin(root, other)
    g, h = xyz(root, ref), xyz(root, other)
    ok = h[..., 0] != -1
    idx = np.argwhere(ok)
    tree = cKDTree(h[ok])
    e = {d: ens(root, other, d) for d in ("fwd", "rev")}
    bg = {d: float((e[d][e[d] > 0] >= T).mean()) for d in e}
    print(f"{other}: background share >= T fwd {bg['fwd']:.1%} rev {bg['rev']:.1%}")
    mapped = []
    for y, x in pts:
        p = g[int((y + ry0) / PER_CELL), int((x + rx0) / PER_CELL)]
        dist, j = tree.query(p)
        rr, cc = idx[j]
        yy, xx = int(rr * PER_CELL + PER_CELL / 2) - oy0, int(cc * PER_CELL + PER_CELL / 2) - ox0
        mapped.append((yy, xx))
        row = f"  row ({y}, {x}) -> 3D {p.round(0).astype(int).tolist()} -> {dist:5.1f} vox -> crop ({yy}, {xx})"
        for d in ("fwd", "rev"):
            q = window(e[d], yy, xx, R)
            row += f"; {d} >= T {(q >= T).mean():5.1%} max {q.max():.2f}"
        print(row)
    my, mx = np.median(np.array(mapped), axis=0).astype(int)
    cy, cx = np.median(pts, axis=0).astype(int)
    panels = [window(ens(root, ref, rdir), cy, cx, HALF)] + [window(e[d], my, mx, HALF) for d in ("fwd", "rev")]
    imgs = []
    for k, pn in enumerate(panels):
        im = np.clip(pn * 230, 0, 230).astype(np.uint8)
        marks = [(y - cy, x - cx) for y, x in pts] if k == 0 else [(y - my, x - mx) for y, x in mapped]
        for dy, dx in marks:
            py, px = dy + HALF, dx + HALF
            for t in range(-12, 13):
                for a, b in ((py + t, px), (py, px + t)):
                    if 0 <= a < im.shape[0] and 0 <= b < im.shape[1] and abs(t) > 5:
                        im[a, b] = 128
        imgs.append(im)
    canvas = np.full((2 * HALF, 3 * 2 * HALF + 24), 255, np.uint8)
    for k, im in enumerate(imgs):
        canvas[:, k * (2 * HALF + 12):k * (2 * HALF + 12) + 2 * HALF] = im
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_bytes(imagecodecs.png_encode(np.ascontiguousarray(canvas[::2, ::2])))
    print(f"  saved {out} (ref {rdir} | other fwd | other rev)")


if __name__ == "__main__":
    main()
