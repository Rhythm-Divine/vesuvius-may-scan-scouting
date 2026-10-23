# Pre-registered readout: PHerc0175B, M1 mesh 1 (outer zone r80_a270)

This was committed before any Hecate output on PHerc0175B existed. The commit hash goes into the run log. After this
commit the rules below do not change for this run. Any deviation gets appended under "Deviations", dated and with the
reason, before the target output is opened.

## Target
- **Volume:** PHerc0175B / 20250521125822, 8.64 µm, 116 keV (BM18, May 2025).
  - Masked CT: `PHerc0175B/volumes/20250521125822-8.640um-1.2m-116keV-masked.zarr` (open-data bucket).
- **Region:** GrowPatch mesh `auto_grown_20261022022706145`.
  - Seed (x, y, z) = (5234, 2047, 7942); 80 generations.
  - Bbox: x 3293–7032, y 1277–2620, z 6184–9689 (level-0 voxels). 7.42 cm² grown.
  - **Readout area:** the mesh interior, at least 16 grid cells (2.8 mm) from the mesh boundary: 4.89 cm².
    `vc_tifxyz_selfcross` found 581 transverse contacts, all within 14 cells of the boundary.
- **Geometry:** `vc_grow_seg_from_seed` from the VC3D AppImage, villa `406e767`.
  - AppImage sha256 22160410ff9a1d70f428b8a990ff64d5bbc39d6dd240586e297c699a48dd00b7.
  - Params as in `m1/grow_job.sh`: step 20, 80 generations, thread_limit 4, CPU.
  - Inputs: the m7 prediction `20250521125822-surface-20260413222639-surface-m7-L0-th0.2.zarr` and its published
    normal grids.
- **Render:** `vc_render_tifxyz` from the same AppImage.
  - `-g 0 --scale 1 -n 48 --slice-step 1 --surface-interpolation smooth`, giving 48 × 3240² at 8.64 µm.
  - Resampled to 9.604 µm (XY origin-aligned, Z centred; `e1/prepare.py resample_render`): 43 × 2914².
  - No tile re-centring.
- **Model:** Hecate 9.6 µm.
  - Weights `hecate_9.6um.pth`, sha256 809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d.
  - Script `hecate.py`, sha256 c232c18a1a86cfb91257a00db13288202bb8ae33732ba26f7291a9b8adb8da59.
  - bf16, batch 4, stride 32, run through `tools/gpu_guard.py`.
  - **Windows:** k = −2..+2 means layers [13 + k, 28 + k] of the 43-layer stack. Layer 21 is the mesh surface.
  - **Directions:** forward, and reverse (`--reverse` on the same 16 layers). They are read separately, because this
    mesh's normal orientation is not known in advance.
  - **Ensemble:** per direction, the per-pixel mean of the five window probability maps. This is the same definition as
    the control. The z-score mode of `sweep.readout.ensemble` is not used, because T was calibrated on probabilities.

## Positive control (passed: E1b, `docs/decisions.md`)
- **Segment:** PHerc0009B `20250919125754-auto_grown_20250919055754487_inp_hr`, 8.64 µm surface volume.
- **Labels:** the organisers' same-mesh labels (2026-09-18) on its 2.401 µm canvas, at the CT-registered shift (10, 8) px.
- **Pass criterion:** ensemble AUC within 0.03 of J. Lu's 0.956 inside the supervision mask. We got 0.941, a pass.
- **Threshold:** T = **0.445**, the median of the −2..+2 ensemble on labelled ink. It is fixed here.

## Candidate rules (`sweep/readout.py` `extract_candidates`, `ReadoutRules`)
- threshold 0.445; px_um 9.604; min_extent_mm 0.5; border_px 8; max_band_aspect 8; min_valid_frac 0.9.
- **valid** = the centre layer (21) of the 9.604 µm render > 0, intersected with the mesh interior defined above (mapped
  to render pixels).
- **Escalate to Rhythm only if both hold:**
  - the candidate reappears at the same place and ≥ T under a second independent model or seed (ink_9um, or a second
    GrowPatch seed on the same sheet);
  - its rows run parallel to the horizontal fibres.

## Verdict sentences (fixed now; exactly one is used)
1. "I didn't see any ink in the region."
2. "I see possible ink traces but no legible letters."
3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

## Deviations
- (none)
