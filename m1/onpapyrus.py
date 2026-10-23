"""M1 QC: how much of a mesh's readout area sits on papyrus, sampled from the level-1 masked CT at the mesh vertices.

No render is needed, so this also works for meshes whose renders were deleted. A readout cell is a mesh grid cell
>= 16 cells from the mesh boundary and more than 8 cells from any vc_tifxyz_selfcross contact (as in m1/readout.py),
whose vertex lies inside the masked CT (> 0). It counts as on papyrus when the brightest level-1 voxel within +-2
voxels (~35 um) of the vertex is above CUT (air reads ~40-60, papyrus ~100-150 on the 8-bit scale). Reads public open
data only. Prints one JSON line per mesh.

Usage: python onpapyrus.py --sample PHerc0490A --volume-id 20250521151210 MESH [MESH ...]
"""
import os
import argparse
import concurrent.futures as cf
import json
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

import numcodecs
import numpy as np
import tifffile
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2"))
from overview import B, catalogue_paths, get  # noqa: E402

CUT, LEVEL, R, INTERIOR_CELLS, EXCLUDE_R = 90, 1, 2, 16, 8
CELL_CM2 = (20 * 8.64e-4) ** 2   # one grid cell: 20 level-0 voxels of 8.64 um on a side


def readout_cells(mesh_dir, selfcross):
    x = tifffile.imread(Path(mesh_dir) / "x.tif")
    keep = ndimage.distance_transform_edt(x != -1) >= INTERIOR_CELLS
    hit = np.zeros(x.shape, bool)
    for c in json.loads(Path(selfcross).read_text())["census"]:
        for t in c.get("transverse_contacts", []):
            for q in (t["quad1"], t["quad2"]):
                if 0 <= int(q[0]) < x.shape[0] and 0 <= int(q[1]) < x.shape[1]:
                    hit[int(q[0]), int(q[1])] = True
    return keep & ~ndimage.binary_dilation(hit, iterations=EXCLUDE_R)


class SparseVolume:
    """Level-L chunks of an OME-Zarr on the open-data bucket, fetched on demand and kept in memory."""

    def __init__(self, prefix, level):
        self.base = f"{B}/{urllib.parse.quote(prefix)}{level}/"
        meta = json.loads(get(self.base + ".zarray"))
        self.shape, self.ch = np.array(meta["shape"]), np.array(meta["chunks"])
        self.sep = meta.get("dimension_separator", ".")
        self.codec = numcodecs.get_codec(meta["compressor"]) if meta.get("compressor") else None
        self.chunks = {}

    def _fetch(self, key):
        for attempt in range(4):   # the bucket occasionally resets connections
            try:
                raw = get(self.base + self.sep.join(map(str, key)))
                break
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        if raw is None:
            return key, np.zeros(tuple(self.ch), np.uint8)
        return key, np.frombuffer(self.codec.decode(raw) if self.codec else raw, np.uint8).reshape(tuple(self.ch))

    def sample(self, zyx):
        """Values at integer level-L coordinates (N x 3); out of range reads 0."""
        zyx = np.asarray(zyx)
        ok = np.all((zyx >= 0) & (zyx < self.shape), axis=1)
        key = zyx // self.ch
        need = {tuple(k) for k in np.unique(key[ok], axis=0)} - self.chunks.keys()
        with cf.ThreadPoolExecutor(16) as ex:   # network-bound
            self.chunks.update(ex.map(self._fetch, need))
        out = np.zeros(len(zyx), np.uint8)
        loc = zyx % self.ch
        lin = np.ravel_multi_index(key[ok].T, tuple(-(-self.shape // self.ch)))
        idx = np.nonzero(ok)[0]
        for u in np.unique(lin):
            sel = idx[lin == u]
            blk = self.chunks[tuple(key[sel[0]])]
            out[sel] = blk[loc[sel, 0], loc[sel, 1], loc[sel, 2]]
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--volume-id", required=True)
    ap.add_argument("meshes", nargs="+")
    a = ap.parse_args()
    root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / a.sample
    _, vol_prefix, _ = catalogue_paths(a.sample, a.volume_id)
    f = 2 ** LEVEL
    offs = np.array([(dz, dy, dx) for dz in range(-R, R + 1) for dy in range(-R, R + 1) for dx in range(-R, R + 1)])
    for mesh in a.meshes:
        vol = SparseVolume(vol_prefix, LEVEL)   # one mesh's chunks at a time
        cells = readout_cells(root / "meshes" / mesh, root / "render" / f"{mesh}_selfcross.json")
        xyz = [tifffile.imread(root / "meshes" / mesh / f"{c}.tif").astype(np.float64) for c in "xyz"]
        rr, cc = np.nonzero(cells)
        v = np.rint(np.stack([xyz[2][rr, cc], xyz[1][rr, cc], xyz[0][rr, cc]], axis=1) / f).astype(np.int64)
        inside = vol.sample(v) > 0
        v = v[inside]
        best = np.zeros(len(v), np.uint8)
        for o in offs:
            best = np.maximum(best, vol.sample(v + o))
        print(json.dumps({"sample": a.sample, "mesh": mesh, "readout_cells": int(len(v)),
                          "readout_cm2_approx": round(len(v) * CELL_CM2, 3),
                          "on_papyrus_share": round(float((best > CUT).mean()), 3) if len(v) else None,
                          "chunks_fetched": len(vol.chunks)}), flush=True)


if __name__ == "__main__":
    main()
