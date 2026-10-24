"""Does a readout's response sit on voids next to the surface? (looking aid, not a rule)
For each crop pixel: the share of render layers 10-18 (one side of the surface, layer 21) and of layers 24-32 (the other
side) darker than that surface's own 25th percentile of CT, i.e. void-like. Prints the correlation of each ensemble with
each void share over the readout area (both smoothed over 0.5 mm), and the void shares inside vs outside the forward >= T
region.  Usage: python m1/voidcorr.py SAMPLE MESH [SAMPLE MESH ...]"""
import json
import os
import sys
from pathlib import Path
import imagecodecs
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from readout import T, interior_mask  # noqa: E402
args = sys.argv[1:]
for s, m in zip(args[::2], args[1::2]):
    root = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1])) / "data/m1" / s
    h = root / "hecate" / m
    y0, y1, x0, x1 = json.loads((h / "crop.json").read_text())["crop"]
    r9 = np.load(root / "render" / f"{m}_9p6.npy", mmap_mode="r")
    valid = ((np.asarray(r9[21]) > 0) & interior_mask(str(root / "meshes" / m), r9.shape[1:],
                                                       str(root / "render" / f"{m}_selfcross.json"), 8))[y0:y1, x0:x1]
    ct = np.asarray(r9[:, y0:y1, x0:x1]).astype(np.float32)
    q25 = np.percentile(ct[21][valid], 25)
    side = {"lo(10-18)": (ct[10:19] < q25).mean(0), "hi(24-32)": (ct[24:33] < q25).mean(0)}
    ens = {d: np.mean([imagecodecs.png_decode((h / f"pred_{d}_{k}.png").read_bytes()).astype(np.float32) / 255
                       for k in (-2, -1, 0, 1, 2)], 0) for d in ("fwd", "rev")}
    sm = lambda a: ndimage.uniform_filter(a, 52)          # 0.5 mm
    strong = (ens["fwd"] >= T) & valid
    line = f"{s} {m}:"
    for d in ("fwd", "rev"):
        for k, v in side.items():
            line += f" r({d},{k})={np.corrcoef(sm(ens[d])[valid], sm(v)[valid])[0, 1]:+.2f}"
    for k, v in side.items():
        line += f"  {k} void share in/out of fwd>=T: {v[strong].mean():.2f}/{v[valid & ~strong].mean():.2f}"
    print(line)
