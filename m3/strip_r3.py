"""S3 looking aid: one map of one surface over a box, as four panels (no number here feeds a verdict): reader-v2's map,
an overlay of reader-v2 >= T2 (red) and Hecate >= T at the same depth (green; yellow where both agree), Hecate's map,
and the CT at the window's middle layer of the 9.604 um render (near 21, p6 26, m6 16). Dotted lines of constant
scroll height every 1 mm. A box wider than tall is stacked top to bottom, otherwise left to right.
Usage: python m3/strip_r3.py SAMPLE MESH DIR FAM Y0 Y1 X0 X1 OUT.jpg     (Y, X in the 9.604 um crop frame)
"""
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "m1"))
sys.path.insert(0, str(ROOT / "e1"))
from readout import CELL_PX, T  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

T2 = 0.6275
PER_CELL = SRC_UM / DST_UM * CELL_PX
K = {"near": (-2, -1, 0, 1, 2), "p6": (3, 4, 5, 6, 7), "m6": (-7, -6, -5, -4, -3)}
CT_LAYER = {"near": 21, "p6": 26, "m6": 16}


def load(p):
    return imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255


def main():
    s, m, dr, fam = sys.argv[1:5]
    ya, yb, xa, xb = (int(v) for v in sys.argv[5:9])
    out = Path(sys.argv[9])
    d = ROOT / f"data/m3/{s}/{m}"
    y0, _, x0, _ = json.loads((d / "crop.json").read_text())["crop"]
    f = d / (f"pred_r3_{dr}.png" if fam == "near" else f"pred_r3_{dr}_{fam}.png")
    if not f.exists() and fam == "near":
        f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
    a = load(f)[ya:yb, xa:xb]
    hh = None
    for h in (d / "hecate", ROOT / f"data/m1/{s}/hecate/{m}"):
        fs = [h / f"pred_{dr}_{k}.png" for k in K[fam]]
        if all(p.exists() for p in fs):
            hh = np.mean([load(p) for p in fs], axis=0)[ya:yb, xa:xb]
            break
    r = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    ct = np.asarray(r[CT_LAYER[fam], y0 + ya:y0 + yb, x0 + xa:x0 + xb]).astype(np.float32)
    lo, hi = np.percentile(ct[ct > 0], [1, 99.5]) if (ct > 0).any() else (0, 1)
    ct = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1)
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0 + ya:y0 + yb, x0 + xa:x0 + xb]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm)) < 0.012) & ((np.arange(xb - xa) // 3) % 2 == 0)[None, :]

    def gray(v):
        g = np.clip(v * 230, 0, 255)
        g[lines] = 120
        return np.repeat(g[..., None], 3, -1)

    over = np.zeros(a.shape + (3,), np.float32)
    over[..., 0] = np.where(a >= T2, 255, 40)
    over[..., 1] = np.where(hh >= T, 255, 40) if hh is not None else 40
    over[..., 2] = 40
    over[lines] = 120
    panels = [gray(a), over, gray(hh) if hh is not None else np.full_like(over, 255), gray(ct)]
    h, w = a.shape
    if w > h:
        canvas = np.full((4 * h + 3 * 6, w, 3), 255, np.uint8)
        for i, p in enumerate(panels):
            canvas[i * (h + 6):i * (h + 6) + h] = p.astype(np.uint8)
    else:
        canvas = np.full((h, 4 * w + 3 * 6, 3), 255, np.uint8)
        for i, p in enumerate(panels):
            canvas[:, i * (w + 6):i * (w + 6) + w] = p.astype(np.uint8)
    out.write_bytes(imagecodecs.jpeg8_encode(canvas, level=88))
    print(f"{s} {m} {dr} {fam} box y {ya}:{yb} x {xa}:{xb}: panels reader-v2, overlay (red reader-v2 >= T2, green "
          f"Hecate >= T, yellow both), Hecate{'' if hh is not None else ' (none)'}, CT layer {CT_LAYER[fam]}")


if __name__ == "__main__":
    main()
