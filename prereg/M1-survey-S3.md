# Pre-registered readout: M1 survey S3 (more windings, reader-v2 first, a deeper read)

This was committed before any S3 surface was grown and before any S3 output on a survey surface existed. It follows
`prereg/M1-survey-S1.md` and `prereg/M1-survey-S2.md` in every rule not stated here. After this commit the rules do not
change for S3; deviations are appended below, dated, before the output they concern is opened. Rhythm approved S3 on
2026-10-24: "Yes: restart aiq-3 and run S3 as proposed. Pre-register it first; reader-v2 leads and Hecate confirms
flagged surfaces. Stop the machine afterwards unless something escalates."

## Why
- S1 and S2 read 108 surfaces (435.9 cm² clean) on nine May volumes with two independent models, and M1 read 158.5 cm²
  before that: about 594 cm² in all, with no ink seen. That is a small share of these scrolls.
- **More papyrus.** S3 grows the neighbouring windings of every zone that grew cleanly in S1. In S1's stage 2 such
  windings passed QC 28 times out of 28, with 4.45 cm² clean on average. Each winding is a different turn of the
  scroll, so a different stretch of text.
- **reader-v2 first.** In S2 it was about ten times faster than Hecate and far quieter on blank papyrus (median 0.8%
  ≥ T2 against its 1.55% control background), so it can read every surface. Hecate checks only the maps behind a
  "possible traces" or "letters" verdict.
- **A deeper read.** S2's windows reach 10 layers (86 µm) from the mesh. When a trace follows the middle or the far face
  of the sheet, the inked recto can lie 10 to 14 layers away. S3 adds two 17-layer windows shifted 6 layers each way,
  on every new surface and on the 108 S1 surfaces.

## Machine, model and code
- **Machine:** the same g6.12xlarge (4× L4, 48 vCPU), restarted 2026-10-24 14:02 UTC. Its NVMe came back empty.
- **reader-v2,** rebuilt on the NVMe exactly as for S2, with the weights checked against their sha256:
  - `reader-v2-step040000.pth`, sha256 `654ec5acec2b6c4788d9cb326e2f0b8c2c730584949a934ef775db7f6ab5d3a6`;
  - `train_config.json`, sha256 `a69e9cf23263d4b17a85f05501333408f923f67f65b6f4ebc6c4539ceb1e81ec`;
  - villa `ink-detection` at `47a9c37`, `uv sync --frozen` on CPython 3.12: torch 2.10.0+cu128, zarr 2.18.7,
    numpy 2.2.0.
- **Hecate and VC3D:** the same files on the instance's own disk, as in S1.
- **New code in `m3/`:**
  - `s3_queue.py` builds the queue;
  - `grow_s3.sh` grows with `m1/grow_more.sh`'s settings, plus per-worker folders and caches, and keeps the native
    render for reader-v2;
  - `batch/s3_trace.sh` and `batch/s3_reader.sh` are the workers;
  - `r2_infer_s3.sh`, `r3_combine.py`, `readout_r3.py` and `triage_r3.py` are S2's reading steps with the extra
    windows;
  - `distinct.py` is the duplicate check, `hecate_confirm.sh` the Hecate check and `sheet_r3.py` the review sheets;
  - `control_s3.sh` and `bg_t2.py` run the controls.

## Controls (run 2026-10-24 on this restart, before this commit)
- **E1b:** the organisers' native PHerc0009B surface volume, scored against their same-mesh labels with S2's window
  and registration (`m3/control_s3.sh`, `e1b/score.py`, `m3/bg_t2.py`).
  - **The near map reproduces S2's control:** forward AUC 0.9266 in the supervision mask (S2: 0.927) and 0.9337 in the
    validation mask (0.934). The median probability on labelled ink is 0.6275, so **T2 stays 0.6275**. The control
    background is 1.55% of non-ink pixels ≥ T2, as in S2. Reverse: 0.567.
  - **p6, forward:** AUC 0.886 (validation 0.914). 32.6% of labelled ink is ≥ T2; the background is **1.44%**.
  - **m6, forward:** AUC 0.782 (validation 0.797). 25.7% of labelled ink is ≥ T2; the background is **4.36%**.
  - Reverse sees no ink on E1b in any window (AUC 0.54–0.57).
  - So the shifted windows still see ink that lies on the mesh, more weakly, and m6 is the noisier of the two. Each
    window family's forward background is its triage threshold, as in S2.
