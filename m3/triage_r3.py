"""S3: the triage row for one surface after its reader-v2 readout (prereg/M1-survey-S3.md).

A map is flagged when its area >= T2 exceeds the E1b control background of its window family (near: 1.55%, as in
S2; p6 and m6: measured on E1b before the pre-registration), or when a candidate reaches 1 mm. A surface is reviewed
by eye when any of its maps is flagged, and also when it is every 5th row in processing order. Rows are appended to
data/m3/s3_triage.tsv under a file lock, so the GPU workers can share it.
Usage: python m3/triage_r3.py SAMPLE MESH
"""
import fcntl
import json
import sys
import time
from pathlib import Path

BG = {"near": 0.0155, "p6": 0.0144, "m6": 0.0436}   # E1b forward, share of non-ink pixels >= T2 (2026-10-24)
EXT_MM = 1.0
MAPS = ["near_fwd", "near_rev", "p6_fwd", "p6_rev", "m6_fwd", "m6_rev"]
COLS = (["time", "sample", "mesh", "kind", "valid_cm2"]
        + [f"{n}_{k}" for n in MAPS for k in ("geT2", "maxext_mm", "ncand")] + ["flags", "review"])
root = Path(__file__).resolve().parents[1]
s, m = sys.argv[1], sys.argv[2]
r = json.loads((root / f"data/m3/{s}/{m}/readout_r3.json").read_text())
vals, flags = [], []
for name in MAPS:
    x = r["maps"].get(name)
    if x is None:
        vals += ["-", "-", "-"]
        continue
    st = x["stats_valid"]
    ext = max([c["extent_mm"] for c in x["candidates"]] or [0.0])
    vals += [st["frac_ge_T"], round(ext, 3), len(x["candidates"])]
    fam = name.split("_")[0]
    flags += [f"{name}_area"] * (st["frac_ge_T"] > BG[fam]) + [f"{name}_cand1mm"] * (ext >= EXT_MM)
log = root / "data/m3/s3_triage.tsv"
with open(f"{log}.lock", "w") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    if not log.exists():
        log.write_text("\t".join(COLS) + "\n")
    n = sum(1 for _ in log.open()) - 1
    review = "yes" if flags or (n + 1) % 5 == 0 else "no"
    row = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), s, m, r["kind"], r["valid_cm2"], *vals,
           ",".join(flags) or "-", review]
    with log.open("a") as fh:
        fh.write("\t".join(str(v) for v in row) + "\n")
print("triage_r3", s, m, ",".join(flags) or "-", "review" if review == "yes" else "")
