"""E1 label transfer, fourth step: depth correspondence and a local displacement field in the labelled text block.

align3 matches the segment outlines (IoU 0.986) but leaves the fine CT texture barely correlated (NCC 0.023), so
the label transfer is unproven. Inside align3's window (supervision-mask bbox +-256 px), starting from its transform:
1. Depth: NCC of band-passed layers, best shift within +-48 px, for every pair of an 8.64 um render layer (resampled
   with the align3 transform) and a 2.401 um render level-2 layer, at a fine and a coarse band. Each peak is scored
   against the correlation at far shifts (z-score), so a match has to beat chance, not just be positive.
2. Tiles: 256 px tiles (stride 128) of the best layer pair (each averaged with its depth neighbours); per tile the
   NCC peak within +-32 px. The null is the same tiles matched against texture 400 px away; tiles above the null's
   99th percentile vote.
3. Trimmed least-squares affine fit of the voting tiles' shifts; gate on inliers and residuals.
Shift convention everywhere: s with hires[p + s] ~ render[p], i.e. label-canvas pixel = render-canvas pixel + s.
Writes align4.json and checker_before.png / checker_after.png (alternating squares of the two scans). Never uses
labels or predictions to fit.

Usage: python align4.py --e1 DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import zarr
from scipy import fft, ndimage, signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align3 import fit_layer  # noqa: E402
from prepare import HOME, RENDER, SEG, fetch_level2, write_png  # noqa: E402

BANDS = {"fine": (1.5, 12.0), "coarse": (3.0, 24.0)}
SEARCH, FAR, PAD = 48, (100, 300), 320
TILE, STRIDE, TSEARCH, NULL_OFF = 256, 128, 32, 400
GATE = {"min_inliers": 12, "min_inlier_frac": 0.2, "max_rms_px": 3.0}


def prep(layer, valid, s1, s2):
    """Band-pass, normalise inside `valid`, zero outside (the papyrus edge must not drive the match)."""
    a = np.asarray(layer, np.float32)
    b = ndimage.gaussian_filter(a, s1) - ndimage.gaussian_filter(a, s2)
    v = b[valid]
    b = (b - v.mean()) / (v.std() + 1e-6)
    b[~valid] = 0
    return b


class Correlator:
    """c[s] = sum_x a[x] b[x + s] / n on zero-padded images (no wrap-around up to PAD px)."""

    def __init__(self, shape, n_valid):
        self.shape = tuple(fft.next_fast_len(s + PAD, real=True) for s in shape)
        self.n = n_valid
        sy, sx = (np.where(np.arange(m) <= m // 2, np.arange(m), np.arange(m) - m) for m in self.shape)
        self.sy, self.sx = sy, sx
        cheb = np.maximum(np.abs(sy)[:, None], np.abs(sx)[None, :])
        self.near = cheb <= SEARCH
        self.far = (cheb >= FAR[0]) & (cheb <= FAR[1])

    def f(self, img):
        return fft.rfft2(img, s=self.shape, workers=4)

    def peak(self, fa, fb):
        c = fft.irfft2(fb * np.conj(fa), s=self.shape, workers=4) / self.n
        iy, ix = (int(v) for v in np.unravel_index(np.argmax(np.where(self.near, c, -np.inf)), c.shape))
        far = c[self.far]
        return {"ncc": round(float(c[iy, ix]), 4), "z": round(float((c[iy, ix] - far.mean()) / (far.std() + 1e-12)), 2),
                "s": [int(self.sy[iy]), int(self.sx[ix])]}


def tile_ncc(A, B, y, x, ay=None, ax=None):
    """Peak NCC of B[y:y+T, x:x+T] against A around (ay, ax) (default: the same place), within +-TSEARCH px.
    Returns (peak, s) with B[p + s] ~ A[p] for the matched content (s relative to (ay, ax))."""
    T, S = TILE, TSEARCH
    ay, ax = (y if ay is None else ay), (x if ax is None else ax)
    b = B[y:y + T, x:x + T].astype(np.float64)
    a = A[ay - S:ay + T + S, ax - S:ax + T + S].astype(np.float64)
    bz = b - b.mean()
    num = signal.fftconvolve(a, bz[::-1, ::-1], mode="valid")
    ii = np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    i2 = np.pad((a * a).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    box = lambda m: m[T:, T:] - m[:-T, T:] - m[T:, :-T] + m[:-T, :-T]  # noqa: E731
    sa, sa2 = box(ii), box(i2)
    c = num / (np.sqrt(np.maximum(sa2 - sa * sa / (T * T), 1e-9)) * np.sqrt((bz * bz).sum()) + 1e-12)
    ky, kx = np.unravel_index(np.argmax(c), c.shape)
    return float(c[ky, kx]), [int(S - ky), int(S - kx)]   # A[p + k - S] ~ B[p]  =>  B[q + S - k] ~ A[q]


def robust_affine(P, S):
    """s = [1, y, x] @ coef per axis; trims points beyond max(median + 3 * 1.4826 * MAD, 2 px), 5 rounds."""
    X = np.c_[np.ones(len(P)), P]
    keep = np.ones(len(P), bool)
    for _ in range(5):
        coef, *_ = np.linalg.lstsq(X[keep], S[keep], rcond=None)
        r = np.linalg.norm(S - X @ coef, axis=1)
        med = np.median(r[keep])
        keep = r <= max(med + 3 * 1.4826 * np.median(np.abs(r[keep] - med)), 2.0)
    return coef, keep, r


def checker(a, b, sq=96):
    """Alternating squares: a where (i // sq + j // sq) is even, b elsewhere; both shown at +-2.5 sigma."""
    yy, xx = np.indices(a.shape)
    m = ((yy // sq + xx // sq) % 2) == 0
    v = np.where(m, a, b)
    return np.clip((v + 2.5) / 5 * 255, 0, 255)


def self_test(B, valid):
    """The sign convention: A[x] = B[x + s0] must come back as s0 from both estimators."""
    s0 = (5, -7)
    A = np.roll(B, (-s0[0], -s0[1]), axis=(0, 1))
    cor = Correlator(B.shape, int(valid.sum()))
    got = cor.peak(cor.f(A), cor.f(B))["s"]
    ys, xs = np.nonzero(valid)
    y = int(np.clip(np.median(ys) - TILE // 2, TSEARCH, B.shape[0] - TILE - TSEARCH))
    x = int(np.clip(np.median(xs) - TILE // 2, TSEARCH, B.shape[1] - TILE - TSEARCH))
    got_t = tile_ncc(A, B, y, x)[1]
    assert got == list(s0) and got_t == list(s0), (got, got_t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1", required=True)
    d = Path(ap.parse_args().e1)
    a3 = json.loads((d / "align2.json").read_text())["local"]
    y0, y1, x0, x1 = a3["window"]
    sy, sx, ty, tx = a3["sy"], a3["sx"], a3["ty"], a3["tx"]
    h, w = y1 - y0, x1 - x0

    # the 8.64 um render, every layer, resampled into the window with the align3 transform (read only what maps in)
    src = zarr.open(str(RENDER), mode="r")["0"]
    ys0 = max(0, int((y0 - ty) / sy) - 16)
    ys1 = min(src.shape[1], int((y1 - ty) / sy) + 16)
    xs0 = max(0, int((x0 - tx) / sx) - 16)
    xs1 = min(src.shape[2], int((x1 - tx) / sx) + 16)
    sub = np.asarray(src[:, ys0:ys1, xs0:xs1])
    A_raw = np.stack([np.clip(np.rint(fit_layer(sub[z], (h, w), sy, sx, ty - y0 + ys0 * sy, tx - x0 + xs0 * sx)),
                              0, 255).astype(np.uint8) for z in range(sub.shape[0])])
    del sub
    B_raw = fetch_level2(HOME / "data/hf" / SEG / "render2um_L2_chunks")[:, y0:y1, x0:x1].copy()
    za_mid, zb_mid = A_raw.shape[0] // 2, B_raw.shape[0] // 2
    print("window", [y0, y1, x0, x1], "render layers", A_raw.shape[0], "hires layers", B_raw.shape[0], flush=True)

    out = {"window": [y0, y1, x0, x1], "align3": a3, "bands": {}}
    for band, (s1, s2) in BANDS.items():
        valid = ndimage.distance_transform_edt((A_raw[za_mid] > 0) & (B_raw[zb_mid] > 0)) > 2 * s2
        A = [prep(l, valid, s1, s2) for l in A_raw]
        B = [prep(l, valid, s1, s2) for l in B_raw]
        if band == "fine":
            self_test(B[zb_mid], valid)
        cor = Correlator((h, w), int(valid.sum()))
        FA, FB = [cor.f(l) for l in A], [cor.f(l) for l in B]
        Z = np.zeros((len(A), len(B)), np.float32)
        best = None
        for i in range(len(A)):
            for j in range(len(B)):
                p = cor.peak(FA[i], FB[j])
                Z[i, j] = p["z"]
                if best is None or p["z"] > best["z"]:
                    best = {**p, "za": i, "zb": j}
        mid = {**cor.peak(FA[za_mid], FB[zb_mid]), "za": za_mid, "zb": zb_mid}
        del FA, FB
        print(band, "depth best", json.dumps(best), "| mid pair", json.dumps(mid), flush=True)

        # tiles on the best pair, each averaged with its depth neighbours
        ia = range(max(0, best["za"] - 1), min(len(A), best["za"] + 2))
        ib = range(max(0, best["zb"] - 1), min(len(B), best["zb"] + 2))
        Aa = np.mean([A[i] for i in ia], axis=0)
        Bb = np.mean([B[j] for j in ib], axis=0)
        Aa = np.where(valid, Aa / (Aa[valid].std() + 1e-6), 0).astype(np.float32)
        Bb = np.where(valid, Bb / (Bb[valid].std() + 1e-6), 0).astype(np.float32)
        tiles, nulls = [], []
        for ty_ in range(TSEARCH, h - TILE - TSEARCH + 1, STRIDE):
            for tx_ in range(TSEARCH, w - TILE - TSEARCH + 1, STRIDE):
                if valid[ty_ - TSEARCH:ty_ + TILE + TSEARCH, tx_ - TSEARCH:tx_ + TILE + TSEARCH].mean() < 0.9:
                    continue
                pk, s = tile_ncc(Aa, Bb, ty_, tx_)
                tiles.append({"y": ty_ + TILE // 2, "x": tx_ + TILE // 2, "ncc": round(pk, 4), "s": s})
                for ox in (NULL_OFF, -NULL_OFF):   # the null: the same tile against texture 400 px away
                    ax_ = tx_ + ox
                    if TSEARCH <= ax_ <= w - TILE - TSEARCH and \
                            valid[ty_ - TSEARCH:ty_ + TILE + TSEARCH, ax_ - TSEARCH:ax_ + TILE + TSEARCH].mean() >= 0.9:
                        nulls.append(tile_ncc(Aa, Bb, ty_, tx_, ty_, ax_)[0])
                        break
        null99 = float(np.percentile(nulls, 99)) if nulls else float("nan")
        vote = [t for t in tiles if t["ncc"] > null99]
        res = {"depth_best": best, "depth_mid_pair": mid, "depth_z_matrix_max_by_render_layer":
               [round(float(v), 2) for v in Z.max(axis=1)], "tiles_evaluated": len(tiles), "null_tiles": len(nulls),
               "null99_ncc": round(null99, 4), "tile_ncc_median": round(float(np.median([t["ncc"] for t in tiles])), 4)
               if tiles else None, "votes": len(vote)}
        if len(vote) >= 3:
            P = np.array([[t["y"], t["x"]] for t in vote], np.float64)
            S = np.array([t["s"] for t in vote], np.float64)
            coef, keep, r = robust_affine(P, S)
            rms = float(np.sqrt(np.mean(r[keep] ** 2)))
            res["affine"] = {"coef_window_coords": coef.round(6).tolist(), "inliers": int(keep.sum()),
                             "rms_px": round(rms, 2), "shift_at_centre": (np.array([1, h / 2, w / 2]) @ coef).round(2)
                             .tolist()}
            res["gate_pass"] = bool(keep.sum() >= GATE["min_inliers"] and keep.sum() >= GATE["min_inlier_frac"] *
                                    len(tiles) and rms <= GATE["max_rms_px"])
        else:
            res["gate_pass"] = False
        res["tiles"] = tiles
        out["bands"][band] = res
        print(band, json.dumps({k: v for k, v in res.items() if k != "tiles"}), flush=True)

        if band == "coarse":   # visual check on the coarse band: before (align3 only) and after (affine field)
            write_png(d / "checker_before.png", checker(Aa, Bb)[::2, ::2])
            if "affine" in res:
                coef = np.array(res["affine"]["coef_window_coords"])
                yy, xx = np.indices((h, w), dtype=np.float32)
                dy = coef[0, 0] + coef[1, 0] * yy + coef[2, 0] * xx
                dx = coef[0, 1] + coef[1, 1] * yy + coef[2, 1] * xx
                Aw = ndimage.map_coordinates(Aa, [yy - dy, xx - dx], order=1)   # hires[p] ~ render[p - s]
                write_png(d / "checker_after.png", checker(Aw, Bb)[::2, ::2])
    out["gate"] = GATE
    (d / "align4.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
