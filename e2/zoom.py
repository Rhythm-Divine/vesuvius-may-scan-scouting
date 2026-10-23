"""E2c: closer looks at an eligible volume to find separable, layered zones before growing surfaces.

At one height, picks crop centres along rays from the slice centroid of the level-3 on-CT prediction (several radii x
several directions), then fetches level-L crops (default level 1, 17.28 um voxels) of CT and m7 prediction around each
and writes an axial PNG (prediction in red) plus per-crop statistics:
  - pred_frac: on-CT prediction share of the crop's CT voxels;
  - spacing_um / cv: spacing between prediction crossings along the crop's radial line and its variation;
  - merged_frac: share of prediction runs along that line thicker than 3 voxels (sheets fused or compressed).
Only PNGs and JSON are kept. Reads public open data only.

Usage: python zoom.py --sample PHerc0175B --volume-id 20250521125822 --z 7944 --out DIR [--level 1] [--size 384]
"""
import argparse
import concurrent.futures as cf
import json
import sys
import urllib.parse
from pathlib import Path

import numcodecs
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overview import B, catalogue_paths, get, overlay, write_png  # noqa: E402


def fetch_box(prefix, level, z0, z1, y0, y1, x0, x1):
    meta = json.loads(get(f"{B}/{urllib.parse.quote(prefix)}{level}/.zarray"))
    shape, ch = meta["shape"], meta["chunks"]
    sep = meta.get("dimension_separator", ".")
    codec = numcodecs.get_codec(meta["compressor"]) if meta.get("compressor") else None
    z0, y0, x0 = max(0, z0), max(0, y0), max(0, x0)
    z1, y1, x1 = min(shape[0], z1), min(shape[1], y1), min(shape[2], x1)
    out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
    keys = [(a, b, c) for a in range(z0 // ch[0], -(-z1 // ch[0])) for b in range(y0 // ch[1], -(-y1 // ch[1]))
            for c in range(x0 // ch[2], -(-x1 // ch[2]))]

    def one(k):
        raw = get(f"{B}/{urllib.parse.quote(prefix)}{level}/{sep.join(map(str, k))}")
        if raw is None:
            return
        blk = np.frombuffer(codec.decode(raw) if codec else raw, np.uint8).reshape(ch)
        lo = [k[i] * ch[i] for i in range(3)]
        src = tuple(slice(max(a, lo[i]) - lo[i], min(b, lo[i] + ch[i]) - lo[i])
                    for i, (a, b) in enumerate(((z0, z1), (y0, y1), (x0, x1))))
        dst = tuple(slice(max(a, lo[i]) - a, min(b, lo[i] + ch[i]) - a)
                    for i, (a, b) in enumerate(((z0, z1), (y0, y1), (x0, x1))))
        out[dst] = blk[src]
    with cf.ThreadPoolExecutor(16) as ex:   # network-bound
        list(ex.map(one, keys))
    return out


def line_stats(prof, vox):
    starts = np.nonzero(prof[1:] & ~prof[:-1])[0] + 1
    ends = np.nonzero(~prof[1:] & prof[:-1])[0] + 1
    ends = ends[ends > starts[0]] if len(starts) else ends[:0]
    n = min(len(starts), len(ends))
    lens = ends[:n] - starts[:n]
    sp = np.diff(starts) * vox if len(starts) >= 3 else np.array([])
    return {"crossings": int(len(starts)), "spacing_um": round(float(np.median(sp)), 1) if sp.size else None,
            "cv": round(float(np.std(sp) / max(np.mean(sp), 1e-6)), 3) if sp.size else None,
            "merged_frac": round(float((lens > 3).mean()), 3) if n else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--volume-id", required=True)
    ap.add_argument("--z", type=int, required=True, help="level-0 slice")
    ap.add_argument("--out", required=True)
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--size", type=int, default=384, help="crop edge in level-L voxels (XY); Z depth is 16")
    ap.add_argument("--radii", type=float, nargs="+", default=[0.3, 0.55, 0.8])
    ap.add_argument("--angles", type=int, default=4)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    props, vol_prefix, pred_prefix = catalogue_paths(a.sample, a.volume_id)
    f3, fL = 2 ** 3, 2 ** a.level
    # centroid and outer radius from the level-3 prediction slice inside the CT
    z3 = a.z // f3
    ct3 = fetch_box(vol_prefix, 3, z3, z3 + 1, 0, 10 ** 6, 0, 10 ** 6)[0]
    pr3 = fetch_box(pred_prefix, 3, z3, z3 + 1, 0, 10 ** 6, 0, 10 ** 6)[0]
    yy, xx = np.nonzero((pr3 > 0) & (ct3 > 0))
    cy, cx = float(np.mean(yy)), float(np.mean(xx))
    rmax = float(np.percentile(np.hypot(yy - cy, xx - cx), 98))
    vox = props["pixel_size_um"] * fL
    crops = []
    for r in a.radii:
        for k in range(a.angles):
            ang = 2 * np.pi * (k + 0.5 * (a.radii.index(r) % 2)) / a.angles
            py3, px3 = cy + r * rmax * np.sin(ang), cx + r * rmax * np.cos(ang)
            yc, xc, zc = int(py3 * f3 / fL), int(px3 * f3 / fL), a.z // fL
            h = a.size // 2
            box = (zc - 8, zc + 8, yc - h, yc + h, xc - h, xc + h)
            ct = fetch_box(vol_prefix, a.level, *box)
            pr = fetch_box(pred_prefix, a.level, *box)
            if ct.shape != pr.shape or ct.size == 0:
                continue
            m = ct[8] > 0
            ins = (pr[8] > 0) & m
            # radial line through the crop centre, along the ray direction
            t = np.arange(-h, h)
            ly = np.clip((h + t * np.sin(ang)).astype(int), 0, ct.shape[1] - 1)
            lx = np.clip((h + t * np.cos(ang)).astype(int), 0, ct.shape[2] - 1)
            st = {"r": r, "angle_deg": round(float(np.degrees(ang)), 1), "centre_yx_level0": [yc * fL, xc * fL],
                  "ct_frac": round(float(m.mean()), 3), "pred_frac": round(float(ins.sum() / max(m.sum(), 1)), 3),
                  **line_stats(ins[ly, lx], vox)}
            name = f"r{int(r * 100):02d}_a{int(st['angle_deg']):03d}"
            write_png(out / f"{name}.png", overlay(ct[8], np.where(ins, 255, 0)))
            crops.append({"name": name, **st})
            print(json.dumps(crops[-1]), flush=True)
    rep = {"sample": a.sample, "volume_id": a.volume_id, "z_level0": a.z, "level": a.level, "voxel_um": vox,
           "centre_level3": [round(cy, 1), round(cx, 1)], "rmax_level3": round(rmax, 1), "crops": crops}
    (out / "zoom.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
