"""E1 preparation: put the PHerc0009B control segment and its ink labels on one 9.604 um canvas for Hecate.

1. Resample the published 8.64 um surface volume to 9.604 um (= 4 x 2.401 um): XY origin-aligned, Z centre-aligned.
2. Fetch level 2 of the 2.401 um render (already at 9.604 um) plus the 2.401 um ink labels and supervision mask
   (HF bucket scrollprize/datasets), and box-downsample labels and mask 4x.
3. Measure the XY offset between the two renders by phase correlation of high-passed mid layers (CT texture only;
   the labels never steer it), then crop labels and mask into the 8.64 um render's frame.
Outputs (OUT/): render.npy (uint8 ZYX), labels.npy, mask.npy (bool YX), align.json, overlay.png.

Usage: python prepare.py --out DIR
"""
import os
import argparse
import concurrent.futures as cf
import json
import urllib.request
from pathlib import Path

import urllib.error

import numcodecs
import numpy as np
import tifffile
import zarr
from scipy import fft, ndimage

HOME = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
RENDER = HOME / ("data/PHerc0009B/segments/20250919125754-auto_grown_20250919055754487_inp_hr/surface-volumes/"
                 "8.64um-1.2m-116keV-volume-20250521125136.zarr")
HF = "https://huggingface.co/buckets/scrollprize/datasets/resolve"
SEG = "ink/0009b/auto_grown_20250919055754487_inp_hr_2um"
STEM = "auto_grown_20250919055754487_inp_hr_2um"
SRC_UM, DST_UM = 8.64, 4 * 2.401


