# Results (22–23 October 2026)

All numbers come from the scripts in this repository, run on the Vesuvius Challenge open data. Per-batch details,
including the full candidate statistics, are in `results/`. AUCs are pixel ROC AUCs inside the stated mask. "T" is
the pre-registered threshold, T = 0.445.

## 1. Positive control on PHerc0009B (published 8.64 µm render)
- **Segment:** `20250919125754-auto_grown_20250919055754487_inp_hr`, 8.64 µm surface volume (31 × 7040 × 5700),
  resampled to 9.604 µm (28 layers).
- **Model:** Hecate 9.6 µm, bf16, batch 4, stride 32. The 16-layer input window is moved by k layers from the stack
  centre.

### 1a. Same-mesh labels (`e1b/`): the clean control
- **Labels:** the organisers' 2026-09-18 labels on the 2.401 µm surface volume of the same mesh (109 × 25360 × 20520 =
  3.60 × the 8.64 µm canvas), at level 2.
- **Registration from CT texture only:** 248 of 248 tiles agree (median tile NCC 0.94) on a pure shift of (10, 8) px,
  robust SD 1.5 px. The sheet sits 1.5 layers below the render centre (p10–p90 −2.5..−0.5).

| Window k | −2 | −1 | 0 | +1 | +2 | ens −1..+1 | ens −2..+2 |
|---|---|---|---|---|---|---|---|
| AUC, supervision mask (2.77 M px, 22% ink) | **0.940** | 0.925 | 0.882 | 0.849 | 0.831 | 0.918 | **0.941** |
| AUC, validation mask (0.79 M px) | 0.872 | 0.887 | 0.878 | 0.879 | 0.865 | 0.898 | 0.897 |
| T = median probability on labelled ink | 0.741 | 0.620 | 0.404 | 0.341 | 0.224 | 0.452 | **0.445** |

- **Nulls:** with labels displaced by 250 px in four directions, AUC is 0.42–0.67. The x-shifted nulls stay above 0.5
  because they slide the labels along the text line.
- **Against J. Lu's published benchmark** (offset 0: 0.914; −1: 0.954; ensembles 0.955 and 0.956):
  - The ensemble and the best single window agree within 0.015.
  - His 27-layer resample centres the window half a layer lower than our 28-layer one. That explains the larger gaps
    at k = 0 and −1..+1, which sit on the slope of the depth profile.
- **The readouts use** the −2..+2 probability-mean ensemble with **T = 0.445**.
- **Background reference:** on the control's non-ink pixels inside the supervision mask, mean p is 0.037 and 1.2% of
  pixels are ≥ T.

### 1b. The Hugging Face 0009B labels sit on a different mesh (`e1/`)
- **Which labels:** `scrollprize/datasets` → `ink/0009b/auto_grown_20250919055754487_inp_hr_2um` (level 2: 17 × 6496
  × 5312).
  - That canvas is not the published 8.64 µm render's mesh at another scale.
  - Phase correlation, an 8-orientation search and a per-axis scale search all fail, with NCC ≤ 0.004.
- **`align3`, a global fit to the segment outlines:** IoU 0.986, at anisotropic scales of 0.881 and 0.918 against
  0.900 for pure voxel scaling. Texture NCC stays at 0.023.
- **`align4`:**
  - The depth search finds render layer 21 of 31 matching hi-res layer 5 of 17 (z ≈ 28–29 against far shifts).
  - 160–173 tiles beat a displaced null's 99th percentile.
  - The residual around the best affine fit is 8.4 px RMS, so the mapping is non-rigid.
- **`align5`, a dense field** (affine + Gaussian-interpolated tile residuals): 1.7–1.8 px leave-one-out RMS.

| Transfer | k = −2 | −1 | 0 | +1 | +2 | ens −2..+2 |
|---|---|---|---|---|---|---|
| Outline fit only (`align3`) | 0.800 | 0.798 | 0.746 | 0.730 | 0.704 | 0.792 |
| Dense field (`align5`) | **0.938** | 0.920 | 0.867 | 0.835 | 0.825 | 0.934 |

- **Practical upshot:** anyone scoring a 9 µm model against those labels on the published 8.64 µm render needs a
  non-rigid transfer, or should use the same-mesh labels from the open-data segment folder.

## 2. Pipeline control on PHerc0343 (`m1/control343_job.sh`)
- **Pass criterion, fixed before the run:** recognisable letter strokes in the −2..+2 ensemble of either direction,
  inside the readout area.
- **Seed:** (5880, 3909, 10467). This is the node of the winner's published mesh nearest the centre of their reading
  area with a horizontal normal; it lies exactly on the m7 prediction.
