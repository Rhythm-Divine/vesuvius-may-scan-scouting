"""E1b scoring: Hecate on render.npy (8.64 -> 9.604 um) against the organisers' same-mesh labels (2026-09-18).

Labels sit on the 2.401 um canvas's level 2 (9.604 um); register.py's median tile shift s maps a render pixel p to
label pixel p + s. Per prediction: AUC inside the supervision mask and inside the validation mask, the AUC with the
labels displaced 250 px (4 directions; the null), and T = median probability on labelled ink. With predictions named
pred_off_<k>.png, also the depth ensembles -1..+1 and -2..+2 (per-pixel mean), as in J. Lu's hecate_perf.md.

Usage: python score.py --out DIR pred_off_-2.png ... pred_off_2.png
"""
import os
import argparse
import json
import re
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import zarr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from score4 import NULL_SHIFTS, shift0  # noqa: E402
from sweep.readout import auc, calibrate  # noqa: E402

LAB = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/e1b/labels"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("preds", nargs="+")
    a = ap.parse_args()
    d = Path(a.out)
    reg = json.loads((d / "register.json").read_text())
    y0, y1, x0, x1 = reg["window"]
    sy, sx = (int(round(v)) for v in reg["shift_median_px"])
    lab = {n: np.asarray(zarr.open_array(str(LAB / f"{n}.zarr/2"), mode="r")[:]) > 127
           for n in ("inklabels", "supervision", "validation")}
    # render pixel p <-> label pixel p + s: take the label window shifted by s (zero outside the label canvas)
    def win(m):
        out = np.zeros((y1 - y0, x1 - x0), bool)
        ya, yb, xa, xb = y0 + sy, y1 + sy, x0 + sx, x1 + sx
        cy0, cy1, cx0, cx1 = max(ya, 0), min(yb, m.shape[0]), max(xa, 0), min(xb, m.shape[1])
        out[cy0 - ya:cy1 - ya, cx0 - xa:cx1 - xa] = m[cy0:cy1, cx0:cx1]
        return out
    L, S, V = (win(lab[n]) for n in ("inklabels", "supervision", "validation"))
    preds = {Path(p).stem: imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255 for p in a.preds}
    offs = {int(m.group(1)): k for k in preds if (m := re.fullmatch(r"pred_off_(-?\d+)", k))}
    for name, ks in (("ens_-1..+1", (-1, 0, 1)), ("ens_-2..+2", (-2, -1, 0, 1, 2))):
        if all(k in offs for k in ks):
            preds[name] = np.mean([preds[offs[k]] for k in ks], axis=0)
    res = {"shift_used_px": [sy, sx], "window": reg["window"], "sup_px": int(S.sum()), "ink_px_in_sup": int((L & S).sum()),
           "val_px": int(V.sum()), "null_shifts": NULL_SHIFTS}
    for n, P in preds.items():
        cal = calibrate(P, L, S)
        res[n] = {"auc_sup": round(cal["auc"], 4), "auc_val": round(auc(P, L, V), 4),
                  "null_aucs_sup": [round(auc(P, shift0(L, dy, dx), shift0(S, dy, dx)), 4) for dy, dx in NULL_SHIFTS],
                  "threshold_T": round(cal["threshold"], 4)}
        print(n, json.dumps(res[n]), flush=True)
    (d / "score.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
