"""Stand-in for nvidia-smi in the gpu_guard tests: answers the two queries from a JSON state file.

State file (path in $FAKE_NVSMI_STATE): {"free_mib": int, "apps": [[pid, used_mib], ...], "fail": bool}
"""
import json
import os
import sys

with open(os.environ["FAKE_NVSMI_STATE"]) as f:
    state = json.load(f)
if state.get("fail"):
    sys.exit(9)
query = next((a for a in sys.argv[1:] if a.startswith("--query-")), "")
if query.startswith("--query-gpu="):
    print(f"0, {state['free_mib']}")
elif query.startswith("--query-compute-apps="):
    for pid, mib in state.get("apps", []):
        print(f"{pid}, {mib}")
else:
    sys.exit(2)
