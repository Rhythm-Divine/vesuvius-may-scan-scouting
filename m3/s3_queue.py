"""M1 survey S3: build the growth queue mechanically, before the pre-registration (prereg/M1-survey-S3.md).

1. Windings. For every S1 stage-1 zone that passed QC (data/m1/survey_qc.tsv), m1/seeds_radial.py --inward 4
   --outward 4 on the radial line through the zone's S1 seed gives up to eight seeds, one per neighbouring winding:
   <zone>_i<k> (k-th thin crossing toward the centre) and <zone>_o<k> (away from it). A seed already grown in S1 (the
   same voxel as an S1 QC row's seed; stage 2 grew i1, i2, o1, o2 around each volume's best zone) is listed but not
   queued. All of a zone's new seeds form one job, grown in one call so they share the normal-grid cache.
2. New zones. S1's zone choice (m1/survey_select.py: the same gate, the same exclusion of zones tried before S1, and
   the same near-duplicate rule, now also against every S1 zone) without its per-volume cap. Each is one job with one
   test surface, seeded as S1 seeded (m1/seed.py at the crop centre).
Order: winding jobs first, round-robin over the volumes (in each volume, zones by S1 clean area, largest first), then
new-zone jobs, round-robin over the volumes in S1's ranking order.
Writes data/m3/s3_queue.tsv (one row per seed) and one job file per job in data/m3/jobs/ready.
Usage: python m3/s3_queue.py [--threads 8]
"""
import argparse
import csv
import glob
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "m1"))
from survey_select import DUP, HALF_HEIGHT, TRIED, near  # noqa: E402

PY = sys.executable
STAGE1 = re.compile(r"^z\d+_r\d+_a\d+$")


def prefix(s, v):
    return f"{s}/representations/predictions/surfaces/{v}-surface-20260413222639-surface-m7-L0-th0.2.zarr/"


def radial(job):
    s, v, zone, seed, cy, cx = job
    out = ROOT / f"data/m3/seeds/{s}/{zone}"
    subprocess.run([PY, str(ROOT / "m1/seeds_radial.py"), "--seed", *seed.split(), "--centre-yx", str(cy), str(cx),
                    "--inward", "4", "--outward", "4", "--prefix", prefix(s, v), "--out", str(out)],
                   capture_output=True, text=True, check=True)
    rep = json.loads((out / "seeds.json").read_text())
    return [(f"{zone}_{d['direction'][0]}{d['rank']}", f"{d['x']} {d['y']} {d['z']}") for d in rep["seeds"]]


def new_seed(r):
    out = ROOT / f"data/m3/seeds/{r['sample']}/{r['zone']}"
    p = subprocess.run([PY, str(ROOT / "m1/seed.py"), "--prefix", prefix(r["sample"], r["volume_id"]), "--z",
                        str(r["z"]), "--y", str(r["y"]), "--x", str(r["x"]), "--centre-yx", str(r["cy"]), str(r["cx"]),
                        "--out", str(out)], capture_output=True, text=True)
    lines = [ln for ln in p.stdout.splitlines() if re.fullmatch(r"-?\d+ -?\d+ -?\d+", ln.strip())]
    return lines[-1].strip() if lines else None