- **Mesh:** 7.9 cm² grown. There are 7,849 self-crossing contacts, so the readout area is 3.43 cm².

| Direction | Candidates | Mean p | p99 | Area ≥ T |
|---|---|---|---|---|
| Forward | 21 | 0.078 | 0.81 | 4.5% |
| Reverse | 15 | 0.055 | 0.56 | 1.8% |

- **Result: PASS.**
  - The forward ensemble shows a band of glyph-like marks about 2 mm tall, running along θ at constant z. The mesh grid's
    rows advance about 20 voxels per step in xy against 5 in z, which is the geometry of a text line. The reverse
    direction shows only scattered blobs.
  - **Same sheet as the winner's text:** the band spans z 9879–10884, inside the winner's reading area (z 9515–10998).
    Against a 4×-densified copy of the winner's mesh, the median distance is 2.86 voxels, with 53% of nodes within 3.
- **Limit:** the strokes are blurrier than in the 0009B control. With Hecate alone at ±2 layers, individual letters are
  not cleanly legible.

## 3. Coarse scouting of the least-searched May volumes (`e2/`)
- **Level 3** (69 µm voxels): CT plus the m7 recto prediction, with metrics computed inside the CT (2-voxel erosion per
  slice).

| Volume | Share of m7 positives outside the CT | Rough on-CT recto area | Crossings per ray at 5 heights | Runs > 3 voxels |
|---|---|---|---|---|
| PHerc0175B | 0.40 | ~11,900 cm² | 61–75 | 7.2% |
| PHerc0490A | 0.43 | ~7,500 cm² | 47–70 | 8.1% |
| PHerc0483A | 0.48 | ~6,400 cm² | 46–58 | 4.8% |
| PHerc1218 | 0.52 | ~5,700 cm² | 32–41 | 4.3% |
| PHerc0490B | 0.47 | ~4,600 cm² | 36–67 | 5.2% |

- **Level-1 close-ups** (17.28 µm, 12 crops per height) rank zones by the share of prediction runs thicker than 3
  voxels ("merged"). In PHerc0175B, the crops under 0.17 show separated or flat layered sheets, and the rest look
  crushed or fused (see `figures/zones_separated_vs_crushed.png`).

## 4. Pre-registered search of PHerc0175B (19 surfaces, all verdict 1)
- **Verdict sentence for every surface:** "I didn't see any ink in the region."

| Batch (pre-registration) | Zone | Surfaces | Readout area | Area ≥ T, forward / reverse |
|---|---|---|---|---|
| m1 (925b417) | outer r80_a270, z 7942 | 1 | 4.86 cm² | 12.1% / 9.4% |
| m1-b (6761b8c) | the next three windings inward | 3 | 14.16 cm² | 1.0–5.2% / 3.2–4.7% |
| m1-c (b2b4b7d) | mid-radius r55_a225, z 7944 (B1–B3) | 3 | 13.32 cm² | 0.4–2.0% / 0.7–1.6% |
| m1-c (b2b4b7d) | inner r30_a090, z 5559 (C1–C3, low-confidence) | 3 | 7.46 cm² | 0.7–1.3% / 0.3–0.6% |
| m1-d (fa09684) | mid-radius z 7944, windings B4–B7 | 4 | 16.55 cm² | 0.3–2.5% / 0.5–1.2% |
| m1-d (fa09684) | outer r80_a090, z 10326, far side (H1–H3, low-confidence) | 3 | 9.85 cm² | 1.0–1.6% / 1.2–1.7% |
| M1-batch-E (7ed51cd) | mid-radius z 7944, windings B8 and B10 (B10 low-confidence) | 2 | 6.35 cm² | 0.8–4.7% / 2.0–2.3% |
| **Total** | | **19** | **≈ 72.5 cm²** | |

- **Not counted:** a 20th surface, G1, was a test surface in a new outer zone (z 10341 r80_a270). It passed the
  self-crossing gate but grew off the papyrus: only 12% of its readout area is on papyrus (section 5b). Its verdict is
  also sentence 1, but its 2.35 cm² is not counted as searched.

- **How the verdicts were read:** each verdict comes from the ensembles at quarter resolution plus full-resolution
  crops of the strongest features. A text line would run horizontally, vertically or obliquely depending on the mesh's
  grid orientation, and that was taken into account.
- **What appeared:** blob or speckle texture, and two-sided clusters next to folded zones (structure, not ink on one
  face). No rows of glyphs appeared.
- **Not read:** six more surfaces (zones E and F at z 5560) grew with 8k–88k interior self-crossing quads and only
  0.2–2.6 cm² clean area each.

