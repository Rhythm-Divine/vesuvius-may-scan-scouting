# Pre-registered readout: PHerc0175B, M1 meshes 2–4 (neighbouring windings of mesh 1, outer zone r80_a270)

This was committed before any Hecate output on these three meshes existed. It follows `prereg/PHerc0175B-m1.md`
(mesh 1, read 2026-10-22, verdict 1) in everything not stated here. After this commit the rules do not change for
these runs; deviations get appended below, dated, before the target output is opened.

## Target
- **Volume:** as for mesh 1 (PHerc0175B / 20250521125822, 8.64 µm, 116 keV, masked CT, open-data bucket).
- **Meshes:** grown by `m1/grow_more.sh`, with the same settings as mesh 1 except thread_limit 8. Seeds come from
  `m1/seeds_radial.py` on mesh 1's seed line, moving toward the scroll centre.

  | Mesh | Seed (x, y, z) | Grown | Interior self-crossing quads | Readout area |
  |---|---|---|---|---|
  | 2 `auto_grown_20261022041932258` | (5234, 2068, 7942) | 7.44 cm² | 0 | 4.85 cm² |
  | 3 `auto_grown_20261022042848633` | (5234, 2084, 7942) | 7.50 cm² | 530 | 4.72 cm² |
  | 4 `auto_grown_20261022043132714` | (5234, 2102, 7942) | 7.54 cm² | 2,175 | 4.59 cm² |

- **Distinct sheets:** `m1/qc_meshes.py` puts the median nearest-point distance between any two of meshes 1–4 at
  18.6–65.8 voxels. The share within 3 voxels is ≤ 0.2%. So these are four different windings, not duplicates.
- **Readout area:** the render centre layer > 0, intersected with the mesh interior (≥ 16 grid cells from the mesh
  boundary). Cells within 8 grid cells of any `vc_tifxyz_selfcross` transverse contact are excluded (`m1/readout.py
  --exclude-contacts 8`).
- **Render:** as for mesh 1 (48 layers at 8.64 µm, smooth interpolation, resampled to 43 × 2914² at 9.604 µm).
- **Model:** as for mesh 1. Hecate 9.6 µm with the same sha256s, bf16, batch 4, stride 32, through `gpu_guard`.
  - **Windows:** k = −2..+2 means layers [13 + k, 28 + k].
  - **Directions:** forward and reverse, each read separately.
  - **Ensemble:** the per-pixel probability mean of the five windows.
  - **Input crop:** each input is cropped to the readout-area bounding box plus 128 px (clipped to the canvas). This
    only saves GPU time: outputs inside the readout area match the full-canvas run up to edge effects 128 px away.

## Positive control and threshold
- E1b as before. T = **0.445**, fixed.

## Candidate rules and escalation
- As for mesh 1: `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9).
- Escalate only on reappearance under a second independent model or seed, with rows parallel to the horizontal fibres.
- **Added for reporting only:** the share of the readout area ≥ T, shown next to the control background's 1.2%.
  Mesh 1 showed that a diffuse raised response makes the candidate count meaningless, so candidates are judged only by
  eye and by the escalation rule.

## Verdict sentences (fixed; exactly one per mesh)
1. "I didn't see any ink in the region."
2. "I see possible ink traces but no legible letters."
3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
