"""S2: combine reader-v2's window maps for one surface volume (prereg/M1-survey-S2.md).

Per direction: the mean of the three 17-layer window maps (r2_<dir>_{c,p2,m2}.tif from m2/r2_infer.sh), resampled
8.64 -> 9.604 um the way e1/prepare.resample_render resamples a render layer (out(i, j) samples in(i / f, j / f),
linear), then cropped to the window Y0:Y1, X0:X1 of the 9.604 um canvas (zero outside the canvas). The result lines up
pixel for pixel with the S1 Hecate maps of the same mesh. Writes pred_r2_fwd.png and pred_r2_rev.png (uint8, 255 p).
Usage: python m2/r2_combine.py IN_DIR OUT_DIR Y0 Y1 X0 X1
"""
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

SRC_UM, DST_UM = 8.64, 9.604


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    y0, y1, x0, x1 = (int(v) for v in sys.argv[3:7])
    dst.mkdir(parents=True, exist_ok=True)
    f = SRC_UM / DST_UM
    for d, name in (("forward", "fwd"), ("reverse", "rev")):
        m = np.mean([tifffile.imread(src / f"r2_{d}_{w}.tif").astype(np.float32) for w in ("c", "p2", "m2")], axis=0)
        r = ndimage.affine_transform(m, [1 / f, 1 / f], output_shape=(int(m.shape[0] * f), int(m.shape[1] * f)),
                                     order=1)
        out = np.zeros((y1 - y0, x1 - x0), np.float32)
        cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, r.shape[0]), max(x0, 0), min(x1, r.shape[1])
        out[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0] = r[cy0:cy1, cx0:cx1]
        (dst / f"pred_r2_{name}.png").write_bytes(imagecodecs.png_encode(np.clip(np.rint(out), 0, 255).astype(np.uint8)))
        print(name, "native", m.shape, "max", float(m.max()), "-> 9.604", r.shape, "crop", out.shape)


if __name__ == "__main__":
    main()
