"""E1b: CT-only registration of the PHerc0009B 8.64 um render to the 2.401 um render of the SAME mesh (open data).

The open-data segment folder holds both surface volumes of one mesh (8.64 um: 31 x 7040 x 5700; 2.401 um:
109 x 25360 x 20520, ratio 3.60 = 8.64 / 2.401) and the organisers' labels on the 2.401 um canvas (2026-09-18:
ink, supervision, validation). So render.npy (8.64 -> 9.604 um, prepare.py) and the labels' level 2 (9.604 um)
should agree up to a small shift. This measures it from CT texture only:
1. fetch the 2.401 um level-2 chunks (all 109 layers, uncompressed 109 x 128 x 128) covering the supervision bbox
   +-256 px, and average them into 27 slabs of 4 layers (9.604 um);
2. depth: band-passed NCC (best shift within +-48 px, z-scored against far shifts) for every render layer x slab;
3. tiles at the best pair (align4): per-tile shift and NCC against a 400 px-displaced null; median shift, spread,
   and the per-tile best render layer for the centre slab (depth offset from the render centre).
Writes register.json. Never uses labels or predictions.

Usage: python register.py --out DIR
"""
import os
import argparse
import concurrent.futures as cf
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import zarr
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e1"))
from align4 import BANDS, NULL_OFF, STRIDE, TILE, TSEARCH, Correlator, prep, tile_ncc  # noqa: E402

HOME = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
SEGB = ("https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0009B/segments/"
        "20250919125754-auto_grown_20250919055754487_inp_hr")
HI = SEGB + "/surface-volumes/2.401um-0.35m-77keV-volume-20250820154339.zarr/2"
LAB = HOME / "data/e1b/labels"


