# Pre-registered readout: PHerc0175B, M1 zones B and C (six meshes in deeper zones)

This was committed before any Hecate output on these six meshes existed. It follows `prereg/PHerc0175B-m1-b.md` in
everything not stated here, and the same rules apply. After this commit they do not change for these runs; deviations
get appended below, dated, before the target output is opened.

## Why these zones
- The E1d pipeline control passed: our chain shows the PHerc0343 First Letters text line. So the four outer-zone
  negatives (meshes 1–4) stand, and the search moves deeper.
- Both zones passed the E2c level-1 separability gate (merged share ≤ 0.17).
  - **Zone B:** z 7944, r55_a225, mid-radius. Separated sheets with air gaps, merged share 0.12.
  - **Zone C:** z 5560, r30_a090, inner. Merged share 0.10.

## Target
- **Volume, growth settings, render, model, windows, directions, ensemble and input crop:** as in
  `prereg/PHerc0175B-m1-b.md`.
- **Seeds:** the thin-sheet prediction voxel nearest each zone centre (`m1/seed.py`), plus one winding inward and one
  outward on its radial line (`m1/seeds_radial.py`). Growth ran through `m1/zones_bc.sh` → `m1/grow_more.sh`.

  | Mesh | Zone | Seed (x, y, z) | Grown | Interior contact quads | Readout area |
  |---|---|---|---|---|---|
  | B1 `auto_grown_20261022074119260` | B | (3866, 3501, 7944) | 7.63 cm² | 1,583 | 4.35 cm² |
  | B2 `auto_grown_20261022075017447` | B | (3873, 3508, 7944) | 7.59 cm² | 2,099 | 4.46 cm² |
  | B3 `auto_grown_20261022075424029` | B | (3849, 3484, 7944) | 7.60 cm² | 1,953 | 4.51 cm² |
  | C1 `auto_grown_20261022080225012` | C | (4803, 5591, 5559) | 8.40 cm² | 19,093 | 2.58 cm² |
  | C2 `auto_grown_20261022081222870` | C | (4803, 5574, 5559) | 8.76 cm² | 31,855 | 1.81 cm² |
  | C3 `auto_grown_20261022081650324` | C | (4803, 5696, 5559) | 8.16 cm² | 13,707 | 3.07 cm² |

- **Distinct sheets** (`m1/qc_meshes.py`):
  - Within zone B, the median nearest-point separations are 21.7–59.0 voxels, with ≤ 0.1% of points within 3 voxels.
    B2's seed sits 10 voxels from B1's, but B2 grew on a different sheet.
  - Within zone C, C1 and C2 are 23–25 voxels apart (0.4% within 3), and C3 is 157–198 voxels from both.
- **Readout area:** as in m1-b. The centre layer must be > 0, the mesh interior is ≥ 16 cells from the boundary, and
  cells within 8 cells of any self-crossing contact are excluded.
- **Geometry confidence:**
  - Zone C meshes cross themselves heavily: 13.7k–31.9k contact quads inside the interior, and nodes 170–380 voxels
    from the neighbouring mesh at p90. They probably switch sheets in places.
  - Their verdicts are reported as **low-confidence geometry**. A zone C "no ink" is weaker evidence than a zone B one.

## Positive control and threshold
- E1b; T = **0.445**.
- The E1d pipeline control passed on PHerc0343 with the same settings.

## Candidate rules, escalation and verdict sentences
- As in `prereg/PHerc0175B-m1-b.md`: `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9).
- The share ≥ T is reported against the control background's 1.2%.
- Candidates are judged by eye and by the escalation rule only.
- One verdict sentence per mesh:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters."

## Deviations
- (none)
