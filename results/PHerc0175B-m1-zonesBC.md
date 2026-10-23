# Result: PHerc0175B, M1 zones B and C (six meshes), read under `prereg/PHerc0175B-m1-c.md` (b2b4b7d)

**Verdict for each of B1, B2, B3, C1, C2 and C3 (pre-registered sentence 1): "I didn't see any ink in the region."**
The zone C verdicts are low-confidence geometry, as pre-registered.

## What ran
- All 60 Hecate outputs exist: 6 meshes × windows −2..+2 × forward and reverse. They ran 08:30–10:33 UTC with no GPU
  yield.

## Mechanical readout (`readout.json` per mesh). Control background: 1.2% of the area ≥ T.

| Mesh | Zone | Readout area | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|---|
| B1 `074119260` | B, z 7944 mid-radius | 4.35 cm² | 11 / 0.065 / 2.0% | 7 / 0.043 / 0.7% |
| B2 `075017447` | B | 4.46 cm² | 2 / 0.041 / 0.4% | 17 / 0.063 / 1.6% |
| B3 `075424029` | B | 4.51 cm² | 14 / 0.071 / 1.4% | 6 / 0.052 / 0.8% |
| C1 `080225012` | C, z 5560 inner | 2.58 cm² | 9 / 0.047 / 1.3% | 1 / 0.037 / 0.3% |
| C2 `081222870` | C | 1.81 cm² | 2 / 0.041 / 0.7% | 1 / 0.037 / 0.3% |
| C3 `081650324` | C | 3.07 cm² | 5 / 0.040 / 0.9% | 6 / 0.038 / 0.6% |

## Why the verdict is "no ink"
- **Quiet baselines:** unlike the outer windings, these zones read close to the control background and to the
  PHerc0343 control (mean p 0.037–0.071). A text line like the one E1d found would stand out here, and none appears.
- **What was checked at full resolution**, using each mesh's grid orientation to know which way a text line would run:
  - **C3 band:** a horizontal band of clouds across the middle. C3's columns run along θ, so a text line would lie
    this way. But the band holds soft clouds and branching blobs, not separated glyphs with straight strokes. It also
    appears in the reverse direction at about the same place, which points to CT structure rather than ink on one
    face.
  - **C2 streak:** one smooth ridge about 4.5 mm × 1 mm, beside an excluded fold zone. That fits a crease or sheet
    contact.
  - **B1 forward and B2 reverse clusters:** a few soft blobs.
- **Escalation:** none. No candidate forms a row of glyphs.

## Running total for M1 on PHerc0175B (all verdict 1)

| Region | Meshes | Readout area |
|---|---|---|
| Outer zone r80_a270, z 6200–9700 | 4 windings | ~19.2 cm² |
| Zone B, mid-radius, z 7944 | 3 sheets | 13.3 cm² |
| Zone C, inner, z 5560 (low-confidence geometry) | 3 sheets | 7.5 cm² |
| **Total** | **10 meshes** | **≈ 40 cm²** |

- E2b rates PHerc0175B at about 11,900 cm² of rough on-CT recto area, so this is about 0.3% of the scroll's
  papyrus.
- The pipeline is validated (E1d), but at the pace of the one shared GPU used here, one scroll would take months.
