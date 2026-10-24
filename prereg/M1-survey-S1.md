# Pre-registered readout: M1 survey S1 (breadth over the ten May-session volumes, on a dedicated g6.12xlarge)

This was committed before any Hecate output of S1 existed. It follows `prereg/M1-batch-F1.md` (and through it the
earlier pre-registrations) in every rule not stated here. After this commit the rules do not change for S1; deviations
get appended below, dated, before the output they concern is opened.

## Why
- 43 surfaces (≈ 158.5 cm²) on PHerc0175B and PHerc0490A showed no ink.
- The next question is whether any of the ten First Letters-eligible May-session volumes shows ink to this chain. A
  dedicated machine makes a first pass over all ten affordable.

## Machine, and the controls that gate it
- **Machine:** a dedicated g6.12xlarge in us-east-2: 4× L4, 48 vCPU.
- **Software:** Python 3.13, torch 2.14.1+cu130 and numpy 2.5.4. The Hecate and VC3D files are the same as before,
  checked against the same sha256s.
- **Gate:** no survey surface is read until both positive controls pass on this machine.
  - **E1b** (PHerc0009B, the organisers' same-mesh labels): the −2..+2 ensemble AUC inside the supervision mask must
    be within 0.02 of 0.941, and the median ensemble probability on labelled ink within 0.03 of 0.445. T stays
    **0.445**.
  - **E1d** (PHerc0343): the forward ensemble must again show the October text line inside the readout area, judged
    by eye as before.
  - If either fails, S1 reads nothing until the cause is found.

## Volumes (`m1/survey_volumes.py`; all 8.64 µm, with m7 predictions and normal grids published)

| Volume | ID | Slices |
|---|---|---|
| PHerc0175A | 20250521115057 | 12,748 |
| PHerc0175B | 20250521125822 | 15,897 |
| PHerc0268 | 20251110183117 | 14,833 |
| PHerc0306B | 20250521133212 | 15,898 |
| PHerc0483A | 20250521140913 | 15,898 |
| PHerc0483B | 20251124083638 | 11,880 |
| PHerc0490A | 20250521151210 | 11,698 |
| PHerc0490B | 20250521151215 | 10,648 |
| PHerc0800 | 20250521135224 | 24,298 |
| PHerc1218 | 20250521120456 | 23,247 |

## Zones, chosen mechanically (`m1/survey_select.py`)
- **Scouting:** `e2/zoom.py --angles 8` at 15, 30, 50, 70 and 85% of each volume's height.
- **Gate:** merged share ≤ 0.17, ≥ 20 crossings, ≥ 90% inside the CT.
- **Exclusions:**
  - zones already grown on PHerc0175B and PHerc0490A (same radius, within 30°, within 1,700 slices);
  - near-duplicates within the survey: the same radius and direction (within 30°), within 2,500 slices of a
    better-ranked crop.
- **Ranking:** by merged share, then by crossings. Up to 12 zones per volume; 4 for PHerc0175B and PHerc0490A.
- **The list:** 87 zones, copied verbatim to `prereg/M1-survey-S1-zones.tsv` (sha256
  `f127ece0c56eef2479b46fc9078a06efabf3d4e7a36b7c45486e30ea6a3f85dc`).
  - Per volume: PHerc0175A 12, PHerc0175B 4, PHerc0268 1, PHerc0306B 12, PHerc0483A 12, PHerc0483B 12,
    PHerc0490A 4, PHerc0490B 6, PHerc0800 12, PHerc1218 12.
  - All 50 scouting heights succeeded.

## Surfaces, also chosen mechanically
- **Stage 1:** one test surface per zone.
  - Seed: `m1/seed.py` at the crop centre.
  - Growth: `m1/grow_more.sh` (step 20, 80 generations, thread limit 8), then the self-crossing census, the 48-layer
    render and the resample to 9.604 µm.
- **QC gate:** ≥ 2 cm² clean (8-cell contact exclusion) and ≥ 0.8 on papyrus. Each QC row goes to
  `data/m1/survey_qc.tsv` before any inference on that surface.
- **Failures:** a zone whose seed, growth or render fails for an infrastructure reason (a network, DNS or storage
  error in its log) is retried once. Any other failure is final and stays in the QC log.
- **Stage 2:** after stage 1's tracing, the zone with the most clean area in each volume, if it has ≥ 3 cm², gets
  four windings, under the same QC gate.
  - Seeds come from `m1/seeds_radial.py --inward 2 --outward 2` (reach 600 voxels) on the radial line through that
    zone's seed, using the volume's m7 prediction.
  - Growth, QC and reading are the same as in stage 1.

## Reading
- **Hecate as in batch F1:** windows k = −2..+2 in both directions, the probability-mean ensemble, bf16, batch 4, the
  readout-bbox + 128 px input crop, and `gpu_guard` on each worker's own GPU.
- **Readout rules unchanged:** T = 0.445; `ReadoutRules` (0.445, 9.604 µm, 0.5 mm, 8 px, aspect 8, 0.9).
- **Triage** (`m1/survey_triage.py`). A surface is reviewed by eye when either direction has:
  - area ≥ T above the control background (1.2%);
  - a candidate of ≥ 1 mm extent;
  - or mean p above 0.06.
  Every fifth surface in processing order is reviewed as well.
- **Verdicts:** each reviewed surface gets one of the three fixed sentences:
  1. "I didn't see any ink in the region."
  2. "I see possible ink traces but no legible letters."
  3. "I see legible letters." Only this triggers the First Letters checklist, and everything stays private.

  Unreviewed surfaces are reported as "below triage, not reviewed by eye", separately from the by-eye verdicts.
- **Escalation unchanged:** a candidate must reappear under a second independent model or seed, and run in rows
  parallel to the horizontal fibres. It then goes to Rhythm, privately.

## Stop rule
- S1 ends when stage 2 has been read.
- If nothing has been escalated by then, the survey stops and is reported.
- A deeper read (wider depth windows, a second model) or more spend needs its own pre-registration (S2).

## Deviations
- **2026-10-23, 22:50 UTC, a clarification written before any S1 QC row existed:**
  - Stage 2 takes the best zone among those that passed the QC gate ("keep"), ranked by clean area.
  - It runs for each volume as soon as that volume's tracer has finished stage 1 (`m1/batch/survey_stage2.sh`).
- **2026-10-24, 01:50 UTC, a follow-up check, added after surface PHerc0175A z6374_r30_a270 was read.** Its verdict
  (1) was recorded first (results/M1-survey-S1-reviews.tsv).
  - **Trigger:** any S1 surface with more than 9.4% of its readout area ≥ T in either direction. That is twice the E1d
    text control's forward share. So far only PHerc0175A z6374_r30_a270 qualifies, at 13.7% forward.
  - **What it adds:** three more surfaces, grown, QC'd and read as in stage 1, ahead of the queue
    (`m1/batch/survey_followup.sh`):
    - the inward and outward neighbouring windings, from `m1/seeds_radial.py --inward 1 --outward 1` through the
      surface's seed;
    - a second seed on the same winding, from `m1/seed.py` at the same (y, x), 200 slices (1.7 mm) higher.
  - **Reading it, fixed now:**
    - A response that recurs at the same place on a neighbouring winding marks a structure through several layers,
      not ink.
    - One that recurs on the second-seed surface belongs to that papyrus surface.
    - Escalation is unchanged: it still needs rows along the horizontal fibres and a second model or seed.
  - The verdict rules do not change.
  - Before this check, no other S1 surface came within 40 voxels of the strong region (`m1/overlap.py`). The
    nearest, the z6374_r30_a225 and z6374_r30_a315 surfaces, lie a median 0.64 mm and 1.21 mm away, several windings
    out.
- **2026-10-24, 04:10 UTC, a row-candidate check, added after surface PHerc0175A z8923_r55_a022 was reviewed.** Its
  verdict (2) was recorded first.
  - **Trigger:** a reviewed surface with a row of separate blobs ≥ T, at least 5 mm long, running along the text
    direction (constant z) and present in at least four of the five depth windows. That is how the E1d text line looks.
  - **Why another check:** the first follow-up's second seed (`m1/seed.py` 200 slices up) landed on another winding.
    This check takes the second seed from the mesh itself, so it stays on the same sheet.
  - **What it adds:** three more surfaces, grown, QC'd and read as in stage 1, ahead of the queue
    (`m1/batch/survey_rowcheck.sh`):
    - a second seed on the same sheet: the mesh vertex 400 slices (3.5 mm) from the row's middle and nearest to it in
      (x, y) (`m1/rowcheck_seeds.py`), snapped to the m7 prediction by `m1/seed.py`;
    - the inward and outward neighbouring windings, from `m1/seeds_radial.py --inward 1 --outward 1` through the row's
      middle.
  - **Reading it, fixed now:**
    - The row passes if, on the second-seed surface, a row of blobs ≥ T lies within 0.3 mm (in 3D) of the original
      row, along the same line, in either direction (a new mesh may face the other way).
    - It fails if a row recurs at the same place on a neighbouring winding, which marks a structure through several
      layers.
    - It also fails if the second-seed surface does not reach the row's location.
    - A row that passes goes to Rhythm privately, as the escalation rule says. Nothing becomes public.
  - The verdict rules do not change.