def fetch(url, dst):
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(url, timeout=300).read()
    tmp = dst.with_name(dst.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(dst)
    return dst


def fetch_level2(cache):
    """Level 2 of the 2.401 um render (17 x 6496 x 5312, blosc, chunks 17x128x128, '.' key separator)."""
    meta = json.loads(urllib.request.urlopen(f"{HF}/{SEG}/{STEM}.zarr/2/.zarray", timeout=60).read())
    nz, ny, nx = meta["shape"]
    cz, cy, cx = meta["chunks"]
    keys = [f"0.{iy}.{ix}" for iy in range(-(-ny // cy)) for ix in range(-(-nx // cx))]

    def get(k):
        try:
            return fetch(f"{HF}/{SEG}/{STEM}.zarr/2/{k}", cache / k)
        except urllib.error.HTTPError as e:   # stores skip all-fill chunks
            if e.code == 404:
                return None
            raise
    with cf.ThreadPoolExecutor(16) as ex:   # network-bound
        got = dict(zip(keys, ex.map(get, keys)))
    codec = numcodecs.get_codec(meta["compressor"]) if meta.get("compressor") else None
    out = np.zeros((nz, ny, nx), dtype=np.uint8)
    for k in keys:
        if got[k] is None:
            continue
        _, iy, ix = map(int, k.split("."))
        raw = (cache / k).read_bytes()
        blk = np.frombuffer(codec.decode(raw) if codec else raw, dtype=np.uint8).reshape(cz, cy, cx)
        out[:, iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = blk[:, :min(cy, ny - iy * cy), :min(cx, nx - ix * cx)]
    return out


def resample_render(src):
    """8.64 -> 9.604 um. XY: out(i, j) samples in(i / f, j / f). Z: centred on the middle layer."""
    f = SRC_UM / DST_UM
    nz, ny, nx = src.shape
    oy, ox, oz = int(ny * f), int(nx * f), int(round(nz * f))
    xy = np.empty((nz, oy, ox), dtype=np.uint8)
    for z in range(nz):
        layer = np.asarray(src[z], dtype=np.float32)
        xy[z] = np.clip(np.rint(ndimage.affine_transform(layer, [1 / f, 1 / f], output_shape=(oy, ox), order=1)),
                        0, 255).astype(np.uint8)
    out = np.empty((oz, oy, ox), dtype=np.uint8)
    for k in range(oz):
        zin = (nz - 1) / 2 + (k - (oz - 1) / 2) / f
        z0 = int(np.clip(np.floor(zin), 0, nz - 2))
        w = float(np.clip(zin - z0, 0, 1))
        out[k] = np.rint(xy[z0] * (1 - w) + xy[z0 + 1] * w).astype(np.uint8)
    return out


def box4(img):
    h, w = (s // 4 * 4 for s in img.shape)
    return img[:h, :w].reshape(h // 4, 4, w // 4, 4).mean(axis=(1, 3), dtype=np.float32)


def highpass(a, sigma=8):
    a = a.astype(np.float32)
    a = a - ndimage.gaussian_filter(a, sigma)
    return (a - a.mean()) / (a.std() + 1e-6)


def phase_offset(a, b):
    """(dy, dx) such that b[y + dy, x + dx] ~ a[y, x]; plus the peak-to-second-peak ratio as a confidence."""
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    win = lambda s: np.outer(np.hanning(s[0]), np.hanning(s[1])).astype(np.float32)
    A = np.zeros((h, w), np.float32)
    B = np.zeros((h, w), np.float32)
    A[:a.shape[0], :a.shape[1]] = highpass(a) * win(a.shape)
    B[:b.shape[0], :b.shape[1]] = highpass(b) * win(b.shape)
    R = fft.rfft2(B, workers=1) * np.conj(fft.rfft2(A, workers=1))
    R /= np.abs(R) + 1e-9
    corr = fft.irfft2(R, s=(h, w), workers=1)
    iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
    peak = float(corr[iy, ix])
    masked = corr.copy()
    masked[max(0, iy - 20):iy + 21, max(0, ix - 20):ix + 21] = -np.inf
    second = float(masked.max())
    dy = iy if iy <= h // 2 else iy - h
    dx = ix if ix <= w // 2 else ix - w
    return int(dy), int(dx), peak / max(second, 1e-9)


def write_png(path, img):
    import struct, zlib
    img = np.ascontiguousarray(img, dtype=np.uint8)
    raw = b"".join(b"\x00" + r.tobytes() for r in img)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", img.shape[1], img.shape[0],
                           8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    hf_dir = HOME / "data/hf" / SEG

    g = zarr.open(str(RENDER), mode="r")
    src = g["0"]
    render = resample_render(src)
    np.save(out / "render.npy", render)
    print("render 9.604 um:", render.shape)

    lab = tifffile.imread(fetch(f"{HF}/{SEG}/{STEM}_inklabels.tif", hf_dir / "inklabels.tif")) > 127
    msk = tifffile.imread(fetch(f"{HF}/{SEG}/{STEM}_supervision_mask.tif", hf_dir / "supervision_mask.tif")) > 127
    lab4, msk4 = box4(lab), box4(msk)
    hi = fetch_level2(hf_dir / "render2um_L2_chunks")
    print("2.401 um render level 2:", hi.shape, "labels/mask after 4x box:", lab4.shape)

    zmid_lo, zmid_hi = render.shape[0] // 2, hi.shape[0] // 2
    dy, dx, conf = phase_offset(render[zmid_lo], hi[zmid_hi])
    # labels on the render's canvas: L[y, x] = lab4[y + dy, x + dx]
    H, W = render.shape[1:]
    L = np.zeros((H, W), np.float32)
    M = np.zeros((H, W), np.float32)
    ys, xs = slice(max(0, -dy), min(H, lab4.shape[0] - dy)), slice(max(0, -dx), min(W, lab4.shape[1] - dx))
    L[ys, xs] = lab4[ys.start + dy:ys.stop + dy, xs.start + dx:xs.stop + dx]
    M[ys, xs] = msk4[ys.start + dy:ys.stop + dy, xs.start + dx:xs.stop + dx]
    labels, mask = L >= 0.5, M >= 0.5
    np.save(out / "labels.npy", labels)
    np.save(out / "mask.npy", mask)
    # texture agreement after the shift, as a sanity number (correlation of high-passed mid layers)
    hp_a = highpass(render[zmid_lo])[ys, xs]
    hp_b = highpass(hi[zmid_hi])[ys.start + dy:ys.stop + dy, xs.start + dx:xs.stop + dx]
    ncc = float(np.mean(hp_a * hp_b))
    info = {"render_shape": list(render.shape), "hi_shape": list(hi.shape), "offset_dy_dx": [dy, dx],
            "peak_ratio": round(conf, 2), "ncc_after_shift": round(ncc, 3),
            "label_px": int(labels.sum()), "mask_px": int(mask.sum()), "ink_frac_in_mask": round(
                float(labels[mask].mean()) if mask.any() else 0.0, 4)}
    (out / "align.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))
    # overlay: mid layer (downsampled 4x for viewing) with label pixels brightened
    view = render[zmid_lo].astype(np.float32)
    view = (view - np.percentile(view, 1)) / max(np.percentile(view, 99) - np.percentile(view, 1), 1) * 200
    edges = labels ^ ndimage.binary_erosion(labels, iterations=1)
    view[edges] = 255
    write_png(out / "overlay.png", np.clip(view[::4, ::4], 0, 255))


if __name__ == "__main__":
    main()
