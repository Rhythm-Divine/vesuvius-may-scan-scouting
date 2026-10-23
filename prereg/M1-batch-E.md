# Pre-registered readout: M1 batch E (PHerc0175B zone B windings 8 and 10, zone G; PHerc0490A windings 6–9)

This was committed before any Hecate output on these seven surfaces existed. It follows `prereg/PHerc0175B-m1-d.md`
(PHerc0175B) and `prereg/PHerc0490A-m1.md` (PHerc0490A) in every rule not stated here. After this commit the rules do
not change for these runs; deviations get appended below, dated, before the target output is opened.

## Why these surfaces
- The search continues in the zones the geometry checks rate cleanest. These are PHerc0175B zone B (z 7944 r55_a225)
  and PHerc0490A z 5848 r55_a225.
- It adds one test surface in an untried gated zone: PHerc0175B zone G, z 10328 r80_a270, level-1 merged share 0.059.
- Seeds come from `m1/seeds_radial.py` beyond the outermost and innermost windings already read in each zone, and from
  `m1/seed.py` for zone G.

## Target

| Surface | Scroll and zone | Seed (x, y, z) | Grown | Readout area | Geometry confidence |
|---|---|---|---|---|---|
| B8 `auto_grown_20261023020844456` | 0175B zone B, inward of B5 | (3988, 3623, 7944) | 7.81 cm² | 3.91 cm² | normal |
| B10 `auto_grown_20261023022208529` | 0175B zone B, outward of B7 | (3799, 3434, 7944) | 8.49 cm² | 2.44 cm² | low |
| G1 `auto_grown_20261023023052075` | 0175B zone G, z 10341 r80_a270 | (4934, 2312, 10341) | 7.81 cm² | 2.35 cm² | low |
| P6 `auto_grown_20261023024102270` | 0490A z 5848, inward of P3 | (3189, 2869, 5848) | 7.78 cm² | 3.93 cm² | normal |
| P7 `auto_grown_20261023025022991` | 0490A z 5848, further inward | (3237, 2917, 5848) | 8.26 cm² | 2.84 cm² | low |
| P8 `auto_grown_20261023025330909` | 0490A z 5848, outward of P5 | (3132, 2812, 5848) | 7.69 cm² | 4.24 cm² | normal |
| P9 `auto_grown_20261023025629824` | 0490A z 5848, further outward | (3125, 2805, 5848) | 7.76 cm² | 4.04 cm² | normal |

- **Not read:** B9 `auto_grown_20261023021753343` (seed 3809, 3444, 7944) kept only 1.85 cm² of clean area.
- **Distinct sheets**, measured from each new surface to every surface already grown in its zone:
  - The medians are 9.4–21 voxels, with ≤ 3.6% of points within 3 voxels (closest: B8 to B1, 9.4 voxels, 3.6%).
  - G1 lies about 1,000 voxels from the PHerc0175B outer windings 1–4. It is all new area.
- **Readout area, render, model, windows, directions, ensemble and input crop:** as in the m1-b to m1-d
  pre-registrations.
  - Readout area: the centre layer > 0, ≥ 16 cells from the mesh boundary, and > 8 cells from any self-crossing contact.
  - Hecate 9.6 µm (same sha256s), bf16, batch 4, through `gpu_guard`.
  - Windows k = −2..+2, forward and reverse read separately, with the probability-mean ensemble.
  - The input is cropped to the readout bbox + 128 px.

## Threshold, candidate rules, escalation and verdict sentences
- T = **0.445** (E1b).
- `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9). The share ≥ T is reported against the control
  background's 1.2%.
- Candidates are judged by eye, using each grid's orientation, and by the escalation rule only.
- One verdict sentence per surface:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
