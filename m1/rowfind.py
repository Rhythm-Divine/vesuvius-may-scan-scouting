"""Rows of readout candidates along the text direction (looking aid for the 04:10 UTC row trigger; not a verdict rule).
Maps each candidate (>= T component >= 0.5 mm, from readout.json) to its 3D scroll height z. Links two candidates when
their heights differ by <= DZ slices and they lie <= GAP mm apart on the surface. Reports linked groups of >= 3
candidates spanning >= SPAN mm. Prints each group's members (crop y x, z) and its z spread.
Usage: python m1/rowfind.py SAMPLE MESH [DZ=70] [GAP=4] [SPAN=5]"""
import json
import os
import sys
from pathlib import Path
import numpy as np
import tifffile
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402
PER_CELL, MM_PX = SRC_UM / DST_UM * CELL_PX, 9.604e-3
s, m = sys.argv[1], sys.argv[2]
DZ, GAP, SPAN = (float(sys.argv[i]) if len(sys.argv) > i else d for i, d in ((3, 70), (4, 4), (5, 5)))
root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / s
h = root / "hecate" / m
r = json.loads((h / "readout.json").read_text())
y0, _, x0, _ = json.loads((h / "crop.json").read_text())["crop"]
zg = tifffile.imread(root / "meshes" / m / "z.tif").astype(np.float64)
for d in ("fwd", "rev"):
    c = r[d]["candidates"]
    if len(c) < 3:
        print(f"{s} {m[11:]} {d}: {len(c)} candidates, no rows"); continue
    yx = np.array([k["centroid_yx"] for k in c])
    z = np.array([zg[min(int((y + y0) / PER_CELL), zg.shape[0] - 1), min(int((x + x0) / PER_CELL), zg.shape[1] - 1)] for y, x in yx])
    n = len(c)
    adj = [[j for j in range(n) if j != i and z[i] > 0 and z[j] > 0 and abs(z[i] - z[j]) <= DZ
            and np.hypot(*(yx[i] - yx[j])) * MM_PX <= GAP] for i in range(n)]
    seen, rows = set(), []
    for i in range(n):
        if i in seen: continue
        comp, stack = [], [i]
        while stack:
            k = stack.pop()
            if k in seen: continue
            seen.add(k); comp.append(k); stack += adj[k]
        if len(comp) >= 3:
            p = yx[comp]
            span = max(np.hypot(*(a - b)) for a in p for b in p) * MM_PX
            if span >= SPAN:
                rows.append((span, comp))
    print(f"{s} {m[11:]} {d}: {n} candidates, {len(rows)} rows (dz <= {DZ:.0f}, gap <= {GAP} mm, span >= {SPAN} mm)")
    for span, comp in sorted(rows, reverse=True):
        print(f"   row span {span:.1f} mm, {len(comp)} blobs, z {z[comp].min():.0f}-{z[comp].max():.0f}: "
              + " ".join(f"({yx[k][0]:.0f},{yx[k][1]:.0f})" for k in sorted(comp, key=lambda k: yx[k][1])))
