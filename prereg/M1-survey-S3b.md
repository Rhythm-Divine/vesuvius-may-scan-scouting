# Pre-registered readout: M1 survey S3b (a closer look at the three escalated S3 rows)

This was committed before any S3b output existed. It follows `prereg/M1-survey-S3.md` in every rule not stated here.
After this commit the rules do not change for S3b; deviations are appended below, dated, before the output they
concern is opened. Rhythm approved S3b on 2026-10-25: "Yes: pre-register and run S3b, the closer look at the three
escalated rows (about 2 h, about $10), then stop aiq-3."

## Why
- **Three rows met S3's escalation rule.** They went to Rhythm privately (`results/M1-survey-S3.md`), and all three
  are verdict 2 (no legible letters):
  - sheet 198, PHerc0483B z10098_r30_a090_o3, p6 reverse;
  - sheet 206, PHerc0483A z4769_r30_a090_i1, m6 forward;
  - sheet 325, PHerc0175A z8923_r30_a225_o1, m6 reverse.
- **The rule cannot settle whether a row is text.** S3b asks three questions:
  1. Does the row continue as a line beyond the surface as grown?
  2. At what depth is it strongest? Ink sits at a face of the sheet; a crack or void can lie anywhere and often
     shows in the CT.
  3. Does the winding that faces it show anything?

## Targets (fixed from S3's outputs by `m3/s3b_prep.py`, before this commit; stored in data/m3b/targets.json)
Boxes are in each surface's S3 crop frame (y0, y1, x0, x1; 9.604 µm px). The row components are the reader-v2
components ≥ T2 of ≥ 300 px in the box, on the S3 map where the row was found. The anchor is their mean centroid and
the axis their principal direction. The seed is the mesh point under the anchor (X Y Z voxels).

| Target | Surface | S3 map | Row box | Anchor | Axis (y, x) | Seed | Facing windings (side: mesh, distance) |
|---|---|---|---|---|---|---|---|
| E1d (control) | PHerc0343 auto_grown_20261023221723612 | near fwd | 1100 1900 820 1420 | 1521.3, 1064.3 | 0.977, 0.214 | 5948 4240 10353 | — |
| 198 | PHerc0483B auto_grown_20261024171724520 | p6 rev | 1950 2450 500 1250 | 2196.3, 898.0 | −0.139, −0.990 | 4344 5516 10819 | plus: auto_grown_20261024171502374, 16.2 vox |
| 206 | PHerc0483A auto_grown_20261024184958725 | m6 fwd | 1380 1720 740 1440 | 1535.8, 1107.5 | −0.061, −0.998 | 3802 5349 4583 | plus: auto_grown_20261023224151702, 46.6; minus: auto_grown_20261024185405569, 30.7 |
| 325 | PHerc0175A auto_grown_20261024214208830 | m6 rev | 1180 1380 40 800 | 1253.9, 414.7 | 0.082, −0.997 | 3249 4434 9152 | plus: auto_grown_20261024213155545, 39.3; minus: auto_grown_20261024214437918, 16.0 |

The facing windings are the nearest windings already read in S1 or S3 on each side of the sheet (the sign of the
mesh normal at the anchor), at least 12 voxels from the row. 198 has none on the minus side.

## What runs (`m3/s3b_row.sh` per target, all four in parallel, one L4 each)
- **Depth sweep of the row's own surface** (`m3/s3b_sweep.sh`), in the row's direction:
  - It renders natively again (48 layers, 8.64 µm, as S3), because the S3 native renders were deleted after reading.
  - reader-v2 runs exactly as in S3 in nine 17-layer windows shifted by −10, −7.5, −5, −2.5, 0, +2.5, +5, +7.5 and
    +10 layers (tags m20 … p20). The model reads the central 17 layers of its input, so trimming 2s layers from one
    end shifts the window by s.
  - Maps are resampled to the 9.604 µm grid and cropped to the S3 crop window (`m3/s3b_combine.py`).
  - Hecate (as S1/S3) runs at the matching depths k = −9, −7, −5, −2, 0, 2, 5, 7, 9 (0.9 × the shift, rounded
    away from 0 at ±4.5). It covers the band box joined with the row box (`m3/s3b_hecate.sh`).
  - The band is the segment anchor ± 1600 px (15.4 mm) along the axis, ± 168 px across it.
