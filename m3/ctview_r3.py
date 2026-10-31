"""S3 looking aid: the CT itself around a point of one surface (no number here feeds a verdict). Panels: layers of the
surface's 9.604 um render (43 layers, the mesh at layer 21; reader-v2's p6 window sits at about +5, m6 at about -5),
each contrast-stretched on the region, with dotted lines of constant scroll height every 1 mm. Structure that shows in
the CT (cracks, voids, fibre crossings) is visible here; carbon ink usually is not.
Usage: python m3/ctview_r3.py SAMPLE MESH Y X HALF OUT.jpg [LAYER ...]   (Y, X in the crop frame of crop.json)
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
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL = SRC_UM / DST_UM * CELL_PX


def main():
    s, m, y, x, half, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    layers = [int(v) for v in sys.argv[7:]] or [13, 17, 21, 25, 29, 33]
    y0, _, x0, _ = json.loads((ROOT / f"data/m3/{s}/{m}/crop.json").read_text())["crop"]
    r = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    ya, yb = max(0, y0 + y - half), min(r.shape[1], y0 + y + half)
    xa, xb = max(0, x0 + x - half), min(r.shape[2], x0 + x + half)
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[ya:yb, xa:xb]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm)) < 0.012) & ((np.arange(xb - xa) // 3) % 2 == 0)[None, :]
    tiles = []
    for k in layers:
        a = np.asarray(r[k, ya:yb, xa:xb]).astype(np.float32)
        lo, hi = np.percentile(a[a > 0], [1, 99.5]) if (a > 0).any() else (0, 1)
        img = np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) * 255
        img[lines] = 255 - img[lines] * 0.5
        tiles.append(img)
    h, w = tiles[0].shape
    ncol = 3
    nrow = (len(tiles) + ncol - 1) // ncol
    canvas = np.full((nrow * h + (nrow - 1) * 6, ncol * w + (ncol - 1) * 6), 255, np.uint8)
    for i, t in enumerate(tiles):
        rr, cc = divmod(i, ncol)
        canvas[rr * (h + 6):rr * (h + 6) + h, cc * (w + 6):cc * (w + 6) + w] = t.astype(np.uint8)
    Path(out).write_bytes(imagecodecs.jpeg8_encode(canvas, level=88))
    print(f"{s} {m} CT layers {layers} around crop ({y},{x}) half {half}; panels row-major, {ncol} per row")


if __name__ == "__main__":
    main()
