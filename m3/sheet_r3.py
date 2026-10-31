"""S3 review sheets (looking only; no number here feeds a verdict). For each surface, reader-v2's maps at quarter
resolution: columns near, p6, m6 (for an S1 surface the near column is S2's map), rows forward and reverse, with dotted
lines of constant scroll height every 2 mm (where a text line would run) and the readout-area outline in mid grey.
Surfaces are stacked PER_SHEET to a JPEG (quality 80); the legend is printed.
Surfaces: data/m3/s3_triage.tsv rows with review = yes, in triage order, from row START (0-based) for COUNT rows; or
explicit SAMPLE:MESH pairs.
Usage: python m3/sheet_r3.py OUT_DIR [--per 1] [--start 0 --count 20 | --pairs S:M ...]
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

ROOT = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "m1"))
sys.path.insert(0, str(ROOT / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

PER_CELL = SRC_UM / DST_UM * CELL_PX
GAP, SEP = 8, 18


def panels(s, m):
    d = ROOT / f"data/m3/{s}/{m}"
    y0, y1, x0, x1 = json.loads((d / "crop.json").read_text())["crop"]
    zg = tifffile.imread(ROOT / f"data/m1/{s}/meshes/{m}/z.tif").astype(np.float64)
    yy, xx = np.mgrid[y0:y1:4, x0:x1:4]
    zc = ndimage.map_coordinates(np.where(zg > 0, zg, np.nan), [yy / PER_CELL - 0.5, xx / PER_CELL - 0.5], order=1,
                                 cval=np.nan)
    zmm = zc * 8.64e-3
    lines = np.isfinite(zmm) & (np.abs(zmm - np.round(zmm / 2) * 2) < 0.03)
    rows = []
    for dr in ("fwd", "rev"):
        row = []
        for fam in ("near", "p6", "m6"):
            f = d / f"ens_r3_{fam}_{dr}.png"
            if not f.exists() and fam == "near":
                f = ROOT / f"data/s2/{s}/{m}/ens_r2_{dr}.png"
            p = imagecodecs.png_decode(f.read_bytes()).astype(np.float32)[::2, ::2]
            h, w = min(p.shape[0], lines.shape[0]), min(p.shape[1], lines.shape[1])
            p = p[:h, :w].copy()
            dots = lines[:h, :w] & ((np.arange(w) // 2) % 2 == 0)[None, :]
            p[dots] = 90
            row.append(p)
        rows.append(row)
    return rows


def block(rows):
    h = max(p.shape[0] for r in rows for p in r)
    w = max(p.shape[1] for r in rows for p in r)
    out = np.full((2 * h + GAP, 3 * w + 2 * GAP), 255, np.float32)
    for i, r in enumerate(rows):
        for j, p in enumerate(r):
            out[i * (h + GAP):i * (h + GAP) + p.shape[0], j * (w + GAP):j * (w + GAP) + p.shape[1]] = p
    return out


def legend(s, m):
    r = json.loads((ROOT / f"data/m3/{s}/{m}/readout_r3.json").read_text())
    parts = []
    for name, x in r["maps"].items():
        ext = max([c["extent_mm"] for c in x["candidates"]] or [0.0])
        ag = x["stats_valid"]["agree_with_hecate"]
        parts.append(f"{name} {x['stats_valid']['frac_ge_T']:.3f}/{ext:.1f}mm" + (f"/ag{ag:.2f}" if ag is not None else ""))
    return f"{r['kind']} {r['valid_cm2']:.2f}cm2 | " + " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--per", type=int, default=1)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=10 ** 6)
    ap.add_argument("--pairs", nargs="*")
    a = ap.parse_args()
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    if a.pairs:
        items = [tuple(p.split(":")) for p in a.pairs]
    else:
        rows = [r for r in csv.DictReader((ROOT / "data/m3/s3_triage.tsv").open(), delimiter="\t") if r["review"] == "yes"]
        items = [(r["sample"], r["mesh"]) for r in rows][a.start:a.start + a.count]
    for i in range(0, len(items), a.per):
        group = items[i:i + a.per]
        blocks = [block(panels(s, m)) for s, m in group]
        H = sum(b.shape[0] for b in blocks) + SEP * (len(blocks) - 1)
        W = max(b.shape[1] for b in blocks)
        canvas = np.full((H, W), 255, np.uint8)
        y = 0
        n = (a.start if not a.pairs else 0) + i
        for (s, m), b in zip(group, blocks):
            canvas[y:y + b.shape[0], :b.shape[1]] = np.clip(b, 0, 255)
            print(f"sheet {n:04d}: {s} {m} | {legend(s, m)}")
            y += b.shape[0] + SEP
        (od / f"s3_sheet_{n:04d}.jpg").write_bytes(imagecodecs.jpeg8_encode(canvas, level=80))


if __name__ == "__main__":
    main()
