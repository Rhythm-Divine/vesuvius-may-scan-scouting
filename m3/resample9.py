"""Resample a native 48-layer render (OME-Zarr, level "0") to the 9.604 um grid with e1/prepare.resample_render,
exactly as m1/grow_more.sh does after each render.
Usage: python m3/resample9.py RENDER.zarr OUT_9p6.npy
"""
import sys
from pathlib import Path

import numpy as np
import zarr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from prepare import resample_render  # noqa: E402

g = zarr.open(sys.argv[1], mode="r")
src = g["0"] if hasattr(g, "keys") and "0" in g else g
out = resample_render(src)
np.save(sys.argv[2], out)
print("9.604 um", out.shape, "valid frac", round(float((out[out.shape[0] // 2] > 0).mean()), 3))
