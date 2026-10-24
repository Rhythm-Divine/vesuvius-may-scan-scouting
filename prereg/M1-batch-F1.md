# Pre-registered readout: M1 batch F1 (PHerc0490A, three untried gated zones)

This was committed before any Hecate output on these three surfaces existed. It follows `prereg/M1-batch-E.md`, and
through it `prereg/PHerc0490A-m1.md`, in every rule not stated here. After this commit the rules do not change for
these runs; deviations get appended below, dated, before the target output is opened.

## Why these surfaces
- These are the PHerc0490A zones that passed or nearly passed the E2c level-1 gate but had no test surface yet.
- One seed per zone comes from `m1/seed.py` at the gated crop's centre:
  - **F-a**, z 5848 r30_a090: merged share 0.103.
  - **F-b**, z 5848 r80_a180: merged share 0.0 with 47 crossings. It was skipped on 22 Oct as an edge crop, but its
    crop is fully inside the CT.
  - **F-c**, z 7600 r80_a270: merged share 0.15.

## New QC gate, from this batch on (checked before pre-registration)
A surface is read only if both hold:
- the clean readout area (`m1/readout_crop.py`, 8-cell contact exclusion) is ≥ 2 cm²;
- the papyrus share (`m1/onpapyrus.py`) is ≥ 0.8. This is the share of readout cells whose brightest level-1 CT voxel
  within ±2 voxels of the mesh vertex is above 90. Air reads about 40–60 and papyrus about 100–150.

**Why:** batch E's G1 left the papyrus. Its readout area is 12% on papyrus, against 0.97–1.00 for every surface read
before it.

## Target

| Surface | Zone | Seed (x, y, z) | Grown | Contacts | Readout area | On papyrus | Geometry confidence |
|---|---|---|---|---|---|---|---|
| F-a `auto_grown_20261023040557208` | z 5848 r30_a090 | (4449, 5133, 5855) | 8.08 cm² | 25,478 | 2.66 cm² | 0.999 | low |
| F-b `auto_grown_20261023041747890` | z 5848 r80_a180 | (1795, 4132, 5847) | 7.62 cm² | 3,181 | 4.47 cm² | 0.997 | normal |
| F-c `auto_grown_20261023042830254` | z 7600 r80_a270 | (4452, 2156, 7600) | 8.35 cm² | 15,382 | 2.40 cm² | 0.885 | low |

- **Distinct** from every PHerc0490A mesh grown so far (`m1/qc_meshes.py`): the closest medians are 315 voxels (F-b to
  P1), 1,053 (F-c) and 1,322 (F-a), with 0% of points within 3 voxels.
- **Everything else is as in batch E:**
  - render: 48 layers, smooth, resampled to 9.604 µm;
  - Hecate 9.6 µm (same sha256s), bf16, batch 4, through `gpu_guard`;
  - windows k = −2..+2, forward and reverse read separately, with the probability-mean ensemble;
  - input crop: the readout bbox + 128 px;
  - readout area: centre layer > 0, ≥ 16 cells from the mesh boundary, > 8 cells from any self-crossing contact.

## Threshold, candidate rules, escalation and verdict sentences
- T = **0.445** (E1b).
- `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9). The share ≥ T is reported against the control
  background's 1.2%.
- Candidates are judged by eye, using each grid's orientation (lines of constant z on the review sheets), and by the
  escalation rule of `prereg/PHerc0175B-m1.md` only.
- One verdict sentence per surface:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
