# M1 survey S3b: results (pre-registration `prereg/M1-survey-S3b.md`, db3f7eb)

## Outcome
- **No strong candidate, and nothing new to escalate. The three S3 rows stay verdict 2, with no legible letters.**
- **The control only half passed, so continuity was not a valid test.**
  - E1d's known text line passed the depth test: its peak is at a sheet face (1.2 layers), with 98% agreement and
    not on voids.
  - It failed the continuity test: the chain finder traced only 7.2 mm (3 components) of the known line on its own
    surface, short of the pre-registered 10 mm.
  - As pre-registered, no row could be a strong candidate, and the rows are reported descriptively.
- **The rows, descriptively:**
  - **198** (PHerc0483B, reverse):
    - It is strongest at the mesh (window c). That is 4 layers from the nearest face, so it fails the depth test.
    - On the 160-generation regrowth at that window, the chain is 1.0 mm (one component, 60% agreement).
    - The facing winding o2, 16 voxels away, shows a Hecate blob field (6–17% ≥ T) at every depth.
  - **206** (PHerc0483A, forward):
    - It is strongest 2.2 layers below the mesh, at a face and not on voids, with 85% agreement.
    - On the regrowth, the chain is 9.2 mm (3 components, 73% agreement). It is dominated by one large cloud
      (56k px), with a component 6 mm away; this is the closest to 10 mm.
    - The facing windings, 31 and 47 voxels away, are quiet (≤ 3.4%).
  - **325** (PHerc0175A, reverse):
    - It is strongest at the deepest window (−9 layers, the edge of the sweep). That is at a face and not on voids,
      with 93% agreement.
    - On the regrowth there is nothing ≥ T2 in the band at that window, so the row is not found.
    - The facing winding o2, 16 voxels away on the minus side, rises to 14–17% ≥ T at k = +7..+9, the side facing
      the row. Its plus-side neighbour, 39 voxels away, is quiet.
- **Caveat:** the regrowths are not the same surface. Their mapped anchors lie 5.7–7.6 voxels from the original
  rows, about half a sheet thickness. A row at a fixed window shift can therefore move out of view, and the regrowth
  results are weak evidence either way.
- **By eye:** the regrown bands at each row's peak window show blob fields and clouds, with no letter forms. The
  verdicts are unchanged (no verdict 3).

## Measurements
### Depth test (row box of the row's own surface)

| Target | Sheet faces (layers from mesh) | Peak window (centre, layers) | reader-v2 share >= T2 by shift (-10 ... +10) | Hecate share >= T by k (-9 ... 9) | Agreement at peak | At a face | Void share | Not on voids |
|---|---|---|---|---|---|---|---|---|
| s325 | -7, 1 | m20 (-9.0) | 17.0 16.4 14.5 10.2 3.4 1.9 0.0 0.0 0.9 | 8.4 11.0 15.8 18.3 21.5 10.6 4.4 0.7 2.4 | 0.93 | yes (2.0) | 0.29 | yes |
| s206 | -4, 21 | m5 (-2.2) | 8.6 11.5 14.8 17.6 15.2 12.0 6.3 3.1 1.8 | 5.6 9.0 8.1 8.5 5.1 4.1 2.6 1.3 1.2 | 0.85 | yes (1.8) | 0.24 | yes |
| s198 | -21, 4 | c (+0.0) | 8.4 11.7 16.9 22.3 22.4 17.6 13.1 9.8 7.2 | 7.8 14.6 14.1 15.1 16.1 19.6 17.2 12.8 11.8 | 0.88 | no (4.0) | 0.29 | yes |
| E1d | -6, 1 | p5 (+2.2) | 0.1 0.5 6.2 9.3 11.1 11.8 8.4 4.4 0.0 | 1.8 6.4 12.6 15.0 12.5 9.1 4.1 3.8 4.4 | 0.98 | yes (1.2) | 0.14 | yes |

### Chain test

