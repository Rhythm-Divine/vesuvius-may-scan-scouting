# First Letters scouting kit for the 8.64 µm (May 2025) scans, with pre-registered readouts and two positive controls

This kit searches the First Letters-eligible scrolls scanned at 8.64 µm / 116 keV (ESRF BM18, May 2025). It needs no
local copy of a volume: surfaces are grown, checked, rendered and read for ink straight from the public open-data
bucket. Every target readout is pre-registered, and the full chain is shown to read known text before its negatives
are reported.

**Why this matters:**
- The two 2025-protocol scrolls that showed text, PHerc. 343 and PHerc. 1447, are May 8.64 µm scans. Four of the 21
  eligible volumes (PHerc0175B, 0483A, 0490A, 1218) have had only one shallow public ink pass.
- A "no ink" result is only worth something if the same chain, settings and threshold demonstrably find ink where it
  is known to exist. This kit makes that check part of the pipeline and publishes its numbers.

**The two controls in brief:**
- **PHerc0009B, published render:** Hecate's depth ensemble scores AUC 0.941 against the organisers' labels.
- **PHerc0343:** a surface grown by this kit, read with the same settings, shows the October First Letters text line,
  a median of 2.9 voxels from the winner's mesh.

Images that show readable letters are not published here, in keeping with the Vesuvius Challenge data agreement.

## What it contains
- **`m1/`: the search pipeline.**
  - A seed on the m7 surface prediction near a zone centre, plus neighbouring windings along the radial line
    (`seed.py`, `seeds_radial.py`).
  - VC3D GrowPatch, streaming the m7 prediction and its published normal grids, with no local volume copies
    (`grow_more.sh`).
  - Mesh QC: interior self-crossings and pairwise distinctness (`qc_meshes.py`), and the share of the readout area
    that sits on papyrus (`onpapyrus.py`).
  - A 48-layer render streamed from the masked CT, resampled to 9.604 µm (`resample_render.py`).
  - Hecate 9.6 µm in five depth windows and both directions, through a shared-GPU guard (`hecate_more.sh`).
  - A pre-registered readout (`readout.py`).
  - Review tools, for looking only:
    - review sheets, full-resolution crops and per-window depth views, with lines of constant z marking where text
      would run (`sheets.py`);
    - a check of whether a feature recurs on the neighbouring windings (`cross_winding.py`).
- **`e1/`, `e1b/`: positive controls on PHerc0009B.**
  - `e1b/`: a CT-only registration to the organisers' same-mesh labels (a pure shift).
  - `e1/`: the tools to move labels between two different meshes of one segment: depth search, tile field, and a dense
    non-rigid field.
- **`m1/control343_job.sh`: the end-to-end pipeline control.** It grows a surface of our own at the PHerc. 343 First
  Letters text, using the winner's published mesh only to choose the seed.
- **`e2/`: coarse scouting.**
  - Level-3 statistics per volume: on-CT papyrus and the share of m7 predictions that fall outside the CT.
  - Level-1 close-ups that rank zones by sheet separability.
- **`sweep/readout.py`:** candidate extraction and control calibration, with unit tests.
- **`prereg/` and `results/`:** every pre-registration and every verdict.

## Results (details in [docs/RESULTS.md](docs/RESULTS.md))
- **The positive control reproduces the published benchmark.** On PHerc0009B with the organisers' same-mesh labels,
  Hecate's −2..+2 depth ensemble scores **AUC 0.941** inside the supervision mask. J. Lu reported 0.956. The best single
  window scores 0.940 against his 0.954. Displaced-label nulls score 0.42–0.67. The threshold for all readouts,
  **T = 0.445**, comes from this control.
- **The 0009B labels in the Hugging Face bucket are on a different mesh.** The labels under
  `ink/0009b/..._inp_hr_2um` do not line up with the published 8.64 µm render by any scale and shift.
  - The best outline fit leaves texture NCC at 0.023, and AUC with that transfer is 0.746.
  - A CT-only dense field (1.7 px leave-one-out) brings it to 0.938 at the best window.
  - The open-data segment folder carries a same-mesh copy of the labels (`ink-labels/2.401um-.../20260918`), and that
    is the one to score against.
