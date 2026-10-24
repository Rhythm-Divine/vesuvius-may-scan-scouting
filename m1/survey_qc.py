"""M1 survey: the QC row for one grown surface (prereg/M1-survey-S1.md).

Prints tab-separated: grown area (cm2), self-crossing contacts, clean readout area (cm2), papyrus share, and the
decision. The decision is "keep" (>= 2 cm2 clean and >= 0.8 on papyrus), "drop", or "failed" when a QC input is
missing.
Usage: python m1/survey_qc.py DATA_DIR MESH     (DATA_DIR = data/m1/<SAMPLE>)
"""
import json
import re
import sys
from pathlib import Path

o, m = Path(sys.argv[1]), sys.argv[2]
try:
    area = json.loads((o / "meshes" / m / "meta.json").read_text())["area_cm2"]
    log = (o / "render" / f"{m}_selfcross.log").read_text()
    contacts = sum(int(n) for n in re.findall(r"(\d+) (?:contacts )?on diagonal", log))
    clean = json.loads((o / "render" / f"{m}_clean.json").read_text())["valid_cm2"]
    pap = json.loads((o / "render" / f"{m}_onpapyrus.json").read_text())["on_papyrus_share"]
except (OSError, KeyError, ValueError):
    print("-\t-\t-\t-\tfailed")
    sys.exit(0)
keep = clean >= 2.0 and pap is not None and pap >= 0.8
print(f"{area:.2f}\t{contacts}\t{clean:.3f}\t{pap}\t{'keep' if keep else 'drop'}")
