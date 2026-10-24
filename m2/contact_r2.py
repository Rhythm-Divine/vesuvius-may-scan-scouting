"""S2 review contact sheets (looking only): for each surface, reader-v2's forward and reverse maps at quarter resolution
(the scale of the S1 review sheets), side by side, with dotted lines of constant scroll height every 2 mm and the
readout-area outline in mid grey. Surfaces are stacked PER_SHEET to a JPEG (quality 78); the legend (sheet, row,
sample, mesh) is printed. Surfaces come from data/s2/s2_triage.tsv rows with review = yes, in triage order.
Usage: python m2/contact_r2.py OUT_DIR [PER_SHEET]
"""
import csv
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
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

ROOT = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
PER_CELL = SRC_UM / DST_UM * CELL_PX


def panels(s, m):
    r = ROOT / f"data/s2/{s}/{m}"
    y0, y1, x0, x1 = json.loads((ROOT / f"data/m1/{s}/hecate/{m}/crop.json").read_text())["crop"]
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y1:4, x0:x1:4]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm / 2) * 2) < 0.03)
    out = []
    for d in ("fwd", "rev"):
        p = imagecodecs.png_decode((r / f"ens_r2_{d}.png").read_bytes()).astype(np.float32)[::2, ::2]
        h, w = min(p.shape[0], lines.shape[0]), min(p.shape[1], lines.shape[1])
        p = p[:h, :w]
        dots = lines[:h, :w] & ((np.arange(w) // 2) % 2 == 0)[None, :]
        p[dots] = 90
        out.append(p)
    return out


def main():
    od = Path(sys.argv[1]); od.mkdir(parents=True, exist_ok=True)
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    rows = [r for r in csv.DictReader((ROOT / "data/s2/s2_triage.tsv").open(), delimiter="\t") if r["review"] == "yes"]
    for i in range(0, len(rows), per):
        group = rows[i:i + per]
        tiles = [panels(r["sample"], r["mesh"]) for r in group]
        H = sum(max(a.shape[0], b.shape[0]) for a, b in tiles) + 10 * (len(tiles) - 1)
        W = max(a.shape[1] + b.shape[1] for a, b in tiles) + 10
        canvas = np.full((H, W), 255, np.uint8)
        y = 0
        for (a, b), r in zip(tiles, group):
            canvas[y:y + a.shape[0], :a.shape[1]] = np.clip(a, 0, 255)
            canvas[y:y + b.shape[0], a.shape[1] + 10:a.shape[1] + 10 + b.shape[1]] = np.clip(b, 0, 255)
            print(f"sheet {i // per:02d} row {group.index(r)}: {r['sample']} {r['mesh']} "
                  f"fwd {float(r['fwd_geT2']):.3f} rev {float(r['rev_geT2']):.3f} agree {r['fwd_agree']}/{r['rev_agree']}")
            y += max(a.shape[0], b.shape[0]) + 10
        (od / f"s2_sheet_{i // per:02d}.jpg").write_bytes(imagecodecs.jpeg8_encode(canvas, level=78))


if __name__ == "__main__":
    main()
