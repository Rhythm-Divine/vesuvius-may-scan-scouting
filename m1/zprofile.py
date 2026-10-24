"""Row test for a readout (looking aid, not a rule). Text lines run along constant scroll height z, so text gives a
response that rises and falls with z at the line pitch (a few mm). For one mesh: the share >= T of each ensemble per 0.1
mm bin of z over the readout area, its autocorrelation after removing a 6 mm running mean, and a "text-up" view (forward
| reverse, rotated so that constant z runs horizontally, z up, 2x downsampled).
Usage: python m1/zprofile.py SAMPLE MESH OUT.png"""
import json
import os
import sys
from pathlib import Path
import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX, T, interior_mask  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402
PER_CELL = SRC_UM / DST_UM * CELL_PX
s, m, out = sys.argv[1], sys.argv[2], sys.argv[3]
root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / s
h = root / "hecate" / m
ens = {d: np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                   for k in (-2, -1, 0, 1, 2)], 0) for d in ("fwd", "rev")}
y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
r9 = np.load(root / "render" / f"{m}_9p6.npy", mmap_mode="r")
valid = ((np.asarray(r9[21]) > 0) & interior_mask(str(root / "meshes" / m), r9.shape[1:],
                                                   str(root / "render" / f"{m}_selfcross.json"), 8))[y0:y1, x0:x1]
zg = tifffile.imread(root / "meshes" / m / "z.tif").astype(np.float64)
yy, xx = np.mgrid[y0:y1, x0:x1]
zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1, cval=np.nan)
valid &= np.isfinite(zc)
zmm = zc * 8.64e-3                                  # level-0 slices of 8.64 um -> mm
b = np.floor((zmm - np.nanmin(zmm[valid])) / 0.1).astype(int)
nb = b[valid].max() + 1
cnt = np.bincount(b[valid], minlength=nb)
print(f"{s} {m}: readout {valid.sum() * (9.604e-4) ** 2:.2f} cm2, z span {nb / 10:.1f} mm")
for d in ("fwd", "rev"):
    hit = np.bincount(b[valid], weights=(ens[d][valid] >= T).astype(float), minlength=nb)
    keep = cnt >= 2000                             # bins with at least ~0.2 mm2 of readout
    prof = np.where(keep, hit / np.maximum(cnt, 1), np.nan)
    p = prof[keep]
    trend = ndimage.uniform_filter1d(p, 61, mode="nearest")
    r = p - trend
    ac = [float(np.corrcoef(r[:-L], r[L:])[0, 1]) for L in range(1, min(81, len(r) // 2))]
    best = int(np.argmax(ac[19:])) + 20            # strongest lag between 2 and 8 mm
    print(f"  {d}: share >= T by 0.5 mm of z: " + " ".join(f"{100 * np.nanmean(prof[i:i + 5]):3.0f}" for i in range(0, nb, 5)))
    print(f"  {d}: autocorrelation peak in 2-8 mm at {best / 10:.1f} mm, r = {ac[best - 1]:.2f}; "
          f"r at 3/4/5/6 mm = {ac[29]:.2f} {ac[39]:.2f} {ac[49]:.2f} {ac[59]:.2f}" if len(ac) >= 60 else f"  {d}: z span too short")
gy, gx = np.gradient(np.where(valid, zc, np.nan))
ang = np.degrees(np.arctan2(np.nanmedian(gy), np.nanmedian(gx)))   # direction of increasing z in the image
panels = []
for d in ("fwd", "rev"):
    img = np.where(valid, ens[d], 0)[::2, ::2]
    rot = ndimage.rotate(img, ang + 90, reshape=True, order=1)       # z up
    panels.append(np.clip(rot * 230, 0, 230).astype(np.uint8))
hh = max(p.shape[0] for p in panels)
canvas = np.full((hh, sum(p.shape[1] for p in panels) + 12), 255, np.uint8)
xo = 0
for p in panels:
    canvas[:p.shape[0], xo:xo + p.shape[1]] = p
    xo += p.shape[1] + 12
Path(out).write_bytes(imagecodecs.png_encode(canvas))
print(f"  text-up view rotated {ang + 90:.0f} deg -> {out}")
