# M1 survey S1: results (pre-registration `prereg/M1-survey-S1.md`)

## Outcome
- **No ink seen, and nothing escalated.** 108 surfaces over the ten May-session volumes were read with Hecate.
- 91 were reviewed by eye. 89 got verdict 1, "I didn't see any ink in the region".
- Two got verdict 2, "I see possible ink traces but no legible letters":
  - PHerc0175A z8923_r55_a022;
  - PHerc0268 z12608_r55_a067.
- Both verdict-2 rows failed their pre-declared row checks. So did a third row check, on PHerc0175A z6374_r55_a112.
  None is escalated.
- 17 surfaces were below triage and were not reviewed by eye.
- The controls passed on this machine before any survey surface was read.
  - E1b: AUC 0.9405, T = 0.4447.
  - E1d: the PHerc0343 text line is seen again.

## Per volume

| Volume | Zones (stage 1 / stage 2 / checks) | Kept / dropped | Clean area kept (cm²) | Read | Flagged | Reviewed | Verdict 1 / 2 |
|---|---|---|---|---|---|---|---|
| PHerc0175A | 12 / 4 / 9 | 25 / 0 | 108.1 | 25 | 25 | 25 | 24 / 1 |
| PHerc0175B | 4 / 4 / 0 | 6 / 2 | 19.1 | 6 | 6 | 6 | 6 / 0 |
| PHerc0268 | 1 / 0 / 3 | 3 / 1 | 7.7 | 3 | 2 | 3 | 2 / 1 |
| PHerc0306B | 12 / 4 / 0 | 15 / 1 | 66.0 | 15 | 14 | 14 | 14 / 0 |
| PHerc0483A | 12 / 4 / 0 | 16 / 0 | 69.3 | 16 | 11 | 13 | 13 / 0 |
| PHerc0483B | 12 / 4 / 0 | 11 / 5 | 41.7 | 11 | 5 | 5 | 5 / 0 |
| PHerc0490A | 4 / 0 / 0 | 0 / 4 | 0.0 | 0 | 0 | 0 | — |
| PHerc0490B | 6 / 0 / 0 | 2 / 4 | 4.9 | 2 | 0 | 1 | 1 / 0 |
| PHerc0800 | 12 / 4 / 0 | 14 / 2 | 56.7 | 14 | 14 | 14 | 14 / 0 |
| PHerc1218 | 12 / 4 / 0 | 16 / 0 | 62.4 | 16 | 10 | 10 | 10 / 0 |
| **Total** | **87 / 28 / 12** | **108 / 19** | **435.9** | **108** | **87** | **91** | **89 / 2** |

- Zones are mechanically chosen crops. Stage 2 is the four windings around each volume's best kept zone. Checks are the
  pre-declared follow-up and row-check surfaces.
- No seed, growth or read failed.
- The per-surface verdicts and notes are in `results/M1-survey-S1-reviews.tsv`. The reasoning behind each check is in
  `docs/decisions.md`, 2026-10-24.

## What S1 taught
- **Hecate's background on these scrolls is high.** The triage thresholds, set from PHerc0175B and PHerc0490A,
  flagged 87 of 108 surfaces.
- **Rows along the text direction are common on background.** A finder that only weakly recovers E1d's text line
  (`m1/rowfind.py`) found chains on 29 of 108 direction-reads. So a row of blobs alone is no evidence of ink here.
- **Depth tests don't separate ink from structure.** Every response stays put across the depth windows, ink or not
  (`m1/depth_shift.py`). E1d's text is as flat across depth as background.
- **Regrowing a second seed rarely stays on the same sheet in damaged papyrus.** It did in one check of four.
- **So the decisive test is a second, independent ink model on the same meshes.** That is S2
  (`prereg/M1-survey-S2.md`, reader-v2).

## Cost and machine
- The g6.12xlarge has been up since 2026-10-23 21:58 UTC.
- S1 ran 1,090 Hecate inferences: 47.2 GPU-hours, the four L4s 95% busy from 22:22 to 10:45 UTC.
- Tracing kept 42 vCPUs busy for about two hours. The CT streamed in was about 1.1 TB.
