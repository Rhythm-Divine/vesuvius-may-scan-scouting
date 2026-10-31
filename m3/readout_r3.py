"""S3 readout of reader-v2 for one surface (prereg/M1-survey-S3.md).

The S2 readout (m2/readout_r2.py) applied to each of S3's maps, with T2 and S1's valid area (render centre layer > 0,
mesh interior, cells within 8 of a self-crossing contact excluded, the readout window in crop.json):
- a new surface: near_<dir> (the c/p2/m2 mean, S2's read), p6_<dir> and m6_<dir> (the deeper windows);
- an S1 surface (already read by S2): p6_<dir> and m6_<dir> only.
Agreement (the share of a map's >= T2 pixels within 0.3 mm of Hecate's >= T pixels on the same mesh, Hecate being the
per-pixel mean of five 16-layer windows at the matching depth: k = -2..+2 for near, +3..+7 for p6, -7..-3 for m6) is
given where those Hecate maps exist: S1's own for an S1 surface's near read, otherwise a Hecate check's
(m3/hecate_confirm.sh) in data/m3/<SAMPLE>/<MESH>/hecate. Otherwise it is null.
Writes readout_r3.json, ens_r3_<map>.png and thr_r3_<map>.png (half resolution) next to the maps.
Usage: python m3/readout_r3.py --sample SAMPLE --mesh MESH --t2 T2 [--kind new|s1] [--dir DIR]
"""
import argparse
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "e1"))
sys.path.insert(0, str(ROOT / "m1"))
from prepare import write_png  # noqa: E402
from readout import PX_UM, T, interior_mask  # noqa: E402
from sweep.readout import ReadoutRules, extract_candidates  # noqa: E402

AGREE_PX = 31   # 0.3 mm at 9.604 um
HECATE_K = {"near": (-2, -1, 0, 1, 2), "p6": (3, 4, 5, 6, 7), "m6": (-7, -6, -5, -4, -3)}
SUFFIX = {"near": "", "p6": "_p6", "m6": "_m6"}


def hecate_mean(dirs, dr, fam):
    for h in dirs:
        files = [h / f"pred_{dr}_{k}.png" for k in HECATE_K[fam]]
        if all(f.exists() for f in files):
            return np.mean([imagecodecs.png_decode(f.read_bytes()).astype(np.float32) / 255 for f in files], axis=0), h
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--t2", type=float, required=True)
    ap.add_argument("--kind", choices=("new", "s1"))
    ap.add_argument("--dir")
    ap.add_argument("--hecate-dir", action="append", default=[], help="further folder of Hecate maps (controls)")
    a = ap.parse_args()
    s, m = a.sample, a.mesh
    d = Path(a.dir) if a.dir else ROOT / f"data/m3/{s}/{m}"
    kind = a.kind or ("s1" if (ROOT / f"data/s2/{s}/{m}/pred_r2_fwd.png").exists() else "new")
    fams = ("near", "p6", "m6") if kind == "new" else ("p6", "m6")
    rd = ROOT / f"data/m1/{s}/render"
    render = np.load(rd / f"{m}_9p6.npy", mmap_mode="r")
    crop = json.loads((d / "crop.json").read_text())
    y0, y1, x0, x1 = crop["crop"]
    valid = ((np.asarray(render[21]) > 0)
             & interior_mask(ROOT / f"data/m1/{s}/meshes/{m}", render.shape[1:], rd / f"{m}_selfcross.json", 8))
    valid = valid[y0:y1, x0:x1]
    rules = ReadoutRules(threshold=a.t2, px_um=PX_UM)
    res = {"prereg": "prereg/M1-survey-S3.md", "model": "reader-v2-step040000", "threshold": a.t2, "kind": kind,
           "valid_cm2": round(float(valid.sum()) * (PX_UM * 1e-4) ** 2, 3), "valid_cm2_crop_json": crop.get("valid_cm2"),
           "crop": [y0, y1, x0, x1], "exclude_contacts_cells": 8, "hecate_threshold": T, "maps": {}}
    edge = valid ^ ndimage.binary_erosion(valid, iterations=3)
    hdirs = ([d / "hecate"] + [Path(h) for h in a.hecate_dir]
             + ([ROOT / f"data/m1/{s}/hecate/{m}"] if kind == "s1" else []))
    for fam in fams:
        for dr in ("fwd", "rev"):
            p = d / f"pred_r3_{dr}{SUFFIX[fam]}.png"
            ens = imagecodecs.png_decode(p.read_bytes()).astype(np.float32) / 255
            r = extract_candidates(ens, valid, rules)
            v = ens[valid]
            r2 = (ens >= a.t2) & valid
            hec, hdir = hecate_mean(hdirs, dr, fam)
            agree = None
            if hec is not None and r2.any():
                near_h = ndimage.binary_dilation((hec >= T) & valid, iterations=AGREE_PX)
                agree = round(float(near_h[r2].mean()), 4)
            r["stats_valid"] = {"mean": round(float(v.mean()), 4), "p99": round(float(np.percentile(v, 99)), 4),
                                "frac_ge_T": round(float((v >= a.t2).mean()), 4), "std": round(float(v.std()), 4),
                                "agree_with_hecate": agree,
                                "hecate_dir": str(hdir) if hdir is not None else None}
            name = f"{fam}_{dr}"
            res["maps"][name] = r
            img = np.clip(ens * 230, 0, 230)
            img[edge] = 128
            write_png(d / f"ens_r3_{name}.png", img[::2, ::2])
            thr = np.where(valid, np.where(ens >= a.t2, 255, 60), 0).astype(np.float32)
            write_png(d / f"thr_r3_{name}.png", thr[::2, ::2])
            print(name, json.dumps(r["counts"]), "candidates", len(r["candidates"]), json.dumps(r["stats_valid"]),
                  flush=True)
    (d / "readout_r3.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
