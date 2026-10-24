"""Does a response stay put across Hecate's depth windows? (looking aid, not a rule)
Ink sits on the traced surface, so it should appear at the same place in every window. A layer boundary or crack
inclined to the surface crosses the window slab at a place that moves as the window moves in depth. For a square of
HALF*2 px around (y, x): cross-correlate the window maps k=-2, -1, +1, +2 against k=0 (mean-removed, Hann-tapered)
and report the in-plane shift (px and mm) at the correlation peak, with the peak's correlation.
Usage: python m1/depth_shift.py SAMPLE MESH DIR Y X [Y X ...]   (crop coordinates)"""
import os
import sys
from pathlib import Path
import imagecodecs
import numpy as np
HALF = 300
s, m, d = sys.argv[1:4]
h = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / f"data/m1/{s}/hecate/{m}"
mp = {k: imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255 for k in (-2, -1, 0, 1, 2)}
win = np.outer(np.hanning(2 * HALF), np.hanning(2 * HALF))
pts = list(map(int, sys.argv[4:]))
for y, x in zip(pts[::2], pts[1::2]):
    sl = (slice(y - HALF, y + HALF), slice(x - HALF, x + HALF))
    ref = mp[0][sl]
    if ref.shape != (2 * HALF, 2 * HALF):
        print(f"{s} ({y},{x}): too close to the edge"); continue
    a = (ref - ref.mean()) * win
    row = f"{s} {d} ({y},{x}):"
    for k in (-2, -1, 1, 2):
        b = (mp[k][sl] - mp[k][sl].mean()) * win
        cc = np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=a.shape)
        cc /= np.sqrt((a ** 2).sum() * (b ** 2).sum()) + 1e-9
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
        dy, dx = (iy + HALF) % (2 * HALF) - HALF, (ix + HALF) % (2 * HALF) - HALF
        row += f"  k{k:+d}: shift ({-dy:+4d},{-dx:+4d}) px = {np.hypot(dy, dx) * 9.604e-3:4.2f} mm, r {cc.max():.2f}"
    print(row)
