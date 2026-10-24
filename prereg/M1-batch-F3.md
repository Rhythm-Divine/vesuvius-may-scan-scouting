# Pre-registered readout: M1 batch F3 (PHerc0490A z 5848 r80_a180, five windings around F-b)

This was committed before any Hecate output on these five surfaces existed. It follows `prereg/M1-batch-F1.md` in
every rule not stated here, including the QC gate (≥ 2 cm² clean and ≥ 0.8 on papyrus). After this commit the rules
do not change for these runs; deviations get appended below, dated, before the target output is opened.

## Why these surfaces
- F-b (batch F1) is the cleanest surface of M1 so far: 3,181 self-crossing contacts and 4.47 cm² clean.
- Its zone gets the neighbouring windings: two outward and three inward along the radial line through F-b's seed
  (`m1/seeds_radial.py --inward 3 --outward 2`, centre (y, x) = (4134, 4454)).
- They were grown, rendered and QC'd by `m1/batch/grow_batchF3.sh`.
- They also allow F-b's strongest features to be checked for recurrence on the neighbouring windings
  (`m1/cross_winding.py`).

## Target (all five passed the QC gate)

| Surface | Position | Seed (x, y, z) | Grown | Contacts | Readout area | On papyrus | Geometry confidence |
|---|---|---|---|---|---|---|---|
| W−2 `auto_grown_20261023063936079` | 2nd winding outward of F-b | (1761, 4132, 5847) | 7.55 cm² | 2,091 | 4.67 cm² | 0.998 | normal |
| W−1 `auto_grown_20261023063611269` | 1st winding outward | (1777, 4132, 5847) | 7.64 cm² | 2,782 | 4.44 cm² | 0.998 | normal |
| W+1 `auto_grown_20261023062021742` | 1st winding inward | (1816, 4132, 5847) | 7.79 cm² | 6,981 | 4.02 cm² | 0.998 | normal |
| W+2 `auto_grown_20261023063007803` | 2nd winding inward | (1832, 4132, 5847) | 7.81 cm² | 7,865 | 3.95 cm² | 0.999 | normal |
| W+3 `auto_grown_20261023063306375` | 3rd winding inward | (1845, 4132, 5847) | 7.73 cm² | 4,861 | 4.32 cm² | 0.999 | normal |

- **Distinct sheets** (`m1/qc_meshes.py`):
  - The closest pair is W+1 and W+2: median 9.3 voxels, 3.5% of points within 3 voxels. They are adjacent sheets in a
    compressed stretch, as with zone B's B4 and B5 (10–12 voxels, ≤ 3.1%), not duplicates (a median under 4 voxels).
  - Every other pair is 12.6 voxels or more apart at the median, with ≤ 1.7% within 3 voxels. W−1 lies 20.7 voxels
    from F-b.
- **Everything else is as in batch F1:** render, Hecate (same sha256s; bf16, batch 4, through `gpu_guard`), windows
  k = −2..+2 in both directions, the probability-mean ensemble, the input crop, and the readout area.

## Threshold, candidate rules, escalation and verdict sentences
- T = **0.445** (E1b).
- `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9). The share ≥ T is reported against the control
  background's 1.2%.
- Candidates are judged by eye, using lines of constant z on the review sheets. They are checked for recurrence on
  the neighbouring windings (`m1/cross_winding.py`), and by the escalation rule of `prereg/PHerc0175B-m1.md` only.
- One verdict sentence per surface:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
