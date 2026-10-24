"""M1 survey: the triage row for one surface after its readout (prereg/M1-survey-S1.md).

Flags a direction when:
- its area >= T exceeds the control background (1.2%);
- a candidate reaches 1 mm extent;
- or its mean p exceeds 0.06.

A surface is reviewed by eye when it carries any flag, and also when it is every 5th row in processing order. The
rows are appended to data/m1/survey_triage.tsv under a file lock, so the four GPU workers can share it.
Usage: python m1/survey_triage.py SAMPLE MESH
"""
import fcntl
import json
import sys
import time
from pathlib import Path

BG, EXT_MM, MEAN = 0.012, 1.0, 0.06
COLS = ["time", "sample", "mesh", "area_cm2", "fwd_cand", "fwd_mean", "fwd_geT", "fwd_maxext_mm", "rev_cand",
        "rev_mean", "rev_geT", "rev_maxext_mm", "flags", "review"]
root = Path(__file__).resolve().parents[1]
s, m = sys.argv[1], sys.argv[2]
r = json.loads((root / f"data/m1/{s}/hecate/{m}/readout.json").read_text())
vals, flags = [], []
for d in ("fwd", "rev"):
    if "error" in r[d]:
        sys.exit(f"triage {s} {m}: {d} readout error: {r[d]['error']}")
    st = r[d]["stats_valid"]
    ext = max([c["extent_mm"] for c in r[d]["candidates"]] or [0.0])
    vals += [len(r[d]["candidates"]), st["mean"], st["frac_ge_T"], ext]
    flags += [f"{d}_area"] * (st["frac_ge_T"] > BG) + [f"{d}_cand1mm"] * (ext >= EXT_MM) + [f"{d}_mean"] * (st["mean"] > MEAN)
log = root / "data/m1/survey_triage.tsv"
with open(f"{log}.lock", "w") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    if not log.exists():
        log.write_text("\t".join(COLS) + "\n")
    n = sum(1 for _ in log.open()) - 1
    review = "yes" if flags or (n + 1) % 5 == 0 else "no"
    row = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), s, m, r["valid_cm2"], *vals, ",".join(flags) or "-", review]
    with log.open("a") as fh:
        fh.write("\t".join(str(v) for v in row) + "\n")
print("triage", s, m, ",".join(flags) or "-", "review" if review == "yes" else "")
