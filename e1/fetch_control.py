"""Fetch the PHerc0009B positive-control surface volume (8.64 um, level 0 + metadata, ~1.0 GB) from the public
Vesuvius Challenge open-data bucket into data/, where e1/prepare.py and e1b/register.py expect it.

Usage: python e1/fetch_control.py
"""
import concurrent.futures as cf
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

B = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
P = ("PHerc0009B/segments/20250919125754-auto_grown_20250919055754487_inp_hr/surface-volumes/"
     "8.64um-1.2m-116keV-volume-20250521125136.zarr/")
ROOT = Path(os.environ.get("VES_ROOT", Path(__file__).resolve().parents[1]))
OUT = ROOT / "data" / P


def list_keys():
    keys, tok = [], None
    while True:
        q = {"list-type": "2", "prefix": P, "max-keys": "1000"}
        if tok:
            q["continuation-token"] = tok
        x = urllib.request.urlopen(f"{B}/?{urllib.parse.urlencode(q)}", timeout=120).read().decode()
        keys += re.findall(r"<Key>([^<]*)</Key>", x)
        m = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", x)
        if not m:
            return keys
        tok = m.group(1)


def get(k):
    dst = OUT / k[len(P):]
    if dst.exists() and dst.stat().st_size > 0:
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):   # the resolver and the bucket occasionally drop a request
        try:
            data = urllib.request.urlopen(f"{B}/{urllib.parse.quote(k)}", timeout=300).read()
            break
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    tmp = dst.with_name(dst.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, dst)
    return len(data)


def main():
    want = [k for k in list_keys() if k[len(P):].split("/")[0] in ("0", ".zattrs", ".zgroup", "metadata.json")]
    with cf.ThreadPoolExecutor(16) as ex:   # network-bound
        n = sum(ex.map(get, want))
    print(f"control volume: {len(want)} objects, {n / 1e9:.2f} GB fetched -> {OUT}")


if __name__ == "__main__":
    main()
