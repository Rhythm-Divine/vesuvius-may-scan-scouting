"""S3b measurements (prereg/M1-survey-S3b.md). All boxes are in a surface's crop frame (data/m3b/<s>/<m>/crop.json).

  band NAME [MESH]        print the band box Y0 Y1 X0 X1: the segment anchor +- 1600 px (15.4 mm) along the row axis,
                          +- 168 px across it, clipped to the map. MESH defaults to the target's own (S3) surface; for a
                          regrown or facing surface the anchor and axis are first mapped onto it through 3D (nearest
                          vertex), and stored in data/m3b/mapped.json.
  depth NAME              the depth test on the target's own surface, over its row box:
                          - CT profile: mean 9.604 um render intensity per layer (layer 21 = mesh) over valid box pixels,
                            3-layer running mean; the sheet is the run of layers >= half-way between the profile's min
                            and max that contains (or is nearest to) layer 21; its faces are the run's end layers;
                          - reader-v2 share >= T2 in the box per sweep window; the peak window is the largest share
                            (ties: the smaller shift); its centre lies 0.9 x shift layers from the mesh on the 9.604 um
                            grid;
                          - at a face: the peak centre is within 3 layers of a face;
                          - not on voids: of the peak window's >= T2 box pixels, at most 0.375 lie on CT voids (pixels
                            below the box's 25th percentile of the render averaged over the 5 layers around the peak
                            centre);
                          - Hecate share >= T per k, and the agreement at the peak (reader-v2 >= T2 box pixels within
                            31 px of Hecate >= T at the nearest k), as in S2 and S3.
  chain NAME MESH TAG K   the continuity test on one surface's map at window TAG, with Hecate at depth K, in the band:
                          components >= T2 of >= 300 px whose centroid lies within 104 px (1.0 mm) of the axis line;
                          starting from the component nearest the anchor (it must lie within 104 px of it), components
                          are chained along the axis while the gap between their extents is <= 312 px (3.0 mm). Reports
                          the chain's length along the axis (mm), its number of components, and the agreement of its
                          pixels with Hecate >= T at K (31 px).
  facing NAME SIDE        Hecate >= T share per k in the mapped row box of the facing winding on SIDE (plus/minus).
Results are appended as JSON lines to data/m3b/analysis.jsonl and printed.
"""
import json
import sys
from pathlib import Path

import imagecodecs
import numpy as np
import tifffile
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "m1"))
sys.path.insert(0, str(ROOT / "e1"))
from readout import CELL_PX  # noqa: E402
from prepare import DST_UM, SRC_UM  # noqa: E402

T2, T, AGREE_PX, PX_MM = 0.6275, 0.445, 31, 9.604e-3
PER_CELL = SRC_UM / DST_UM * CELL_PX
TAGS = ("m20", "m15", "m10", "m5", "c", "p5", "p10", "p15", "p20")
SHIFT = {t: (0.0 if t == "c" else (1 if t[0] == "p" else -1) * int(t[1:]) / 2) for t in TAGS}
KOF = {"m20": -9, "m15": -7, "m10": -5, "m5": -2, "c": 0, "p5": 2, "p10": 5, "p15": 7, "p20": 9}
ALONG, ACROSS, BAND_TOL, GAP, MIN_PX = 1600, 168, 104, 312, 300
TGT = json.loads((ROOT / "data/m3b/targets.json").read_text())
MAPPED = ROOT / "data/m3b/mapped.json"


def load(p):
    return imagecodecs.png_decode(Path(p).read_bytes()).astype(np.float32) / 255


def crop(s, m):
    p = ROOT / f"data/m3b/{s}/{m}/crop.json"
    if not p.exists():
        p = ROOT / f"data/m3/{s}/{m}/crop.json"
    return json.loads(p.read_text())["crop"]


def grid(s, m):
    d = ROOT / "data/m1" / s / "meshes" / m
    return np.stack([tifffile.imread(d / f"{c}.tif").astype(np.float64) for c in "xyz"], -1)


