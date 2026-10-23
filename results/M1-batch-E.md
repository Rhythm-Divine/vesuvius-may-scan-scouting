# Result: M1 batch E (PHerc0175B zone B windings 8 and 10, zone G; PHerc0490A windings 6–9), read under `prereg/M1-batch-E.md` (7ed51cd)

**Verdict for each of B8, B10, G1, P6, P7, P8 and P9 (pre-registered sentence 1): "I didn't see any ink in the region."**
- B10, G1 and P7 are low-confidence geometry, as pre-registered.
- **G1 is a geometry failure and is not counted as searched area.** Only 12% of its readout area sits on papyrus. The
  surface left the sheet and ran into air.

## What ran
- All 70 Hecate outputs exist: 7 surfaces × windows −2..+2 × forward and reverse.
- They ran 03:07–05:46 UTC on 23 Oct with no GPU yield, sharing the A10G with another job. Runs took 2–2.5 min each.

## Mechanical readout (`readout.json` per surface). Control background: 1.2% of the area ≥ T.

| Surface | Zone | Readout area | On papyrus | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|---|---|
| B8 `020844456` | 0175B zone B, inward of B5 | 3.91 cm² | 0.985 | 7 / 0.047 / 0.8% | 20 / 0.074 / 2.3% |
| B10 `022208529` | 0175B zone B, outward of B7 (low-confidence) | 2.44 cm² | 0.972 | 5 / 0.080 / 4.7% | 7 / 0.056 / 2.0% |
| G1 `023052075` | 0175B z 10341 r80_a270 (low-confidence) | 2.35 cm² | **0.123** | 0 / 0.023 / 1.6% | 0 / 0.007 / 0.0% |
| P6 `024102270` | 0490A z 5848, inward of P3 | 3.93 cm² | 0.994 | 9 / 0.050 / 0.8% | 2 / 0.045 / 0.5% |
| P7 `025022991` | 0490A z 5848, further inward (low-confidence) | 2.84 cm² | 0.991 | 2 / 0.049 / 0.4% | 2 / 0.043 / 0.3% |
| P8 `025330909` | 0490A z 5848, outward of P5 | 4.24 cm² | 0.989 | 16 / 0.053 / 1.7% | 7 / 0.034 / 0.5% |
| P9 `025629824` | 0490A z 5848, further outward | 4.04 cm² | 0.991 | 15 / 0.051 / 1.6% | 4 / 0.036 / 0.6% |

**On papyrus** (`m1/onpapyrus.py`) is the share of readout cells whose brightest level-1 CT voxel within ±2 voxels of
the mesh vertex is above 90. Air reads about 40–60 and papyrus about 100–150. It was computed after the readout as a
diagnostic and is now a QC gate from batch F1 on.

## Why the verdict is "no ink"
Each surface was read from its quarter-resolution review sheet (`m1/sheets.py`). The sheet carries dotted lines of
constant z, which show where a line of text would run. The strongest features were then checked on full-resolution
crops (CT | forward | reverse) and per depth window.

- **B8:** speckle in both directions. Its largest reverse cluster has a forward counterpart at the same place, which
  makes it two-sided: structure.
- **B10: the strongest one-sided response of M1 so far, and still not ink.**
  - In the forward direction, an upper-left cluster fills 13% of a 7.7 mm square at ≥ T, against 2% in reverse. It is
    present in all five depth windows (8–15%).
  - At full resolution it is soft round blobs 1–2 mm across. It sits at the edge of large voids that dominate the CT
    layers just below the surface.
  - It has no strokes and no rows along the lines of constant z.
  - B10's other bright band, in the lower left, is two-sided (11% reverse, 5% forward) and lies along a fold edge.
- **G1:** the render is air noise (layer-21 median 50) over most of the readout area. Hecate is near zero except at
  fold edges.
- **P6:** clean crosshatched papyrus in the CT, both fibre directions visible, and only soft blobs in both directions.
  A faint column of blobs along the lines of constant z appears in reverse as well (1.5% vs 1.2%).
- **P7:** the quietest surface of the batch (0.4% and 0.3% ≥ T). It shows fine speckle in both directions. Its
  only concentration lies along the edge of an excluded contact zone.
- **P8 and P9: one-sided streaks that are cracks.**
  - The forward ensembles show elongated streaks about 1 mm wide and 4–5 mm long, one of them a parallel pair.
  - In every depth window they follow dark cracks visible in the CT layers just below the surface.
  - `m1/cross_winding.py` maps the pair to 3D and looks at the same place on the neighbouring windings:
    - it recurs with the same double shape on P9 (13 voxels away, forward, 13.5% ≥ T) and on P5 (3.5 voxels, reverse,
      22%);
    - more weakly on P4 and P1 (26 and 25 voxels away, 7.5% and 4.2%);
    - not on P2 or P3 (57 and 72 voxels away, 0%).
  - A mark that runs through five windings is a crack, not writing.
  - P8's second streak also recurs on P9 and P1.
- **Escalation:** none. No candidate forms rows.

## QC lesson: the papyrus share
- G1 passed every existing gate: the level-1 merged share, the clean area after the contact exclusion, and
  distinctness. Yet it is 88% air.
- `m1/onpapyrus.py` needs no render. It samples the level-1 CT at the mesh vertices, so it was also run on every
  earlier surface:
  - 0.973–0.998 for the 17 PHerc0175B surfaces of batches m1 to m1-d;
  - 0.991–0.996 for the 6 PHerc0490A surfaces of batch 1.
- So the areas reported before batch E stand. From batch F1 on, a surface is read only with ≥ 2 cm² clean and
  ≥ 0.8 on papyrus.

## Running total for M1 (every surface verdict 1; G1 not counted)

| Scroll | Surfaces read | Readout area on papyrus |
|---|---|---|
| PHerc0175B | 19 | 72.5 cm² |
| PHerc0490A | 10 | 36.4 cm² |
| **Total** | **29** | **≈ 109.0 cm²** |
