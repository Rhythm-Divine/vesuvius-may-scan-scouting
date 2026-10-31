"""S3 looking aid: CT layers of a surface's 9.604 um render over a box, with the outline of one reader-v2 map's >= T2
pixels drawn on each layer in red (no number here feeds a verdict). Shows whether >= T2 forms sit on cracks, voids or
fibre bundles visible in the CT; carbon ink itself is usually not visible.
Usage: python m3/ctmask_r3.py SAMPLE MESH DIR FAM Y0 Y1 X0 X1 OUT.jpg [LAYER ...]   (default layers by family:
near 19 21 23, p6 24 26 28, m6 14 16 18)
"""
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
T2 = 0.6275
LAYERS = {"near": [19, 21, 23], "p6": [24, 26, 28], "m6": [14, 16, 18]}


def main():
    s, m, dr, fam = sys.argv[1:5]
    ya, yb, xa, xb = (int(v) for v in sys.argv[5:9])
    out = Path(sys.argv[9])
    layers = [int(v) for v in sys.argv[10:]] or LAYERS[fam]
    d = ROOT / f"data/m3/{s}/{m}"
    y0, _, x0, _ = json.loads((d / "crop.json").read_text())["crop"]
    f = d / (f"pred_r3_{dr}.png" if fam == "near" else f"pred_r3_{dr}_{fam}.png")
    if not f.exists() and fam == "near":
        f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
    a = imagecodecs.png_decode(f.read_bytes()).astype(np.float32)[ya:yb, xa:xb] / 255
    mask = a >= T2
    edge = mask & ~ndimage.binary_erosion(mask, iterations=2)
    r = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    tiles = []
    for k in layers:
        ct = np.asarray(r[k, y0 + ya:y0 + yb, x0 + xa:x0 + xb]).astype(np.float32)
        lo, hi = np.percentile(ct[ct > 0], [1, 99.5]) if (ct > 0).any() else (0, 1)
        g = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1) * 255
        rgb = np.repeat(g[..., None], 3, -1)
        rgb[edge] = (255, 40, 40)
        tiles.append(rgb.astype(np.uint8))
    h, w = tiles[0].shape[:2]
    canvas = np.full((h, len(tiles) * w + 6 * (len(tiles) - 1), 3), 255, np.uint8)
    for i, t in enumerate(tiles):
        canvas[:, i * (w + 6):i * (w + 6) + w] = t
    out.write_bytes(imagecodecs.jpeg8_encode(canvas, level=88))
    print(f"{s} {m} {dr} {fam} box y {ya}:{yb} x {xa}:{xb}: CT layers {layers} with reader-v2 >= T2 outlines")


if __name__ == "__main__":
    main()