def map_point(s, ma, mb, ga, gb_tree, gb_idx, y, x):
    y0, _, x0, _ = crop(s, ma)
    r, c = int(round((y0 + y) / PER_CELL - 0.5)), int(round((x0 + x) / PER_CELL - 0.5))
    r, c = min(max(r, 0), ga.shape[0] - 1), min(max(c, 0), ga.shape[1] - 1)
    dist, j = gb_tree.query(ga[r, c])
    rr, cc = gb_idx[j]
    by0, _, bx0, _ = crop(s, mb)
    return (rr + 0.5) * PER_CELL - by0, (cc + 0.5) * PER_CELL - bx0, float(dist)


def geometry(name, mesh=None):
    t = TGT[name]
    s, m = t["sample"], t["mesh"]
    if mesh is None or mesh == m:
        return np.array(t["anchor"]), np.array(t["axis"]), 0.0
    mp = json.loads(MAPPED.read_text()) if MAPPED.exists() else {}
    key = f"{name}:{mesh}"
    if key not in mp:
        ga, gb = grid(s, m), grid(s, mesh)
        ok = gb[..., 0] != -1
        tree, idx = cKDTree(gb[ok]), np.argwhere(ok)
        a = np.array(t["anchor"])
        u = np.array(t["axis"])
        pa = map_point(s, m, mesh, ga, tree, idx, *a)
        pb = map_point(s, m, mesh, ga, tree, idx, *(a + 300 * u))
        v = np.array(pb[:2]) - np.array(pa[:2])
        mp[key] = {"anchor": [pa[0], pa[1]], "axis": list(v / np.linalg.norm(v)), "anchor_dist_vox": pa[2]}
        MAPPED.write_text(json.dumps(mp, indent=1))
    g = mp[key]
    return np.array(g["anchor"]), np.array(g["axis"]), g["anchor_dist_vox"]


def band_box(name, mesh=None):
    t = TGT[name]
    m = mesh or t["mesh"]
    a, u, _ = geometry(name, m)
    y0, y1, x0, x1 = crop(t["sample"], m)
    pts = np.array([a + ALONG * u, a - ALONG * u])
    lo, hi = pts.min(0) - ACROSS, pts.max(0) + ACROSS
    return [int(max(lo[0], 0)), int(min(hi[0], y1 - y0)), int(max(lo[1], 0)), int(min(hi[1], x1 - x0))]


def hecate(s, m, dr, k, shape):
    P = ROOT / f"data/m3b/{s}/{m}/hecate"
    by0, by1, bx0, bx1 = (int(v) for v in (P / f"box_{dr}.txt").read_text().split())
    out = np.zeros(shape, np.float32)
    out[by0:by1, bx0:bx1] = load(P / f"pred_{dr}_{k}.png")[:min(by1, shape[0]) - by0, :min(bx1, shape[1]) - bx0]
    cover = np.zeros(shape, bool)
    cover[by0:by1, bx0:bx1] = True
    return out, cover