def round_robin(groups):
    out, i = [], 0
    while any(i < len(g) for g in groups):
        out += [g[i] for g in groups if i < len(g)]
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    zones = list(csv.DictReader((ROOT / "data/m1/survey_zones.tsv").open(), delimiter="\t"))
    zinfo = {(z["sample"], z["zone"]): z for z in zones}
    qc = list(csv.DictReader((ROOT / "data/m1/survey_qc.tsv").open(), delimiter="\t"))
    grown = {(r["sample"], r["seed"]) for r in qc}
    vols = [r["sample"] for r in json.loads((ROOT / "data/m1/survey_volumes.json").read_text())]
    vid = {r["sample"]: r["volume_id"] for r in json.loads((ROOT / "data/m1/survey_volumes.json").read_text())}

    # 1. windings around kept stage-1 zones
    kept = [r for r in qc if r["decision"] == "keep" and STAGE1.match(r["zone"])]
    jobs = [(r["sample"], vid[r["sample"]], r["zone"], r["seed"], zinfo[(r["sample"], r["zone"])]["cy"],
             zinfo[(r["sample"], r["zone"])]["cx"]) for r in kept]
    with ThreadPoolExecutor(a.threads) as ex:
        seeds = list(ex.map(radial, jobs))
    clean = {(r["sample"], r["zone"]): float(r["clean_cm2"]) for r in kept}
    per_vol = {s: [] for s in vols}
    for job, sd in zip(jobs, seeds):
        s, _, zone = job[:3]
        rows = [(lab, xyz, "grown_in_S1" if (s, xyz) in grown else "queued") for lab, xyz in sd]
        per_vol[s].append((clean[(s, zone)], s, zone, "winding", rows))
    wjobs = round_robin([sorted(per_vol[s], key=lambda j: -j[0]) for s in vols])

    # 2. new zones: S1's choice without the cap
    cand = []
    for f in sorted(glob.glob(str(ROOT / "data/e2/zoom/*_a8/zoom.json"))):
        r = json.loads(Path(f).read_text())
        s, z = r["sample"], r["z_level0"]
        if s not in vid:
            continue
        cy, cx = (round(v * 8) for v in r["centre_level3"])
        for c in r["crops"]:
            if c["merged_frac"] is None or c["merged_frac"] > 0.17 or c["crossings"] < 20 or c["ct_frac"] < 0.9:
                continue
            if any(near(c["name"], z, n, tz, HALF_HEIGHT) for n, tz in TRIED.get(s, [])):
                continue
            y, x = c["centre_yx_level0"]
            cand.append({"sample": s, "volume_id": vid[s], "zone": f"z{z}_{c['name']}", "name": c["name"], "z": z,
                         "y": y, "x": x, "cy": cy, "cx": cx, "merged": c["merged_frac"], "crossings": c["crossings"]})
    new_per_vol = {s: [] for s in vols}
    for s in vols:
        chosen = [{"name": z["zone"].split("_", 1)[1], "z": int(z["z"])} for z in zones if z["sample"] == s]
        for r in sorted((c for c in cand if c["sample"] == s), key=lambda r: (r["merged"], -r["crossings"])):
            if any(near(r["name"], r["z"], k["name"], k["z"], DUP) for k in chosen):
                continue
            chosen.append(r)
            new_per_vol[s].append(r)
    flat = [r for s in vols for r in new_per_vol[s]]
    with ThreadPoolExecutor(a.threads) as ex:
        nseeds = list(ex.map(new_seed, flat))
    sd = {(r["sample"], r["zone"]): x for r, x in zip(flat, nseeds)}
    njobs = round_robin([[(0.0, s, r["zone"], "new_zone",
                           [(r["zone"], sd[(s, r["zone"])] or "-", "queued" if sd[(s, r["zone"])] else "no_seed")])
                          for r in new_per_vol[s]] for s in vols])

    # write the queue table and the job files
    jd = ROOT / "data/m3/jobs/ready"
    jd.mkdir(parents=True, exist_ok=True)
    out = ["order\tsample\tvolume_id\tzone\tkind\tsurface\tseed\tstatus"]
    n_jobs = n_seeds = 0
    for i, (_, s, zone, kind, rows) in enumerate(wjobs + njobs, 1):
        q = [(lab, xyz) for lab, xyz, st in rows if st == "queued"]
        out += [f"{i:04d}\t{s}\t{vid[s]}\t{zone}\t{kind}\t{lab}\t{xyz}\t{st}" for lab, xyz, st in rows]
        if q:
            (jd / f"{i:04d}__{s}__{zone}.tsv").write_text("".join(f"{s}\t{vid[s]}\t{lab}\t{xyz}\n" for lab, xyz in q))
            n_jobs += 1
            n_seeds += len(q)
    (ROOT / "data/m3/s3_queue.tsv").write_text("\n".join(out) + "\n")
    for s in vols:
        w = sum(len([x for x in j[4] if x[2] == "queued"]) for j in per_vol[s])
        print(f"{s}: {len(per_vol[s])} kept zones, {w} new winding seeds; {len(new_per_vol[s])} new zones")
    print(f"{n_jobs} jobs, {n_seeds} seeds queued -> data/m3/jobs/ready, data/m3/s3_queue.tsv")


if __name__ == "__main__":
    main()