def fetch_hi(y0, y1, x0, x1):
    meta = json.loads(urllib.request.urlopen(HI + "/.zarray", timeout=60).read())
    nz, c = meta["shape"][0], meta["chunks"][1]
    sep = meta.get("dimension_separator", ".")
    out = np.zeros((nz, y1 - y0, x1 - x0), np.uint8)

    def one(k):
        iy, ix = k
        try:
            raw = urllib.request.urlopen(f"{HI}/0{sep}{iy}{sep}{ix}", timeout=300).read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):   # air chunks are omitted
                return
            raise
        blk = np.frombuffer(raw, np.uint8).reshape(nz, c, c)
        ya, xa = iy * c, ix * c
        sy, sx = slice(max(ya, y0), min(ya + c, y1)), slice(max(xa, x0), min(xa + c, x1))
        out[:, sy.start - y0:sy.stop - y0, sx.start - x0:sx.stop - x0] = blk[:, sy.start - ya:sy.stop - ya,
                                                                             sx.start - xa:sx.stop - xa]
    keys = [(iy, ix) for iy in range(y0 // c, -(-y1 // c)) for ix in range(x0 // c, -(-x1 // c))]
    with cf.ThreadPoolExecutor(16) as ex:   # network-bound
        list(ex.map(one, keys))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    d = Path(ap.parse_args().out)
    sup = np.asarray(zarr.open_array(str(LAB / "supervision.zarr/2"), mode="r")[:]) > 127
    render = np.load(HOME / "data/e1/render.npy", mmap_mode="r")
    H, W = min(sup.shape[0], render.shape[1]), min(sup.shape[1], render.shape[2])
    ys, xs = np.nonzero(sup[:H, :W])
    y0, y1 = max(0, int(ys.min()) - 256), min(H, int(ys.max()) + 257)
    x0, x1 = max(0, int(xs.min()) - 256), min(W, int(xs.max()) + 257)
    h, w = y1 - y0, x1 - x0
    hi = fetch_hi(y0, y1, x0, x1)
    slabs = [hi[4 * j:4 * j + 4].mean(axis=0, dtype=np.float32) for j in range(hi.shape[0] // 4)]
    del hi
    A_raw = np.asarray(render[:, y0:y1, x0:x1])
    za_mid, zb_mid = (A_raw.shape[0] - 1) / 2, len(slabs) // 2
    print("window", [y0, y1, x0, x1], "render layers", A_raw.shape[0], "slabs", len(slabs), flush=True)

    s1, s2 = BANDS["coarse"]
    valid = ndimage.distance_transform_edt((A_raw[A_raw.shape[0] // 2] > 0) & (slabs[zb_mid] > 0)) > 2 * s2
    A = [prep(l, valid, s1, s2) for l in A_raw]
    B = [prep(l, valid, s1, s2) for l in slabs]
    cor = Correlator((h, w), int(valid.sum()))
    FA, FB = [cor.f(l) for l in A], [cor.f(l) for l in B]
    best, zmat = None, np.zeros((len(A), len(B)), np.float32)
    for i in range(len(A)):
        for j in range(len(B)):
            p = cor.peak(FA[i], FB[j])
            zmat[i, j] = p["z"]
            if best is None or p["z"] > best["z"]:
                best = {**p, "za": i, "zb": j}
    del FA, FB
    print("depth best", json.dumps(best), flush=True)

    # tiles at the best pair (each averaged with its depth neighbours)
    Aa = np.mean([A[i] for i in range(max(0, best["za"] - 1), min(len(A), best["za"] + 2))], axis=0)
    Bb = np.mean([B[j] for j in range(max(0, best["zb"] - 1), min(len(B), best["zb"] + 2))], axis=0)
    Aa = np.where(valid, Aa / (Aa[valid].std() + 1e-6), 0).astype(np.float32)
    Bb = np.where(valid, Bb / (Bb[valid].std() + 1e-6), 0).astype(np.float32)
    tiles, nulls = [], []
    for ty in range(TSEARCH, h - TILE - TSEARCH + 1, STRIDE):
        for tx in range(TSEARCH, w - TILE - TSEARCH + 1, STRIDE):
            if valid[ty - TSEARCH:ty + TILE + TSEARCH, tx - TSEARCH:tx + TILE + TSEARCH].mean() < 0.9:
                continue
            pk, s = tile_ncc(Aa, Bb, ty, tx)
            # depth at this tile: which render layer best matches the centre slab
            bz = B[zb_mid]
            prof = [tile_ncc(A[i], bz, ty, tx)[0] for i in range(len(A))]
            tiles.append({"y": ty + TILE // 2, "x": tx + TILE // 2, "ncc": round(pk, 4), "s": s,
                          "best_layer_for_centre_slab": int(np.argmax(prof)), "depth_ncc": round(float(max(prof)), 4)})
            for ox in (NULL_OFF, -NULL_OFF):
                ax = tx + ox
                if TSEARCH <= ax <= w - TILE - TSEARCH and \
                        valid[ty - TSEARCH:ty + TILE + TSEARCH, ax - TSEARCH:ax + TILE + TSEARCH].mean() >= 0.9:
                    nulls.append(tile_ncc(Aa, Bb, ty, tx, ty, ax)[0])
                    break
    null99 = float(np.percentile(nulls, 99)) if nulls else float("nan")
    vote = [t for t in tiles if t["ncc"] > null99]
    S = np.array([t["s"] for t in vote], np.float64) if vote else np.zeros((0, 2))
    med = np.median(S, axis=0) if len(S) else np.array([np.nan, np.nan])
    spread = np.median(np.abs(S - med), axis=0) * 1.4826 if len(S) else np.array([np.nan, np.nan])
    dvote = [t for t in tiles if t["depth_ncc"] > null99]
    offs = np.array([t["best_layer_for_centre_slab"] - za_mid for t in dvote], np.float64)
    res = {"window": [y0, y1, x0, x1], "band": "coarse", "depth_best": best,
           "depth_z_max_by_render_layer": [round(float(v), 2) for v in zmat.max(axis=1)],
           "tiles_evaluated": len(tiles), "null99_ncc": round(null99, 4), "votes": len(vote),
           "tile_ncc_median": round(float(np.median([t["ncc"] for t in tiles])), 4) if tiles else None,
           "shift_median_px": [round(float(v), 2) for v in med], "shift_robust_sd_px": [round(float(v), 2)
                                                                                         for v in spread],
           "depth_offset_layers_median": round(float(np.median(offs)), 2) if len(offs) else None,
           "depth_offset_p10_p90": [round(float(np.percentile(offs, q)), 2) for q in (10, 90)] if len(offs) else None,
           "depth_tiles": len(dvote), "tiles": tiles}
    (d / "register.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "tiles"}), flush=True)


if __name__ == "__main__":
    main()
