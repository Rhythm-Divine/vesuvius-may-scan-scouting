# Pre-registered readout: M1 batch F2 (test surfaces in new zones from the scouting at 12 new heights)

This was committed before any Hecate output on these surfaces existed. It follows `prereg/M1-batch-F1.md` (and through
it batch E and the earlier pre-registrations) in every rule not stated here, including the QC gate. After this commit
the rules do not change for these runs; deviations get appended below, dated, before the target output is opened.

## Why these surfaces
- **Scouting:** E2c ran at 12 new heights with 8 directions per radius (`e2/zoom.py --angles 8`):
  - PHerc0175B at z 3176, 4368, 6752, 9136, 11520 and 12712;
  - PHerc0490A at z 2328, 3208, 4968, 6724, 8476 and 9352.
- **Choice:** together with the earlier heights, 45 crops pass the level-1 gate (merged ≤ 0.17, ≥ 20 crossings, ≥ 90%
  inside the CT). That gate has proved weak, so nine zones were chosen by eye from a contact sheet of the gated crops:
  clean, parallel, separated sheets, not overlapping any zone already grown.
- **One test surface per zone,** seeded by `m1/seed.py` at the crop centre. The surfaces were grown, rendered and
  QC'd by `m1/batch/grow_batchF2.sh`.
- **Read:** only the surfaces that pass the gate, ≥ 2 cm² clean and ≥ 0.8 on papyrus (`m1/onpapyrus.py`).

## Target (passed the QC gate)

| Surface | Scroll and zone | Seed (x, y, z) | Grown | Contacts | Readout area | On papyrus | Geometry confidence |
|---|---|---|---|---|---|---|---|
| F-d `auto_grown_20261023043929419` | 0175B z 12712 r55_a112 | (3690, 6951, 12712) | 8.91 cm² | 8,504 | 2.08 cm² | 0.910 | low |
| F-e `auto_grown_20261023045946231` | 0175B z 6752 r80_a225 | (3090, 2514, 6750) | 8.16 cm² | 11,288 | 3.12 cm² | 0.997 | normal |
| F-f `auto_grown_20261023051139630` | 0490A z 8476 r55_a067 | (5110, 6629, 8476) | 8.06 cm² | 8,212 | 3.41 cm² | 0.991 | normal |
| F-g `auto_grown_20261023053515135` | 0490A z 9352 r80_a135 | (2631, 6932, 9350) | 7.93 cm² | 7,350 | 3.79 cm² | 0.998 | normal |
| F-h `auto_grown_20261023054634538` | 0175B z 9136 r55_a337 | (6790, 4336, 9135) | 8.38 cm² | 12,361 | 3.09 cm² | 0.990 | normal |
| F-i `auto_grown_20261023055805094` | 0490A z 4968 r30_a045 | (5180, 4840, 4971) | 8.29 cm² | 9,783 | 3.14 cm² | 0.999 | normal |

- **Geometry confidence:** "low" means a readout area under 3 cm². The papyrus share is the main geometry check
  now.
- **Not read (failed the gate):** three zones folded, with 24k–37k contacts:
  - 0490A z 8476 r80_a045 (`auto_grown_20261023045004407`): 1.56 cm² clean;
  - 0175B z 6752 r80_a045 (`auto_grown_20261023052323370`): 1.56 cm²;
  - 0490A z 4968 r55_a157 (`auto_grown_20261023060905473`): 1.07 cm².
- **Distinct** from every surface grown so far in the same scroll (`m1/qc_meshes.py`): the closest medians are
  944–1,777 voxels. The exception is F-i, which lies 188 voxels from F-a (F1, z 5848 r30_a090). All have 0% of points
  within 3 voxels.
- **Everything else is as in batch F1:** render, Hecate (same sha256s; bf16, batch 4, through `gpu_guard`), windows
  k = −2..+2 in both directions, the probability-mean ensemble, the input crop, and the readout area.

## Threshold, candidate rules, escalation and verdict sentences
- T = **0.445** (E1b).
- `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9). The share ≥ T is reported against the control
  background's 1.2%.
- Candidates are judged by eye, using lines of constant z on the review sheets. They are checked for recurrence on
  neighbouring surfaces where these exist (`m1/cross_winding.py`), and by the escalation rule of
  `prereg/PHerc0175B-m1.md` only.
- One verdict sentence per surface:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