| Target | Surface | Window / k | Starts at the row | Length (mm) | Components | Agreement | Hecate cover |
|---|---|---|---|---|---|---|---|
| s325 | own (S3) auto_grown_20261024214208830 | m20 / -9 | yes | 7.1 | 4 | 0.94 | 1.0 |
| s206 | own (S3) auto_grown_20261024184958725 | m5 / -2 | yes | 5.7 | 4 | 0.90 | 1.0 |
| s198 | own (S3) auto_grown_20261024171724520 | c / 0 | yes | 6.4 | 3 | 0.87 | 1.0 |
| E1d | own (S3) auto_grown_20261023221723612 | p5 / 2 | yes | 7.2 | 3 | 0.97 | 1.0 |
| s198 | regrown auto_grown_20261025092124150 | c / 0 | yes | 1.0 | 1 | 0.60 | 1.0 |
| s325 | regrown auto_grown_20261025092124435 | m20 / -9 | no | 0.0 | 0 | — | — |
| s206 | regrown auto_grown_20261025092124154 | m5 / -2 | yes | 9.2 | 3 | 0.73 | 1.0 |

### Facing windings (Hecate share >= T in the mapped row box, by k -9 ... 9)

| Target | Side | Mesh | Distance (vox) | Shares (%) |
|---|---|---|---|---|
| s206 | plus | auto_grown_20261023224151702 | 46.6 | 0.0 0.2 1.1 0.2 0.2 0.3 0.0 0.4 1.9 |
| s325 | plus | auto_grown_20261024213155545 | 39.3 | 1.8 2.6 0.5 0.0 0.4 0.0 0.2 0.3 0.5 |
| s198 | plus | auto_grown_20261024171502374 | 16.2 | 17.0 13.5 7.8 7.0 6.8 8.9 11.7 9.3 6.1 |
| s325 | minus | auto_grown_20261024214437918 | 16.0 | 0.4 0.1 0.6 0.0 0.6 4.1 4.6 14.1 17.3 |
| s206 | minus | auto_grown_20261024185405569 | 30.7 | 0.4 0.8 2.0 3.4 2.3 1.5 0.6 0.7 0.6 |

### Reading

- Control E1d: chain part UNCALIBRATED, depth part calibrated.
- s198: (a) continuity fail; (b) agreement pass; (c) depth fail -> not a strong candidate
- s206: (a) continuity fail; (b) agreement pass; (c) depth pass -> not a strong candidate
- s325: (a) continuity fail; (b) agreement fail; (c) depth pass -> not a strong candidate

## What S3b showed
- **The depth test works on the control.** E1d's known line peaks at a sheet face, and so do two of the three rows
  (206 and 325). Depth alone does not separate them from text.
- **The continuity test as written is too strict, or the E1d mesh too small.**
  - The control failed it at 7.2 mm. A future test needs a longer control line, or a calibrated gap and band
    tolerance.
  - Changing the rule now, after seeing the outputs, is not allowed. It is left for a new pre-registration.
- **Regrowing from a point is not a reliable way to extend a surface.** All three regrowths landed 6–8 voxels off
  the original row. Extending the original mesh at its edge (or growing from several seeds on it) would keep the
  same sheet.
- **Row 325's facing winding rises at the depths facing the row** (14–17% at k = +7..+9). That fits an offset image
  or shared structure, and is worth a look if this zone is revisited.

## Operations and deviations
- **Time label:** the start entry in our lab notebook is labelled 09:50 UTC. The prereg commit and the runs were at
  09:21 UTC (the commit is authoritative).
- **Idle time:** the runs finished at 10:01 UTC. A wait loop that matched its own command line delayed the write-up
  by about 20 minutes, while the machine idled.
- **Machine:** the rented machine idled from 23:39 UTC until 09:21 UTC (escalation rule), and S3b ran from 09:21 to 10:01 UTC.
  It is stopped after this commit and the backup.