- **Facing windings** (not the control): Hecate at the nine depths over the band and row box mapped onto each
  facing winding through 3D (nearest vertex).
- **Longer regrowth** (not the control): `m3/grow_s3b.sh`, which is `m3/grow_s3.sh` with 160 generations instead of
  80, from the seed above, then a native render and the 9.604 µm resample.
  - reader-v2 reads it at the peak window of the row's own sweep only (see below), with Hecate at the matching k
    over the mapped band and row box. It is read over its whole canvas (crop = full).
- **The control E1d** (our PHerc0343 mesh with the known October text line) gets the same depth sweep in its
  forward direction, and the chain test on its own surface.

## Measurements (`m3/s3b_analyse.py`, written down in full in its docstring)
- **Depth test** (row box of the row's own surface):
  - **CT profile:** the mean 9.604 µm render intensity per layer (layer 21 = mesh) over valid box pixels, with a
    3-layer running mean. The sheet is the run of layers at or above half-way between the profile's min and max that
    contains, or is nearest to, layer 21. Its faces are the run's end layers.
  - **Peak window:** the window with the largest reader-v2 share ≥ T2 in the box (ties: the smaller shift). Its centre
    is 0.9 × shift layers on the 9.604 µm grid.
  - **At a face:** the peak centre is within 3 layers of a face.
  - **Not on voids:** of the peak window's ≥ T2 box pixels, at most 0.375 lie on CT voids. Voids are pixels below
    the box's 25th percentile of the render averaged over the 5 layers around the peak centre (1.5 × the 25% a random
    pixel has).
  - **Recorded:** the Hecate share ≥ T per depth, and the agreement at the peak (reader-v2 ≥ T2 within 31 px of
    Hecate ≥ T at the matching k, as in S2/S3).
- **Chain test** (one map at one window, in the band):
  - Components ≥ T2 of ≥ 300 px count if their centroid lies within 1.0 mm (104 px) of the axis line.
  - Start from the component nearest the anchor; it must lie within 1.0 mm of it, or the row is "not found".
  - Chain components along the axis while the gap between their extents is ≤ 3.0 mm.
  - Report the chain length along the axis (mm), its number of components, and the share of its pixels within 31 px
    of Hecate ≥ T at the matching depth.
- **Facing test:** Hecate's share ≥ T per depth in the mapped row box. This is descriptive only.

## Reading (pre-registered)
- **The control must pass first:**
  - E1d's chain on its own surface at its peak window must be ≥ 10 mm, with ≥ 3 components and ≥ 50% agreement.
  - E1d's depth test must find its peak at a face and not on voids.
  - If E1d fails the chain part or the depth part, that part is "uncalibrated". Then no row can be a strong
    candidate, and the rows are reported descriptively.
- **A row is a strong candidate when all of these hold:**
  - **(a) Continuity:** on the longer regrowth, at the row's peak window, the chain starts at the row (within 1.0 mm
    of the mapped anchor), is ≥ 10 mm long, and has ≥ 3 components.
  - **(b) Agreement:** ≥ 50% of the chain's pixels agree with Hecate at the matching depth.
  - **(c) Depth:** on the row's own surface, the peak is at a face and not on voids.
- **A strong candidate** goes to Rhythm privately at once, with the First Letters checklist prepared. Everything
  stays private, and the machine stays up for Rhythm's decision.
- **Otherwise:** each row is reported with the part(s) it failed, and the machine is stopped as Rhythm asked.
- **Unchanged:** verdicts stay as in S3 unless a new by-eye review of the S3b maps sees legible letters (verdict 3).
  Images showing letters stay private.

## Budget and stop
- About 2 h of aiq-3 from the start of the runs. If a regrowth has not produced a mesh within 60 minutes, it is
  stopped and that row's continuity part is reported as "not measured".
- After the results are written and backed up, aiq-3 is stopped, unless a strong candidate appears.

## Deviations
- (none)
