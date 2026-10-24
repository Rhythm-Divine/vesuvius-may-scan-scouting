# Methods

The chain runs from public data to a pre-registered verdict. Coordinates are level-0 voxels (x, y, z) of the 8.64 µm
volume unless stated otherwise.

## 1. Choosing where to grow (`e2/`)
- **`e2/overview.py --scout`** fetches level 3 (69 µm voxels) of the CT and the m7 recto prediction. It computes:
  - the share of predictions outside the CT, after a 2-voxel erosion of CT support per slice;
  - a rough on-CT recto area;
  - along 16 rays at 5 heights: crossings, spacing regularity and the share of runs thicker than 3 voxels.
  It keeps only JSON and PNGs.
- **`e2/zoom.py`** takes 12 level-1 crops (384² × 16 slices, 17.28 µm) at 3 radii × 4 directions around the slice
  centroid.
  - Each crop gets the share of prediction runs thicker than 3 voxels along its radial line ("merged").
  - Zones with merged ≤ 0.17 are candidates.
- **The level-1 score is not enough** (see RESULTS §4). Grow one test surface per candidate zone, and keep the zone
  only if its self-crossing QC (§3) leaves several cm² clean.

## 2. Seeds and growth (`m1/`)
- **`m1/seed.py`** reads a level-0 crop of the prediction around a zone centre. It returns the nearest predicted voxel
  whose run along the radial direction (away from the scroll centre) is at most 4 voxels, so the seed sits on a thin
  sheet rather than a fused blob.
- **`m1/seeds_radial.py`** reads the prediction along the radial line through a seed and lists its sheet crossings.
  Thin runs (≤ 8 voxels after ±1-voxel bridging) inward and outward become seeds for the neighbouring windings. On
  PHerc0175B and PHerc0490A the median pitch was 15.5–16.5 voxels (0.13–0.14 mm).
- **`m1/grow_more.sh`** runs VC3D `vc_grow_seg_from_seed` (villa 406e767): `mode seed`, `step_size 20`, 80
  generations, CPU.
  - It streams the m7 prediction over https as `-v`, and the published normal grids (spiral step 20) through a local
    directory holding `normal-grids-remote.json`. Grid files are fetched on demand, about 6 GB per zone, and deleted
    after growth.
  - VC3D's remote chunk cache defaults to `~/.VC3D/remote_cache`. The job redirects it into the repository through
    `VC3D_CONFIG_DIR/VC3D.ini` (`[viewer] remote_cache_dir`).

## 3. Mesh QC (`m1/qc_meshes.py`, `vc_tifxyz_selfcross`)
- **Readout area** = grid cells at least 16 cells (2.8 mm) from the mesh boundary, excluding cells within 8 cells of
  any transverse self-crossing contact (`m1/readout.py --exclude-contacts 8`).
  - Growth folds at its fringe, so most contacts sit within the outer 15 cells.
  - Folded zones also produce interior contacts, which this rule removes.
- **Distinctness:** for every pair of surfaces, the distance from each interior grid point of one to the nearest grid
  point of the other.
  - A median under 4 voxels would mean the same sheet, a duplicate.
  - Adjacent windings came out 10–66 voxels apart, with ≤ 3% of points within 3 voxels.
- **Grid orientation:** from |dz| per grid step along rows and columns. This tells which way a text line (constant z,
  along θ) would run in the rendered image.
- **Papyrus share (`m1/onpapyrus.py`, used from batch F1 on):** the share of readout cells whose brightest level-1 CT
  voxel within ±2 voxels of the mesh vertex is above 90 on the 8-bit scale. Air reads about 40–60 and papyrus about
  100–150.
  - It needs no render: only the chunks under the mesh vertices are fetched, about 120–180 per surface.
  - A surface is read only with ≥ 0.8 on papyrus and ≥ 2 cm² of readout area.

## 4. Render (`vc_render_tifxyz`, `m1/resample_render.py`)
- **Render:** `-g 0 --scale 1 -n 48 --slice-step 1 --surface-interpolation smooth --prefetch-remote`, streaming the
  masked CT from the bucket. That gives 48 layers at 8.64 µm, 3240² for an 80-generation surface.