- **E1d:** our own PHerc0343 mesh, rendered natively again and read the S3 way (`m3/control_s3.sh`).
  - **The near map reproduces S2:** forward 5.07% ≥ T2, 18 candidates, and 93% of the ≥ T2 pixels within 0.3 mm of
    Hecate's ≥ T pixels (S2: 5.07%, 18, 93%). Reverse: 0.32%, 4 candidates, 68%.
  - **p6, forward:** 3.76% ≥ T2 and 20 candidates. Hecate at k = +3..+7 agrees on 79%.
  - **m6, forward:** 2.31% ≥ T2 and 17 candidates. Hecate at k = −7..−3 agrees on 82%.
  - **By eye** (the image stays private): the October text line shows as separate stroke shapes in the near map. It
    shows in p6 a little weaker, and in m6 more faintly, among more background blobs. Reverse shows no line in any
    window.
  - So on known text, the Hecate check at the deeper depths agrees with reader-v2 well above the 50% the escalation
    rule asks for.
- **The S3 chain on the control scroll** (PHerc0343, not a survey volume):
  - A surface regrown from the E1d seed went through growth, QC (3.50 cm² clean, 0.984 on papyrus), the duplicate
    check, and reader-v2's ten windows (255 s on three cores). Its near forward read gave 5.46% ≥ T2, against the
    original's 5.07%.
  - The duplicate check called it a copy of the E1d mesh: median 2.2 voxels, with 62% of its points within 4 voxels.
    The rest had wandered by up to about one winding. So the same seed does not give the same surface twice, and
    partial overlaps between surfaces are expected.

