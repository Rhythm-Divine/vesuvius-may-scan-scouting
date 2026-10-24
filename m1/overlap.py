"""Which other meshes pass under a reference mesh's strong forward region? Geometry only (looking aid, not a rule).
Takes the reference's readout cells where the forward ensemble >= T, maps them to 3D, and reports for every other mesh
of the sample: the median and 10th-percentile distance to its nearest vertex, and the share of those points within 10
voxels (same sheet) and within 40 voxels (a neighbouring winding).
Usage: python m1/overlap.py SAMPLE REF_MESH"""
import json
import os
import sys
from pathlib import Path
import imagecodecs
import numpy as np
import tifffile
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from readout import CELL_PX, T  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402
PER_CELL = SRC_UM / DST_UM * CELL_PX
root, ref = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / sys.argv[1], sys.argv[2]
xyz = lambda m: np.stack([tifffile.imread(root / "meshes" / m / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)
h = root / "hecate" / ref
ens = np.mean([imagecodecs.png_decode((h / f"pred_fwd_{k}.png").read_bytes()).astype(np.float32) / 255 for k in (-2, -1, 0, 1, 2)], 0)
y0, _, x0, _ = json.loads((h / "crop.json").read_text())["crop"]
g = xyz(ref)
ys, xs = np.nonzero(ens >= T)
r, c = ((ys + y0) / PER_CELL).astype(int), ((xs + x0) / PER_CELL).astype(int)
ok = (r < g.shape[0]) & (c < g.shape[1])
cells = np.unique(np.stack([r[ok], c[ok]], 1), axis=0)
p = g[cells[:, 0], cells[:, 1]]
p = p[p[:, 0] != -1]
print(f"{ref}: {len(p)} strong cells")
for m in sorted(d.name for d in (root / "meshes").iterdir() if d.name != ref):
    q = xyz(m)
    q = q[q[..., 0] != -1]
    d, _ = cKDTree(q).query(p)
    print(f"  {m}: median {np.median(d):7.1f}  p10 {np.percentile(d, 10):7.1f}  within 10 vox {np.mean(d <= 10):5.1%}  within 40 vox {np.mean(d <= 40):5.1%}")
