# M1 survey S3: results (pre-registration `prereg/M1-survey-S3.md`)

## Outcome
- **Three surfaces met the escalation rule and went to Rhythm privately. None shows legible letters (no verdict 3).**
  All three stay verdict 2, and the machine stays up, as the rule requires, until Rhythm decides what next.
  - **PHerc0483B z10098_r30_a090_o3, p6 reverse (sheet 198).**
    - There is a row of four or five separate forms ≥ T2 over about 6.6 mm: two ovals, a third oval, a 2.1 mm bar
      and a T-shaped form.
    - 75% of its ≥ T2 pixels lie within 0.3 mm of Hecate's ≥ T pixels at the p6 depth, and 100% of the ovals and
      the bar.
    - Near reverse has three letter-sized forms at the same places.
    - At the same scale it resembles the E1d control line at p6.
  - **PHerc0483A z4769_r30_a090_i1, m6 forward (sheet 206).**
    - There is a row of five separate round and oval blobs ≥ T2 (0.7–1.1 mm) over about 5.8 mm, with 81%
      agreement at the m6 depth.
    - It is the most conspicuous feature of a quiet map.
    - Four neighbouring windings, 26–50 voxels away, show nothing at the matching points.
  - **PHerc0175A z8923_r30_a225_o1, m6 reverse (sheet 325).**
    - There is a row of a cloud and then five evenly spaced round dots (0.5–0.9 mm) over about 6.9 mm, with 100%
      agreement at the m6 depth.
    - It is the most conspicuous feature of a quiet map.
    - The independent windings i1 and o2 show nothing there.
  - **Against all three:**
    - The forms are blobs and bars, not clear strokes, and no row continues as a longer line on the surface as
      grown.
    - Rows of round blobs along the fibres occur elsewhere on these volumes.
    - Sheet 325's dots are uniform, like beads, and may follow the fibre lattice. S1's mesh of the same place,
      6–14 voxels away, showed them as a 3.8 mm row of dots (verdict 1).
- **Reading:**
  - reader-v2 read 315 new surfaces near the mesh and at ±6 layers: 1,296.4 cm² clean. That is about 1,123 cm²
    after removing each surface's overlap with the nearest surface read before it.
  - It also read the 108 S1 surfaces at the two deeper windows.
- **Reviews:**
  - 383 surfaces were reviewed by eye: every flagged surface, and every fifth.
  - 363 got verdict 1, 20 verdict 2 and none verdict 3.
  - Hecate checked all 28 maps behind the 20 verdict-2 surfaces.
  - Most verdict-2 rows met the rule's numeric parts (≥ 5 mm along the text direction, ≥ 50% agreement). The by-eye
    comparison with the E1d line decided, as in S2.
- **Growth:**
  - 49 of the 134 queued jobs started before the 22:30 UTC stop. All were winding jobs; none of the 65 new-zone
    jobs started.
  - They grew all 361 of their seeds. 12 failed QC and 34 were duplicates of surfaces already read.
  - Every surface grown by the stop was read; the reads finished at 23:39 UTC.
- **Controls** (on this restart, before the pre-registration):
  - E1b forward AUC: 0.9266 near, 0.886 at p6, 0.782 at m6.
  - The E1d text line is seen at all three depths, with Hecate agreeing on 93%, 79% and 82%.

