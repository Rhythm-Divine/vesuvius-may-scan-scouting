# Result: PHerc0175B, M1 batch D (zone B windings 4–7; outer zone H), read under `prereg/PHerc0175B-m1-d.md` (fa09684)

**Verdict for each of B4, B5, B6, B7, H1, H2 and H3 (pre-registered sentence 1): "I didn't see any ink in the
region."** The zone H verdicts are low-confidence geometry, as pre-registered.

## What ran
- All 70 Hecate outputs exist: 7 meshes × windows −2..+2 × forward and reverse.
- They ran 12:20–17:12 UTC with no yield. Runs took about 4 min each, twice as long as earlier, so the GPU was busier.

## Mechanical readout (`readout.json` per mesh). Control background: 1.2% of the area ≥ T.

| Mesh | Readout area | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|
| B4 `112556831` | 3.78 cm² | 4 / 0.037 / 0.4% | 9 / 0.063 / 1.2% |
| B5 `113517001` | 4.30 cm² | 0 / 0.032 / 0.3% | 4 / 0.049 / 0.6% |
| B6 `113913756` | 4.24 cm² | 6 / 0.060 / 0.8% | 10 / 0.054 / 0.9% |
| B7 `114237201` | 4.23 cm² | 31 / 0.084 / 2.5% | 5 / 0.040 / 0.5% |
| H1 `115152504` | 3.47 cm² | 5 / 0.046 / 1.0% | 5 / 0.053 / 1.3% |
| H2 `120053693` | 2.76 cm² | 11 / 0.048 / 1.6% | 10 / 0.055 / 1.7% |
| H3 `120727005` | 3.62 cm² | 7 / 0.052 / 1.3% | 7 / 0.055 / 1.2% |

## Why the verdict is "no ink"
- **Zone B (B4–B6):** scattered speckle only. The brightest spots sit at the edges of excluded fold zones, and there
  are no rows.
- **B7 forward:** the one one-sided signal, 2.5% of the area ≥ T. It is a broad, diffuse speckle field over half the
  patch, a weaker version of mesh 1's raised texture. At full resolution, around the top candidate, it is soft round
  blobs of 0.5–1 mm with no strokes or glyphs.
- **Zone H:** a text line would run horizontally in these images. None does. The brightest clusters in H1, H2 and H3
  appear in both directions at the same place, against excluded fold zones, which points to geometry or CT structure
  rather than ink on one face.
- **Escalation:** none.

## Running total for M1 on PHerc0175B (every mesh verdict 1)

| Region | Meshes | Readout area |
|---|---|---|
| Outer zone r80_a270, z 6200–9700 | 4 | 19.0 cm² |
| Zone B, mid-radius, z 7944 | 7 | 29.9 cm² |
| Zone C, inner, z 5560 (low-confidence geometry) | 3 | 7.5 cm² |
| Zone H, outer, far side, z 10326 (low-confidence geometry) | 3 | 9.9 cm² |
| **Total** | **17** | **≈ 66.2 cm²** |

- Zones E and F (6 meshes) were grown but not read, because they folded.
- 66.2 cm² is about 0.6% of PHerc0175B's rough on-CT recto area (E2b, ~11,900 cm²). An earlier version of this
  table said 64.5 cm²; that was a summing slip in the zone B row (28.1 instead of 29.9 cm²).