def depth(name):
    t = TGT[name]
    s, m, dr = t["sample"], t["mesh"], t["dir"]
    y0, y1, x0, x1 = t["box"]
    cy0, _, cx0, _ = crop(s, m)
    r = np.load(ROOT / f"data/m1/{s}/render/{m}_9p6.npy", mmap_mode="r")
    ct = np.asarray(r[:, cy0 + y0:cy0 + y1, cx0 + x0:cx0 + x1]).astype(np.float32)
    valid = ct[21] > 0
    prof = np.array([ct[k][valid].mean() for k in range(ct.shape[0])])
    sm = np.convolve(np.pad(prof, 1, mode="edge"), np.ones(3) / 3, mode="valid")
    thr = (sm.min() + sm.max()) / 2
    lab, n = ndimage.label(sm >= thr)
    runs = [(np.flatnonzero(lab == i)) for i in range(1, n + 1)]
    run = min(runs, key=lambda q: 0 if q[0] <= 21 <= q[-1] else min(abs(q[0] - 21), abs(q[-1] - 21)))
    faces = [int(run[0]) - 21, int(run[-1]) - 21]
    shares, maps = {}, {}
    for tg in TAGS:
        a = load(ROOT / f"data/m3b/{s}/{m}/pred_s3b_{dr}_{tg}.png")[y0:y1, x0:x1]
        maps[tg] = a
        shares[tg] = float(((a >= T2) & valid).mean())
    peak = max(TAGS, key=lambda q: (shares[q], -abs(SHIFT[q])))
    centre = 0.9 * SHIFT[peak]
    face_d = min(abs(centre - f) for f in faces)
    L = int(round(21 + centre))
    ctm = ct[max(L - 2, 0):L + 3].mean(0)
    void = ctm < np.percentile(ctm[valid], 25)
    rowpx = (maps[peak] >= T2) & valid
    void_share = float(void[rowpx].mean()) if rowpx.any() else None
    full = load(ROOT / f"data/m3b/{s}/{m}/pred_s3b_{dr}_c.png").shape
    hsh, agree = {}, None
    for tg in TAGS:
        h, cover = hecate(s, m, dr, KOF[tg], full)
        hb = h[y0:y1, x0:x1]
        hsh[KOF[tg]] = float(((hb >= T) & valid).mean())
        if tg == peak and rowpx.any():
            near = ndimage.binary_dilation(h >= T, iterations=AGREE_PX)[y0:y1, x0:x1]
            agree = float(near[rowpx].mean())
    res = {"test": "depth", "name": name, "sample": s, "mesh": m, "dir": dr, "box": t["box"],
           "ct_profile": [round(float(v), 1) for v in prof], "faces": faces,
           "r2_share": {k: round(v, 4) for k, v in shares.items()}, "peak": peak, "peak_centre": centre,
           "face_dist": round(face_d, 2), "at_face": face_d <= 3, "void_share": void_share,
           "not_on_voids": void_share is not None and void_share <= 0.375,
           "hecate_share": {str(k): round(v, 4) for k, v in hsh.items()}, "agree_at_peak": agree}
    return res


def chain(name, mesh, tag, k):
    t = TGT[name]
    s, dr = t["sample"], t["dir"]
    a0, u, adist = geometry(name, mesh)
    mp = load(ROOT / f"data/m3b/{s}/{mesh}/pred_s3b_{dr}_{tag}.png")
    h, cover = hecate(s, mesh, dr, int(k), mp.shape)
    by0, by1, bx0, bx1 = band_box(name, mesh)
    inband = np.zeros(mp.shape, bool)
    inband[by0:by1, bx0:bx1] = True
    lab, n = ndimage.label((mp >= T2) & inband)
    nv = np.array([-u[1], u[0]])
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        yy, xx = np.nonzero(lab[sl] == i)
        if len(yy) < MIN_PX:
            continue
        pts = np.stack([yy + sl[0].start, xx + sl[1].start], 1) - a0
        along, across = pts @ u, pts @ nv
        if abs(across.mean()) > BAND_TOL:
            continue
        comps.append({"i": i, "lo": float(along.min()), "hi": float(along.max()), "c": float(along.mean()),
                      "across": float(across.mean()), "px": int(len(yy)), "sl": sl})
    res = {"test": "chain", "name": name, "mesh": mesh, "tag": tag, "k": int(k), "anchor_dist_vox": adist,
           "components_in_band": len(comps)}
    if not comps:
        return {**res, "length_mm": 0.0, "n": 0, "start_ok": False, "agree": None}
    comps.sort(key=lambda c: c["c"])
    j = min(range(len(comps)), key=lambda q: 0 if comps[q]["lo"] <= 0 <= comps[q]["hi"]
            else min(abs(comps[q]["lo"]), abs(comps[q]["hi"])))
    st = comps[j]
    start_ok = (st["lo"] <= 0 <= st["hi"] or min(abs(st["lo"]), abs(st["hi"])) <= BAND_TOL)
    lo_i = hi_i = j
    lo, hi = st["lo"], st["hi"]
    while hi_i + 1 < len(comps) and comps[hi_i + 1]["lo"] - hi <= GAP:
        hi_i += 1
        hi = max(hi, comps[hi_i]["hi"])
    while lo_i - 1 >= 0 and lo - comps[lo_i - 1]["hi"] <= GAP:
        lo_i -= 1
        lo = min(lo, comps[lo_i]["lo"])
    sel = np.isin(lab, [c["i"] for c in comps[lo_i:hi_i + 1]])
    near = ndimage.binary_dilation(h >= T, iterations=AGREE_PX)
    covered = cover[sel].mean()
    return {**res, "length_mm": round((hi - lo) * PX_MM, 2), "n": hi_i - lo_i + 1, "start_ok": bool(start_ok),
            "agree": round(float(near[sel].mean()), 3), "hecate_cover": round(float(covered), 3),
            "chain": [{"along_mm": round(c["c"] * PX_MM, 2), "across_mm": round(c["across"] * PX_MM, 2),
                       "px": c["px"]} for c in comps[lo_i:hi_i + 1]]}


