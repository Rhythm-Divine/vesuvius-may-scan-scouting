"""S2 crops (looking only): full-resolution 800 px squares (7.7 mm) around (y, x) in crop coordinates, CT centre layer |
reader-v2 forward | reader-v2 reverse | Hecate forward | Hecate reverse, with dotted lines of constant scroll height
every 1 mm and the readout-area outline in mid grey. Prints each map's share >= its threshold in the square. One JPEG
per point (quality 85).
Usage: python m2/crop_r2.py SAMPLE MESH OUT_DIR Y X [Y X ...]
"""
import json
import os
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX, T, interior_mask  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

ROOT = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
PER_CELL, HALF, T2 = SRC_UM / DST_UM * CELL_PX, 400, 0.6275


def win(a, y, x):
    out = np.zeros((2 * HALF, 2 * HALF), np.float32)
    y0, x0, y1, x1 = max(0, y - HALF), max(0, x - HALF), min(a.shape[0], y + HALF), min(a.shape[1], x + HALF)
    if y1 > y0 and x1 > x0:
        out[y0 - (y - HALF):y1 - (y - HALF), x0 - (x - HALF):x1 - (x - HALF)] = a[y0:y1, x0:x1]
    return out


def main():
    s, m, od = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    pts = list(map(int, sys.argv[4:]))
    od.mkdir(parents=True, exist_ok=True)
    h, r = ROOT / f"data/m1/{s}/hecate/{m}", ROOT / f"data/s2/{s}/{m}"
    y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
    r9 = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    ct = np.asarray(r9[21, y0:y1, x0:x1]).astype(np.float32)
    valid = ((np.asarray(r9[21]) > 0) & interior_mask(str(ROOT / f"data/m1/{s}/meshes/{m}"), r9.shape[1:],
                                                       str(ROOT / f"data/m1/{s}/render/{m}_selfcross.json"), 8))[y0:y1, x0:x1]
    edge = valid ^ ndimage.binary_erosion(valid, iterations=3)
    rd = {d: imagecodecs.png_decode((r / f"pred_r2_{d}.png").read_bytes()).astype(np.float32) / 255 for d in ("fwd", "rev")}
    hd = {d: np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                      for k in (-2, -1, 0, 1, 2)], 0) for d in ("fwd", "rev")}
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1, cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm)) < 0.006) & (((yy + xx) // 3) % 2 == 0)
    lo, hi = np.percentile(ct[valid], [1, 99]) if valid.any() else (0, 255)
    for y, x in zip(pts[::2], pts[1::2]):
        panels = [np.clip((win(ct, y, x) - lo) / max(hi - lo, 1) * 255, 0, 255)]
        msg = f"{s} {m[11:]} ({y},{x}):"
        for name, a, t in (("r2_fwd", rd["fwd"], T2), ("r2_rev", rd["rev"], T2), ("hec_fwd", hd["fwd"], T), ("hec_rev", hd["rev"], T)):
            w = win(a, y, x)
            v = win(valid.astype(np.float32), y, x) > 0
            msg += f" {name} >= T {100 * ((w >= t) & v).sum() / max(v.sum(), 1):.1f}%"
            p = np.clip(w * 230, 0, 230)
            p[win(lines.astype(np.float32), y, x) > 0] = 110
            p[win(edge.astype(np.float32), y, x) > 0] = 128
            panels.append(p)
        print(msg)
        canvas = np.full((2 * HALF, 5 * 2 * HALF + 4 * 10), 255, np.uint8)
        for i, p in enumerate(panels):
            canvas[:, i * (2 * HALF + 10):i * (2 * HALF + 10) + 2 * HALF] = p.astype(np.uint8)
        (od / f"crop_{s}_{m[11:]}_{y}_{x}.jpg").write_bytes(imagecodecs.jpeg8_encode(canvas, level=85))


if __name__ == "__main__":
    main()
