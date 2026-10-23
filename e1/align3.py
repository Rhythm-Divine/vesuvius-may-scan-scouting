"""E1 label transfer, third method: global fit from the segment outline, local refinement on CT texture inside the
labelled text block (labels are only there, so that is where the fit must be exact).

1. Global: per-axis scale (+-5% around the canvas ratios) and shift that maximise the IoU of the valid-region masks of
   the 8.64 um render and the 2.401 um render's level 2 (both at 1/8 scale).
2. Local: in the supervision-mask bounding box (+-256 px), refine shift (and a +-1.5% scale) by normalised
   cross-correlation of band-passed mid layers; report the local NCC.
3. Write render_fit.npy (the 8.64 um render resampled onto the 9.604 um label canvas with the fitted transform; Z
   from 8.64 to 9.604 um steps) and labels_fit.npy / mask_fit.npy, plus zoomed overlays for a visual check.
Never uses the labels to fit.

Usage: python align3.py --e1 DIR
"""
import os
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import tifffile
import zarr
from scipy import fft, ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import HF, RENDER, SEG, STEM, box4, fetch, fetch_level2, write_png  # noqa: E402

HOME = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
Z_SRC_UM, Z_DST_UM = 8.64, 4 * 2.401


def fit_layer(layer, out_shape, sy, sx, ty=0.0, tx=0.0, order=1):
    """out(i, j) = layer((i - ty) / sy, (j - tx) / sx)."""
    return ndimage.affine_transform(np.asarray(layer, np.float32), [1 / sy, 1 / sx], offset=[-ty / sy, -tx / sx],
                                    output_shape=out_shape, order=order)


def bandpass(a, s1=1.5, s2=12.0):
    a = np.asarray(a, np.float32)
    b = ndimage.gaussian_filter(a, s1) - ndimage.gaussian_filter(a, s2)
    return (b - b.mean()) / (b.std() + 1e-6)


