"""M1 survey S1: choose the zones to grow, mechanically, from the E2c level-1 scouting (prereg/M1-survey-S1.md).

1. Gate each crop of data/e2/zoom/<SAMPLE>_z<Z>_a8/zoom.json: merged share <= 0.17, >= 20 crossings, >= 90% inside
   the CT.
2. Drop zones already grown on PHerc0175B and PHerc0490A. A crop is dropped when it has the same radius, lies within 30°
   of a tried direction, and sits within 1,700 slices (a surface's half-height) of a tried height. The 4-direction
   and 8-direction scouts name their crops differently, so matching names alone would miss overlaps.
3. Drop near-duplicates within the survey: the same crop name within 2,500 slices of a better-ranked crop.
4. Rank each volume's survivors by merged share, then by crossings (more first). Keep the top 12, or the top 4 for
   PHerc0175B and PHerc0490A, which have 43 surfaces read already.

Writes data/m1/survey_zones.tsv and prints a per-volume count.
Usage: python m1/survey_select.py
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIED = {"PHerc0175B": [("r80_a270", 7942), ("r55_a225", 7944), ("r30_a090", 5559), ("r55_a045", 5560),
                        ("r80_a000", 5560), ("r80_a090", 10326), ("r80_a270", 10341), ("r55_a112", 12712),
                        ("r80_a225", 6752), ("r55_a337", 9136), ("r80_a045", 6752)],
         "PHerc0490A": [("r55_a225", 5848), ("r55_a225", 7600), ("r30_a090", 7600), ("r30_a180", 7600),
                        ("r30_a090", 5848), ("r80_a180", 5848), ("r80_a270", 7600), ("r55_a067", 8476),
                        ("r80_a135", 9352), ("r30_a045", 4968), ("r80_a045", 8476), ("r55_a157", 4968)]}
CAP = {"PHerc0175B": 4, "PHerc0490A": 4}
HALF_HEIGHT, DUP, NEAR_DEG = 1700, 2500, 30


def near(name_a, z_a, name_b, z_b, dz):
    """Same radius, directions within NEAR_DEG, heights within dz."""
    (ra, aa), (rb, ab) = ((int(p[1:]) for p in n.split("_")) for n in (name_a, name_b))
    d = abs(aa - ab) % 360
    return ra == rb and min(d, 360 - d) <= NEAR_DEG and abs(z_a - z_b) <= dz


def main():
    vols = {r["sample"]: r["volume_id"] for r in json.loads((ROOT / "data/m1/survey_volumes.json").read_text())}
    rows = []
    for f in sorted(glob.glob(str(ROOT / "data/e2/zoom/*_a8/zoom.json"))):
        r = json.loads(Path(f).read_text())
        s, z = r["sample"], r["z_level0"]
        if s not in vols:
            continue
        cy, cx = (round(v * 8) for v in r["centre_level3"])
        for c in r["crops"]:
            if c["merged_frac"] is None or c["merged_frac"] > 0.17 or c["crossings"] < 20 or c["ct_frac"] < 0.9:
                continue
            if any(near(c["name"], z, n, tz, HALF_HEIGHT) for n, tz in TRIED.get(s, [])):
                continue
            y, x = c["centre_yx_level0"]
            rows.append({"sample": s, "volume_id": vols[s], "zone": f"z{z}_{c['name']}", "name": c["name"], "z": z,
                         "y": y, "x": x, "cy": cy, "cx": cx, "merged": c["merged_frac"],
                         "crossings": c["crossings"], "ct": c["ct_frac"]})
    keep = []
    for s in vols:
        cand = sorted((r for r in rows if r["sample"] == s), key=lambda r: (r["merged"], -r["crossings"]))
        chosen = []
        for r in cand:
            if any(near(r["name"], r["z"], k["name"], k["z"], DUP) for k in chosen):
                continue
            chosen.append(r)
            if len(chosen) == CAP.get(s, 12):
                break
        keep += chosen
        print(f"{s}: {len(cand)} gated, {len(chosen)} chosen")
    cols = ["sample", "volume_id", "zone", "z", "y", "x", "cy", "cx", "merged", "crossings", "ct"]
    out = ROOT / "data/m1/survey_zones.tsv"
    out.write_text("\t".join(cols) + "\n" + "".join("\t".join(str(r[c]) for c in cols) + "\n" for r in keep))
    print(f"{len(keep)} zones -> {out}")


if __name__ == "__main__":
    main()