- **The pipeline control passes.** On PHerc0343, a GrowPatch surface seeded at the First Letters text area shows a
  line of glyph-like marks about 2 mm tall in the forward direction only.
  - The line lies on the winner's text sheet: a median of 2.9 voxels from their published mesh, at the text's height.
  - So the kit's own surfaces, render and threshold read real ink on a May 8.64 µm scroll.
- **Pre-registered negatives.** These are areas other teams can deprioritise or attack differently:

  | Volume | Surfaces read | Readout area | Verdict on every surface |
  |---|---|---|---|
  | PHerc0175B | 19, in four zones (outer windings; mid-radius at z 7944; inner; outer far side) | 72.5 cm² | "I didn't see any ink in the region." |
  | PHerc0490A | 10, in the mid-radius zones at z 5848 (nine windings) and z 7600 | 36.4 cm² | "I didn't see any ink in the region." |

  Every counted surface sits on papyrus: 0.97–1.00 of its readout area by `m1/onpapyrus.py`. A 20th PHerc0175B
  surface grew off the papyrus (0.12) and is not counted.

- **What it costs:** 6.5–13 cm² of readout area per GPU-hour on one shared A10G (Hecate bf16, 5 windows × 2
  directions, ≤ 1.8 GB). On the CPU, growth takes about 3–10 min and rendering about 1.5 min per 7.5 cm² surface.
- **Lessons that change how to search:**
  - The level-1 separability score is necessary but not sufficient. Two PHerc0175B zones that passed it folded badly
    once grown: 8k–88k interior self-crossing quads, leaving only 0.2–2.6 cm² clean per 7.5 cm² surface. The
    self-crossing count after growth is the real gate (`m1/qc_meshes.py`).
  - Across the five scouted May volumes, 40–52% of m7 positives lie outside the CT (`e2/overview.py --scout`). Mask
    predictions to the CT before using them.
  - Hecate's response on PHerc0175B's outermost winding is diffusely raised (12% of the area ≥ T, against 1.2% on
    control background) without any stroke structure. It falls to 1–5% on the next three windings inward. Candidate
    counts are meaningless there. Read by eye, and use the one-sided test: ink shows in one direction, structure in
    both.
  - One-sided is not enough. Cracks give one-sided responses too: P8's streaks follow cracks in the CT and recur at the
    same 3D place on five windings. Ink would not repeat a whole turn away. Check the neighbouring windings
    (`m1/cross_winding.py`).
  - A surface can pass the self-crossing gate and still not be on papyrus. One test surface was 88% air. Check the
    papyrus share before reading (`m1/onpapyrus.py`).

![Separated vs crushed](figures/zones_separated_vs_crushed.png)

*Level-1 close-ups of PHerc0175B at z 7944 (m7 prediction in red). Left: separated sheets with air gaps, where growth
works. Right: the crushed core.*

## Quickstart
```bash
bash setup.sh                          # venv + Hecate 9.6 µm (MIT) + VC3D AppImage (villa 406e767)
.venv/bin/python -m pytest tests       # readout rules and GPU guard

# 1) Positive control on PHerc0009B with the same-mesh labels (CPU registration, then GPU)
.venv/bin/python e1/fetch_control.py && bash e1b/fetch_labels.sh
.venv/bin/python e1/prepare.py --out data/e1     # 8.64 -> 9.604 um render.npy
bash e1b/job.sh                                  # writes data/e1b/register.json and score.json

# 2) Pipeline control on PHerc0343 (grow -> QC -> render -> Hecate -> readout)
bash m1/control343_job.sh

# 3) Search a zone: three windings per "NAME Z Y X CENTRE_Y CENTRE_X" (level-0 voxels)
bash m1/zones.sh "B 7944 3504 3862 4876 5234"
.venv/bin/python m1/qc_meshes.py --meshes data/m1/PHerc0175B/meshes --render data/m1/PHerc0175B/render \
    --out qc.json <mesh names>
.venv/bin/python m1/onpapyrus.py --sample PHerc0175B --volume-id 20250521125822 <mesh names>   # read only if >= 0.8
# write and commit prereg/<scroll>-<batch>.md, then:
PRE=prereg/<scroll>-<batch>.md bash m1/hecate_more.sh <mesh names>
```
- **Settings:** every script takes its settings from `config.sh` and the environment: `CPUS`, `NICE`, `THREADS`,
  `GROW_THREADS`, `GPU_MIN_FREE_GB`, `GPU_MAX_OWN_GB`, `GPU_RESERVE_FILE`, `VC3D`, `HECATE_DIR`, `PY`.
