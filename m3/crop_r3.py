"""S3 looking aid: full-resolution crops of one surface's maps around a point, side by side (no number here feeds a
verdict). Panels: reader-v2's near, p6 and m6 maps for one direction (for an S1 surface the near map is S2's), the
same region thresholded at T2, and Hecate's maps where they exist (S1's -2..+2 mean, or a Hecate check's at the matching
depth). Dotted lines of constant scroll height every 1 mm mark the text direction.
Usage: python m3/crop_r3.py SAMPLE MESH DIR Y X [HALF] OUT.jpg     (Y, X in the 9.604 um crop frame; HALF default 300)
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
    s, m, dr, y, x = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    half = int(sys.argv[6]) if len(sys.argv) > 7 else 300
    out = Path(sys.argv[-1])
    d = ROOT / f"data/m3/{s}/{m}"
    y0, y1, x0, x1 = json.loads((d / "crop.json").read_text())["crop"]
    ya, yb, xa, xb = max(0, y - half), y + half, max(0, x - half), x + half
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0 + ya:y0 + yb, x0 + xa:x0 + xb]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm)) < 0.012) & ((np.arange(xx.shape[1]) // 3) % 2 == 0)[None, :]
    maps = {}
    for fam, f in (("near", d / f"pred_r3_{dr}.png"), ("p6", d / f"pred_r3_{dr}_p6.png"), ("m6", d / f"pred_r3_{dr}_m6.png")):
        if not f.exists() and fam == "near":
            f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
        maps[fam] = load(f)
    hec = {}
    for fam, ks in K.items():
        for h in (d / "hecate", ROOT / f"data/m1/{s}/hecate/{m}"):
            fs = [h / f"pred_{dr}_{k}.png" for k in ks]
            if all(p.exists() for p in fs):
                hec[fam] = np.mean([load(p) for p in fs], axis=0)
                break
    tiles = []
    for fam in ("near", "p6", "m6"):
        a = maps[fam][ya:yb, xa:xb]
        t = np.where(a >= T2, 1.0, 0.25)
        row = [a, t]
        if fam in hec:
            hh = hec[fam][ya:yb, xa:xb]
            row += [hh, np.where(hh >= T, 1.0, 0.25)]
        tiles.append(row)
    h, w = tiles[0][0].shape
    ncol = max(len(r) for r in tiles)
    canvas = np.full((3 * h + 2 * 6, ncol * w + (ncol - 1) * 6), 255, np.uint8)
    for i, row in enumerate(tiles):
        for j, a in enumerate(row):
            img = np.clip(a * 230, 0, 255)
            img[lines[:a.shape[0], :a.shape[1]]] = 120
            canvas[i * (h + 6):i * (h + 6) + a.shape[0], j * (w + 6):j * (w + 6) + a.shape[1]] = img.astype(np.uint8)
    out.write_bytes(imagecodecs.jpeg8_encode(canvas, level=85))
    print(f"{s} {m} {dr} centre ({y},{x}) half {half}: rows near/p6/m6; columns reader-v2, >=T2"
          + (", Hecate, >=T" if hec else "") + f"; Hecate families {sorted(hec)}")


if __name__ == "__main__":
    main()
