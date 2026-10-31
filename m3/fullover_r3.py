"""S3 looking aid: a whole reader-v2 map of one surface, downsampled, beside its overlay with Hecate at the same depth
(red reader-v2 >= T2, green Hecate >= T, yellow both), to judge whether a row stands out from the rest of the map (no
number here feeds a verdict). Dotted lines of constant scroll height every 1 mm.
Usage: python m3/fullover_r3.py SAMPLE MESH DIR FAM STEP OUT.jpg
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


def load(p):
    return imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255


def main():
    s, m, dr, fam, step, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), Path(sys.argv[6])
    d = ROOT / f"data/m3/{s}/{m}"
    y0, _, x0, _ = json.loads((d / "crop.json").read_text())["crop"]
    f = d / (f"pred_r3_{dr}.png" if fam == "near" else f"pred_r3_{dr}_{fam}.png")
    if not f.exists() and fam == "near":
        f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
    a = load(f)
    hh = None
    for h in (d / "hecate", ROOT / f"data/m1/{s}/hecate/{m}"):
        fs = [h / f"pred_{dr}_{k}.png" for k in K[fam]]
        if all(p.exists() for p in fs):
            hh = np.mean([load(p) for p in fs], axis=0)
            break
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y0 + a.shape[0]:step, x0:x0 + a.shape[1]:step]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm)) < 0.012 * step)
    ad = a[::step, ::step]
    g = np.clip(ad * 230, 0, 255)
    g[lines] = 120
    over = np.zeros(ad.shape + (3,), np.float32) + 40
    over[..., 0] = np.where(ad >= T2, 255, 40)
    if hh is not None:
        over[..., 1] = np.where(hh[::step, ::step] >= T, 255, 40)
    over[lines] = 120
    h, w = ad.shape
    canvas = np.full((h, 2 * w + 6, 3), 255, np.uint8)
    canvas[:, :w] = np.repeat(g[..., None], 3, -1).astype(np.uint8)
    canvas[:, w + 6:] = over.astype(np.uint8)
    out.write_bytes(imagecodecs.jpeg8_encode(canvas, level=88))
    print(f"{s} {m} {dr} {fam}: whole map / {step}; Hecate {'yes' if hh is not None else 'none'}")


if __name__ == "__main__":
    main()
