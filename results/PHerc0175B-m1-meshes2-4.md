# Result: PHerc0175B, M1 meshes 2–4 (neighbouring windings), read under `prereg/PHerc0175B-m1-b.md` (6761b8c)

**Verdict for each of meshes 2, 3 and 4 (pre-registered sentence 1): "I didn't see any ink in the region."**

## What ran
- All 30 pre-registered Hecate outputs exist: 3 meshes × windows −2..+2 × forward and reverse.
- They ran 04:42–06:54 UTC with no GPU yield. Inputs were cropped to the readout bbox + 128 px.

## Mechanical readout (`readout.json` per mesh)

| Mesh | Readout area | Direction | Candidates | Mean p | p99 | Area ≥ T (control background: 1.2%) |
|---|---|---|---|---|---|---|
| 2 `041932258` | 4.85 cm² | forward / reverse | 28 / 43 | 0.095 / 0.122 | 0.55 / 0.71 | 2.2% / 4.7% |
| 3 `042848633` | 4.72 cm² | forward / reverse | 52 / 42 | 0.134 / 0.109 | 0.66 / 0.64 | 5.2% / 3.5% |
| 4 `043132714` | 4.59 cm² | forward / reverse | 14 / 34 | 0.078 / 0.110 | 0.45 / 0.62 | 1.0% / 3.2% |

## Why the verdict is "no ink"
- **The maps:** the ensembles at quarter resolution and full-resolution crops around the top candidate in each of the
  six mesh/direction maps (5.8 mm squares) show soft, roundish blobs and clouds.
  - There are no thin strokes of constant width, no letter shapes and no rows.
  - At the same scale, the control's letters are unmistakable.
- **The level:** the raised response seen on mesh 1 (12% of the area ≥ T) is weaker on these inner windings, 1.0–5.2%.
  That is still mostly above the control background.
- **Escalation:** none.

## Running total for M1 on PHerc0175B (outer zone r80_a270, z ≈ 6200–9700)
- Four adjacent windings, about 19 cm² of clean interior, all with verdict 1.

## Not established
- These negatives say something about the scroll only if our self-grown surfaces sit where Hecate expects the ink.
- The positive control used the organisers' published render. A control for our own render settings (E1c) and, where
  the data exist, for our growth pipeline on a scroll with known text is the next check (our lab notebook).