## Surfaces (`prereg/M1-survey-S3-queue.tsv`, sha256 `96aeaf966ce89cb97d1eff822798aea58b499aef6d31a611c636c551b9ef5a02`)
- **Windings** (`m3/s3_queue.py`, run before this commit):
  - For each of the 69 S1 stage-1 zones that passed QC, `m1/seeds_radial.py --inward 4 --outward 4` runs on the radial
    line through the zone's S1 seed. That gives up to eight seeds, one per neighbouring winding.
  - They are named `<zone>_i<k>` for the k-th thin crossing toward the centre and `<zone>_o<k>` for the k-th away
    from it.
  - A seed already grown in S1 is listed but not queued: 30 of them (stage 2 grew i1, i2, o1 and o2 around each
    volume's best zone).
  - That leaves 512 seeds in 69 jobs. A job is one zone's seeds, grown in one call so that they share the
    normal-grid cache.
- **New zones:**
  - S1's zone choice without its per-volume cap: the same gate, the same exclusion of zones tried before S1, and the
    same near-duplicate rule, now also checked against every S1 zone.
  - That gives 70 zones, 65 of them with a seed (`m1/seed.py`, as in S1), each one job with one test surface.
- **Order:**
  - All winding jobs come first, round-robin over the volumes; within a volume, zones go by S1 clean area, largest
    first.
  - Then the new-zone jobs, round-robin over the volumes in S1's ranking order.
- **Growth and QC as in S1:**
  - step 20, 80 generations, the self-crossing census, a 48-layer native render and the 9.604 µm resample;
  - the QC gate: ≥ 2 cm² clean (8-cell contact exclusion) and ≥ 0.8 on papyrus. The QC row is logged before any read.
- **Duplicate check** (`m3/distinct.py`), under the QC-log lock:
  - A kept surface is compared with every surface of its volume already read: S1 and M1 surfaces with a Hecate readout,
    and S3 surfaces already accepted.
  - If the median distance from its interior grid points to the other surface (densified 4×) is under 4 voxels, it is
    a duplicate. It is logged and not read.
  - Each distinct surface also records the share of its points within 4 voxels of the nearest read surface. S3's area
    is reported both as clean area and as clean area times one minus that share.
- **Failures:** as in S1, a job that fails for an infrastructure reason (network, DNS or storage) is retried once.
  Other failures are final and stay in the logs.
- **Stop:** no growth job starts at or after 2026-10-24 22:30 UTC. Every surface grown by then is read.
- **The 108 S1 surfaces:** each is rendered natively again (the NVMe was wiped), resampled, and its self-crossing
  census redone. Its readout area is then checked against S1's. It gets the deeper read only, since S2 has already
  read it near the mesh.

## Reading (`m3/batch/s3_reader.sh`, one worker per GPU)
- **reader-v2** exactly as in S2 (`--overlap 0.5 --blend-mode hann`), forward and reverse:
  - **a new surface:** windows c, p2 and m2, whose mean is the near map (S2's read), and p6 and m6, each a map of its
    own;
  - **an S1 surface:** p6 and m6 only.
  - p6 and m6 are the 17-layer windows shifted +6 and −6 layers: `--layer-start 12` and `--layer-end D−12`.
- **Alignment:** as in S2. The maps are resampled to the 9.604 µm grid and cropped to the readout window, which is
  S1's window for an S1 surface and the readout bbox + 128 px for a new one.
- **Readout** (`m3/readout_r3.py`): S2's rules for each map. They are S1's valid area (centre layer > 0, mesh
  interior, 8-cell contact exclusion), `ReadoutRules` and **T2 = 0.6275**.
- **Triage** (`m3/triage_r3.py`):
  - A map is flagged when its area ≥ T2 exceeds its window family's E1b background (near 1.55%, as in S2; p6 1.44%;
    m6 4.36%), or when a candidate reaches 1 mm.
  - A surface is reviewed by eye when any of its maps is flagged, and every fifth surface in processing order is
    reviewed as well.
  - Unreviewed surfaces are reported as "below triage, not reviewed by eye".

## Verdicts, the Hecate check and escalation
- **Verdicts:**
  - Each reviewed surface gets one of S1's three fixed sentences:
    1. "I didn't see any ink in the region."
    2. "I see possible ink traces but no legible letters."
    3. "I see legible letters."
  - The verdict comes from reader-v2's maps on the review sheet (`m3/sheet_r3.py`): near, p6 and m6, forward and
    reverse. For an S1 surface, S2's near map takes the near column.
- **The Hecate check** ("Hecate confirms flagged surfaces"):
  - It runs on every map behind a verdict 2 or 3.
  - Hecate (as in S1) reads that map's direction at the map's depth: five 16-layer windows at k = −2..+2 for near,
    +3..+7 for p6 and −7..−3 for m6, averaged (`m3/hecate_confirm.sh`).
  - Agreement is computed as in S2: the share of the map's ≥ T2 pixels within 0.3 mm of Hecate's ≥ T pixels.
- **Escalation** (S2's rule, for any of the maps). A surface goes to Rhythm, privately, when, by eye on reader-v2's
  map:
  - there is a conspicuous row of separate blobs ≥ T2, at least 5 mm long along the text direction, like the E1d line;
  - and at least half of that row's ≥ T2 pixels lie within 0.3 mm of Hecate's ≥ T pixels at the same depth.
  The machine then stays up. Verdict 3 triggers the First Letters checklist, and everything stays private.
- **Neighbouring windings now exist for most surfaces.** A row that recurs at the same 3D place on a neighbouring
  winding is reported as structure, as in S1's row checks, but this does not change the escalation rule.

## Stop rule
- S3 ends when every surface grown by 22:30 UTC has been read, the flagged ones reviewed, and every verdict-2 or
  verdict-3 map given its Hecate check.
- If nothing escalates, the survey is reported and the machine stopped, as Rhythm asked.

## Deviations
- **2026-10-24 20:02 UTC: a faster duplicate check, with the same answers.**
  - Why: `m3/distinct.py` densified every nearby read surface of the volume, under the QC-log lock. As accepted S3
    surfaces accumulated, one call took up to about 8 minutes. From about 17:00 UTC the tracers spent most of their
    time waiting for the lock.
  - The change: each candidate's median distance to its grid vertices is taken first. A candidate is densified only
    when that median minus h (the farthest a densified point lies from a corner of its own cell) is not above the
    best densified median found so far. A densified distance is never below the vertex distance minus h, so a
    skipped surface cannot be the nearest. The decision, the nearest surface and its share are unchanged.
  - Checked on three S3 surfaces before the switch: identical output, in 6–9 s instead of 6–62 s. The one call
    already running at the switch finished with the old code.
- **2026-10-24 20:10 UTC: a wording error above.** The duplicate-check rule says "densified 4×"; it should say 8×.
  The committed `m3/distinct.py` uses 8× (`DENSE = 8`), as does the notebook entry committed with this file. The
  change from 4× was made before the commit, after the control test, whose 2.2-voxel median is the 8× figure. Every
  S3 surface was checked at 8×.