## 5. Pre-registered search of PHerc0490A (10 surfaces, all verdict 1)
- **Pre-registrations:** `prereg/PHerc0490A-m1.md` (76796e3) for P1–P5 and Q1; `prereg/M1-batch-E.md` (7ed51cd) for
  P6–P9.
- **Zone choice:** E2c gated six zones. One test surface per promising zone was grown first. Zone z 5848 r55_a225 kept
  4.06 cm² clean, and eight neighbouring windings were added there. The two inner z 7600 zones folded to 0.5 and
  1.3 cm² and were not read.

| Surface | Zone | Readout area | Area ≥ T, forward / reverse |
|---|---|---|---|
| P1 | z 5848 r55_a225 | 4.06 cm² | 0.6% / 1.5% |
| P2 | same, inward | 3.82 cm² | 0.6% / 0.6% |
| P3 (low-confidence) | same, inward | 3.38 cm² | 1.4% / 0.9% |
| P4 | same, outward | 3.65 cm² | 0.8% / 1.0% |
| P5 | same, outward | 3.95 cm² | 0.3% / 1.8% |
| Q1 (low-confidence) | z 7600 r55_a225 | 2.51 cm² | 0.7% / 0.9% |
| P6 | z 5848 r55_a225, inward of P3 | 3.93 cm² | 0.8% / 0.5% |
| P7 (low-confidence) | same, further inward | 2.84 cm² | 0.4% / 0.3% |
| P8 | same, outward of P5 | 4.24 cm² | 1.7% / 0.5% |
| P9 | same, further outward | 4.04 cm² | 1.6% / 0.6% |
| **Total** | | **36.4 cm²** | |

- **Baselines are quiet** (mean p 0.033–0.067), and no row of glyphs appears in either direction.
- **The strongest one-sided features at full resolution:**
  - P1 reverse: a soft smear about 5 mm long along the edge of an excluded fold zone.
  - P5 reverse: a small cluster of soft blobs.
  - P8 and P9 forward: streaks about 1 mm wide and 4–5 mm long. They follow cracks in the CT and run through five
    windings (section 5b).
  - None has strokes.
- **Verdict sentence for every surface:** "I didn't see any ink in the region."

### 5a. Batch E on PHerc0175B: the strongest one-sided response so far
- **B10 forward:** a cluster that fills 13% of a 7.7 mm square at ≥ T, against 2% in reverse. It is present in all
  five depth windows.
- **At full resolution:** soft round blobs 1–2 mm across. They sit at the edge of large voids that dominate the CT
  layers just below the surface.
- It has no strokes and no rows along the lines of constant z.
- Details are in `results/M1-batch-E.md`.

### 5b. Two checks added during batch E
- **The papyrus share** (`m1/onpapyrus.py`).
  - It samples the level-1 CT at the mesh vertices and counts readout cells whose brightest voxel within ±2 voxels is
    above 90. Air reads about 40–60 and papyrus about 100–150. No render is needed.
  - Batch E's G1 scores 0.12. It passed the self-crossing gate, but most of it is air.
  - Every other surface read so far scores 0.97–1.00, so the areas above are papyrus.
  - From the next batch on, a surface is read only with ≥ 2 cm² clean and ≥ 0.8 on papyrus.
- **Cross-winding recurrence** (`m1/cross_winding.py`).
  - It maps a feature to 3D and looks at the same place on the neighbouring windings. Ink on one winding has no reason
    to recur a whole turn away; a crack or fold through several layers does.
  - P8's forward double streak recurs with the same shape on P9 (13 voxels away, 13.5% ≥ T) and on P5 (3.5 voxels,
    22%), and more weakly on P4 and P1. It is absent on P2 and P3, 57–72 voxels away.
- **M1 total:** 29 surfaces, ≈ 109.0 cm² of papyrus on two scrolls, all verdict 1.

## 6. Throughput (shared A10G, other jobs on the GPU)
- **Hecate:** about 2.1–4.2 min per run on a 2559² crop (≈ 6 cm²), depending on the other load.
  - 10 runs per surface (5 windows × 2 directions) gives 6.5–13 cm² of readout area per GPU-hour.
  - Peak GPU memory is ≤ 1.8 GB.
- **GrowPatch:** 80 generations reach about 7.5 cm² in 2.5–10 min with 8 threads. Runs that reuse a warm normal-grid
  cache are the fast ones. Streaming the normal grids for one zone fills about 6 GB of cache.
- **Render:** 48 layers of 3240² at 8.64 µm in about 80 s. It prefetches about 1,200 CT chunks into a ~4.6 GB cache.
