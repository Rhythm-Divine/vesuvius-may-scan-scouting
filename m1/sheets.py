"""Review sheets for M1 readouts (looking only; no numbers here feed a verdict rule).

  sheet: quarter-resolution forward | reverse ensembles of one surface, the grid orientation (which way a text line
         would run) and the readout's candidates, largest first.
  crop:  full-resolution 800 px squares (7.7 mm) around (y, x) in crop coordinates: CT centre layer | forward
         ensemble | reverse ensemble, with the readout-area outline in mid grey.
  depth: the same squares at half resolution, per depth window: CT layers 13, 17, 21, 25, 29 | forward k = -2..+2 |
         reverse k = -2..+2.

Dotted lines of constant scroll height z (every 2 mm on sheets, 1 mm on crops) show where a line of text would run.

Usage: python m1/sheets.py SAMPLE OUTDIR sheet TAG=MESH [TAG=MESH ...]
       python m1/sheets.py SAMPLE OUTDIR crop|depth TAG=MESH Y X [Y X ...]
"""
import os
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import CELL_PX, T, interior_mask  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

GAP, HALF, CONTOUR = 12, 400, 90


def orientation(mesh_dir):
    z = tifffile.imread(Path(mesh_dir) / "z.tif").astype(float)
    v = z != -1
    dr = np.where(v[1:] & v[:-1], z[1:] - z[:-1], np.nan)
    dc = np.where(v[:, 1:] & v[:, :-1], z[:, 1:] - z[:, :-1], np.nan)
    gr, gc = np.nanmedian(np.abs(dr)), np.nanmedian(np.abs(dc))
    way = "vertical" if gr < 0.7 * gc else ("horizontal" if gc < 0.7 * gr else "oblique")
    sr, sc = np.nanmedian(dr), np.nanmedian(dc)
    if way == "oblique":
        way += " (top-left to bottom-right)" if sr * sc < 0 else " (bottom-left to top-right)"
    return f"dz per step: rows {sr:+.1f} (|{gr:.1f}|), cols {sc:+.1f} (|{gc:.1f}|) -> a text line would run {way}"


def z_contours(mesh_dir, y0, x0, shape, step, every_mm):
    """Dotted iso-z lines on a (shape) image whose pixels are `step` crop pixels apart, starting at canvas (y0, x0)."""
    z = tifffile.imread(Path(mesh_dir) / "z.tif").astype(float)
    per_cell = SRC_UM / DST_UM * CELL_PX
    rows = ((y0 + np.arange(shape[0]) * step) / per_cell).astype(int)
    cols = ((x0 + np.arange(shape[1]) * step) / per_cell).astype(int)
    ok_r, ok_c = rows < z.shape[0], cols < z.shape[1]
    zz = np.full(shape, -1.0)
    zz[np.ix_(ok_r, ok_c)] = z[np.ix_(rows[ok_r], cols[ok_c])]
    band = np.floor(zz / (every_mm * 1000 / SRC_UM))
    valid = zz != -1
    line = np.zeros(shape, bool)
    line[:-1] |= (band[:-1] != band[1:]) & valid[:-1] & valid[1:]
    line[:, :-1] |= (band[:, :-1] != band[:, 1:]) & valid[:, :-1] & valid[:, 1:]
    yy, xx = np.indices(shape)
    return line & ((yy + xx) % 4 == 0)


