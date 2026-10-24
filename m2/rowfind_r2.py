"""rowfind on reader-v2 candidates (readout_r2.json). Usage: python m2/rowfind_r2.py SAMPLE MESH [DZ GAP SPAN]"""
import json, sys
from pathlib import Path
import numpy as np, tifffile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1")); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX  # noqa
from prepare import DST_UM, SRC_UM  # noqa
PER_CELL, MM = SRC_UM / DST_UM * CELL_PX, 9.604e-3
s, m = sys.argv[1], sys.argv[2]
DZ, GAP, SPAN = (float(sys.argv[i]) if len(sys.argv) > i else d for i, d in ((3, 70), (4, 4), (5, 5)))
root = Path(__file__).resolve().parents[1]
r = json.loads((root / f"data/s2/{s}/{m}/readout_r2.json").read_text())
y0, _, x0, _ = json.loads((root / f"data/m1/{s}/hecate/{m}/crop.json").read_text())["crop"]
zg = tifffile.imread(root / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
for d in ("fwd", "rev"):
    c = r[d]["candidates"]
    yx = np.array([k["centroid_yx"] for k in c]) if c else np.zeros((0, 2))
    z = np.array([zg[min(int((y + y0) / PER_CELL), zg.shape[0] - 1), min(int((x + x0) / PER_CELL), zg.shape[1] - 1)] for y, x in yx])
    n = len(c); seen = set(); rows = []
    adj = [[j for j in range(n) if j != i and abs(z[i] - z[j]) <= DZ and np.hypot(*(yx[i] - yx[j])) * MM <= GAP] for i in range(n)]
    for i in range(n):
        if i in seen: continue
        comp, st = [], [i]
        while st:
            k = st.pop()
            if k in seen: continue
            seen.add(k); comp.append(k); st += adj[k]
        if len(comp) >= 3:
            span = max(np.hypot(*(yx[a] - yx[b])) for a in comp for b in comp) * MM
            if span >= SPAN: rows.append((span, comp))
    print(f"{s} {m[11:]} {d}: {n} candidates, {len(rows)} rows")
    for span, comp in sorted(rows, reverse=True):
        print(f"   span {span:.1f} mm, {len(comp)} blobs, z {z[comp].min():.0f}-{z[comp].max():.0f}: " + " ".join(f"({yx[k][0]:.0f},{yx[k][1]:.0f};{c[k]['extent_mm']})" for k in sorted(comp, key=lambda k: yx[k][1])))
