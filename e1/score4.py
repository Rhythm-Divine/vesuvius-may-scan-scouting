"""Score Hecate on the E1 text-block window under each label transfer, against displaced-label nulls.

Transfers: 'align3' (labels_fit / mask_fit as they are) and, for each band whose align4 gate passed, 'align4_<band>'
(labels and mask pulled onto the render canvas through the affine field: L_render(p) = L(p + s(p))).
Null: the AUC with labels and mask displaced by 250 px (4 directions, zero fill). A transfer that is right has to
beat all four by a clear margin; one that is wrong sits among them.
Writes DIR/<report> and ov_<tag><transfer>.png (the mean prediction at half resolution with label edges in white).

Usage: python score4.py --e1 DIR [--report score4.json] [--tag ""] pred_win_fwd.png [pred_win_rev.png ...]
(with several predictions, 'mean' is their average: fwd/rev, or a depth-offset ensemble)
"""
import argparse
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import write_png  # noqa: E402
from sweep.readout import auc, calibrate  # noqa: E402

NULL_SHIFTS = [(0, 250), (0, -250), (250, 0), (-250, 0)]


def shift0(a, dy, dx):
    """out[y + dy, x + dx] = a[y, x], zero fill."""
    out = np.zeros_like(a)
    h, w = a.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = a[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", required=True)
    ap.add_argument("--report", default="score4.json")
    ap.add_argument("--tag", default="", help="prefix for the overlay PNG names")
    ap.add_argument("preds", nargs="+")
    a = ap.parse_args()
    d = Path(a.e1)
    Y0, Y1, X0, X1 = json.loads((d / "render_fit_win.json").read_text())["crop"]
    lab_full, msk_full = np.load(d / "labels_fit.npy"), np.load(d / "mask_fit.npy")
    preds = {Path(p).stem: imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255 for p in a.preds}
    if len(preds) > 1:
        preds["mean"] = np.mean(list(preds.values()), axis=0)
    transfers = {"align3": (lab_full[Y0:Y1, X0:X1], msk_full[Y0:Y1, X0:X1])}
    a4p = d / "align4.json"
    a4 = json.loads(a4p.read_text()) if a4p.exists() else {"bands": {}}
    for band, r in a4["bands"].items():
        if not r.get("gate_pass"):
            continue
        coef = np.array(r["affine"]["coef_window_coords"])
        wy0, _, wx0, _ = a4["window"]
        yy, xx = np.indices((Y1 - Y0, X1 - X0), dtype=np.float32)
        wy, wx = yy + (Y0 - wy0), xx + (X0 - wx0)
        cy = yy + Y0 + coef[0, 0] + coef[1, 0] * wy + coef[2, 0] * wx
        cx = xx + X0 + coef[0, 1] + coef[1, 1] * wy + coef[2, 1] * wx
        transfers[f"align4_{band}"] = tuple(ndimage.map_coordinates(m.astype(np.uint8), [cy, cx], order=0) > 0
                                            for m in (lab_full, msk_full))
    a5p = d / "align5.json"   # dense fields: label-canvas pixel = render-canvas pixel + (dy, dx)
    for band, r in (json.loads(a5p.read_text())["bands"].items() if a5p.exists() else []):
        if not r.get("gate_pass"):
            continue
        f = np.load(d / f"field_{band}.npz")
        yy, xx = np.indices((Y1 - Y0, X1 - X0), dtype=np.float32)
        cy, cx = yy + Y0 + f["dy"], xx + X0 + f["dx"]
        transfers[f"field_{band}"] = tuple(ndimage.map_coordinates(m.astype(np.uint8), [cy, cx], order=0) > 0
                                           for m in (lab_full, msk_full))
    res = {"crop": [Y0, Y1, X0, X1], "null_shifts": NULL_SHIFTS, "align4_gates": {b: r.get("gate_pass")
           for b, r in a4["bands"].items()}}
    show = preds.get("mean", next(iter(preds.values())))
    for tname, (L, M) in transfers.items():
        r = {"mask_px": int(M.sum()), "ink_px": int((L & M).sum())}
        for pname, P in preds.items():
            if P.shape != L.shape:
                raise SystemExit(f"{pname}: shape {P.shape} != labels {L.shape}")
            nulls = [round(auc(P, shift0(L, dy, dx), shift0(M, dy, dx)), 4) for dy, dx in NULL_SHIFTS]
            cal = calibrate(P, L, M)
            r[pname] = {"auc": round(cal["auc"], 4), "null_aucs": nulls, "threshold_T": round(cal["threshold"], 4),
                        "n_ink_px": cal["n_ink_px"]}
        res[tname] = r
        edges = (L ^ ndimage.binary_erosion(L, iterations=2)) | (M ^ ndimage.binary_erosion(M, iterations=2))
        v = np.clip(show * 220, 0, 220)
        v[edges] = 255
        write_png(d / f"ov_{a.tag}{tname}.png", v[::2, ::2])
    (d / a.report).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
