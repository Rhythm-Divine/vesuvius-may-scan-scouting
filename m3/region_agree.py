"""S3 looking aid: the escalation rule's agreement for one region of one map (the share of reader-v2's >= T2 pixels in
the box that lie within 0.3 mm of Hecate's >= T pixels at the matching depth), plus the region's reader-v2 components
>= T2 (size and extent) for the record.
Usage: python m3/region_agree.py SAMPLE MESH FAMILY DIR Y0 Y1 X0 X1     (box in the crop frame of crop.json)
"""
import sys
from pathlib import Path

import imagecodecs
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
T2, T, AGREE_PX, PX_MM = 0.6275, 0.445, 31, 9.604e-3
K = {"near": (-2, -1, 0, 1, 2), "p6": (3, 4, 5, 6, 7), "m6": (-7, -6, -5, -4, -3)}
SUF = {"near": "", "p6": "_p6", "m6": "_m6"}


def load(p):
    return imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255


def main():
    s, m, fam, dr = sys.argv[1:5]
    y0, y1, x0, x1 = (int(v) for v in sys.argv[5:9])
    d = ROOT / f"data/m3/{s}/{m}"
    f = d / f"pred_r3_{dr}{SUF[fam]}.png"
    if not f.exists() and fam == "near":
        f = ROOT / f"data/s2/{s}/{m}/pred_r2_{dr}.png"
    r2 = load(f)
    hec = None
    for h in (d / "hecate", ROOT / f"data/m1/{s}/hecate/{m}"):
        fs = [h / f"pred_{dr}_{k}.png" for k in K[fam]]
        if all(p.exists() for p in fs):
            hec = np.mean([load(p) for p in fs], axis=0)
            break
    if hec is None:
        sys.exit("no Hecate maps at this depth")
    box = np.zeros(r2.shape, bool)
    box[y0:y1, x0:x1] = True
    a = (r2 >= T2) & box
    near_h = ndimage.binary_dilation(hec >= T, iterations=AGREE_PX)
    print(f"{s} {m} {fam} {dr} box y {y0}:{y1} x {x0}:{x1}: reader-v2 >= T2 pixels {int(a.sum())}, "
          f"agreement {near_h[a].mean():.3f}" if a.any() else "no reader-v2 pixels >= T2 in the box")
    lab, n = ndimage.label(a)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        comp = lab[sl] == i
        if comp.sum() < 50:
            continue
        hy, hx = (sl[0].stop - sl[0].start) * PX_MM, (sl[1].stop - sl[1].start) * PX_MM
        ag = near_h[sl][comp].mean()
        print(f"  component at y {sl[0].start}-{sl[0].stop} x {sl[1].start}-{sl[1].stop}: {int(comp.sum())} px, "
              f"{hy:.1f} x {hx:.1f} mm, agreement {ag:.2f}")


if __name__ == "__main__":
    main()