def facing(name, side):
    t = TGT[name]
    f = t["facing"].get(side)
    if not f:
        return {"test": "facing", "name": name, "side": side, "mesh": None}
    s, m, dr = t["sample"], f["mesh"], t["dir"]
    a, u, adist = geometry(name, m)
    y0, y1, x0, x1 = t["box"]
    hy, hx = (y1 - y0) // 2, (x1 - x0) // 2
    shape = load(ROOT / f"data/m3/{s}/{m}/pred_r3_{dr}.png").shape if (ROOT / f"data/m3/{s}/{m}/pred_r3_{dr}.png").exists() \
        else (crop(s, m)[1] - crop(s, m)[0], crop(s, m)[3] - crop(s, m)[2])
    ry0, ry1 = int(max(a[0] - hy, 0)), int(min(a[0] + hy, shape[0]))
    rx0, rx1 = int(max(a[1] - hx, 0)), int(min(a[1] + hx, shape[1]))
    sh = {}
    for k in (-9, -7, -5, -2, 0, 2, 5, 7, 9):
        h, cover = hecate(s, m, dr, k, shape)
        sh[str(k)] = round(float((h[ry0:ry1, rx0:rx1] >= T).mean()), 4)
    return {"test": "facing", "name": name, "side": side, "mesh": m, "dist_vox": f["dist_vox"],
            "anchor_dist_vox": adist, "row_box": [ry0, ry1, rx0, rx1], "hecate_share": sh}


def main():
    cmd = sys.argv[1]
    if cmd == "band":
        print(*band_box(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
        return
    if cmd == "box":   # the Hecate box on MESH: the band box joined with the row box around the (mapped) anchor
        name = sys.argv[2]
        t = TGT[name]
        m = sys.argv[3] if len(sys.argv) > 3 else t["mesh"]
        b = band_box(name, m)
        a, _, _ = geometry(name, m)
        y0, y1, x0, x1 = t["box"]
        hy, hx = (y1 - y0) // 2, (x1 - x0) // 2
        cy0, cy1, cx0, cx1 = crop(t["sample"], m)
        print(int(max(min(b[0], a[0] - hy), 0)), int(min(max(b[1], a[0] + hy), cy1 - cy0)),
              int(max(min(b[2], a[1] - hx), 0)), int(min(max(b[3], a[1] + hx), cx1 - cx0)))
        return
    res = {"depth": lambda: depth(sys.argv[2]), "chain": lambda: chain(*sys.argv[2:6]),
           "facing": lambda: facing(sys.argv[2], sys.argv[3])}[cmd]()
    with open(ROOT / "data/m3b/analysis.jsonl", "a") as f:
        f.write(json.dumps(res) + "\n")
    print(json.dumps(res))


if __name__ == "__main__":
    main()
