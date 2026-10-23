# Pre-registered readout: <VOLUME> <REGION> (template)

Copy this file to `prereg/<volume>-<region>.md` and fill it in. Commit it **before** any target inference output
exists. Record the commit hash in the run log. After that, the rules below do not change for this run. Any deviation
gets appended under "Deviations", dated, with the reason, before the target output is opened.

## Target
- Volume: `<sample>/<volume id>` (e.g. PHerc0490B / 20250521151215, 8.64 µm, 116 keV). Region: windings or patches,
  z-range, and cm² of flattened area.
- Geometry: spiral fit or GrowPatch, with villa commit, params file and seed.
- Render: `vc_render_tifxyz` commit; `--num-slices`, `--slice-step`, resampling to 9.6 µm (yes/no), tile re-centring
  (yes/no).
- Models: name, file sha256, depth offsets, directions.

## Positive control (must pass first)
- Segment: e.g. PHerc0009B `20250919125754-auto_grown_20250919055754487_inp_hr` (8.64 µm surface volume), with labels
  and their source.
- Pass criterion: ensemble AUC ≥ <value> inside the supervision mask. Reference: Hecate 0.914 forward and 0.955 with
  the −1..+1 ensemble, as reported by J. Lu.
- Threshold T: the median ensemble value on labelled ink, taken from the control run. T = <value>, fixed here.

## Candidate rules (`sweep/readout.py`, `ReadoutRules`)
- Components ≥ T (8-connected). Size floor: longest bbox side ≥ 0.5 mm.
- Exclude components within 8 px of the valid-render edge (boundary), aspect > 8 (bands or seams), or with < 90% valid
  pixels in the bbox.
- Escalate to the human reviewer only if the candidate reappears, at the same place and ≥ T, under a **second independent model or
  seed**, and its rows run parallel to the horizontal fibres.

## Verdict sentences (fixed now; exactly one is used)
1. "I didn't see any ink in the region."
2. "I see possible ink traces but no legible letters."
3. "I see legible letters." Only this triggers the First Letters checklist and keeps everything private.

## Deviations
- (none)
