"""S3 control numbers on E1b at a fixed threshold: for each reader-v2 map, the share of non-ink supervision pixels >= T2
(the control background that S3's triage uses for that window family), and the share of labelled ink >= T2. Same
window, shift and labels as e1b/score.py and m2/r2_bg.py.
Usage: python m3/bg_t2.py --out DIR --t2 T2 pred.png [pred.png ...]   (DIR holds register.json)
"""
import argparse
import json
from pathlib import Path

import imagecodecs
import numpy as np
import zarr

LAB = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/e1b/labels"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--t2", type=float, required=True)
    ap.add_argument("preds", nargs="+")
    a = ap.parse_args()
    d = Path(a.out)
    reg = json.loads((d / "register.json").read_text())
    y0, y1, x0, x1 = reg["window"]
    sy, sx = (int(round(v)) for v in reg["shift_median_px"])
    lab = {n: np.asarray(zarr.open_array(str(LAB / f"{n}.zarr/2"), mode="r")[:]) > 127 for n in ("inklabels", "supervision")}

    def win(m):
        out = np.zeros((y1 - y0, x1 - x0), bool)
        ya, yb, xa, xb = y0 + sy, y1 + sy, x0 + sx, x1 + sx
        cy0, cy1, cx0, cx1 = max(ya, 0), min(yb, m.shape[0]), max(xa, 0), min(xb, m.shape[1])
        out[cy0 - ya:cy1 - ya, cx0 - xa:cx1 - xa] = m[cy0:cy1, cx0:cx1]
        return out

    L, S = win(lab["inklabels"]), win(lab["supervision"])
    res = {}
    for p in a.preds:
        n = Path(p).stem
        P = imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255
        ink, bg = P[L & S], P[~L & S]
        res[n] = {"T2": a.t2, "bg_frac_ge_T2": round(float((bg >= a.t2).mean()), 4),
                  "ink_frac_ge_T2": round(float((ink >= a.t2).mean()), 4), "median_p_on_ink": round(float(np.median(ink)), 4),
                  "mean_bg": round(float(bg.mean()), 4)}
        print(n, json.dumps(res[n]))
    (d / "bg_t2.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
