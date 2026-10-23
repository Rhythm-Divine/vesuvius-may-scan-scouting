"""M1 mesh QC before pre-registering a readout: interior, self-crossings and whether meshes are distinct sheets.

Per mesh (tifxyz in MESH_ROOT): interior area (cells >= 16 from the mesh boundary), and the self-crossing contacts
from <render dir>/<mesh>_selfcross.json split into boundary band vs interior. Per pair: the distance from each
interior grid point of A to the nearest grid point of B (KD-tree, voxels). A median under 4 voxels means the same sheet
(a duplicate); adjacent windings here sit ~16 voxels apart. Writes qc.json.

Usage: python qc_meshes.py --meshes DIR --render DIR --out qc.json MESH [MESH ...]
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage
from scipy.spatial import cKDTree

INTERIOR_CELLS, CELL_UM = 16, 20 * 8.64


def load(mesh_dir):
    x, y, z = (tifffile.imread(Path(mesh_dir) / f"{c}.tif").astype(np.float64) for c in "xyz")
    valid = x != -1
    dist = ndimage.distance_transform_edt(np.pad(valid, 1, constant_values=False))[1:-1, 1:-1]
    return np.stack([x, y, z], -1), valid, dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meshes", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("names", nargs="+")
    a = ap.parse_args()
    res, pts = {"meshes": {}, "pairs": {}}, {}
    for n in a.names:
        P, valid, dist = load(Path(a.meshes) / n)
        interior = dist >= INTERIOR_CELLS
        pts[n] = (P[valid], P[interior])
        sc = json.loads((Path(a.render) / f"{n}_selfcross.json").read_text())
        d = []
        for c in sc["census"]:
            for t in c.get("transverse_contacts", []):
                for q in (t["quad1"], t["quad2"]):
                    i, j = int(q[0]), int(q[1])
                    if 0 <= i < dist.shape[0] and 0 <= j < dist.shape[1]:
                        d.append(dist[i, j])
        d = np.array(d) if d else np.zeros(0)
        res["meshes"][n] = {"grid": list(valid.shape), "valid_cm2": round(float(valid.sum()) * (CELL_UM * 1e-4) ** 2, 2),
                            "interior_cm2": round(float(interior.sum()) * (CELL_UM * 1e-4) ** 2, 2),
                            "contact_quads": int(len(d)), "contacts_in_interior": int((d >= INTERIOR_CELLS).sum()),
                            "contact_dist_max_cells": float(d.max()) if len(d) else None}
    for a_, b_ in itertools.permutations(a.names, 2):
        tree = cKDTree(pts[b_][0])
        dd, _ = tree.query(pts[a_][1], k=1)
        res["pairs"][f"{a_} -> {b_}"] = {"median_vox": round(float(np.median(dd)), 2),
                                         "frac_within_3vox": round(float((dd <= 3).mean()), 3),
                                         "p10_p90_vox": [round(float(v), 1) for v in np.percentile(dd, [10, 90])]}
    Path(a.out).write_text(json.dumps(res, indent=1))
    for k, v in res["meshes"].items():
        print(k, json.dumps(v))
    for k, v in res["pairs"].items():
        print(k, json.dumps(v))


if __name__ == "__main__":
    main()