## Per volume
| Volume | Grown | Kept, distinct | Clean (cm²) | Unique (cm²) | Duplicates | Dropped | New read | S1 re-read | Reviewed | Verdict 1 / 2 / 3 | Median near fwd / rev (new) | Above background (new / S1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PHerc0175A | 58 | 41 | 183.9 | 168.7 | 17 | 0 | 41 | 25 | 66 | 64 / 2 / 0 | 1.4% / 1.0% | 34 / 23 |
| PHerc0175B | 12 | 12 | 34.0 | 28.2 | 0 | 0 | 12 | 6 | 18 | 16 / 2 / 0 | 0.7% / 0.4% | 6 / 3 |
| PHerc0268 | 8 | 6 | 13.7 | 10.1 | 0 | 2 | 6 | 3 | 7 | 6 / 1 / 0 | 0.6% / 0.8% | 0 / 0 |
| PHerc0306B | 60 | 55 | 242.5 | 217.5 | 5 | 0 | 55 | 15 | 60 | 60 / 0 / 0 | 0.4% / 0.4% | 20 / 6 |
| PHerc0483A | 51 | 50 | 230.8 | 202.9 | 0 | 1 | 50 | 16 | 62 | 57 / 5 / 0 | 1.0% / 0.7% | 19 / 3 |
| PHerc0483B | 52 | 49 | 190.3 | 160.6 | 3 | 0 | 49 | 11 | 57 | 55 / 2 / 0 | 0.9% / 0.9% | 24 / 2 |
| PHerc0490B | 16 | 8 | 21.4 | 15.9 | 0 | 8 | 8 | 2 | 3 | 3 / 0 / 0 | 0.0% / 0.0% | 0 / 0 |
| PHerc0800 | 52 | 48 | 181.8 | 154.9 | 3 | 1 | 48 | 14 | 61 | 56 / 5 / 0 | 2.1% / 2.1% | 44 / 13 |
| PHerc1218 | 52 | 46 | 198.0 | 164.3 | 6 | 0 | 46 | 16 | 49 | 46 / 3 / 0 | 0.3% / 0.4% | 12 / 2 |
| **Total** | **361** | **315** | **1296.4** | **1123.0** | **34** | **12** | **315** | **108** | **383** | **363 / 20 / 0** | 0.8% / 0.8% | 159 / 52 |

- "Unique" is the clean area times one minus the share of the surface within 4 voxels of the nearest surface read
  before it. It does not remove overlaps with two earlier surfaces at once, so it is an upper bound.
- "Above background" counts surfaces with any map above its window family's E1b background: near 1.55%, p6 1.44%,
  m6 4.36%. The S1 surfaces have p6 and m6 maps only.
- Per-surface verdicts and notes are in `results/M1-survey-S3-reviews.tsv`.
- The Hecate checks, with their boxes and per-form agreement, are in `results/M1-survey-S3-hecate.tsv`.

## The verdict-2 surfaces and their Hecate checks
| Sheet | Volume | Map(s) | Agreement on the row | Outcome |
|---|---|---|---|---|
| 28 | PHerc0175B | near fwd | 0.67 (map) | Not escalated: a blob field with no row ≥ 5 mm. |
| 40 | PHerc0268 | m6 rev | 0.52 (map) | Not escalated: S1's row again, as one continuous streak, with only 1.4 mm ≥ T2. |
| 74 | PHerc0483A | p6 rev | 0.00 | Not escalated: Hecate does not see the row. |
| 78 | PHerc0483A | p6 rev | 0.81 | Not escalated: only two forms, on a crack system visible in the CT. Neither recurs on four neighbouring windings. |
| 83 | PHerc0483A | p6 fwd | 0.45 | Not escalated: two pieces 6.9 mm apart, and under half agree. |
| 125 | PHerc0175A | near fwd | 0.77 (map) | Not escalated: a blob field whose main grouping runs across the text direction. |
| 133 | PHerc1218 | p6 rev | 0.59 (map) | Not escalated: round blobs over most of the surface (as in S2). |
| 158 | PHerc0175B | near fwd | 1.00 | Not escalated: a cloud, a speck and a blob over a column of CT voids, in a two-model blob field. |
| 162 | PHerc1218 | p6 fwd | 0.63 | Not escalated: sparse round dots in a band 3 mm high, not a line. |
| 172 | PHerc0800 | p6, m6 fwd | 0.75 / 0.83 | Not escalated: letter-sized forms side by side across the text direction, not a row. |
| **198** | PHerc0483B | near, p6 rev | 0.72 / 0.75 (1.00 on four p6 forms) | **Escalated.** At p6, a 6.6 mm row of ovals, a bar and a T that resembles the E1d line at that depth. |
| **206** | PHerc0483A | near, m6 fwd | 0.56 / 0.81 | **Escalated.** At m6, a 5.8 mm row of five blobs, the most conspicuous feature of a quiet map. It is absent on the independent neighbouring windings. |
| 213 | PHerc0483A | near, m6 rev | 0.54 / 0.27 | Not escalated: four forms over 12 mm with gaps of 2–4 mm. Only two agree. |
| 216 | PHerc0800 | p6 fwd | 0.77 | Not escalated: stroke-like forms on a CT-visible crack system, seen only at p6. |
| 223 | PHerc0800 | near, m6 fwd | 0.95 / 0.89 | Not escalated: two forms along the text direction and a dot field at m6, in cracked CT. |
| 260 | PHerc1218 | p6 rev | 0.28 | Not escalated: 4.7 mm at T2, and under half agree. This is S2's closest case, seen from a second mesh. |
| 268 | PHerc0800 | p6 fwd | 0.67 | Not escalated: the main form recurs on independent windings (structure). The rest spans 2.3 mm. |
| 321 | PHerc0483B | near, p6 fwd | 0.42 / 0.55 | Not escalated: under half of the near row agrees, and at p6 only fragments remain. |
| **325** | PHerc0175A | m6, p6 rev | 1.00 / 0.86 | **Escalated.** At m6, a 6.9 mm row (a cloud, then five even dots), the most conspicuous feature of a quiet map. It may follow the fibre lattice. |
| 351 | PHerc0800 | near, p6 rev | 0.38 / 0.83 | Not escalated: under half of the near row agrees, and at p6 there are three sparse round blobs. |

## What S3 showed
- **About 1,700 cm² has now been read by two models.**
  - M1, S1 and S2 read about 594 cm², and S3 adds about 1,123 cm² unique.
  - No legible letters were seen. Three rows are now open questions.
- **The deeper windows matter.**
  - All three escalated rows are clearest at p6 or m6, not near the mesh.
  - Several other letter-sized forms showed at only one deep window.
  - On the E1d control, the shifted windows still see the known line, with Hecate agreeing on about 80%.
- **Two-model agreement is common and is not the test.**
  - On 17 of the 20 checked surfaces, Hecate agreed with reader-v2 on more than half of the row in at least one
    map. That includes blob fields and forms sitting on cracks and voids visible in the CT (sheets 78, 158, 216
    and 223).
- **PHerc0800 zone z12149 has the most letter-like forms that are not rows.**
  - On sheets 172, 216 and 223, both models agree on letter-sized forms with stroke-like parts at the deeper
    windows.
  - These forms lie side by side across the text direction, or on cracks.
  - S2's strongest two-model clouds were in this zone too.
- **S2's closest case was seen again from a second mesh** (sheet 260): under 5 mm at T2, with 28% agreement.
- **The neighbour check helps when the windings are far enough apart.**
  - The rows on sheets 206 and 325 and the forms on sheet 78 do not recur on windings 16–64 voxels away.
  - Sheet 268's main form does recur, so it is structure.
  - At 8–15 voxels, a neighbouring mesh sees the same material.

## Operations and deviations
- **Readers:** moved to the shared cores 20–47 at 15:05 UTC. This was operational, and the interrupted items were
  read again from the start.
- **Duplicate check:**
  - From about 17:00 UTC it held the tracers behind the QC-log lock.
  - A faster check with identical answers went live at 20:02 UTC.
  - The stall cost growth time before the stop.
  - The prereg's "densified 4×" is corrected to 8×, the factor the code always used.
  - Both are dated deviation notes in the prereg.
- **Looking aids** (none feeds a verdict):
  - `m3/crop_r3.py`, `ctview_r3.py`, `strip_r3.py`, `region_agree.py`, `xwind_r3.py`, `ctmask_r3.py`,
    `fullover_r3.py` and `summary_s3.py`.
  - A further aid made side-by-side images of a row and the E1d line. It and its images stay private under the data
    agreement, because the E1d line shows letters.
- **Times:** the escalation times in the Hecate log are approximate. The private messages to Rhythm are
  authoritative.

## Cost and machine
- The rented 4× L4 machine (on demand at about $4.60/h) was restarted at 14:02 UTC.
- By the end of the reads at 23:39 UTC, S3 had used about 9.6 h, about $44. The four L4s read from 15:05 to
  23:39 UTC.
- As the escalation rule requires, the machine stays up after S3, at about $4.60 an hour, until Rhythm decides.
  A closer look at the three rows, S3b, is proposed in our lab notebook (draft, not approved).
