"""S2 review sheet (looking only): Hecate's forward and reverse ensembles from S1 next to reader-v2's forward and
reverse maps, all at half resolution on the same crop, with the readout-area outline in mid grey and dotted lines of
constant scroll height every 2 mm. Saved as one JPEG (quality 80), to keep it small for a slow link.
Usage: python m2/sheet_r2.py SAMPLE MESH OUT.jpg
"""
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL = SRC_UM / DST_UM * CELL_PX


def main():
    s, m, out = sys.argv[1:4]
    root = Path(__file__).resolve().parents[1]
    h, r = root / f"data/m1/{s}/hecate/{m}", root / f"data/s2/{s}/{m}"
    y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
    zg = tifffile.imread(root / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y1:2, x0:x1:2]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm / 2) * 2) < 0.02)
    panels = []
    for name in ("ens_fwd", "ens_rev"):
        panels.append(imagecodecs.png_decode((h / f"{name}.png").read_bytes()).astype(np.float32))
    for name in ("ens_r2_fwd", "ens_r2_rev"):
        panels.append(imagecodecs.png_decode((r / f"{name}.png").read_bytes()).astype(np.float32))
    hh, ww = panels[0].shape
    canvas = np.full((hh, 4 * ww + 3 * 12), 255, np.uint8)
    for i, p in enumerate(panels):
        p = p[:hh, :ww].copy()
        p[lines[:p.shape[0], :p.shape[1]] & ((np.arange(p.shape[1]) // 3) % 2 == 0)[None, :]] = 90
        canvas[:p.shape[0], i * (ww + 12):i * (ww + 12) + p.shape[1]] = np.clip(p, 0, 255).astype(np.uint8)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_bytes(imagecodecs.jpeg8_encode(canvas, level=80))
    print(out, canvas.shape)


if __name__ == "__main__":
    main()
