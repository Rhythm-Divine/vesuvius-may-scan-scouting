"""E1 label transfer, fifth step: a dense displacement field from align4's tile matches.

align4 found the matching depth (render layer 21 ~ hires layer 5, z ~ 28) and 160-173 tiles whose NCC beats the
null's 99th percentile, but their shifts leave 8.5 px RMS around the best affine field: the two segments' flattenings
differ non-rigidly. Here, per band:
1. drop tiles that disagree with the median of their voting neighbours (5 x 5 grid) by more than 6 px;
2. field = robust affine + Gaussian-weighted (sigma = 1 grid step) interpolation of the residuals;
3. leave-one-out: predict each kept tile from the others; the RMS of that error is the gate (<= 4 px; letter strokes
   are ~50-80 px wide at 9.6 um);
4. sample the field on the score crop (render_fit_win.json) and save field_<band>.npz (dy, dx: label-canvas pixel =
   render-canvas pixel + (dy, dx)), and checker_field.png for the coarse band.
Never uses labels or predictions.

Usage: python align5.py --e1 DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align3 import Z_DST_UM, Z_SRC_UM  # noqa: E402
from align4 import BANDS, STRIDE, TILE, TSEARCH, checker, prep, robust_affine  # noqa: E402
from prepare import HOME, SEG, fetch_level2, write_png  # noqa: E402

SIGMA, OUTLIER_PX, GATE_LOO_PX = 1.0, 6.0, 4.0


def smooth_residual(gy, gx, R, W, sigma, skip=None):
    """Normalised Gaussian interpolation on the tile grid: sum(w * r * k) / sum(w * k); `skip` removes one tile."""
    Wm = W.copy()
    if skip is not None:
        Wm[skip] = 0
    num = np.stack([ndimage.gaussian_filter(R[..., c] * Wm, sigma, mode="constant") for c in range(2)], -1)
    den = ndimage.gaussian_filter(Wm, sigma, mode="constant")[..., None]
    return np.where(den > 1e-3, num / np.maximum(den, 1e-12), 0.0), den[..., 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", required=True)
    d = Path(ap.parse_args().e1)
    a4 = json.loads((d / "align4.json").read_text())
    wy0, wy1, wx0, wx1 = a4["window"]
    Y0, Y1, X0, X1 = json.loads((d / "render_fit_win.json").read_text())["crop"]
    out = {"sigma_grid": SIGMA, "outlier_px": OUTLIER_PX, "gate_loo_px": GATE_LOO_PX, "bands": {}}
    for band, r in a4["bands"].items():
        thr = r["null99_ncc"]
        tiles = r["tiles"]
        ys = sorted({t["y"] for t in tiles})
        xs = sorted({t["x"] for t in tiles})
        # tile centres sit on TSEARCH + TILE / 2 + k * STRIDE
        iy = {y: (y - TSEARCH - TILE // 2) // STRIDE for y in ys}
        ix = {x: (x - TSEARCH - TILE // 2) // STRIDE for x in xs}
        ny, nx = max(iy.values()) + 1, max(ix.values()) + 1
        S = np.full((ny, nx, 2), np.nan)
        for t in tiles:
            if t["ncc"] > thr:
                S[iy[t["y"]], ix[t["x"]]] = t["s"]
        # 1) neighbour-consistency outliers
        vote = ~np.isnan(S[..., 0])
        clean = vote.copy()
        for j, i in zip(*np.nonzero(vote)):
            nb = S[max(0, j - 2):j + 3, max(0, i - 2):i + 3].reshape(-1, 2)
            nb = nb[~np.isnan(nb[:, 0])]
            if len(nb) >= 4 and np.linalg.norm(S[j, i] - np.median(nb, axis=0)) > OUTLIER_PX:
                clean[j, i] = False
        gy = TSEARCH + TILE // 2 + STRIDE * np.arange(ny)
        gx = TSEARCH + TILE // 2 + STRIDE * np.arange(nx)
        J, I = np.nonzero(clean)
        P = np.c_[gy[J], gx[I]].astype(np.float64)
        coef, keep, _ = robust_affine(P, S[J, I])
        GY, GX = np.meshgrid(gy, gx, indexing="ij")
        aff = np.stack([coef[0, c] + coef[1, c] * GY + coef[2, c] * GX for c in range(2)], -1)
        R = np.nan_to_num(S - aff)
        W = clean.astype(np.float64)
        res_s, den = smooth_residual(gy, gx, R, W, SIGMA)
        # 3) leave-one-out
        loo = []
        for j, i in zip(J, I):
            rs, _ = smooth_residual(gy, gx, R, W, SIGMA, skip=(j, i))
            loo.append(float(np.linalg.norm(aff[j, i] + rs[j, i] - S[j, i])))
        loo = np.array(loo)
        aff_err = np.linalg.norm(aff[J, I] - S[J, I], axis=1)
        info = {"votes": int(vote.sum()), "kept": int(clean.sum()), "affine_rms_px": round(float(np.sqrt(np.mean(
            aff_err ** 2))), 2), "loo_rms_px": round(float(np.sqrt(np.mean(loo ** 2))), 2), "loo_p90_px": round(float(
            np.percentile(loo, 90)), 2), "field_range_dy": [round(float(v), 1) for v in np.percentile(
            (aff + res_s)[clean][:, 0], [1, 99])], "field_range_dx": [round(float(v), 1) for v in np.percentile(
            (aff + res_s)[clean][:, 1], [1, 99])]}
        info["gate_pass"] = bool(info["loo_rms_px"] <= GATE_LOO_PX and info["kept"] >= 30)
        # 4) dense field on the score crop (window coordinates -> grid coordinates; nearest beyond the grid)
        field = aff + res_s
        yy, xx = np.indices((Y1 - Y0, X1 - X0), dtype=np.float32)
        gyc = (yy + (Y0 - wy0) - gy[0]) / STRIDE
        gxc = (xx + (X0 - wx0) - gx[0]) / STRIDE
        dense = [ndimage.map_coordinates(field[..., c], [gyc, gxc], order=1, mode="nearest").astype(np.float32)
                 for c in range(2)]
        np.savez_compressed(d / f"field_{band}.npz", dy=dense[0], dx=dense[1], crop=np.array([Y0, Y1, X0, X1]))
        out["bands"][band] = info
        print(band, json.dumps(info), flush=True)
        if band == "coarse":   # visual check at the matched depth: render_fit layer for 8.64 um layer za, hires zb
            za, zb = r["depth_best"]["za"], r["depth_best"]["zb"]
            win = np.load(d / "render_fit_win.npy", mmap_mode="r")
            k = int(round((win.shape[0] - 1) / 2 + (za - 15) * Z_SRC_UM / Z_DST_UM))
            A = np.asarray(win[k], np.float32)
            B = fetch_level2(HOME / "data/hf" / SEG / "render2um_L2_chunks")[zb, Y0:Y1, X0:X1].astype(np.float32)
            valid = (A > 0) & (B > 0)
            Aw = ndimage.map_coordinates(A, [yy - dense[0], xx - dense[1]], order=1)   # hires[p] ~ render[p - s]
            s1, s2 = BANDS["coarse"]
            for name, img in (("checker_field.png", Aw), ("checker_align3.png", A)):
                write_png(d / name, checker(prep(img, valid, s1, s2), prep(B, valid, s1, s2))[::2, ::2])
    (d / "align5.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
