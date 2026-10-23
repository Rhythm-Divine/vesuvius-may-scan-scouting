"""Readout-area bounding box + 128 px (clipped) on a 9.604 um render, for cropping Hecate's input.

Usage: python readout_crop.py --mesh MESH --render9 R.npy --selfcross SC.json --exclude-contacts 8 --out crop.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import PX_UM, interior_mask  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--mesh", required=True)
ap.add_argument("--render9", required=True)
ap.add_argument("--selfcross", required=True)
ap.add_argument("--exclude-contacts", type=int, default=8)
ap.add_argument("--out", required=True)
a = ap.parse_args()
r = np.load(a.render9, mmap_mode="r")
assert r.shape[0] == 43, r.shape
valid = (np.asarray(r[21]) > 0) & interior_mask(a.mesh, r.shape[1:], a.selfcross, a.exclude_contacts)
ys, xs = np.nonzero(valid)
H, W = r.shape[1:]
crop = [max(0, int(ys.min()) - 128), min(H, int(ys.max()) + 129), max(0, int(xs.min()) - 128), min(W, int(xs.max()) + 129)]
rep = {"crop": crop, "valid_cm2": round(float(valid.sum()) * (PX_UM * 1e-4) ** 2, 3)}
Path(a.out).write_text(json.dumps(rep))
print(json.dumps(rep))
