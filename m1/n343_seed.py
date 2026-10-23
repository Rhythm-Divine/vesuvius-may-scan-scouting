"""Seed for the PHerc0343 pipeline control, from the winner's published segment mesh (read as data).

Among the mesh nodes inside the winner's reading area (sidecar "area.given", raw render px; one node per 20 px), keep
those whose local normal n = dP/dcolumn x dP/drow (outward, per the sidecar) is nearly horizontal (|n_z| < 0.2, as for
a sheet wrapped around a vertical axis) and whose 5 x 5 neighbourhood is fully valid; return the one nearest the area
centre, plus the scroll-centre direction for m1/seed.py (centre = node - 1000 * horizontal normal).

Usage: python -I n343_seed.py WINNER_OUTPUTS_DIR
"""
import json
import sys
from pathlib import Path

import numpy as np
import tifffile

d = Path(sys.argv[1])
x, y, z = (tifffile.imread(d / "concat.tifxyz" / f"{c}.tif").astype(np.float64) for c in "xyz")
side = json.loads((d / "sidecar.json").read_text(encoding="utf-8"))
c0, r0, c1, r1 = side["area"]["given"]["values"]
s = side["mesh"]["scale"]
valid = (x != -1) & (y != -1) & (z != -1)
P = np.stack([x, y, z], -1)
H, W = x.shape
rc, cc = (r0 + r1) / 2 * s, (c0 + c1) / 2 * s
best = None
for i in range(max(2, int(r0 * s)), min(H - 2, int(r1 * s))):
    for j in range(max(2, int(c0 * s)), min(W - 2, int(c1 * s))):
        if not valid[i - 2:i + 3, j - 2:j + 3].all():
            continue
        n = np.cross(P[i, j + 1] - P[i, j - 1], P[i + 1, j] - P[i - 1, j])
        n /= np.linalg.norm(n)
        if abs(n[2]) >= 0.2:
            continue
        dist = (i - rc) ** 2 + (j - cc) ** 2
        if best is None or dist < best[0]:
            best = (dist, i, j, n)
_, i, j, n = best
h = n.copy(); h[2] = 0; h /= np.linalg.norm(h)
px, py, pz = P[i, j]
print(json.dumps({"node_rc": [i, j], "area_centre_node": [round(rc, 1), round(cc, 1)],
                  "xyz": [round(float(px), 1), round(float(py), 1), round(float(pz), 1)],
                  "normal_xyz": [round(float(v), 4) for v in n],
                  "centre_yx_for_seed": [round(float(py - 1000 * h[1]), 1), round(float(px - 1000 * h[0]), 1)]}))
