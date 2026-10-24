"""Row test for a reader-v2 readout (looking aid, not a rule), as m1/zprofile.py does for Hecate. Text lines run along
constant scroll height z, so text gives a share >= T2 that rises and falls with z at the line pitch, with quieter gaps
between lines. Prints the share >= T2 per 0.5 mm of z over the readout area, the autocorrelation of that profile (0.1 mm
bins, after removing a 6 mm running mean) at 2-8 mm, and the contrast between the best 1 mm band and the median band.
Optionally saves a "text-up" view (forward | reverse, constant z horizontal, z up, half resolution) as JPEG.
Usage: python m2/zprofile_r2.py SAMPLE MESH [OUT.jpg]
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
from readout import CELL_PX, interior_mask  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

ROOT = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
PER_CELL, T2 = SRC_UM / DST_UM * CELL_PX, 0.6275


def main():
    s, m = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    h, r = ROOT / f"data/m1/{s}/hecate/{m}", ROOT / f"data/s2/{s}/{m}"
    y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
    r9 = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    valid = ((np.asarray(r9[21]) > 0) & interior_mask(str(ROOT / f"data/m1/{s}/meshes/{m}"), r9.shape[1:],
                                                       str(ROOT / f"data/m1/{s}/render/{m}_selfcross.json"), 8))[y0:y1, x0:x1]
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1, cval=np.nan)
    valid &= np.isfinite(zc)
    zmm = zc * 8.64e-3
    b = np.floor((zmm - np.nanmin(zmm[valid])) / 0.1).astype(int)
    nb = b[valid].max() + 1
    cnt = np.bincount(b[valid], minlength=nb)
    print(f"{s} {m[11:]}: readout {valid.sum() * (9.604e-4) ** 2:.2f} cm2, z span {nb / 10:.1f} mm")
    ens = {d: imagecodecs.png_decode((r / f"pred_r2_{d}.png").read_bytes()).astype(np.float32) / 255 for d in ("fwd", "rev")}
    for d in ("fwd", "rev"):
        hit = np.bincount(b[valid], weights=(ens[d][valid] >= T2).astype(float), minlength=nb)
        keep = cnt >= 2000
        prof = np.where(keep, hit / np.maximum(cnt, 1), np.nan)
        p = prof[keep]
        if len(p) < 120:
            print(f"  {d}: z span too short"); continue
        resid = p - ndimage.uniform_filter1d(p, 61, mode="nearest")
        ac = [float(np.corrcoef(resid[:-L], resid[L:])[0, 1]) for L in range(1, min(81, len(resid) // 2))]
        best = int(np.argmax(ac[19:])) + 20
        band = ndimage.uniform_filter1d(p, 10, mode="nearest")
        print(f"  {d}: share >= T2 by 0.5 mm of z: " + " ".join(f"{100 * np.nanmean(prof[i:i + 5]):3.0f}" for i in range(0, nb, 5)))
        print(f"  {d}: autocorrelation peak in 2-8 mm at {best / 10:.1f} mm, r = {ac[best - 1]:.2f}; "
              f"best 1 mm band {100 * band.max():.1f}% vs median band {100 * np.median(band):.1f}% "
              f"(ratio {band.max() / max(np.median(band), 1e-4):.1f})")
    if out:
        gy, gx = np.gradient(np.where(valid, zc, np.nan))
        ang = np.degrees(np.arctan2(np.nanmedian(gy), np.nanmedian(gx)))
        panels = [np.clip(ndimage.rotate(np.where(valid, ens[d], 0)[::2, ::2], ang + 90, reshape=True, order=1) * 230, 0, 230)
                  .astype(np.uint8) for d in ("fwd", "rev")]
        hh = max(p.shape[0] for p in panels)
        canvas = np.full((hh, sum(p.shape[1] for p in panels) + 12), 255, np.uint8)
        xo = 0
        for p in panels:
            canvas[:p.shape[0], xo:xo + p.shape[1]] = p
            xo += p.shape[1] + 12
        Path(out).write_bytes(imagecodecs.jpeg8_encode(canvas, level=80))
        print(f"  text-up view rotated {ang + 90:.0f} deg -> {out}")


if __name__ == "__main__":
    main()
