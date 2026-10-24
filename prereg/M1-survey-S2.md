# Pre-registered readout: M1 survey S2 (a second, independent ink model on every S1 surface)

This was committed before any S2 output on a survey surface existed. After this commit the rules do not change for S2;
deviations are appended below, dated, before the output they concern is opened. Rhythm approved S2 on 2026-10-24:
download reader-v2, set up villa's ink-detection environment, run the controls, pre-register, read all kept S1
surfaces, then stop the machine unless something escalates.

## Why
- S1 read 108 kept surfaces (about 436 cm² of clean papyrus) over the ten May volumes with Hecate. It found no ink.
  All three row checks failed.
- At this resolution, Hecate's rows and clouds along the text direction are common on background. Its blank-papyrus
  false-positive rate is high: 58% at 80% recall, per reader-v2's README.
- A second model with a low false-positive rate, run on the same meshes, is the discriminating test. Regrowing a second
  seed proved unreliable in damaged papyrus.

## Model and code
- **Model:** reader-v2, `domenicor046/reader-v2`, checkpoint `reader-v2-step040000.pth`, MIT.
  - sha256 `654ec5acec2b6c4788d9cb326e2f0b8c2c730584949a934ef775db7f6ab5d3a6`.
  - `train_config.json` sha256 `a69e9cf23263d4b17a85f05501333408f923f67f65b6f4ebc6c4539ceb1e81ec`.
  - It is a 3D-stem/2D U-Net trained for native 8.64 µm, 116 keV scans like ours.
  - It reads a 17-layer depth window and 128 px patches, in fp16.
- **Code:** villa `ink-detection` (koine_machines, MIT), branch merge-ink-pipelines at `47a9c37`.
  - Locked environment (`uv sync --frozen`) on CPython 3.12: torch 2.10.0+cu128, zarr 2.18.7, numpy 2.2.0.
- **Independence from Hecate:**
  - Different architecture and labels, and a very different false-positive rate on blank papyrus.
  - Its training includes 14 PHerc0009B and 6 PHerc0343 segments. So the controls below test the pipeline only, not
    held-out ink.

## Controls (run 2026-10-24, before this commit)
- **E1b:** the organisers' native PHerc0009B surface volume (31 layers), scored against their same-mesh labels with
  `e1b/score.py` on the same window and registration as Hecate.
  - Forward AUC 0.927 in the supervision mask and 0.934 in the validation mask; Hecate's ensemble gave 0.941 and 0.897.
    Reverse: 0.567.
  - **T2 = 0.6275**, the median reader-v2 probability on labelled ink, the same rule as Hecate's T.
  - **Control background: 1.55%** of non-ink supervision pixels are ≥ T2 (Hecate: 1.2%). At 80% recall reader-v2
    flags 9.6% of non-ink pixels.
- **E1d:** our own PHerc0343 mesh, re-rendered natively and read the S2 way. The forward map shows the October text line
  in the same column as Hecate's, with clearer stroke shapes (by eye; the image stays private).
  - S2 readout, forward: 5.07% ≥ T2, 18 candidates, and 93% of the ≥ T2 pixels within 0.3 mm of Hecate's ≥ T pixels.
  - Reverse: 0.32% ≥ T2, 4 candidates, agreement 68%.
  - This is the reference for known text read the S2 way.

## Reading (every kept S1 surface: 108, all read by Hecate in S1)
- **Render:** natively, exactly as S1 rendered before resampling: `vc_render_tifxyz -n 48 --scale 1 --slice-step 1
  --surface-interpolation smooth`, same mesh.
- **reader-v2:** forward and reverse, each the mean of three 17-layer windows, centred and ±2 layers
  (`m2/r2_infer.sh`; `--overlap 0.5 --blend-mode hann`).
- **Alignment:** the maps are resampled to S1's 9.604 µm grid the same way S1's renders were, then cropped to S1's
  window (`m2/r2_combine.py`). So they line up pixel for pixel with the Hecate maps.
- **Readout** (`m2/readout_r2.py`): S1's valid area (centre layer > 0, mesh interior, 8-cell contact exclusion) and
  `ReadoutRules` with T2.
  - It also gives, per direction, the share of reader-v2's ≥ T2 pixels within 0.3 mm of Hecate's ≥ T pixels on the
    same mesh (agreement).
- **Triage** (`m2/triage_r2.py`): a direction is flagged when its area ≥ T2 exceeds 1.55%, or a candidate reaches
  1 mm. Flagged surfaces, and every fifth surface in processing order, are reviewed by eye.

## Verdicts and escalation
- **Verdicts:** each reviewed surface gets one of S1's three fixed sentences, from reader-v2's maps, with Hecate's
  alongside.
- **Escalation:** a surface goes to Rhythm, privately, when, by eye on reader-v2's map:
  - there is a conspicuous row of separate blobs ≥ T2, at least 5 mm long along the text direction, like the E1d line
    in reader-v2;
  - and at least half of that row's ≥ T2 pixels lie within 0.3 mm of Hecate's ≥ T pixels on the same mesh.
- **Letters:** anything reader-v2 shows as letter-like forms is verdict 3. That triggers the First Letters checklist,
  and everything stays private.
- **No new regrowth checks in S2.** Agreement between two independent models on the same mesh replaces them.

## Stop rule
- S2 ends when all 108 surfaces are read and the flagged ones reviewed.
- If nothing escalates, the survey is reported and the machine stopped, as Rhythm asked.

## Deviations
- (none)
