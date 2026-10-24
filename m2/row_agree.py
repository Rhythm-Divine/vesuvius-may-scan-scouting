"""For given reader-v2 candidates (by centroid), the share of their >= T2 pixels (inside the candidate bboxes) that lie
within 0.3 mm of Hecate's >= T pixels on the same mesh and direction: the S2 escalation agreement test.
Usage: python m2/row_agree.py SAMPLE MESH DIR Y X [Y X ...]   (centroids as printed by rowfind_r2.py)"""
import json, sys
from pathlib import Path
import imagecodecs, numpy as np
from scipy import ndimage
T, T2 = 0.445, 0.6275
s, m, d = sys.argv[1:4]
pts = np.array(list(map(float, sys.argv[4:]))).reshape(-1, 2)
root = Path(__file__).resolve().parents[1]
r = json.loads((root / f"data/s2/{s}/{m}/readout_r2.json").read_text())
h = root / f"data/m1/{s}/hecate/{m}"
r2 = imagecodecs.png_decode((root / f"data/s2/{s}/{m}/pred_r2_{d}.png").read_bytes()).astype(np.float32) / 255
hec = np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255 for k in (-2, -1, 0, 1, 2)], 0)
near = ndimage.binary_dilation(hec >= T, iterations=31)
tot = agree = 0
for y, x in pts:
    c = min(r[d]["candidates"], key=lambda c: np.hypot(c["centroid_yx"][0] - y, c["centroid_yx"][1] - x))
    y0, x0, y1, x1 = c["bbox_yx"]
    sel = r2[y0:y1 + 1, x0:x1 + 1] >= T2
    n, a = int(sel.sum()), int((sel & near[y0:y1 + 1, x0:x1 + 1]).sum())
    tot += n; agree += a
    print(f"  cand ({c['centroid_yx'][0]:.0f},{c['centroid_yx'][1]:.0f}) extent {c['extent_mm']} mm: {n} px >= T2, {a / max(n, 1):.0%} within 0.3 mm of Hecate >= T")
print(f"{s} {m[11:]} {d}: row agreement {agree / max(tot, 1):.0%} of {tot} px")