def corr_shift(a, b):
    """Integer (dy, dx) maximising the circular cross-correlation: b[y + dy, x + dx] ~ a[y, x] (same shape)."""
    c = fft.irfft2(fft.rfft2(b, workers=4) * np.conj(fft.rfft2(a, workers=4)), s=a.shape, workers=4)
    iy, ix = (int(v) for v in np.unravel_index(np.argmax(c), c.shape))
    h, w = a.shape
    return (iy if iy <= h // 2 else iy - h), (ix if ix <= w // 2 else ix - w)


def ncc(a, b, v):
    a, b = a[v], b[v]
    if a.size < 500:
        return 0.0
    a = (a - a.mean()) / (a.std() + 1e-6)
    b = (b - b.mean()) / (b.std() + 1e-6)
    return float(np.mean(a * b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", required=True)
    d = Path(ap.parse_args().e1)
    hf_dir = HOME / "data/hf" / SEG
    src = zarr.open(str(RENDER), mode="r")["0"]                 # 31 x 7040 x 5700
    hi = fetch_level2(hf_dir / "render2um_L2_chunks")           # 17 x 6496 x 5312 (9.604 um)
    H, W = hi.shape[1:]
    a_mid = np.asarray(src[src.shape[0] // 2], np.float32)
    b_mid = hi[hi.shape[0] // 2].astype(np.float32)
    sy0, sx0 = H / src.shape[1], W / src.shape[2]

    # 1) global, from outlines at 1/8
    f = 8
    Bv = (b_mid[::f, ::f] > 0).astype(np.float32)
    best = None
    for fy in np.linspace(0.95, 1.05, 21):
        for fx in np.linspace(0.95, 1.05, 21):
            sy, sx = sy0 * fy, sx0 * fx
            Av = (fit_layer(a_mid[::f, ::f] > 0, Bv.shape, sy, sx, order=0) > 0.5).astype(np.float32)
            dy, dx = corr_shift(Av, Bv)                         # maximises the overlap of the two masks
            Avs = np.roll(np.roll(Av, dy, 0), dx, 1)
            iou = float((Avs * Bv).sum() / max(((Avs + Bv) > 0).sum(), 1))
            if best is None or iou > best["iou"]:
                best = {"fy": round(float(fy), 4), "fx": round(float(fx), 4), "sy": sy, "sx": sx,
                        "ty": dy * f, "tx": dx * f, "iou": round(iou, 4)}
    print("global", json.dumps(best), flush=True)

    # 2) local refinement inside the labelled block
    msk = tifffile.imread(fetch(f"{HF}/{SEG}/{STEM}_supervision_mask.tif", hf_dir / "supervision_mask.tif")) > 127
    mask4 = box4(msk)[:H, :W] >= 0.5
    ys, xs = np.nonzero(mask4)
    y0, y1 = max(0, ys.min() - 256), min(H, ys.max() + 256)
    x0, x1 = max(0, xs.min() - 256), min(W, xs.max() + 256)
    Bloc = bandpass(b_mid[y0:y1, x0:x1])
    Bval = b_mid[y0:y1, x0:x1] > 0
    loc = None
    for fs in np.linspace(0.985, 1.015, 7):
        sy, sx = best["sy"] * fs, best["sx"] * fs
        # render the local window directly: shift the transform so output (0, 0) = canvas (y0, x0)
        A = fit_layer(a_mid, (y1 - y0, x1 - x0), sy, sx, ty=best["ty"] - y0, tx=best["tx"] - x0)
        Aloc = bandpass(A)
        dy, dx = corr_shift(Aloc, Bloc)
        if abs(dy) > 64 or abs(dx) > 64:
            dy, dx = 0, 0
        A2 = fit_layer(a_mid, (y1 - y0, x1 - x0), sy, sx, ty=best["ty"] - y0 + dy, tx=best["tx"] - x0 + dx)
        s = ncc(bandpass(A2), Bloc, (A2 > 0) & Bval)
        if loc is None or s > loc["ncc"]:
            loc = {"scale_factor": round(float(fs), 4), "sy": sy, "sx": sx, "ty": best["ty"] + dy, "tx": best["tx"] + dx,
                   "ncc": round(s, 4)}
    # a null for comparison: the same NCC with the texture shifted by 40 px
    A2 = fit_layer(a_mid, (y1 - y0, x1 - x0), loc["sy"], loc["sx"], ty=loc["ty"] - y0 + 40, tx=loc["tx"] - x0 + 40)
    loc["ncc_null_40px"] = round(ncc(bandpass(A2), Bloc, (A2 > 0) & Bval), 4)
    loc["window"] = [int(y0), int(y1), int(x0), int(x1)]
    print("local", json.dumps(loc), flush=True)

    # 3) resample all layers with the local transform onto the label canvas; Z to 9.604 um steps
    sy, sx, ty, tx = loc["sy"], loc["sx"], loc["ty"], loc["tx"]
    nz = src.shape[0]
    oz = int(round(nz * Z_SRC_UM / Z_DST_UM))
    xy = np.empty((nz, H, W), np.uint8)
    for z in range(nz):
        xy[z] = np.clip(np.rint(fit_layer(src[z], (H, W), sy, sx, ty, tx)), 0, 255).astype(np.uint8)
    out = np.empty((oz, H, W), np.uint8)
    for k in range(oz):
        zin = (nz - 1) / 2 + (k - (oz - 1) / 2) * Z_DST_UM / Z_SRC_UM
        z0 = int(np.clip(np.floor(zin), 0, nz - 2))
        w = float(np.clip(zin - z0, 0, 1))
        out[k] = np.rint(xy[z0] * (1 - w) + xy[z0 + 1] * w).astype(np.uint8)
    np.save(d / "render_fit.npy", out)
    lab = tifffile.imread(fetch(f"{HF}/{SEG}/{STEM}_inklabels.tif", hf_dir / "inklabels.tif")) > 127
    labels = box4(lab)[:H, :W] >= 0.5
    np.save(d / "labels_fit.npy", labels)
    np.save(d / "mask_fit.npy", mask4)
    info = {"method": "align3 (outline IoU global + local band-pass NCC)", "global": best, "local": loc,
            "render_fit_shape": list(out.shape), "label_px": int(labels.sum()), "mask_px": int(mask4.sum()),
            "ink_frac_in_mask": round(float(labels[mask4].mean()), 4),
            "ncc": loc["ncc"]}
    (d / "align2.json").write_text(json.dumps(info, indent=1))
    # visual checks in the labelled block: render mid layer (8.64 um scan) and hi-res mid layer, label edges in white
    edges = labels ^ ndimage.binary_erosion(labels, iterations=2)
    for name, img in (("zoom_render.png", out[oz // 2]), ("zoom_hires.png", hi[hi.shape[0] // 2])):
        v = img[y0:y1, x0:x1].astype(np.float32)
        nzv = v[v > 0]
        lo, hi_ = np.percentile(nzv, [1, 99]) if nzv.size else (0, 1)
        v = np.clip((v - lo) / max(hi_ - lo, 1) * 200, 0, 200)
        v[edges[y0:y1, x0:x1]] = 255
        write_png(d / name, v[::2, ::2])


if __name__ == "__main__":
    main()
