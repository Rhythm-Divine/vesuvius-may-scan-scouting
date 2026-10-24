"""S2: the triage row for one surface after its reader-v2 readout (prereg/M1-survey-S2.md).

Flags a direction when its area >= T2 exceeds reader-v2's E1b control background (1.55%), or a candidate reaches 1 mm.
A surface is reviewed by eye when it carries any flag, and also when it is every 5th row in processing order. Rows are
appended to data/s2/s2_triage.tsv under a file lock, so the GPU workers can share it.
Usage: python m2/triage_r2.py SAMPLE MESH
"""
import fcntl
import json
import sys
import time
from pathlib import Path

BG, EXT_MM = 0.0155, 1.0
COLS = ["time", "sample", "mesh", "area_cm2", "fwd_cand", "fwd_mean", "fwd_geT2", "fwd_maxext_mm", "fwd_agree",
        "rev_cand", "rev_mean", "rev_geT2", "rev_maxext_mm", "rev_agree", "flags", "review"]
root = Path(__file__).resolve().parents[1]
s, m = sys.argv[1], sys.argv[2]
r = json.loads((root / f"data/s2/{s}/{m}/readout_r2.json").read_text())
vals, flags = [], []
for d in ("fwd", "rev"):
    st = r[d]["stats_valid"]
    ext = max([c["extent_mm"] for c in r[d]["candidates"]] or [0.0])
    vals += [len(r[d]["candidates"]), st["mean"], st["frac_ge_T"], ext, st["agree_with_hecate"]]
    flags += [f"{d}_area"] * (st["frac_ge_T"] > BG) + [f"{d}_cand1mm"] * (ext >= EXT_MM)
log = root / "data/s2/s2_triage.tsv"
with open(f"{log}.lock", "w") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    if not log.exists():
        log.write_text("\t".join(COLS) + "\n")
    n = sum(1 for _ in log.open()) - 1
    review = "yes" if flags or (n + 1) % 5 == 0 else "no"
    row = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), s, m, r["valid_cm2"], *vals, ",".join(flags) or "-", review]
    with log.open("a") as fh:
        fh.write("\t".join(str(v) for v in row) + "\n")
print("triage_r2", s, m, ",".join(flags) or "-", "review" if review == "yes" else "")
