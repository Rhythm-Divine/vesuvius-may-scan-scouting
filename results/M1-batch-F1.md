# Result: M1 batch F1 (PHerc0490A, three untried gated zones), read under `prereg/M1-batch-F1.md` (ca475c0)

**Verdict for each of F-a, F-b and F-c (pre-registered sentence 1): "I didn't see any ink in the region."**
- F-a and F-c are low-confidence geometry, as pre-registered.
- **F-a is flagged:** Hecate barely responds there.

## What ran
- All 30 Hecate outputs exist: 3 surfaces × windows −2..+2 × forward and reverse.
- They ran 05:47–14:19 UTC on 23 Oct.
- The run was not slow; it waited. From about 06:33 to 14:00, another job held 16–18 GB of the shared A10G, and
  `gpu_guard` refused every start (rc 4) until ≥ 8 GB was free.

## Mechanical readout. Control background: 1.2% of the area ≥ T.

| Surface | Zone | Readout area | On papyrus | Forward: candidates / mean p / area ≥ T | Reverse: candidates / mean p / area ≥ T |
|---|---|---|---|---|---|
| F-a `040557208` | z 5848 r30_a090 (low-confidence) | 2.66 cm² | 0.999 | 0 / 0.011 / 0.0% | 0 / 0.010 / 0.0% |
| F-b `041747890` | z 5848 r80_a180 | 4.47 cm² | 0.997 | 10 / 0.043 / 0.7% | 9 / 0.044 / 1.3% |
| F-c `042830254` | z 7600 r80_a270 (low-confidence) | 2.40 cm² | 0.885 | 5 / 0.070 / 3.2% | 8 / 0.060 / 1.5% |
| **Total** | | **9.53 cm²** | | | |

## Why the verdict is "no ink"
- **F-a: almost silent.**
  - Mean p is 0.010, about a quarter of the control background, and nothing reaches T in either direction.
  - The CT is papyrus at every layer within ±16 layers: p10/p50/p90 of 71/119/144, with no air gap on either side.
    The surface lies inside compressed sheets.
  - A dead response here may mean this model can't see a surface at all. So F-a's negative is weak evidence, though
    it counts under the pre-registered rules.
- **F-b: quiet overall, with one reverse feature.**
  - The feature is a band of soft blobs about 5 mm long near the upper-right edge of the readout area. It holds across
    depth windows and grows toward k = +2.
  - It has no strokes, and it runs about 77° across the lines of constant z, which run steeply on this grid. A text
    line would not lie that way.
  - Forward has a cluster at the same place, so it is partly two-sided.
  - A cross-winding check on F-b's neighbours (batch F3) follows once they are read.
- **F-c: one-sided vertical streaks, which are fibre structure.**
  - In the forward direction, an upper-right patch fills 10% of a 7.7 mm square at ≥ T, against 2% in reverse.
    It is present in all five windows (9–14%).
  - At full resolution it is vertical streaks about 0.5 mm wide and 1–2 mm long. They sit on vertical fibre bundles
    visible in the CT, beside a large void and a dense inclusion.
  - Text lines would run horizontally on this grid, and the streaks run across them.
  - F-c's middle cluster is soft blobs around an excluded fold zone, partly two-sided.
- **Escalation:** none. No candidate forms rows.

## Running total for M1 (every surface verdict 1; G1 not counted)

| Scroll | Surfaces read | Readout area on papyrus |
|---|---|---|
| PHerc0175B | 19 | 72.5 cm² |
| PHerc0490A | 13 | 45.9 cm² |
| **Total** | **32** | **≈ 118.5 cm²** |
