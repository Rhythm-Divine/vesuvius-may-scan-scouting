"""S3b (prereg/M1-survey-S3b.md): fix each target's geometry from S3's existing outputs, before any S3b output exists.
For each escalated row (and the E1d control) it writes to data/m3b/targets.json:
- the row's reader-v2 components >= T2 in its S3 box, on the S3 map where it was found (centroids, crop frame);
- the row axis: the principal direction of those centroids (unit vector, crop frame) and their mean (anchor);
- the seed for the longer regrowth: the mesh point under the anchor (integer X Y Z voxels);
- for the facing-winding read, the nearest already-read neighbouring winding on each side of the sheet (sign of the
  mesh normal), at least 12 voxels from the row, with the anchor mapped to its crop frame.
Usage: python m3/s3b_prep.py
"""
import csv
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "m1"))
sys.path.insert(0, str(ROOT / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

T2, PX_MM, MIN_PX = 0.6275, 9.604e-3, 300
PER_CELL = SRC_UM / DST_UM * CELL_PX
SUF = {"near": "", "p6": "_p6", "m6": "_m6"}
TARGETS = [  # name, sample, mesh, S3 family, direction, box y0 y1 x0 x1 (crop frame), zone
    ("E1d", "PHerc0343", "auto_grown_20261023221723612", "near", "fwd", (1100, 1900, 820, 1420), None),
    ("s198", "PHerc0483B", "auto_grown_20261024171724520", "p6", "rev", (1950, 2450, 500, 1250), "z10098_r30_a090"),
    ("s206", "PHerc0483A", "auto_grown_20261024184958725", "m6", "fwd", (1380, 1720, 740, 1440), "z4769_r30_a090"),
    ("s325", "PHerc0175A", "auto_grown_20261024214208830", "m6", "rev", (1180, 1380, 40, 800), "z8923_r30_a225"),
]


def grid(s, m):
    d = ROOT / "data/m1" / s / "meshes" / m
    return np.stack([tifffile.imread(d / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def origin(s, m):
    y0, _, x0, _ = json.loads((ROOT / f"data/m3/{s}/{m}/crop.json").read_text())["crop"]
    return y0, x0


def to3d(g, s, m, y, x):
    y0, x0 = origin(s, m)
    r, c = int(round((y0 + y) / PER_CELL - 0.5)), int(round((x0 + x) / PER_CELL - 0.5))
    r, c = min(max(r, 1), g.shape[0] - 2), min(max(c, 1), g.shape[1] - 2)
    return g[r, c], r, c


def normal(g, r, c):
    a, b = g[r, c + 1] - g[r, c - 1], g[r + 1, c] - g[r - 1, c]
    n = np.cross(a, b)
    return n / np.linalg.norm(n)


def neighbours(s, zone, m):
    out = set()
    for r in csv.DictReader(open(ROOT / "data/m3/s3_qc.tsv"), delimiter="\t"):
        if r["sample"] == s and r["surface"].startswith(zone) and r["decision"] == "keep" \
                and r["distinct"].startswith("distinct") and r["mesh"] != m:
            out.add(r["mesh"])
    for r in csv.DictReader(open(ROOT / "data/m1/survey_qc.tsv"), delimiter="\t"):
        if r.get("sample") == s and zone in r.values():
            out.update(v for v in r.values() if v and v.startswith("auto_grown_") and v != m)
    return sorted(o for o in out if (ROOT / f"data/m3/{s}/{o}/crop.json").exists())


def main():
    res = {}
    for name, s, m, fam, dr, (y0, y1, x0, x1), zone in TARGETS:
        d = ROOT / f"data/m3/{s}/{m}"
        a = imagecodecs.png_decode((d / f"pred_r3_{dr}{SUF[fam]}.png").read_bytes()).astype(np.float32) / 255
        box = np.zeros(a.shape, bool)
        box[y0:y1, x0:x1] = True
        lab, n = ndimage.label((a >= T2) & box)
        comps = []
        for i, sl in enumerate(ndimage.find_objects(lab), 1):
            px = int((lab[sl] == i).sum())
            if px >= MIN_PX:
                cy, cx = ndimage.center_of_mass(lab == i)
                comps.append({"y": round(cy, 1), "x": round(cx, 1), "px": px})
        c = np.array([[q["y"], q["x"]] for q in comps])
        anchor = c.mean(0)
        u = np.linalg.svd(c - anchor)[2][0] if len(c) > 1 else np.array([1.0, 0.0])
        g = grid(s, m)
        p, r, cc = to3d(g, s, m, *anchor)
        nrm = normal(g, r, cc)
        t = {"sample": s, "mesh": m, "family": fam, "dir": dr, "box": [y0, y1, x0, x1], "components": comps,
             "anchor": [round(float(v), 1) for v in anchor], "axis": [round(float(v), 4) for v in u],
             "seed": [int(round(v)) for v in p], "normal": [round(float(v), 4) for v in nrm], "facing": {}}
        if zone:
            best = {}
            for o in neighbours(s, zone, m):
                h = grid(s, o)
                ok = h[..., 0] != -1
                idx = np.argwhere(ok)
                dist, j = cKDTree(h[ok]).query(p)
                if dist < 12:
                    continue
                rr, c2 = idx[j]
                side = "plus" if float(np.dot(h[rr, c2] - p, nrm)) > 0 else "minus"
                if side not in best or dist < best[side][0]:
                    oy0, ox0 = origin(s, o)
                    best[side] = (float(dist), o, int((rr + 0.5) * PER_CELL) - oy0, int((c2 + 0.5) * PER_CELL) - ox0)
            for side, (dist, o, yy, xx) in best.items():
                t["facing"][side] = {"mesh": o, "dist_vox": round(dist, 1), "anchor": [yy, xx]}
        res[name] = t
        print(name, s, m, fam, dr, f"{len(comps)} components, anchor {t['anchor']}, axis {t['axis']}, seed {t['seed']}",
              {k: (v["mesh"], v["dist_vox"]) for k, v in t["facing"].items()})
    out = ROOT / "data/m3b/targets.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
