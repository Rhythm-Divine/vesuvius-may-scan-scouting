"""E2a: first look at an eligible volume from its coarse pyramid level (PHerc0490B by default).

Fetches level L (default 3, i.e. 8x downsampled: 69.12 um voxels) of the CT volume and of the published m7 recto
surface prediction from the open-data bucket, writes them as standalone local OME-Zarr volumes that VC3D's tools
accept, and reports:
  - papyrus extent (z range, radius) from the prediction;
  - a rough papyrus-area estimate: recto-surface voxels per slice x voxel size, summed over z (for cost planning);
  - winding count along rays from the centre;
  - axial / vertical overview PNGs with the prediction in red (private: data/ is gitignored).
The umbilicus is then estimated with vc_gen_normalgrids + vc_gen_umbilicus (see job.sh).

Usage: python overview.py --sample PHerc0490B --volume-id 20250521151215 --level 3 --out DIR
"""
import argparse
import concurrent.futures as cf
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numcodecs
import numpy as np
from scipy import ndimage

B = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
CAT = B + "/metadata.json"


def get(url, timeout=300):
    try:
        return urllib.request.urlopen(url, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def catalogue_paths(sample, vid):
    import gzip
    raw = get(CAT)
    raw = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
    v = json.loads(raw)["samples"][sample]["volumes"][vid]
    paths = {d["type"]: d["origins"][0]["path"] for d in v["data"]}
    return v["properties"], paths["ome-zarr"], paths["surface-prediction-zarr"]


def fetch_level(prefix, level):
    meta = json.loads(get(f"{B}/{urllib.parse.quote(prefix)}{level}/.zarray"))
    shape, chunks = meta["shape"], meta["chunks"]
    sep = meta.get("dimension_separator", ".")
    codec = numcodecs.get_codec(meta["compressor"]) if meta.get("compressor") else None
    grid = [range(-(-s // c)) for s, c in zip(shape, chunks)]
    keys = [(iz, iy, ix) for iz in grid[0] for iy in grid[1] for ix in grid[2]]
    out = np.zeros(shape, dtype=np.uint8)

    def one(k):
        raw = get(f"{B}/{urllib.parse.quote(prefix)}{level}/{sep.join(map(str, k))}")
        if raw is None:
            return
        blk = np.frombuffer(codec.decode(raw) if codec else raw, dtype=np.uint8).reshape(chunks)
        sl = tuple(slice(i * c, min((i + 1) * c, s)) for i, c, s in zip(k, chunks, shape))
        out[sl] = blk[tuple(slice(0, x.stop - x.start) for x in sl)]
    with cf.ThreadPoolExecutor(16) as ex:   # network-bound; one core is enough
        list(ex.map(one, keys))
    return out


def write_local(root, arr, voxel_um):
    """Standalone OME-Zarr (single level '0') + meta.json in the form VC3D's Volume.cpp reads."""
    import shutil
    if root.exists():
        shutil.rmtree(root)
    (root / "0").mkdir(parents=True)
    c = 128
    (root / ".zgroup").write_text(json.dumps({"zarr_format": 2}))
    (root / ".zattrs").write_text(json.dumps({"multiscales": [{"axes": [{"name": a, "type": "space"} for a in "zyx"],
        "datasets": [{"coordinateTransformations": [{"scale": [1.0] * 3, "type": "scale"}], "path": "0"}],
        "name": "/", "version": "0.4"}]}))
    (root / "0" / ".zarray").write_text(json.dumps({"shape": list(arr.shape), "chunks": [c] * 3, "fill_value": 0,
        "order": "C", "filters": None, "dimension_separator": "/", "compressor": None, "zarr_format": 2,
        "dtype": "|u1"}))
    z, y, x = arr.shape
    (root / "meta.json").write_text(json.dumps({"type": "vol", "uuid": root.stem, "name": root.stem,
        "format": "zarr", "width": x, "height": y, "slices": z, "voxelsize": voxel_um, "min": 0.0, "max": 255.0}))
    for iz in range(-(-z // c)):
        for iy in range(-(-y // c)):
            for ix in range(-(-x // c)):
                blk = arr[iz * c:(iz + 1) * c, iy * c:(iy + 1) * c, ix * c:(ix + 1) * c]
                if not blk.any():
                    continue
                full = np.zeros((c, c, c), np.uint8)
                full[:blk.shape[0], :blk.shape[1], :blk.shape[2]] = blk
                p = root / "0" / str(iz) / str(iy)
                p.mkdir(parents=True, exist_ok=True)
                (p / str(ix)).write_bytes(full.tobytes())


def write_png(path, rgb):
    import struct, zlib
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    raw = b"".join(b"\x00" + r.tobytes() for r in rgb)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", rgb.shape[1], rgb.shape[0], 8, 2,
                     0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def overlay(ct, pred):
    g = ct.astype(np.float32)
    lo, hi = np.percentile(g[g > 0], [1, 99]) if (g > 0).any() else (0, 255)
    g = np.clip((g - lo) / max(hi - lo, 1) * 255, 0, 255)
    rgb = np.stack([g, g, g], -1)
    rgb[pred > 0] = [255, 40, 40]
    return rgb


def inside_ct(ct, pred, slab=64):
    """Prediction voxels on CT support (2-voxel erosion per slice, so the masked-out border cannot count), and the
    number of CT-support voxels. Slab-wise to keep memory near one extra bool volume."""
    out = np.zeros(pred.shape, bool)
    n_sup = 0
    for z0 in range(0, ct.shape[0], slab):
        sup = ndimage.binary_erosion(ct[z0:z0 + slab] > 0, structure=np.ones((1, 3, 3), bool), iterations=2)
        n_sup += int(sup.sum())
        out[z0:z0 + slab] = sup & (pred[z0:z0 + slab] > 0)
    return out, n_sup


def scout_metrics(ct, inside, vox, level, fracs=(0.2, 0.35, 0.5, 0.65, 0.8)):
    """Coarse sheet statistics inside the CT at several heights, along 16 rays from the slice centroid:
    crossings (~ windings on that ray), spacing between crossings (um) and its coefficient of variation (a crushed
    or merged stack gives irregular spacing), and the share of runs thicker than 3 voxels (merged or compressed)."""
    per_h = {}
    sp_all, cv_all, thick, runs = [], [], 0, 0
    for f in fracs:
        z = int(f * (ct.shape[0] - 1))
        yy, xx = np.nonzero(inside[z])
        if len(yy) < 100:
            continue
        cy, cx = float(np.mean(yy)), float(np.mean(xx))
        cross = []
        for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
            r = np.arange(0, max(ct.shape[1:]) / 2)
            py, px = (cy + r * np.sin(ang)).astype(int), (cx + r * np.cos(ang)).astype(int)
            ok = (py >= 0) & (py < ct.shape[1]) & (px >= 0) & (px < ct.shape[2])
            prof = inside[z, py[ok], px[ok]]
            starts = np.nonzero(prof[1:] & ~prof[:-1])[0] + 1
            ends = np.nonzero(~prof[1:] & prof[:-1])[0] + 1
            cross.append(len(starts))
            if len(starts) >= 3:
                sp = np.diff(starts) * vox
                sp_all.extend(sp.tolist())
                cv_all.append(float(np.std(sp) / max(np.mean(sp), 1e-6)))
            n = min(len(starts), len(ends[ends > starts[0]])) if len(starts) else 0
            if n:
                lens = ends[ends > starts[0]][:n] - starts[:n]
                thick += int((lens > 3).sum())
                runs += n
        per_h[f"z{z * 2 ** level:05d}"] = {"crossings_median": float(np.median(cross)), "min": int(min(cross)),
                                           "max": int(max(cross))}
    return {"inside_ct_by_height": per_h,
            "crossing_spacing_um_median": round(float(np.median(sp_all)), 1) if sp_all else None,
            "crossing_spacing_cv_median": round(float(np.median(cv_all)), 3) if cv_all else None,
            "thick_run_fraction": round(thick / max(runs, 1), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="PHerc0490B")
    ap.add_argument("--volume-id", default="20250521151215")
    ap.add_argument("--level", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scout", action="store_true",
                    help="no local zarrs (disk); add the inside-CT metrics; reuse OUT/ct.zarr + pred.zarr if present")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    props, vol_prefix, pred_prefix = catalogue_paths(a.sample, a.volume_id)
    vox = props["pixel_size_um"] * 2 ** a.level
    if a.scout and (out / "ct.zarr").exists() and (out / "pred.zarr").exists():
        import zarr
        ct, pred = (np.asarray(zarr.open(str(out / n), mode="r")["0"][:]) for n in ("ct.zarr", "pred.zarr"))
    else:
        ct = fetch_level(vol_prefix, a.level)
        pred = fetch_level(pred_prefix, a.level)
    if pred.shape != ct.shape:   # pyramids can differ by a voxel at odd sizes
        z, y, x = (min(s, t) for s, t in zip(ct.shape, pred.shape))
        ct, pred = ct[:z, :y, :x], pred[:z, :y, :x]
    if not a.scout:
        write_local(out / "ct.zarr", ct, vox)
        write_local(out / "pred.zarr", pred, vox)

    zs = np.nonzero(pred.reshape(pred.shape[0], -1).any(1))[0]
    per_slice = (pred > 0).reshape(pred.shape[0], -1).sum(1)
    # recto voxels x voxel edge ~ sheet length per slice (the binarised coarse mask is ~1-2 voxels thick)
    area_cm2 = float(per_slice.sum()) * (vox * 1e-4) ** 2
    zc = int(np.median(zs)) if len(zs) else pred.shape[0] // 2
    yy, xx = np.nonzero(pred[zc])
    cy, cx = (float(np.mean(yy)), float(np.mean(xx))) if len(yy) else (pred.shape[1] / 2, pred.shape[2] / 2)
    crossings = []
    for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
        r = np.arange(0, max(pred.shape[1:]) / 2)
        py, px = (cy + r * np.sin(ang)).astype(int), (cx + r * np.cos(ang)).astype(int)
        ok = (py >= 0) & (py < pred.shape[1]) & (px >= 0) & (px < pred.shape[2])
        prof = pred[zc, py[ok], px[ok]] > 0
        crossings.append(int(np.sum(prof[1:] & ~prof[:-1])))
    rep = {"sample": a.sample, "volume_id": a.volume_id, "level": a.level, "voxel_um": vox,
           "shape_zyx": list(ct.shape), "pred_z_range_level0": [int(zs.min()) * 2 ** a.level,
                                                                 int(zs.max()) * 2 ** a.level] if len(zs) else None,
           "rough_recto_area_cm2": round(area_cm2, 0),
           "windings_along_rays_mid_height": {"median": float(np.median(crossings)), "min": min(crossings),
                                              "max": max(crossings)},
           "centre_yx_level0_mid_height": [round(cy * 2 ** a.level, 1), round(cx * 2 ** a.level, 1)],
           "mid_height_z_level0": zc * 2 ** a.level}
    if a.scout:
        ins, n_sup = inside_ct(ct, pred)
        n_pred, n_in = int(np.count_nonzero(pred)), int(np.count_nonzero(ins))
        rep.update({"pred_voxels": n_pred, "pred_voxels_inside_ct": n_in,
                    "phantom_fraction": round(1 - n_in / max(n_pred, 1), 3),
                    "rough_recto_area_cm2_inside_ct": round(float(n_in) * (vox * 1e-4) ** 2, 0),
                    "ct_support_fraction_of_bbox": round(n_sup / ct.size, 3),
                    **scout_metrics(ct, ins, vox, a.level)})
        np.multiply(pred, ins, out=pred, casting="unsafe")   # the PNGs show only on-CT predictions
    (out / "overview.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    for f in (0.15, 0.35, 0.5, 0.65, 0.85):
        z = int(f * (ct.shape[0] - 1))
        write_png(out / f"axial_z{z * 2 ** a.level:05d}.png", overlay(ct[z], pred[z]))
    write_png(out / "vertical_xz.png", overlay(ct[:, int(cy), :], pred[:, int(cy), :]))
    write_png(out / "vertical_yz.png", overlay(ct[:, :, int(cx)], pred[:, :, int(cx)]))


if __name__ == "__main__":
    main()
