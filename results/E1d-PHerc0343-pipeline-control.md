# Result: E1d pipeline control on PHerc0343 (criterion fixed in f42614f before the run)

**Verdict: PASS.** Our own M1 chain (seed → GrowPatch on the m7 prediction → render → 9.604 µm → Hecate windows
−2..+2) shows a line of letter strokes on the sheet that carries the October First Letters text.

## What ran (`m1/control343_job.sh`, 07:03–07:35 UTC)
- **Seed:** (5880, 3909, 10467), from the winner's mesh node nearest their reading-area centre. It sits exactly on the
  m7 prediction.
- **Mesh:** `auto_grown_20261022070326457`, 7.9 cm² grown, bbox z 8942–12135.
  - `vc_tifxyz_selfcross` found 7,849 transverse contacts, many more than on PHerc0175B.
  - The readout area after the 8-cell contact exclusion is 3.43 cm².
- **Hecate:** 10 runs, about 2.1 min each, all through `gpu_guard` with no yield.
- **Readout:**

  | Direction | Candidates | Mean p | p99 | Area ≥ T |
  |---|---|---|---|---|
  | Forward | 21 | 0.078 | 0.81 | 4.5% |
  | Reverse | 15 | 0.055 | 0.56 | 1.8% |

## Why it passes
- **The forward ensemble:** a band of bright, structured marks about 2 mm wide runs the full length of the patch.
  - The mesh grid's rows advance around the scroll (about 20 voxels per step in xy, 5 in z), so the band lies at
    constant height running along θ: the geometry of a line of text.
  - Rotated so it runs horizontally, it is a row of separated glyph-like marks about 2 mm tall, with straight
    horizontal bars and vertical stems. The reverse direction shows only scattered blobs.
- **Same sheet as the winner's text:**
  - The band's mesh nodes span z 9879–10884, inside the winner's reading area (z 9515–10998).
  - Against a 4×-densified copy of the winner's published mesh, the median distance is 2.86 voxels (25 µm). 53% of
    nodes lie within 3 voxels and 69% within 6.
- **Contrast with PHerc0175B mesh 1:** there, Hecate gave a diffusely raised blob texture (mean p 0.21) with no line
  structure. Here the baseline is low (0.055–0.078) and the signal is organised into a text line.

## Limits
- The strokes are blurrier than the PHerc0009B control's. Individual letters are not cleanly legible with Hecate
  alone at windows −2..+2. The winner used 4 models over 31 depths.
- The direction that read here (forward) is not established for every GrowPatch mesh, so both directions stay in the
  readout.
- This mesh has many self-crossings; the readout area kept only 3.43 cm².

## What it means for M1
- **The PHerc0175B outer-zone negatives stand** as evidence about that region: four adjacent windings, about 19 cm².
  The same chain, settings and threshold show a text line on known text.
- **Next:** search deeper zones of PHerc0175B that pass the level-1 separability gate (E2c), under a new
  pre-registration.
