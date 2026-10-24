# Result: M1 batches F2 (six new zones) and F3 (five windings around F-b), read under `prereg/M1-batch-F2.md` (5dcf094) and `prereg/M1-batch-F3.md` (f0008b9)

**Verdict for every one of the 11 surfaces (pre-registered sentence 1): "I didn't see any ink in the region."**
F-d is low-confidence geometry, as pre-registered.

## What ran
- All 110 Hecate outputs exist: 11 surfaces × windows −2..+2 × forward and reverse.
- F2 ran 14:19–17:03 UTC on 23 Oct and F3 ran 17:03–19:50, through `gpu_guard` with no yield.
- They were read at 21:40 UTC, after a session restart. While no readout was waiting, the GPU slot sat idle.

## Mechanical readout. Control background: 1.2% of the area ≥ T.

| Surface | Scroll and zone | Readout area | On papyrus | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|---|---|
| F-d `043929419` | 0175B z 12712 r55_a112 (low-confidence) | 2.08 cm² | 0.910 | 5 / 0.042 / 0.9% | 8 / 0.055 / 1.7% |
| F-e `045946231` | 0175B z 6752 r80_a225 | 3.12 cm² | 0.997 | 8 / 0.061 / 2.4% | 6 / 0.048 / 0.7% |
| F-h `054634538` | 0175B z 9136 r55_a337 | 3.09 cm² | 0.990 | 1 / 0.044 / 0.3% | 3 / 0.034 / 0.4% |
| F-f `051139630` | 0490A z 8476 r55_a067 | 3.41 cm² | 0.991 | 3 / 0.039 / 0.3% | 4 / 0.044 / 0.5% |
| F-g `053515135` | 0490A z 9352 r80_a135 | 3.79 cm² | 0.998 | 0 / 0.023 / 0.1% | 1 / 0.024 / 0.1% |
| F-i `055805094` | 0490A z 4968 r30_a045 | 3.14 cm² | 0.999 | 1 / 0.015 / 0.1% | 5 / 0.020 / 0.4% |
| W−2 `063936079` | 0490A z 5848 r80_a180, 2nd winding outward of F-b | 4.67 cm² | 0.998 | 3 / 0.035 / 0.2% | 1 / 0.025 / 0.1% |
| W−1 `063611269` | same, 1st winding outward | 4.44 cm² | 0.998 | 3 / 0.040 / 0.5% | 8 / 0.045 / 0.4% |
| W+1 `062021742` | same, 1st winding inward | 4.02 cm² | 0.998 | 6 / 0.049 / 1.0% | 3 / 0.039 / 0.3% |
| W+2 `063007803` | same, 2nd winding inward | 3.95 cm² | 0.999 | 3 / 0.046 / 0.4% | 1 / 0.039 / 0.3% |
| W+3 `063306375` | same, 3rd winding inward | 4.32 cm² | 0.999 | 2 / 0.033 / 0.3% | 1 / 0.029 / 0.2% |
| **Total** | | **40.03 cm²** | | | |

## Why the verdict is "no ink"
- **The quietest batch so far.** Nine of the eleven surfaces sit below the control background in both directions.
  The F3 windings, in the cleanest geometry of M1, show uniform faint speckle on both faces.
- **F-e forward: one-sided, but a cloud, not writing.** It fills 13.7% of a 7.7 mm square at ≥ T, against 2.1% in
  reverse. At full resolution it is a broad, shapeless blob about 4 mm across, lying along diagonal cracks in the CT,
  with no strokes and no rows along the lines of constant z.
- **F-d reverse, F-h and F-i:** small clusters along the edges of excluded fold zones, partly two-sided.
  - F-i's short reverse blob chain reaches only 0.7–1.0% ≥ T in its square.
- **F-f's reverse speckle** lies in a broad diagonal band, at 0.5% ≥ T: diffuse texture, not marks.
- **W+3 forward:** a single blob group about 2 mm across beside a fold edge (2.3% against 0.1% reverse). It is one
  cluster, not a row of glyphs.
- **F-b's reverse band, checked across windings** (`m1/cross_winding.py`, from F-b crop (520, 2000)):
  - It does not recur on the nearest neighbour, W−1 (24 voxels away, 0.0% ≥ T).
  - W+1 (32 voxels away) shows 6.6% forward at its nearest point. W+2, W−2 and W+3 show 0–1%.
  - None of the neighbours comes within 21 voxels of that spot, so this check is weak there. F-b's verdict rests on
    the feature's morphology and its orientation across the text direction.
- **Escalation:** none. No candidate forms rows.

## Running total for M1 (every surface verdict 1; G1 not counted)

| Scroll | Surfaces read | Readout area on papyrus |
|---|---|---|
| PHerc0175B | 22 | 80.8 cm² |
| PHerc0490A | 21 | 77.7 cm² |
| **Total** | **43** | **≈ 158.5 cm²** |
