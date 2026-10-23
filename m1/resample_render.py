"""Resample a vc_render_tifxyz zarr (8.64 um, ZYX uint8) to 9.604 um for Hecate, as e1/prepare.py does.

Usage: python resample_render.py RENDER.zarr OUT.npy
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