- **Resample** to 9.604 µm: XY origin-aligned, Z centred, giving 43 × 2914². Layer 21 is the mesh surface.

## 5. Ink (`m1/hecate_more.sh`, `tools/gpu_guard.py`)
- **Model:** Hecate 9.6 µm (sha256 in `SHA256SUMS.models`), bf16, batch 4, stride 32.
- **Windows:** the 16-layer input is layers [13 + k, 28 + k] for k = −2..+2, in both directions (`--reverse` on the
  same 16 layers).
  - Forward is not always the reading direction for self-grown meshes, so each direction is read separately.
  - The per-direction ensemble is the per-pixel probability mean over k. This matches how T was calibrated.
- **Input crop:** the readout bbox + 128 px, to save GPU time.
- **`tools/gpu_guard.py`** runs each job only if the GPU has ≥ `GPU_MIN_FREE_GB` free. It stops the job if the job
  exceeds `GPU_MAX_OWN_GB`, and yields at once when `GPU_RESERVE_FILE` appears, for sharing a GPU with other users.
  Refused or yielded runs are retried later, and finished outputs are kept.

## 6. Pre-registered readout (`m1/readout.py`, `sweep/readout.py`)
- **Rules:**
  - Components ≥ T (8-connected) inside the readout area.
  - A size floor of 0.5 mm on the longest bbox side.
  - Drop components within 8 px of the area edge, with aspect > 8, or less than 90% inside the area.
- **Reporting:** candidate counts, mean p, p99, and the share of the area ≥ T next to the control background (1.2%).
- **Verdicts:** one of three fixed sentences per surface, by eye.
  - The ensembles are read at quarter resolution, plus full-resolution crops of the strongest features, with the
    grid orientation in mind (`m1/sheets.py`).
    - The sheets carry dotted lines of constant z, which mark where a line of text would run.
    - Per-window depth views show whether a feature follows something visible in the CT layers, such as a crack or
      void.
  - A feature present in both directions at the same place is treated as structure, not ink on one face.
  - **Cross-winding check (`m1/cross_winding.py`):** a feature that recurs at the same 3D place on the neighbouring
    windings is structure running through the layers. Ink on one winding has no reason to recur a whole turn away.
  - Escalation needs reappearance under a second independent model or seed.

## 7. Controls (`e1/`, `e1b/`, `m1/control343_job.sh`)
- **E1b, same-mesh labels:**
  - Register the 8.64 µm render (resampled) to the 2.401 µm render of the same mesh, from CT texture only. The steps
    are band-passed NCC over every render layer × 4-layer slab of the 2.4 µm render, then 256 px tiles.
  - Score Hecate windows −2..+2 inside the supervision mask. T is the median ensemble probability on labelled ink.
- **E1, Hugging Face labels on another mesh:**
  - `align3`: outline IoU for a global anisotropic scale and shift.
  - `align4`: depth search, then tiles with a 400 px-displaced null; tiles above the null's 99th percentile vote.
  - `align5`: affine + Gaussian-interpolated tile residuals, checked by leave-one-out.
  - The labels never steer any fit.
- **E1d, the pipeline control:**
  - The seed is the winner's published-mesh node nearest their reading-area centre, with a horizontal normal
    (`m1/n343_seed.py`).
  - Everything else is the search pipeline unchanged.
  - The pass criterion was fixed before the run. Agreement with the winner's sheet was checked afterwards, against a
    4×-densified copy of their mesh.

## 8. Survey S1 over the ten May volumes (`m1/survey_*.py`, `m1/batch/`)
- **Volumes:** the ten May 8.64 µm volumes with m7 predictions and normal grids in the public catalogue
  (`m1/survey_volumes.py`).
- **Scouting:** `e2/zoom.py --angles 8` at 15, 30, 50, 70 and 85% of each volume's height. That gives 24 level-1 crops
  per height, at 3 radii × 8 directions.
- **Zones, chosen mechanically** (`m1/survey_select.py`):
  - **Gate:** merged share ≤ 0.17, ≥ 20 crossings, ≥ 90% inside the CT.
  - **Exclusions:** zones already grown (same radius, within 30°, within 1,700 slices), and near-duplicates within the
    survey (within 2,500 slices).
  - **Ranking:** by merged share, then crossings. Up to 12 zones per volume, 4 for the two volumes searched before.
  - The list (87 zones) was committed with the pre-registration.
