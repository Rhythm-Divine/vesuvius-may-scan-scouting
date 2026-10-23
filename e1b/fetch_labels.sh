#!/usr/bin/env bash
# Fetch the organisers' same-mesh PHerc0009B ink labels (2026-09-18: ink, supervision, validation) at level 2 (9.604 um,
# zarr v3, one shard each, ~100 KB in total) from the open-data bucket into data/e1b/labels, for e1b/register.py and
# e1b/score.py.
set -euo pipefail
R="${VES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"; cd "$R"
P="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0009B/segments/20250919125754-auto_grown_20250919055754487_inp_hr/ink-labels/2.401um-volume-20250820154339/20260918"
O=data/e1b/labels
for z in inklabels supervision validation; do
  mkdir -p "$O/$z.zarr/2/c/0"
  curl -sS --fail -o "$O/$z.zarr/zarr.json" "$P/$z.zarr/zarr.json"
  curl -sS --fail -o "$O/$z.zarr/2/zarr.json" "$P/$z.zarr/2/zarr.json"
  curl -sS --fail -o "$O/$z.zarr/2/c/0/0" "$P/$z.zarr/2/c/0/0"
done
du -sh "$O"
