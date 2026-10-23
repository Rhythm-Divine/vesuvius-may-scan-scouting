"""Ensemble ink-probability maps and extract First Letters candidates under pre-registered rules.

Every array is 2D on the flattened-surface pixel grid of one segment. `valid` marks pixels where the
render has data. The rules are fixed (prereg/readout.md) before any target output is looked at.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import numpy as np
from scipy import ndimage


@dataclass(frozen=True)
class ReadoutRules:
    threshold: float              # on the ensemble map; fixed from the positive control
    px_um: float                  # flattened-grid pixel size, µm
    min_extent_mm: float = 0.5    # size floor on the longest bbox side
    border_px: int = 8            # drop components this close to the edge of the valid render
    max_band_aspect: float = 8.0  # drop thin bands, typically rendering seams
    min_valid_frac: float = 0.9   # bbox must be mostly inside the valid render


def _robust_scale(values: np.ndarray) -> tuple[float, float]:
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med))) * 1.4826
    return med, max(mad, 1e-6)


def ensemble(maps_by_model: dict[str, list[np.ndarray]], valid: np.ndarray) -> np.ndarray:
    """One robust z-score per model over all its depth/direction maps, mean within the model, then mean
    across models. Invalid pixels come back as NaN."""
    per_model = []
    for maps in maps_by_model.values():
        stack = np.stack(maps).astype(np.float32)
        med, mad = _robust_scale(stack[:, valid])
        per_model.append(((stack - med) / mad).mean(axis=0))
    out = np.mean(per_model, axis=0)
    out[~valid] = np.nan
    return out


def auc(scores: np.ndarray, labels: np.ndarray, mask: np.ndarray | None = None) -> float:
    """Pixel ROC AUC via the Mann-Whitney statistic (ties get average ranks)."""
    m = np.isfinite(scores) if mask is None else (mask & np.isfinite(scores))
    s, y = scores[m].ravel(), labels[m].ravel().astype(bool)
    n_pos, n_neg = int(y.sum()), int((~y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = _average_ranks(s)
    return float((ranks[y].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def _average_ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    sx = x[order]
    ranks = np.empty(len(x), dtype=np.float64)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def calibrate(ens: np.ndarray, labels: np.ndarray, mask: np.ndarray) -> dict:
    """Positive control: threshold = median ensemble value on labelled ink inside the supervision mask."""
    ink = mask & labels.astype(bool) & np.isfinite(ens)
    return {"threshold": float(np.median(ens[ink])), "auc": auc(ens, labels, mask), "n_ink_px": int(ink.sum())}


def coverage_cm2(valid: np.ndarray, px_um: float) -> float:
    return float(valid.sum()) * (px_um * 1e-4) ** 2


def extract_candidates(ens: np.ndarray, valid: np.ndarray, rules: ReadoutRules) -> dict:
    """Connected components above threshold, filtered by the pre-registered rules."""
    above = np.nan_to_num(ens, nan=-np.inf) >= rules.threshold
    above &= valid
    comp, n = ndimage.label(above, structure=np.ones((3, 3), dtype=bool))
    near_edge = ndimage.binary_dilation(~valid, iterations=rules.border_px) if rules.border_px > 0 else ~valid
    counts = {"components": int(n), "below_floor": 0, "boundary": 0, "band": 0, "coverage": 0}
    candidates = []
    for idx, sl in enumerate(ndimage.find_objects(comp), start=1):
        if sl is None:
            continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        extent_mm = max(h, w) * rules.px_um / 1000
        if extent_mm < rules.min_extent_mm:
            counts["below_floor"] += 1
            continue
        blob = comp[sl] == idx
        if (blob & near_edge[sl]).any():
            counts["boundary"] += 1
            continue
        if max(h, w) / max(1, min(h, w)) > rules.max_band_aspect:
            counts["band"] += 1
            continue
        if valid[sl].mean() < rules.min_valid_frac:
            counts["coverage"] += 1
            continue
        ys, xs = np.nonzero(blob)
        vals = ens[sl][blob]
        candidates.append({
            "bbox_yx": [int(sl[0].start), int(sl[1].start), int(sl[0].stop), int(sl[1].stop)],
            "extent_mm": round(extent_mm, 3),
            "area_mm2": round(float(blob.sum()) * (rules.px_um / 1000) ** 2, 4),
            "centroid_yx": [round(float(ys.mean()) + sl[0].start, 1), round(float(xs.mean()) + sl[1].start, 1)],
            "peak": round(float(vals.max()), 3),
            "mean": round(float(vals.mean()), 3),
        })
    candidates.sort(key=lambda c: c["area_mm2"], reverse=True)
    return {"rules": asdict(rules), "counts": counts, "coverage_cm2": round(coverage_cm2(valid, rules.px_um), 3),
            "candidates": candidates}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", action="append", required=True, metavar="MODEL=PATH.npy",
                    help="one per model/depth/direction map; repeat the model name to group them")
    ap.add_argument("--valid", required=True, help="bool .npy mask of valid render pixels")
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--px-um", type=float, required=True)
    ap.add_argument("--out", required=True, help="output JSON")
    args = ap.parse_args()
    valid = np.load(args.valid).astype(bool)
    maps: dict[str, list[np.ndarray]] = {}
    for spec in args.map:
        name, path = spec.split("=", 1)
        maps.setdefault(name, []).append(np.load(path))
    result = extract_candidates(ensemble(maps, valid), valid, ReadoutRules(args.threshold, args.px_um))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result["counts"]), f"candidates={len(result['candidates'])}", f"coverage_cm2={result['coverage_cm2']}")


if __name__ == "__main__":
    main()
