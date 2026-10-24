"""M1 survey: the ten First Letters-eligible May-session (8.64 um) volumes and whether each has what the pipeline needs.

For each volume, from the public catalogue: voxel size, height in slices (level 0), and whether the m7 surface
prediction and its normal grids are published. Writes data/m1/survey_volumes.json and prints one line per volume.

Usage: python m1/survey_volumes.py
"""
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "e2"))
from overview import B, catalogue_paths, get  # noqa: E402

# Eligible volume IDs as listed on scrollprize.org/prizes (read 2026-10-21; tools/catalog_eligible.py), May session
VOLUMES = {"PHerc0175A": "20250521115057", "PHerc0175B": "20250521125822", "PHerc0268": "20251110183117",
           "PHerc0306B": "20250521133212", "PHerc0483A": "20250521140913", "PHerc0483B": "20251124083638",
           "PHerc0490A": "20250521151210", "PHerc0490B": "20250521151215", "PHerc0800": "20250521135224",
           "PHerc1218": "20250521120456"}
M7 = "-surface-20260413222639-surface-m7-L0-th0.2"


def main():
    rows = []
    for s, v in VOLUMES.items():
        props, vol, pred = catalogue_paths(s, v)
        nz = json.loads(get(f"{B}/{urllib.parse.quote(vol)}0/.zarray"))["shape"][0]
        base = f"{s}/representations/predictions/surfaces/{v}{M7}"
        has_pred = get(f"{B}/{urllib.parse.quote(base)}.zarr/0/.zarray") is not None
        lst = get(f"{B}/?list-type=2&max-keys=2&prefix={urllib.parse.quote(base + '.normal-grids/')}")
        has_ng = lst is not None and b"<Key>" in lst
        row = {"sample": s, "volume_id": v, "voxel_um": props.get("pixel_size_um"), "slices": nz,
               "m7_prediction": has_pred, "normal_grids": has_ng}
        rows.append(row)
        print(json.dumps(row), flush=True)
    out = ROOT / "data/m1/survey_volumes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
