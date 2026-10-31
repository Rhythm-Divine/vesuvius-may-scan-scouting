"""S3b: apply the pre-registered reading (prereg/M1-survey-S3b.md) to data/m3b/analysis.jsonl and print Markdown
tables (the last entry per test and target counts). No number here is new: it only reads the logged measurements.
Usage: python m3/s3b_report.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TGT = json.loads((ROOT / "data/m3b/targets.json").read_text())


def main():
    last = {}
    for line in (ROOT / "data/m3b/analysis.jsonl").read_text().splitlines():
        r = json.loads(line)
        key = (r["test"], r["name"], r.get("mesh"), r.get("side"))
        last[key] = r
    depth = {k[1]: v for k, v in last.items() if k[0] == "depth"}
    chains = [v for k, v in last.items() if k[0] == "chain"]
    facing = [v for k, v in last.items() if k[0] == "facing"]

    print("### Depth test (row box of the row's own surface)\n")
    print("| Target | Sheet faces (layers from mesh) | Peak window (centre, layers) | reader-v2 share >= T2 by shift "
          "(-10 ... +10) | Hecate share >= T by k (-9 ... 9) | Agreement at peak | At a face | Void share | Not on voids |")
    print("|---|---|---|---|---|---|---|---|---|")
    for n, d in depth.items():
        r2 = " ".join(f"{100 * v:.1f}" for v in d["r2_share"].values())
        hc = " ".join(f"{100 * v:.1f}" for v in d["hecate_share"].values())
        ag = "—" if d["agree_at_peak"] is None else f"{d['agree_at_peak']:.2f}"
        vs = "—" if d["void_share"] is None else f"{d['void_share']:.2f}"
        print(f"| {n} | {d['faces'][0]}, {d['faces'][1]} | {d['peak']} ({d['peak_centre']:+.1f}) | {r2} | {hc} | {ag} | "
              f"{'yes' if d['at_face'] else 'no'} ({d['face_dist']:.1f}) | {vs} | {'yes' if d['not_on_voids'] else 'no'} |")

    print("\n### Chain test\n")
    print("| Target | Surface | Window / k | Starts at the row | Length (mm) | Components | Agreement | Hecate cover |")
    print("|---|---|---|---|---|---|---|---|")
    for c in chains:
        kind = "own (S3)" if c["mesh"] == TGT[c["name"]]["mesh"] else "regrown"
        ag = "—" if c.get("agree") is None else f"{c['agree']:.2f}"
        print(f"| {c['name']} | {kind} {c['mesh']} | {c['tag']} / {c['k']} | {'yes' if c['start_ok'] else 'no'} | "
              f"{c['length_mm']:.1f} | {c['n']} | {ag} | {c.get('hecate_cover', '—')} |")

    print("\n### Facing windings (Hecate share >= T in the mapped row box, by k -9 ... 9)\n")
    print("| Target | Side | Mesh | Distance (vox) | Shares (%) |")
    print("|---|---|---|---|---|")
    for f in facing:
        if not f.get("mesh"):
            continue
        sh = " ".join(f"{100 * v:.1f}" for v in f["hecate_share"].values())
        print(f"| {f['name']} | {f['side']} | {f['mesh']} | {f['dist_vox']} | {sh} |")

    e = depth.get("E1d")
    ec = next((c for c in chains if c["name"] == "E1d"), None)
    chain_cal = bool(ec and ec["start_ok"] and ec["length_mm"] >= 10 and ec["n"] >= 3 and (ec["agree"] or 0) >= 0.5)
    depth_cal = bool(e and e["at_face"] and e["not_on_voids"])
    print(f"\n### Reading\n\n- Control E1d: chain part {'calibrated' if chain_cal else 'UNCALIBRATED'}, depth part "
          f"{'calibrated' if depth_cal else 'UNCALIBRATED'}.")
    for n in ("s198", "s206", "s325"):
        d = depth.get(n)
        rc = next((c for c in chains if c["name"] == n and c["mesh"] != TGT[n]["mesh"]), None)
        a = bool(rc and rc["start_ok"] and rc["length_mm"] >= 10 and rc["n"] >= 3)
        b = bool(rc and (rc["agree"] or 0) >= 0.5)
        c = bool(d and d["at_face"] and d["not_on_voids"])
        strong = a and b and c and chain_cal and depth_cal
        print(f"- {n}: (a) continuity {'pass' if a else 'fail' if rc else 'not measured'}; (b) agreement "
              f"{'pass' if b else 'fail' if rc else 'not measured'}; (c) depth {'pass' if c else 'fail'} -> "
              f"{'STRONG CANDIDATE' if strong else 'not a strong candidate'}")


if __name__ == "__main__":
    main()
