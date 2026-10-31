"""S3 summary for results/M1-survey-S3.md: per-volume counts and areas from the QC log, the triage log and the review
log, printed as Markdown tables (no number here changes a verdict).
Usage: python m3/summary_s3.py [REVIEWS.tsv]     (default results/M1-survey-S3-reviews.tsv)
"""
import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BG = {"near": 0.0155, "p6": 0.0144, "m6": 0.0436}


def rows(p):
    with open(p) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def num(v):
    return None if v in ("", "-") else float(v)


def pct(v):
    return "—" if v is None else f"{100 * v:.1f}%"


def main():
    rev_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/M1-survey-S3-reviews.tsv"
    qc, tri, rev = rows(ROOT / "data/m3/s3_qc.tsv"), rows(ROOT / "data/m3/s3_triage.tsv"), rows(rev_path)
    vols = sorted({r["sample"] for r in qc} | {r["sample"] for r in tri})
    q, t, v = defaultdict(list), defaultdict(list), defaultdict(Counter)
    for r in qc:
        q[r["sample"]].append(r)
    for r in tri:
        t[r["sample"]].append(r)
    for r in rev:
        v[r["sample"]][r["verdict"]] += 1

    print("| Volume | Grown | Kept, distinct | Clean (cm²) | Unique (cm²) | Duplicates | Dropped | New read | S1 re-read "
          "| Reviewed | Verdict 1 / 2 / 3 | Median near fwd / rev (new) | Above background (new / S1) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    tot = Counter()
    allnf, allnr = [], []
    for s in vols:
        keep = [r for r in q[s] if r["decision"] == "keep" and r["distinct"].startswith("distinct")]
        dup = [r for r in q[s] if r["decision"] == "keep" and r["distinct"].startswith("duplicate")]
        drop = [r for r in q[s] if r["decision"] != "keep"]
        clean = sum(float(r["clean_cm2"]) for r in keep)
        uniq = sum(float(r["clean_cm2"]) * (1 - float(r["distinct"].split()[3])) for r in keep)
        new = [r for r in t[s] if r["kind"] == "new"]
        old = [r for r in t[s] if r["kind"] == "s1"]
        nf = [num(r["near_fwd_geT2"]) for r in new if num(r["near_fwd_geT2"]) is not None]
        nr = [num(r["near_rev_geT2"]) for r in new if num(r["near_rev_geT2"]) is not None]
        allnf += nf
        allnr += nr

        def above(rr, fams):
            return sum(any((num(r[f"{f}_{d}_geT2"]) or 0) > BG[f] for f in fams for d in ("fwd", "rev")) for r in rr)

        ab_new, ab_old = above(new, ("near", "p6", "m6")), above(old, ("p6", "m6"))
        reviewed = sum(r["review"] == "yes" for r in t[s])
        vv = v[s]
        print(f"| {s} | {len(q[s])} | {len(keep)} | {clean:.1f} | {uniq:.1f} | {len(dup)} | {len(drop)} | {len(new)} "
              f"| {len(old)} | {reviewed} | {vv['1']} / {vv['2']} / {vv['3']} "
              f"| {pct(statistics.median(nf) if nf else None)} / {pct(statistics.median(nr) if nr else None)} "
              f"| {ab_new} / {ab_old} |")
        tot.update(grown=len(q[s]), keep=len(keep), dup=len(dup), drop=len(drop), new=len(new), old=len(old),
                   reviewed=reviewed, v1=vv["1"], v2=vv["2"], v3=vv["3"], ab_new=ab_new, ab_old=ab_old)
        tot["clean"] += clean
        tot["uniq"] += uniq
    print(f"| **Total** | **{tot['grown']}** | **{tot['keep']}** | **{tot['clean']:.1f}** | **{tot['uniq']:.1f}** "
          f"| **{tot['dup']}** | **{tot['drop']}** | **{tot['new']}** | **{tot['old']}** | **{tot['reviewed']}** "
          f"| **{tot['v1']} / {tot['v2']} / {tot['v3']}** "
          f"| {pct(statistics.median(allnf) if allnf else None)} / {pct(statistics.median(allnr) if allnr else None)} "
          f"| {tot['ab_new']} / {tot['ab_old']} |")
    print()
    print(f"QC rows {len(qc)}; triage rows {len(tri)}; review rows {len(rev)}; "
          f"triage rows marked for review {sum(r['review'] == 'yes' for r in tri)}")
    reviewed_meshes = {(r["sample"], r["mesh"]) for r in rev}
    missing = [(r["sample"], r["mesh"]) for r in tri if r["review"] == "yes" and (r["sample"], r["mesh"]) not in
               reviewed_meshes]
    print(f"marked for review but not in the review log: {len(missing)}")
    for m in missing:
        print("  ", *m)


if __name__ == "__main__":
    main()
