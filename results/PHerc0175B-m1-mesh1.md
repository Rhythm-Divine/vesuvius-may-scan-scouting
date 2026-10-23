# Result: PHerc0175B, M1 mesh 1 (`auto_grown_20261022022706145`), read under `prereg/PHerc0175B-m1.md` (925b417)

**Verdict (pre-registered sentence 1): "I didn't see any ink in the region."**

## What ran
- All ten pre-registered Hecate outputs exist: windows −2..+2, forward and reverse.
- Another project reserved the shared GPU at 03:02 UTC, so the last four ran after it released at about 04:22. The command was identical.
- Readout area: 4.86 cm² of the mesh interior that is also render-valid.

## Mechanical readout (`readout.json`)

| Direction | Components | Below 0.5 mm floor | Boundary | Candidates | Mean p | p99 | Area ≥ T |
|---|---|---|---|---|---|---|---|
| Forward | 1,397 | 1,292 | 10 | 95 | 0.211 | 0.755 | 12.1% |
| Reverse | 864 | 786 | 7 | 71 | 0.144 | 0.902 | 9.4% |

- Candidate extents have a median of 0.9 mm (forward) and 0.7 mm (reverse). The largest are 5.8 mm and 4.3 mm, and
  they are merged blobs.

## Why the verdict is "no ink"
- **The pattern:** at full resolution (9.6 µm) both ensembles are a cloudy texture of roundish blobs 0.5–1.5 mm
  across.
  - There are no strokes, no letter shapes and no lines of text.
  - In the control the same pipeline shows crisp 0.5 mm strokes on a dark background.
- **The level:** the response is raised over the whole area. The control's non-ink background inside its supervision
  mask has mean p 0.037 and only 1.2% of its area ≥ T. Here it is 0.21 and 12%.
  - Under a uniform raise like this, the threshold-and-size rules alone are not selective. They count blobs, not ink.
- **Escalation:** none. No candidate forms rows parallel to the horizontal fibres, and none looks like a letter. A
  second-model check was therefore not triggered.

## Not established
- Whether this outer winding carries no text, or whether Hecate's response is raised here for another reason. Possible
  reasons: texture or condition of the outer layers, or a surface sitting more than 2 layers off the ink.
- Raw maps, ensembles and overlays are in `data/m1/PHerc0175B/hecate/auto_grown_20261022022706145/` (private).
