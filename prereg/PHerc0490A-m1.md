# Pre-registered readout: PHerc0490A, M1 batch 1 (mid-radius zone r55_a225)

This was committed before any Hecate output on PHerc0490A existed. Except for the target, it follows the PHerc0175B
pre-registrations (`prereg/PHerc0175B-m1-b.md` to `-d.md`) in every rule. After this commit the rules do not change for
these runs; deviations get appended below, dated, before the target output is opened.

## Target
- **Volume:** PHerc0490A / 20250521151210, 8.64 µm, 116 keV (BM18, May 2025).
  - Masked CT: `PHerc0490A/volumes/20250521151210-8.640um-1.2m-116keV-masked.zarr` (open-data bucket).
  - m7 prediction: `20250521151210-surface-20260413222639-surface-m7-L0-th0.2.zarr`, with its published normal grids.
- **Why this scroll and zone:**
  - PHerc0490A is the second-ranked least-searched May volume (E2b). Its only public search was one shallow ink_9um
    pass.
  - E2c gated six zones. One test surface per promising zone was grown, and zone z 5848 r55_a225 kept the most clean
    area (`docs/decisions.md`).
- **Meshes:** grown by `m1/grow_more.sh` (`SAMPLE=PHerc0490A`) with the same settings as the PHerc0175B meshes. The four
  neighbour seeds come from `m1/seeds_radial.py --prefix`.

  | Mesh | Zone | Seed (x, y, z) | Grown | Interior contact quads | Readout area | Geometry confidence |
  |---|---|---|---|---|---|---|
  | P1 `auto_grown_20261022174346125` | z 5848 r55_a225 | (3161, 2841, 5848) | 7.94 cm² | 7,060 | 4.06 cm² | normal |
  | P2 `auto_grown_20261022175903212` | same, inward | (3172, 2852, 5848) | 7.90 cm² | 10,338 | 3.82 cm² | normal |
  | P3 `auto_grown_20261022180912923` | same, inward | (3180, 2860, 5848) | 8.00 cm² | 21,331 | 3.38 cm² | low |
  | P4 `auto_grown_20261022181232834` | same, outward | (3149, 2829, 5848) | 7.99 cm² | 7,645 | 3.65 cm² | normal |
  | P5 `auto_grown_20261022181555183` | same, outward | (3140, 2820, 5848) | 7.81 cm² | 6,766 | 3.95 cm² | normal |
  | Q1 `auto_grown_20261022172303661` | z 7600 r55_a225 | (3148, 3536, 7599) | 8.71 cm² | n/a | 2.51 cm² | low |

- **Distinct sheets** (`m1/qc_meshes.py` over P1–P5): the closest pairs are 12.5–15.8 voxels apart at the median, with
  ≤ 1.8% of points within 3 voxels. They are adjacent sheets, not duplicates.
- **Readout area:** the render centre layer > 0, ≥ 16 grid cells from the mesh boundary, and > 8 cells from any
  self-crossing contact.
- **Render, model, windows, directions, ensemble and crop:** as for PHerc0175B.
  - Render: 48 layers, smooth, resampled to 9.604 µm.
  - Model: Hecate 9.6 µm (same sha256s), bf16, batch 4, stride 32, through `gpu_guard`.
  - Windows k = −2..+2 (layers 13+k..28+k), forward and reverse, each read separately; probability-mean ensemble.
  - Input cropped to the readout bbox + 128 px.

## Positive controls and threshold
- E1b (PHerc0009B) gives T = **0.445**.
- The E1d pipeline control (PHerc0343) passed.

## Candidate rules, escalation and verdict sentences
- `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9).
- The share ≥ T is reported against the control background's 1.2%.
- Candidates are judged by eye, using each mesh's grid orientation to know which way a text line would run, and by the
  escalation rule only: reappearance under a second independent model or seed, with rows parallel to the horizontal
  fibres.
- One verdict sentence per mesh:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
