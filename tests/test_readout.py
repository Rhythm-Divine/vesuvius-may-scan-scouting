"""Unit tests for sweep.readout on small synthetic arrays (internal checks of our own code only)."""
import numpy as np
import pytest

from sweep.readout import ReadoutRules, auc, calibrate, coverage_cm2, ensemble, extract_candidates

PX = 9.6  # µm per flattened pixel


def _rules(**kw):
    return ReadoutRules(threshold=kw.pop("threshold", 3.0), px_um=PX, **kw)


def test_ensemble_is_scale_invariant_per_model():
    rng = np.random.default_rng(0)
    base = rng.normal(size=(64, 64)).astype(np.float32)
    valid = np.ones_like(base, dtype=bool)
    a = ensemble({"m1": [base], "m2": [base * 10 + 5]}, valid)
    b = ensemble({"m1": [base]}, valid)
    np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-5)


def test_ensemble_masks_invalid_pixels():
    valid = np.ones((8, 8), dtype=bool)
    valid[:, :2] = False
    out = ensemble({"m": [np.arange(64, dtype=np.float32).reshape(8, 8)]}, valid)
    assert np.isnan(out[:, :2]).all() and np.isfinite(out[:, 2:]).all()


def test_auc_perfect_reversed_and_ties():
    s = np.array([0.1, 0.2, 0.8, 0.9])
    y = np.array([0, 0, 1, 1])
    assert auc(s, y) == 1.0
    assert auc(-s, y) == 0.0
    assert auc(np.zeros(4), y) == 0.5


def test_calibrate_uses_median_on_labelled_ink():
    ens = np.zeros((10, 10))
    labels = np.zeros((10, 10), dtype=bool)
    labels[2:4, 2:4] = True
    ens[2:4, 2:4] = [[1, 2], [3, 4]]
    cal = calibrate(ens, labels, np.ones((10, 10), dtype=bool))
    assert cal["threshold"] == 2.5 and cal["n_ink_px"] == 4 and cal["auc"] > 0.9


def test_size_floor_and_candidate():
    ens = np.zeros((300, 300))
    valid = np.ones_like(ens, dtype=bool)
    ens[20:30, 20:30] = 5.0      # 10 px = 0.096 mm: below the 0.5 mm floor
    ens[100:180, 100:160] = 5.0  # 80 px = 0.768 mm: kept
    res = extract_candidates(ens, valid, _rules())
    assert res["counts"]["below_floor"] == 1
    assert len(res["candidates"]) == 1
    c = res["candidates"][0]
    assert c["bbox_yx"] == [100, 100, 180, 160] and c["extent_mm"] == pytest.approx(0.768)


def test_boundary_and_band_exclusions():
    ens = np.zeros((400, 400))
    valid = np.ones_like(ens, dtype=bool)
    valid[:, 350:] = False
    ens[50:130, 300:350] = 5.0   # touches the invalid edge: boundary
    ens[150:380, 50:56] = 5.0    # 230 x 6 px: band
    res = extract_candidates(ens, valid, _rules())
    assert res["counts"]["boundary"] == 1 and res["counts"]["band"] == 1 and res["candidates"] == []


def test_coverage_cm2():
    valid = np.ones((1000, 1000), dtype=bool)  # 1000 px * 9.6 µm = 0.96 cm per side
    assert coverage_cm2(valid, PX) == pytest.approx(0.9216)
