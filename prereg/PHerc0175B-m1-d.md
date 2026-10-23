# Pre-registered readout: PHerc0175B, M1 batch D (zone B windings 4–7; outer zone H)

This was committed before any Hecate output on these seven meshes existed. It follows `prereg/PHerc0175B-m1-c.md`,
and through it `prereg/PHerc0175B-m1-b.md`, in everything not stated here. After this commit the rules do not change
for these runs; deviations get appended below, dated, before the target output is opened.

## Why these meshes
- Zone B (z 7944, mid-radius r55_a225) gave the best geometry so far, so it gets four more windings beyond B1–B3:
  two inward of B2 and two outward of B3 (`m1/seeds_radial.py`).
- Zones E and F were grown but are not read, because their geometry folded (`docs/decisions.md`).
- Zone H (z 10326, outer r80_a090) is on the far side of the scroll from meshes 1–4. It passed the level-1 gate with a
  merged share of 0.156.

## Target

| Mesh | Zone | Seed (x, y, z) | Grown | Interior contact quads | Readout area | Geometry confidence |
|---|---|---|---|---|---|---|
| B4 `auto_grown_20261022112556831` | B | (3909, 3544, 7944) | 7.78 cm² | 2,818 | 3.78 cm² | normal |
| B5 `auto_grown_20261022113517001` | B | (3945, 3580, 7944) | 7.62 cm² | 1,339 | 4.30 cm² | normal |
| B6 `auto_grown_20261022113913756` | B | (3833, 3468, 7944) | 7.60 cm² | 4,548 | 4.24 cm² | normal |
| B7 `auto_grown_20261022114237201` | B | (3824, 3459, 7944) | 7.88 cm² | 3,825 | 4.23 cm² | normal |
| H1 `auto_grown_20261022115152504` | H | (4912, 8037, 10326) | 7.95 cm² | 9,679 | 3.47 cm² | low |
| H2 `auto_grown_20261022120053693` | H | (4912, 8020, 10326) | 8.31 cm² | 9,791 | 2.76 cm² | low |
| H3 `auto_grown_20261022120727005` | H | (4912, 8051, 10326) | 8.05 cm² | 6,651 | 3.62 cm² | low |

- **Distinct sheets** (`m1/qc_meshes.py`):
  - Across zone B's seven meshes, the closest pairs (B4–B5, B6–B3, B7–B2) are 10–12 voxels apart at the median, with
    ≤ 3.1% of points within 3 voxels. Those are adjacent sheets in a compressed zone, not duplicates.
  - In zone H, the pairs are 15–39 voxels apart at the median, with ≤ 1.3% of points within 3 voxels.
- **Everything else** is as in m1-c:
  - growth settings and render (48 layers, smooth, resampled to 9.604 µm);
  - Hecate (same sha256s, bf16, batch 4, stride 32) with windows k = −2..+2 forward and reverse, through `gpu_guard`;
  - the probability-mean ensemble per direction and the input crop to the readout bbox + 128 px;
  - the readout area: centre layer > 0, ≥ 16 cells from the mesh boundary, excluding 8 cells around self-crossings.

## Positive controls and threshold
- The E1b control gives T = **0.445**.
- The E1d pipeline control passed on PHerc0343.

## Candidate rules, escalation and verdict sentences
- As in m1-b and m1-c: `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9).
- The share ≥ T is reported against the control background's 1.2%.
- Candidates are judged by eye, using each mesh's grid orientation to know which way a text line would run, and by the
  escalation rule only.
- One verdict sentence per mesh:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters."

## Deviations
- (none)
