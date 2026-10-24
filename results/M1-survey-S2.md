# M1 survey S2: results (pre-registration `prereg/M1-survey-S2.md`)

## Outcome
- **No ink seen, and nothing escalated.** reader-v2, a second ink model independent of Hecate, read all 108 kept S1
  surfaces (435.9 cm²) forward and reverse.
- **Reviews:** 91 were reviewed by eye; 88 got verdict 1 and 3 got verdict 2. None showed letter-like forms (verdict 3).
- **Controls first, on the same machine:**
  - E1b: forward AUC 0.927 (validation 0.934), T2 = 0.6275, with 1.55% of non-ink pixels ≥ T2.
  - E1d: the October text line shows as separate stroke shapes, 5.07% ≥ T2 forward, 93% of it within 0.3 mm of
    Hecate's ≥ T pixels.
- **Run:** 108 surfaces from 11:17 to 12:33 UTC on 2026-10-24 (four L4s), none failed.
  - Each surface was rendered natively at 8.64 µm with 48 layers.
  - Each was read with three 17-layer windows per direction, then aligned pixel for pixel with the S1 Hecate maps.

## Per volume

| Volume | Read | Area (cm²) | Flagged | Reviewed | Verdict 1 / 2 / 3 | Median fwd / rev ≥ T2 | Max fwd / rev ≥ T2 | Above background |
|---|---|---|---|---|---|---|---|---|
| PHerc0175A | 25 | 108.1 | 24 | 24 | 23 / 1 / 0 | 1.7% / 1.9% | 18.0% / 6.3% | 18 |
| PHerc0175B | 6 | 19.1 | 5 | 5 | 5 / 0 / 0 | 0.9% / 0.3% | 4.3% / 0.5% | 2 |
| PHerc0268 | 3 | 7.7 | 2 | 2 | 2 / 0 / 0 | 0.2% / 0.5% | 0.8% / 1.0% | 0 |
| PHerc0306B | 15 | 66.0 | 13 | 14 | 14 / 0 / 0 | 0.7% / 0.7% | 2.2% / 3.7% | 5 |
| PHerc0483A | 16 | 69.3 | 14 | 14 | 13 / 1 / 0 | 0.6% / 0.7% | 2.1% / 2.6% | 2 |
| PHerc0483B | 11 | 41.7 | 9 | 10 | 10 / 0 / 0 | 0.6% / 0.8% | 2.7% / 3.8% | 3 |
| PHerc0490B | 2 | 4.9 | 0 | 0 | — | 0.1% / 0.1% | 0.1% / 0.1% | 0 |
| PHerc0800 | 14 | 56.7 | 14 | 14 | 14 / 0 / 0 | 3.7% / 3.6% | 16.3% / 13.3% | 13 |
| PHerc1218 | 16 | 62.4 | 6 | 8 | 7 / 1 / 0 | 0.1% / 0.1% | 1.8% / 3.3% | 3 |
| **Total** | **108** | **435.9** | **87** | **91** | **88 / 3 / 0** | 0.8% / 0.8% | 18.0% / 13.3% | 46 |

- "Above background" counts surfaces with more than 1.55% ≥ T2 in either direction.
- PHerc0490A had no surface that passed QC in S1, so S2 has nothing from it.
- Per-surface verdicts and notes are in `results/M1-survey-S2-reviews.tsv`.

## The three verdict-2 surfaces (none escalated)
- **PHerc1218 z6974_r55_a067, reverse: the closest case.**
  - A field of soft round blobs 1–2 mm across covers most of the surface (3.3% ≥ T2, forward 0.5%).
  - Within it, 5 separate blobs chain over 5.4 mm along the text direction, at heights within 1.1 mm. 61% of their
    ≥ T2 pixels lie within 0.3 mm of Hecate's ≥ T pixels. The numeric parts of the escalation rule are therefore met.
  - By eye it is not like the E1d line, which the rule also requires. The blobs are round, with no strokes, and are
    spread over 14 mm of height rather than forming one line on a quiet background.
  - The best 1 mm band of z holds 10.7% ≥ T2, against a median of 2.4%. E1d's text reaches 37.8% against 2.9%.
- **PHerc0483A z7949_r55_a202, forward.**
  - Two letter-sized blobs (0.8 × 1.6 mm and 2.3 × 1.3 mm) run 4.4 mm along the text direction on an otherwise quiet
    surface.
  - Hecate shows a cluster at the same place in both directions; 44% of the pair's ≥ T2 pixels agree.
  - It is below the 5 mm row length the rule requires.
- **PHerc0175A z8923_r55_a022, reverse.**
  - The S1 verdict-2 row shows in reader-v2 as one continuous smooth band, not separate blobs.
  - The S1 row check had already found it on the inward winding.

## What S2 showed
- **The strongest Hecate clouds are reader-v2 clouds too.** Both models respond to the same few areas: PHerc0175A
  z6374_r30_a270 and its second-seed surface, and four PHerc0800 surfaces in zone z12149. They reach up to 18.0% ≥ T2,
  with 70–95% agreement, but as shapeless clouds without strokes.
  - These are the most interesting unexplained responses in the survey. Two models agreeing is not enough to call
    them ink.
- **Agreement alone is not the test.**
  - On PHerc0306B z11128_r30_a315, both models show the same reverse band, but it runs across the text direction
    along a vertical fibre bundle seen in the CT.
  - The rule's direction and shape conditions are what separate structure from text.
- **reader-v2 is far quieter than Hecate on most surfaces.** The median share is 0.8% ≥ T2, under its own control
  background of 1.55%. Its responses are concentrated in a few zones.

## Cost and machine
- S2 used the four L4s for 76 minutes on the same g6.12xlarge. The controls took 4 minutes before that.
- The instance was stopped after S2, as Rhythm asked, because nothing escalated.
