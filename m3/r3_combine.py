"""S3: combine reader-v2's window maps for one surface volume (prereg/M1-survey-S3.md).

Per direction, as m2/r2_combine.py: maps are resampled 8.64 -> 9.604 um the way e1/prepare.resample_render resamples a
render layer (linear), then cropped to the window Y0:Y1, X0:X1 of the 9.604 um canvas (zero outside it).
- near: the mean of windows c, p2 and m2 (S2's read), written as pred_r3_<fwd|rev>.png, when all three are present;
- p6 and m6: each deeper window on its own, written as pred_r3_<fwd|rev>_<p6|m6>.png.
Usage: python m3/r3_combine.py IN_DIR OUT_DIR Y0 Y1 X0 X1
"""
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

SRC_UM, DST_UM = 8.64, 9.604
MAPS = {"": ("c", "p2", "m2"), "_p6": ("p6",), "_m6": ("m6",)}


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    y0, y1, x0, x1 = (int(v) for v in sys.argv[3:7])
    dst.mkdir(parents=True, exist_ok=True)
    f = SRC_UM / DST_UM
    for d, name in (("forward", "fwd"), ("reverse", "rev")):
        for suffix, wins in MAPS.items():
            files = [src / f"r2_{d}_{w}.tif" for w in wins]
            if not all(p.exists() for p in files):
                continue
            m = np.mean([tifffile.imread(p).astype(np.float32) for p in files], axis=0)
            r = ndimage.affine_transform(m, [1 / f, 1 / f], output_shape=(int(m.shape[0] * f), int(m.shape[1] * f)),
                                         order=1)
            out = np.zeros((y1 - y0, x1 - x0), np.float32)
            cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, r.shape[0]), max(x0, 0), min(x1, r.shape[1])
            out[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0] = r[cy0:cy1, cx0:cx1]
            png = np.clip(np.rint(out), 0, 255).astype(np.uint8)
            (dst / f"pred_r3_{name}{suffix}.png").write_bytes(imagecodecs.png_encode(png))
            print(name + suffix, "native", m.shape, "max", float(m.max()), "-> 9.604", r.shape, "crop", out.shape)


if __name__ == "__main__":
    main()
