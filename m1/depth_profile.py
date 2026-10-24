"""Per-window share >= T in an 800 px square, from the saved Hecate maps (numbers only; writes no image).
Usage: python m1/depth_profile.py SAMPLE MESH Y X [Y X ...]   (crop coordinates, as in m1/sheets.py)"""
import os
import sys
from pathlib import Path
import imagecodecs
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import T  # noqa: E402
s, m = sys.argv[1], sys.argv[2]
d = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / f"data/m1/{s}/hecate/{m}"
maps = {(dr, k): imagecodecs.png_decode((d / f"pred_{dr}_{k}.png").read_bytes()).astype(np.float32) / 255
        for dr in ("fwd", "rev") for k in (-2, -1, 0, 1, 2)}
pts = list(map(int, sys.argv[3:]))
for y, x in zip(pts[::2], pts[1::2]):
    sl = (slice(max(0, y - 400), y + 400), slice(max(0, x - 400), x + 400))
    for dr in ("fwd", "rev"):
        v = [float((maps[dr, k][sl] >= T).mean()) for k in (-2, -1, 0, 1, 2)]
        print(f"{s} ({y},{x}) {dr} k=-2..+2: " + " ".join(f"{100 * a:5.1f}" for a in v) + f"   ratio k-2/k+2 {v[0] / max(v[4], 1e-4):.2f}")