- **Other scrolls:** set `SAMPLE` and `VOL` for `m1/grow_more.sh` and `m1/hecate_more.sh`, and `--prefix` for the seed
  tools.
- **Requirements:** Linux x86_64, Python ≥ 3.11, and a CUDA GPU with ≥ 8 GB free for Hecate. Disk use stays under
  about 20 GB, because the streamed caches are cleared after each step. Access to the open-data bucket in us-east-1
  costs nothing to read.
- **Formats:** OME-Zarr in, tifxyz meshes, zarr/`.npy` renders, PNG probability maps and JSON reports.

## How the readouts are kept honest
- **Pre-registration first.** Each batch is pre-registered in `prereg/` before any inference on it: target meshes,
  readout area, model and checksums, depth windows, ensemble, threshold, candidate rules, escalation rule and the
  fixed verdict sentences.
  - `m1/hecate_more.sh` refuses to run unless that file is committed and unmodified.
  - The pre-registrations were committed in our private lab repository. The files here are byte-identical copies,
    including their references to our private lab notebook.
  - The commits and the first inference of each batch:

  | Pre-registration | Committed (UTC) | First inference (UTC) |
  |---|---|---|
  | `prereg/PHerc0175B-m1.md` | 2026-10-22 02:42:36 | 02:42:36 |
  | `prereg/PHerc0175B-m1-b.md` | 04:42:18 | 04:42:19 |
  | `prereg/PHerc0175B-m1-c.md` | 08:27:38 | 08:27:39 |
  | `prereg/PHerc0175B-m1-d.md` | 12:18:37 | 12:18:38 |
  | `prereg/PHerc0490A-m1.md` | 18:26:30 | 18:26:30 |
  | `prereg/M1-batch-E.md` | 2026-10-23 03:07:42 | 03:07:43 |
  | E1d pass criterion (in the lab notebook) | 2026-10-22 07:03:09 | 07:13:49 |

  The full private history is available to the Vesuvius Challenge team on request.
- **Verdicts are by eye**, and a candidate count never counts as a finding.
  - Escalation needs reappearance under a second independent model or seed, in rows parallel to the horizontal fibres.
  - Surfaces with heavy self-crossing are reported as low-confidence geometry.

## Limitations
- **One ink model (Hecate)** with windows ±2 layers around the surface. The PHerc. 343 winner averaged four models over
  31 depths. A negative here is "not seen by this chain", not "no ink".
- **GrowPatch patches**, about 7.5 cm² each, seeded zone by zone, not whole-winding spiral fits. 72.5 cm² is about 0.6%
  of PHerc0175B's papyrus.
- **The outer windings' raised response** is unexplained. It may be crust or the condition of the outer layers, or a
  surface that sits more than 2 layers off the ink.

## Credits and licences
- **Code:** MIT (`LICENSE`). Data and third-party terms are in `NOTICE.md`.
- **Data:** scan data, labels and all derived images come from the Vesuvius Challenge open data, CC BY-NC 4.0 and the
  data agreement.
- **Tools and models:**
  - Hecate 9.6 µm and the m7 surface predictions are by the Vesuvius Challenge team.
  - VC3D comes from ScrollPrize/villa (GPL-3.0, run as a program).
- **Prior work:**
  - The Hecate benchmark and depth-window analysis we reproduce are J. Lu's (ArcheyChen/vesuvius-eligible-scouting).
  - The PHerc. 343 mesh used to seed the pipeline control is E. Nieuwlaar's (Nieuwlaar/pherc343-first-letters).
