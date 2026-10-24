"""S2 readout of reader-v2 for one S1 mesh (prereg/M1-survey-S2.md).

The S1 readout (m1/readout.py), with reader-v2's window-averaged map per direction (pred_r2_<dir>.png from
m2/r2_combine.py) in place of Hecate's five-window ensemble, reader-v2's own threshold T2 and control background (both
from E1b), and one more number per direction: the share of reader-v2's >= T2 pixels that lie within 0.3 mm (31 px) of
Hecate's >= T pixels on the same mesh (agreement). Same valid area: render centre layer > 0, mesh interior, cells within
8 of a self-crossing contact excluded, S1 crop.
Writes readout_r2.json, ens_r2_<dir>.png and thr_r2_<dir>.png next to the maps.
Usage: python m2/readout_r2.py --mesh MESH --render9 R9.npy --hecate-dir HDIR --pred-dir DIR --t2 T2 --bg BG
       --selfcross SC.json --crop Y0 Y1 X0 X1
"""
import argparse
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))
from prepare import write_png  # noqa: E402
from readout import PX_UM, T, interior_mask  # noqa: E402
from sweep.readout import ReadoutRules, extract_candidates  # noqa: E402

AGREE_PX = 31   # 0.3 mm at 9.604 um


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--render9", required=True)
    ap.add_argument("--hecate-dir", required=True)
    ap.add_argument("--pred-dir", required=True)
    ap.add_argument("--t2", type=float, required=True)
    ap.add_argument("--bg", type=float, required=True)
    ap.add_argument("--selfcross", required=True)
    ap.add_argument("--crop", type=int, nargs=4, required=True, metavar=("Y0", "Y1", "X0", "X1"))
    a = ap.parse_args()
    d, h = Path(a.pred_dir), Path(a.hecate_dir)
    render = np.load(a.render9, mmap_mode="r")
    y0, y1, x0, x1 = a.crop
    valid = ((np.asarray(render[21]) > 0) & interior_mask(a.mesh, render.shape[1:], a.selfcross, 8))[y0:y1, x0:x1]
    rules = ReadoutRules(threshold=a.t2, px_um=PX_UM)
    res = {"prereg": "prereg/M1-survey-S2.md", "model": "reader-v2-step040000", "threshold": a.t2,
           "valid_cm2": round(float(valid.sum()) * (PX_UM * 1e-4) ** 2, 3), "crop": a.crop, "exclude_contacts_cells": 8,
           "control_background_frac_ge_T": a.bg, "hecate_threshold": T}
    edge = valid ^ ndimage.binary_erosion(valid, iterations=3)
    for dr in ("fwd", "rev"):
        ens = imagecodecs.png_decode((d / f"pred_r2_{dr}.png").read_bytes()).astype(np.float32) / 255
        hec = np.mean([imagecodecs.png_decode((h / f"pred_{dr}_{k}.png").read_bytes()).astype(np.float32) / 255
                       for k in (-2, -1, 0, 1, 2)], axis=0)
        r = extract_candidates(ens, valid, rules)
        v = ens[valid]
        r2 = (ens >= a.t2) & valid
        near_h = ndimage.binary_dilation((hec >= T) & valid, iterations=AGREE_PX)
        r["stats_valid"] = {"mean": round(float(v.mean()), 4), "p99": round(float(np.percentile(v, 99)), 4),
                            "frac_ge_T": round(float((v >= a.t2).mean()), 4), "std": round(float(v.std()), 4),
                            "agree_with_hecate": round(float(near_h[r2].mean()), 4) if r2.any() else None}
        res[dr] = r
        img = np.clip(ens * 230, 0, 230)
        img[edge] = 128
        write_png(d / f"ens_r2_{dr}.png", img[::2, ::2])
        thr = np.where(valid, np.where(ens >= a.t2, 255, 60), 0).astype(np.float32)
        write_png(d / f"thr_r2_{dr}.png", thr[::2, ::2])
        print(dr, json.dumps(r["counts"]), "candidates", len(r["candidates"]), json.dumps(r["stats_valid"]), flush=True)
    (d / "readout_r2.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
