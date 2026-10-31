"""S3b: resample each reader-v2 sweep map 8.64 -> 9.604 um (linear, as m3/r3_combine.py) and crop it to the surface's
crop window, writing OUT_DIR/pred_s3b_<DIR>_<tag>.png (tags m20 m15 m10 m5 c p5 p10 p15 p20: a shift of tag/2 layers).
Usage: python m3/s3b_combine.py IN_DIR OUT_DIR Y0 Y1 X0 X1 DIR
"""
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

SRC_UM, DST_UM = 8.64, 9.604
TAGS = ("m20", "m15", "m10", "m5", "c", "p5", "p10", "p15", "p20")


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    y0, y1, x0, x1 = (int(v) for v in sys.argv[3:7])
    dr = sys.argv[7]
    d = "forward" if dr == "fwd" else "reverse"
    f = SRC_UM / DST_UM
    for t in TAGS:
        if not (src / f"r2_{d}_{t}.tif").exists():
            continue
        m = tifffile.imread(src / f"r2_{d}_{t}.tif").astype(np.float32)
        r = ndimage.affine_transform(m, [1 / f, 1 / f], output_shape=(int(m.shape[0] * f), int(m.shape[1] * f)), order=1)
        out = np.zeros((y1 - y0, x1 - x0), np.float32)
        cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, r.shape[0]), max(x0, 0), min(x1, r.shape[1])
        out[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0] = r[cy0:cy1, cx0:cx1]
        (dst / f"pred_s3b_{dr}_{t}.png").write_bytes(imagecodecs.png_encode(np.clip(np.rint(out), 0, 255).astype(np.uint8)))
    print("combined", dr, len(TAGS), "maps", out.shape)


if __name__ == "__main__":
    main()
