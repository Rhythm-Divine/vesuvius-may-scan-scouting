"""S3 duplicate check (prereg/M1-survey-S3.md): is a new kept surface a second copy of a surface already read?

The new mesh's interior grid points (>= 16 cells from its boundary) are compared with every surface of the same sample
that has been read: S1 and M1 surfaces with a Hecate readout (data/m1/<SAMPLE>/hecate/<mesh>/readout.json), and S3
surfaces already accepted (data/m3/s3_qc.tsv rows with decision keep and distinct). The other surface is densified 8x
(bilinear between grid vertices, 2.5-voxel spacing), so the distance approximates point-to-surface.
A median distance under 4 voxels makes it a duplicate (S1's distinctness rule). Prints
"distinct <nearest mesh> <median vox> <share within 4 vox>" or "duplicate <mesh> <median vox> <share>".

Speed (2026-10-24, 17:40 UTC; same result as before): the densified comparison is skipped for a surface that cannot
be the nearest. Each dense point lies within h of a vertex of its own cell, so per point the dense distance is at least
the vertex distance minus h, and so is the median. A surface whose vertex-only median minus h is above the best
dense median found so far cannot win, even on a tie, and is not densified.
Usage: python m3/distinct.py SAMPLE MESH
"""
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DUP_VOX, INTERIOR, DENSE = 4.0, 16, 8


def grid(sample, mesh):
    d = ROOT / "data/m1" / sample / "meshes" / mesh
    return np.stack([tifffile.imread(d / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def interior_points(g):
    ok = g[..., 0] != -1
    ok &= ndimage.distance_transform_edt(ok) >= INTERIOR
    return g[ok]


def dense_points(g):
    """Bilinear samples at 1/DENSE of a cell inside every grid cell whose four corners are valid, and h, the largest
    distance from a sample to the nearest corner of its own cell."""
    ok = g[..., 0] != -1
    cell = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    i, j = np.nonzero(cell)
    if len(i) == 0:
        return np.zeros((0, 3)), 0.0
    t = np.arange(DENSE) / DENSE
    u, v = np.meshgrid(t, t, indexing="ij")
    u, v = u.ravel()[None, :, None], v.ravel()[None, :, None]
    a, b = g[i, j][:, None], g[i + 1, j][:, None]
    c, d = g[i, j + 1][:, None], g[i + 1, j + 1][:, None]
    p = (1 - u) * (1 - v) * a + u * (1 - v) * b + (1 - u) * v * c + u * v * d
    h = np.min(np.stack([np.linalg.norm(p - q, axis=-1) for q in (a, b, c, d)], -1), -1).max()
    return p.reshape(-1, 3), float(h)


def read_meshes(sample, new):
    out = {f.parent.name for f in (ROOT / "data/m1" / sample / "hecate").glob("*/readout.json")}
    log = ROOT / "data/m3/s3_qc.tsv"
    if log.exists():
        for r in csv.DictReader(log.open(), delimiter="\t"):
            if r["sample"] == sample and r["decision"] == "keep" and r["distinct"].startswith("distinct"):
                out.add(r["mesh"])
    out.discard(new)
    return sorted(out)


def main():
    s, m = sys.argv[1], sys.argv[2]
    p = interior_points(grid(s, m))
    best = ("-", float("inf"), 0.0)
    if len(p):
        cands = []
        for rank, o in enumerate(read_meshes(s, m)):
            g = grid(s, o)
            ok = g[..., 0] != -1
            if not ok.any():
                continue
            lo, hi = g[ok].min(0) - 50, g[ok].max(0) + 50
            if not ((p >= lo) & (p <= hi)).all(1).any():
                continue
            coarse, _ = cKDTree(g[ok]).query(p, k=1)
            cands.append((float(np.median(coarse)), rank, o, g))
        found = []
        for cmed, rank, o, g in sorted(cands, key=lambda c: c[0]):
            dense, h = dense_points(g)
            if found and cmed - h > min(f[0] for f in found):
                continue
            dist, _ = cKDTree(dense).query(p, k=1)
            found.append((float(np.median(dist)), rank, o, float((dist < DUP_VOX).mean())))
        if found:
            med, _, o, share = min(found, key=lambda f: (f[0], f[1]))
            best = (o, med, share)
    word = "duplicate" if best[1] < DUP_VOX else "distinct"
    print(f"{word} {best[0]} {best[1]:.1f} {best[2]:.3f}")


if __name__ == "__main__":
    main()