- **Stage 1** (`m1/batch/survey_trace.sh`): one test surface per zone.
  - Seed at the crop centre, growth (step 20, 80 generations), self-crossing census, 48-layer render, resample to
    9.604 µm.
  - Each worker has its own VC3D cache and CPU slice and takes whole volumes, because the normal-grid cache is per
    volume.
  - **QC gate:** ≥ 2 cm² clean (8-cell contact exclusion) and ≥ 0.8 on papyrus. The QC row is logged before any
    inference.
- **Stage 2** (`m1/batch/survey_stage2.sh`): four neighbouring windings (`m1/seeds_radial.py --inward 2 --outward 2`)
  around each volume's best kept zone with ≥ 3 cm² clean.
- **Reading** (`m1/batch/survey_gpu.sh`): Hecate exactly as in §5–6, one worker per GPU, from a shared queue.
- **Triage** (`m1/survey_triage.py`): a surface is reviewed by eye when either direction has area ≥ T above 1.2%, a
  candidate ≥ 1 mm, or mean p above 0.06, and also every fifth surface.
- **Pre-declared checks, added as dated deviations before their surfaces were grown:**
  - **Follow-up** (`m1/batch/survey_followup.sh`): for surfaces above 9.4% ≥ T, grow the neighbouring windings and a
    second seed.
  - **Row check** (`m1/batch/survey_rowcheck.sh`, `m1/rowcheck_seeds.py`, `m1/rowcheck_eval.py`): for a reviewed row
    of blobs ≥ 5 mm along the text direction, grow a second seed taken from the mesh 3.5 mm away, plus both
    neighbouring windings, and map the row onto each.
  - **Pass and fail readings were fixed in advance:**
    - a row recurring on a neighbouring winding fails;
    - a second-seed surface that does not reach the row fails;
    - a row recurring on the same sheet passes, and goes to escalation.

## 9. Survey S2: a second, independent ink model (`m2/`)
- **Model:** reader-v2 (`reader-v2-step040000.pth`, sha256 in `SHA256SUMS.models`), a 3D-stem/2D U-Net with a
  17-layer window, run through villa's `koine_machines` at 47a9c37 in a locked uv environment
  (`setup_reader_v2.sh`).
- **Input:** each kept S1 mesh, rendered again natively at 8.64 µm with 48 layers, exactly as S1 rendered before
  resampling.
- **Reading** (`m2/r2_infer.sh`): forward and reverse, each the mean of three 17-layer windows (centred, +2, −2;
  overlap 0.5, Hann blending).
- **Alignment** (`m2/r2_combine.py`): the maps are resampled to S1's 9.604 µm grid the way the renders were and
  cropped to S1's window, so they line up pixel for pixel with Hecate's.
- **Readout** (`m2/readout_r2.py`): S1's valid area and candidate rules with reader-v2's own threshold T2 = 0.6275.
  T2 is the median reader-v2 probability on the organisers' PHerc0009B ink labels.
  - It also reports, per direction, the share of ≥ T2 pixels within 0.3 mm of Hecate's ≥ T pixels (agreement).
- **Triage** (`m2/triage_r2.py`): area ≥ T2 above reader-v2's control background (1.55%) or a candidate ≥ 1 mm, and
  also every fifth surface.
- **Escalation:** a reader-v2 row of separate blobs ≥ 5 mm along the text direction, like the E1d line, with at least
  half of its ≥ T2 pixels within 0.3 mm of Hecate's ≥ T pixels.
- **Looking aids** (no numbers feed a verdict):
  - contact sheets and full-resolution crops beside Hecate's maps (`m2/contact_r2.py`, `m2/crop_r2.py`);
  - a row test on reader-v2's map, with band contrast and z-autocorrelation (`m2/zprofile_r2.py`);
  - a row finder on reader-v2 candidates (`m2/rowfind_r2.py`);
  - a row agreement check (`m2/row_agree.py`).