def side_by_side(panels):
    h = max(p.shape[0] for p in panels)
    out = np.full((h, sum(p.shape[1] for p in panels) + GAP * (len(panels) - 1)), 255, np.uint8)
    x = 0
    for p in panels:
        out[:p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + GAP
    return out


def save(path, img):
    Path(path).write_bytes(imagecodecs.png_encode(np.ascontiguousarray(img)))


def sheet(root, out, tag, mesh):
    h = root / "hecate" / mesh
    print(f"== {tag} {mesh}: {orientation(root / 'meshes' / mesh)}")
    r = json.loads((h / "readout.json").read_text())
    print(f"   readout area {r['valid_cm2']} cm2, crop {r['crop']}")
    for d in ("fwd", "rev"):
        s = r[d]["stats_valid"]
        print(f"   {d}: mean {s['mean']}, p99 {s['p99']}, area >= T {s['frac_ge_T']:.1%}, counts {r[d]['counts']}")
        for c in sorted(r[d]["candidates"], key=lambda c: -c["area_mm2"])[:6]:
            print(f"      cand centroid {[round(v) for v in c['centroid_yx']]} extent {c['extent_mm']} mm "
                  f"area {c['area_mm2']} mm2 peak {c['peak']} mean {c['mean']}")
    panels = [imagecodecs.png_decode((h / f"ens_{d}.png").read_bytes())[::2, ::2].copy() for d in ("fwd", "rev")]
    y0, _, x0, _ = r["crop"]
    lines = z_contours(root / "meshes" / mesh, y0, x0, panels[0].shape, 4, 2)
    for p in panels:
        p[lines & (p < CONTOUR)] = CONTOUR
    save(out / f"sheet_{tag}.png", side_by_side(panels))


def crop(root, out, tag, mesh, points):
    h = root / "hecate" / mesh
    y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
    r9 = np.load(root / "render" / f"{mesh}_9p6.npy", mmap_mode="r")
    valid = (np.asarray(r9[21]) > 0) & interior_mask(root / "meshes" / mesh, r9.shape[1:],
                                                     root / "render" / f"{mesh}_selfcross.json", 8)
    valid = valid[y0:y1, x0:x1]
    edge = valid ^ ndimage.binary_erosion(valid, iterations=3)
    ens = {d: np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                       for k in (-2, -1, 0, 1, 2)], axis=0) for d in ("fwd", "rev")}
    ct = np.asarray(r9[21, y0:y1, x0:x1]).astype(np.float32)
    for y, x in points:
        a, b = max(0, y - HALF), max(0, x - HALF)
        sl = (slice(a, a + 2 * HALF), slice(b, b + 2 * HALF))
        c = ct[sl]
        lo, hi = np.percentile(c[c > 0], (1, 99)) if (c > 0).any() else (0, 1)
        panels = [np.clip((c - lo) / max(hi - lo, 1e-6) * 255, 0, 255)]
        for d in ("fwd", "rev"):
            e = ens[d][sl]
            print(f"   {tag} ({y}, {x}) {d}: mean {e.mean():.3f}, area >= T {(e >= T).mean():.1%} (inside outline "
                  f"{(e[valid[sl]] >= T).mean() if valid[sl].any() else float('nan'):.1%})")
            panels.append(np.clip(e * 230, 0, 230))
        lines = z_contours(root / "meshes" / mesh, y0 + a, x0 + b, c.shape, 1, 1)
        for i, p in enumerate(panels):
            p[edge[sl]] = 128
            if i:
                p[lines & (p < CONTOUR)] = CONTOUR
        save(out / f"crop_{tag}_{y}_{x}.png", side_by_side([p.astype(np.uint8) for p in panels]))


def depth(root, out, tag, mesh, points):
    """Per-window view at half resolution: CT layers 13, 17, 21, 25, 29 | forward k = -2..+2 | reverse k = -2..+2."""
    h = root / "hecate" / mesh
    y0, _, x0, _ = json.loads((h / "crop.json").read_text())["crop"]
    r9 = np.load(root / "render" / f"{mesh}_9p6.npy", mmap_mode="r")
    maps = {(d, k): imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes())
            for d in ("fwd", "rev") for k in (-2, -1, 0, 1, 2)}
    for y, x in points:
        a, b = max(0, y - HALF), max(0, x - HALF)
        rows = []
        cts = [np.asarray(r9[z, y0 + a:y0 + a + 2 * HALF, x0 + b:x0 + b + 2 * HALF]).astype(np.float32)
               for z in (13, 17, 21, 25, 29)]
        good = np.concatenate([c[c > 0] for c in cts]) if any((c > 0).any() for c in cts) else np.array([0.0, 1.0])
        lo, hi = np.percentile(good, (1, 99))
        rows.append(side_by_side([np.clip((c - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)[::2, ::2]
                                  for c in cts]))
        for d in ("fwd", "rev"):
            panels = []
            for k in (-2, -1, 0, 1, 2):
                m = maps[(d, k)][a:a + 2 * HALF, b:b + 2 * HALF]
                print(f"   {tag} ({y}, {x}) {d} k={k:+d}: area >= T {(m >= T * 255).mean():.1%}")
                panels.append((m.astype(np.float32) * 230 / 255).astype(np.uint8)[::2, ::2])
            rows.append(side_by_side(panels))
        w = max(r.shape[1] for r in rows)
        img = np.full((sum(r.shape[0] for r in rows) + GAP * (len(rows) - 1), w), 255, np.uint8)
        yy = 0
        for r in rows:
            img[yy:yy + r.shape[0], :r.shape[1]] = r
            yy += r.shape[0] + GAP
        save(out / f"depth_{tag}_{y}_{x}.png", img)


def main():
    root, out, mode = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    out.mkdir(parents=True, exist_ok=True)
    if mode == "sheet":
        for tm in sys.argv[4:]:
            sheet(root, out, *tm.split("="))
    else:
        tag, mesh = sys.argv[4].split("=")
        nums = [int(v) for v in sys.argv[5:]]
        (crop if mode == "crop" else depth)(root, out, tag, mesh, list(zip(nums[::2], nums[1::2])))


if __name__ == "__main__":
    main()
