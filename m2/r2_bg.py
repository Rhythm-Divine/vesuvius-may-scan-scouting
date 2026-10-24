"""S2 control numbers for reader-v2 on E1b that e1b/score.py does not give: for each map, the share of non-ink
supervision pixels >= the map's own T (median p on labelled ink), i.e. the control background used by triage, and the
recall at that T (0.5 by construction) next to the share of non-ink flagged at 80% recall. Same window, shift and labels
as e1b/score.py.
Usage: python m2/r2_bg.py --out DIR pred.png [pred.png ...]   (DIR holds register.json and score.json)
"""
import argparse
import json
import os
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import zarr

LAB = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/e1b/labels"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("preds", nargs="+")
    a = ap.parse_args()
    d = Path(a.out)
    reg = json.loads((d / "register.json").read_text())
    sc = json.loads((d / "score.json").read_text())
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
        t = sc[n]["threshold_T"]
        ink, bg = P[L & S], P[~L & S]
        t80 = float(np.percentile(ink, 20))
        res[n] = {"T": t, "bg_frac_ge_T": round(float((bg >= t).mean()), 4), "T_at_80pct_recall": round(t80, 4),
                  "bg_frac_at_80pct_recall": round(float((bg >= t80).mean()), 4), "mean_bg": round(float(bg.mean()), 4)}
        print(n, json.dumps(res[n]))
    (d / "bg.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
