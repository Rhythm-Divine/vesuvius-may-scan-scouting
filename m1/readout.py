"""M1 readout for one PHerc0175B mesh, exactly as pre-registered (prereg/PHerc0175B-m1.md).

Per direction (fwd, rev): the per-pixel mean of the five window probability maps (k = -2..+2), then
sweep.readout.extract_candidates with T = 0.445 on valid = render centre layer > 0 AND the mesh interior (>= 16 grid
cells from the mesh boundary, where vc_tifxyz_selfcross found no contacts). Writes readout.json and, for looking,
ens_<dir>.png (half resolution; the valid outline in mid grey) and the T-thresholded map thr_<dir>.png.

With --exclude-contacts R (prereg/PHerc0175B-m1-b.md), grid cells within R cells of any vc_tifxyz_selfcross contact
(from --selfcross) are also excluded. With --crop Y0 Y1 X0 X1, the prediction maps cover that window of the render
canvas (the mask is built on the full canvas and cropped). The area >= T is reported next to the control background's
1.2% (E1b).

Usage: python readout.py --mesh MESH_DIR --render9 RENDER_9P6.npy --pred-dir DIR --out readout.json
       [--selfcross SELFCROSS.json --exclude-contacts 8] [--crop Y0 Y1 X0 X1]
"""
import argparse
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from prepare import DST_UM, SRC_UM, write_png  # noqa: E402
from sweep.readout import ReadoutRules, extract_candidates  # noqa: E402

T, PX_UM, INTERIOR_CELLS, CELL_PX = 0.445, 9.604, 16, 20
CONTROL_BG_FRAC_GE_T = 0.012   # E1b: share of non-ink supervision pixels >= T in the -2..+2 ensemble


def interior_mask(mesh_dir, shape, selfcross=None, exclude_r=0):
    """Render pixels (9.604 um grid) whose mesh grid cell is >= INTERIOR_CELLS cells from the mesh boundary and, with
    exclude_r > 0, more than exclude_r cells from every self-crossing contact."""
    x = tifffile.imread(Path(mesh_dir) / "x.tif")
    dist = ndimage.distance_transform_edt(x != -1)
    keep = dist >= INTERIOR_CELLS
    if exclude_r > 0:
        hit = np.zeros(x.shape, bool)
        for c in json.loads(Path(selfcross).read_text())["census"]:
            for t in c.get("transverse_contacts", []):
                for q in (t["quad1"], t["quad2"]):
                    if 0 <= int(q[0]) < x.shape[0] and 0 <= int(q[1]) < x.shape[1]:
                        hit[int(q[0]), int(q[1])] = True
        keep &= ~ndimage.binary_dilation(hit, iterations=exclude_r)
    f = SRC_UM / DST_UM
    rows = np.minimum((np.arange(shape[0]) / f / CELL_PX).astype(int), dist.shape[0] - 1)
    cols = np.minimum((np.arange(shape[1]) / f / CELL_PX).astype(int), dist.shape[1] - 1)
    return keep[np.ix_(rows, cols)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--render9", required=True)
    ap.add_argument("--pred-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--selfcross")
    ap.add_argument("--exclude-contacts", type=int, default=0)
    ap.add_argument("--crop", type=int, nargs=4, metavar=("Y0", "Y1", "X0", "X1"))
    a = ap.parse_args()
    d = Path(a.pred_dir)
    render = np.load(a.render9, mmap_mode="r")
    valid = (np.asarray(render[21]) > 0) & interior_mask(a.mesh, render.shape[1:], a.selfcross, a.exclude_contacts)
    if a.crop:
        y0, y1, x0, x1 = a.crop
        valid = valid[y0:y1, x0:x1]
    rules = ReadoutRules(threshold=T, px_um=PX_UM)
    res = {"prereg": "prereg/PHerc0175B-m1-b.md" if a.exclude_contacts else "prereg/PHerc0175B-m1.md", "threshold": T,
           "valid_cm2": round(float(valid.sum()) * (PX_UM * 1e-4) ** 2, 3), "crop": a.crop,
           "exclude_contacts_cells": a.exclude_contacts, "control_background_frac_ge_T": CONTROL_BG_FRAC_GE_T}
    edge = valid ^ ndimage.binary_erosion(valid, iterations=3)
    for dr in ("fwd", "rev"):
        maps = [imagecodecs.png_decode((d / f"pred_{dr}_{k}.png").read_bytes()).astype(np.float32) / 255
                for k in (-2, -1, 0, 1, 2) if (d / f"pred_{dr}_{k}.png").exists()]
        if len(maps) < 5:
            res[dr] = {"error": f"{len(maps)} of 5 window maps present"}
            continue
        ens = np.mean(maps, axis=0)
        r = extract_candidates(ens, valid, rules)
        v = ens[valid]
        r["stats_valid"] = {"mean": round(float(v.mean()), 4), "p99": round(float(np.percentile(v, 99)), 4),
                            "frac_ge_T": round(float((v >= T).mean()), 4), "std": round(float(v.std()), 4)}
        res[dr] = r
        img = np.clip(ens * 230, 0, 230)
        img[edge] = 128
        write_png(d / f"ens_{dr}.png", img[::2, ::2])
        thr = np.where(valid, np.where(ens >= T, 255, 60), 0).astype(np.float32)
        write_png(d / f"thr_{dr}.png", thr[::2, ::2])
        print(dr, json.dumps(r["counts"]), "candidates", len(r["candidates"]), json.dumps(r["stats_valid"]), flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
