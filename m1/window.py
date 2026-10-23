"""Hecate input window k of a 43-layer 9.604 um render: layers 13+k..28+k, cropped to Y0:Y1, X0:X1.

Usage: python window.py RENDER9.npy K Y0 Y1 X0 X1 OUT.npy
"""
import sys

import numpy as np

r = np.load(sys.argv[1], mmap_mode="r")
k, y0, y1, x0, x1 = (int(v) for v in sys.argv[2:7])
assert r.shape[0] == 43, r.shape
z0 = 13 + k
np.save(sys.argv[7], np.ascontiguousarray(r[z0:z0 + 16, y0:y1, x0:x1]))
print("window", k, "layers", z0, z0 + 15)
