# Result: PHerc0490A, M1 batch 1 (mid-radius zone r55_a225), read under `prereg/PHerc0490A-m1.md` (76796e3)

**Verdict for each of P1, P2, P3, P4, P5 and Q1 (pre-registered sentence 1): "I didn't see any ink in the region."**
The P3 and Q1 verdicts are low-confidence geometry, as pre-registered.

## What ran
- All 60 Hecate outputs exist: 6 surfaces × windows −2..+2 × forward and reverse.
- They ran 18:26–22:37 UTC on 22 Oct with no GPU yield. Runs took about 4 min each on the busy shared GPU.

## Mechanical readout (`readout.json` per surface). Control background: 1.2% of the area ≥ T.

| Surface | Zone | Readout area | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|---|
| P1 `174346125` | z 5848 r55_a225 | 4.06 cm² | 7 / 0.038 / 0.6% | 13 / 0.046 / 1.5% |
| P2 `175903212` | same, inward | 3.82 cm² | 4 / 0.047 / 0.6% | 4 / 0.040 / 0.6% |
| P3 `180912923` | same, inward (low-confidence) | 3.38 cm² | 11 / 0.067 / 1.4% | 5 / 0.062 / 0.9% |
| P4 `181232834` | same, outward | 3.65 cm² | 7 / 0.041 / 0.8% | 6 / 0.047 / 1.0% |
| P5 `181555183` | same, outward | 3.95 cm² | 3 / 0.033 / 0.3% | 13 / 0.053 / 1.8% |
| Q1 `172303661` | z 7600 r55_a225 (low-confidence) | 2.51 cm² | 4 / 0.056 / 0.7% | 6 / 0.057 / 0.9% |
| **Total** | | **21.4 cm²** | | |

## Why the verdict is "no ink"
- **The baselines are quiet**: mean p 0.033–0.067, close to the control background (0.037) and to the PHerc0343
  control (0.055–0.078), whose text line stood out clearly at this level. At most 1.8% of any surface is ≥ T.
- **Grid orientation:** five of the six grids are oblique to z, so a text line would run diagonally. In P2 it would run
  horizontally. No diagonal or horizontal row of glyphs appears in any ensemble, in either direction.
- **The strongest one-sided features** were checked at full resolution (7.7 mm squares):
  - P1 reverse is a soft diagonal smear about 5 mm long, lying along the edge of an excluded fold zone. That is the
    signature of sheet contact, and it has no strokes.
  - P5 reverse is a small cluster of soft round blobs.
- **Everything else** is speckle. P3's denser field looks the same in both directions, which points to structure.
- **Escalation:** none.

## Running total for M1 (every surface verdict 1)

| Scroll | Surfaces read | Readout area |
|---|---|---|
| PHerc0175B | 17 | 66.2 cm² |
| PHerc0490A | 6 | 21.4 cm² |
| **Total** | **23** | **≈ 87.6 cm²** |
