"""Kennzahlen der Flüsse und Statistik: Handwerte, Eigenschaften, Randfälle."""

import math

import numpy as np
import pytest

import izs_constants as C
import izs_evaluation as ev
import izs_instance as I


def _F(values, n):
    """Symmetrische Matrix aus den Paarflüssen in der Reihenfolge (0,1), (0,2), …"""
    F = np.zeros((n, n), dtype=np.int16)
    k = 0
    for a in range(n):
        for b in range(a + 1, n):
            F[a, b] = F[b, a] = values[k]
            k += 1
    return F


def test_flow_statistics_of_the_hand_example_by_hand(hand):
    """Paarflüsse 5, 0, 1: Mittel 2, Varianz (9 + 4 + 1)/3, fd = 100 · √(14/3)/2 = 108,0; Dichte 2/3; Gini: aufsteigend 0, 1, 5 → (−2·0 + 0·1 + 2·5)/(3 · 6) = 5/9; die drei stärksten Paare tragen alles."""
    st = ev.flow_stats(hand.F)
    assert st["fd"] == pytest.approx(100 * math.sqrt(14 / 3) / 2) and round(st["fd"], 1) == 108.0
    assert st["dens"] == pytest.approx(2 / 3) and st["gini"] == pytest.approx(5 / 9) and st["top3"] == 1.0 and st["total"] == 6 and st["max"] == 5


def test_equal_flows_have_no_dominance_and_zero_gini():
    F = _F([2, 2, 2], 3)
    assert ev.flow_dominance(F) == 0.0 and ev.gini(F) == pytest.approx(0.0) and ev.density(F) == 1.0 and ev.top_share(F, 2) == pytest.approx(2 / 3)


def test_one_carrying_pair_has_the_maximal_gini_and_dominance_of_a_single_peak():
    F = _F([9, 0, 0, 0, 0, 0], 4)
    assert ev.gini(F) == pytest.approx(5 / 6) and ev.top_share(F, 1) == 1.0 and ev.density(F) == pytest.approx(1 / 6)
    assert ev.flow_dominance(F) == pytest.approx(100 * math.sqrt(5) )   # Paarflüsse 9, 0 ×5: Mittel 1,5, Std 1,5·√5


def test_degenerate_matrices_give_nan_not_an_error():
    z = np.zeros((4, 4), dtype=np.int16)
    st = ev.flow_stats(z)
    assert math.isnan(st["fd"]) and math.isnan(st["gini"]) and math.isnan(st["top3"]) and st["dens"] == 0.0 and st["total"] == 0


def test_flow_statistics_are_invariant_under_relabelling_and_scaling():
    F = I.make_instance("skewed", 8, 4).F
    perm = np.random.default_rng(1).permutation(8)
    G = F[np.ix_(perm, perm)]
    for k in ("fd", "dens", "gini", "top3"):
        assert ev.flow_stats(F)[k] == pytest.approx(ev.flow_stats(G)[k])
    H = (3 * F).astype(np.int16)
    for k in ("fd", "dens", "gini", "top3"):
        assert ev.flow_stats(F)[k] == pytest.approx(ev.flow_stats(H)[k])


def test_ranks_give_ties_the_mean_rank():
    assert ev.ranks([10, 20, 20, 30]).tolist() == [1.0, 2.5, 2.5, 4.0] and ev.ranks([3, 1, 2]).tolist() == [3.0, 1.0, 2.0]


def test_spearman_by_hand():
    """d = (−1, 1, −1, 1, 0), Σd² = 4: ρ = 1 − 6 · 4 / (5 · 24) = 0,8."""
    assert ev.spearman([1, 2, 3, 4, 5], [2, 1, 4, 3, 5]) == pytest.approx(0.8)
    assert ev.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0) and ev.spearman([1, 2, 3, 4], [1, 4, 9, 16]) == pytest.approx(1.0)


def test_spearman_degenerate_cases_are_nan():
    assert math.isnan(ev.spearman([1, 1, 1], [1, 2, 3])) and math.isnan(ev.spearman([1], [2])) and math.isnan(ev.spearman([1, float("nan"), 3], [1, 2, 3]))
    with pytest.raises(ValueError):
        ev.spearman([1, 2], [1, 2, 3])


def test_spearman_is_invariant_under_monotone_transformation_and_swap_of_arguments():
    rng = np.random.default_rng(3)
    a, b = rng.random(30), rng.random(30)
    assert ev.spearman(a, b) == pytest.approx(ev.spearman(b, a)) == pytest.approx(ev.spearman(np.exp(5 * a), b ** 3))


def test_eta_squared_by_hand():
    """Gruppen a, a, b, b mit Werten 1, 2, 3, 4: Ränge 1…4, Gruppenmittel 1,5 und 3,5, zwischen = 4, gesamt = 5."""
    assert ev.eta_squared(["a", "a", "b", "b"], [1, 2, 3, 4]) == pytest.approx(0.8)
    assert ev.eta_squared(["a", "b", "a", "b"], [1, 2, 3, 4]) == pytest.approx(0.2)
    assert math.isnan(ev.eta_squared(["a", "b"], [5, 5]))


def test_eta_squared_is_between_zero_and_one_and_one_for_separated_groups():
    rng = np.random.default_rng(0)
    g = ["x"] * 10 + ["y"] * 10 + ["z"] * 10
    assert 0 <= ev.eta_squared(g, rng.random(30)) <= 1
    assert ev.eta_squared(g, list(range(30))) == pytest.approx(2000 / 2247.5)     # Gruppenmittel der Ränge 5,5 / 15,5 / 25,5: zwischen = 10 · (100 + 0 + 100), gesamt = 30 · 899 / 12


def test_spearman_band_by_hand():
    assert ev.spearman_band(120) == pytest.approx(1.96 * 1.06 / math.sqrt(117)) and ev.spearman_band(120) == pytest.approx(0.192, abs=0.001)
    assert ev.spearman_band(30) == pytest.approx(0.400, abs=0.001) and math.isnan(ev.spearman_band(3))


def test_quartiles_and_summary_by_hand():
    assert ev.quartiles([1, 2, 3, 4, 5]) == (2.0, 3.0, 4.0)
    rows = [{"success": s, "end_gap": g, "mean_gap": 0.5, "fd": 100.0, "dens": 0.5, "n_local": 10} for s, g in ((0.1, 0.05), (0.3, 0.03), (0.5, 0.01), (0.9, 0.0))]
    sm = ev.family_summary(rows)
    assert sm["count"] == 4 and sm["success"] == pytest.approx(0.4) and sm["success_min"] == 0.1 and sm["success_max"] == 0.9 and sm["share_half"] == 0.5 and sm["share_low"] == 0.25
    assert sm["end_gap"] == pytest.approx(0.02) and sm["success_q1"] == pytest.approx(0.25) and sm["success_q3"] == pytest.approx(0.6)


def test_correlations_and_explained_share_use_the_rows():
    rows = [{"family": f, "success": s, "end_gap": 1 - s, "mean_gap": m, "fd": s * 100, "dens": 1 - s, "gini": s, "top3": s} for f, s, m in (("a", 0.1, 1), ("a", 0.2, 1), ("b", 0.8, 2), ("b", 0.9, 2))]
    c = {k: (r, g) for k, _, r, g in ev.correlations(rows)}
    assert c["fd"][0] == pytest.approx(1.0) and c["fd"][1] == pytest.approx(-1.0) and c["dens"][0] == pytest.approx(-1.0)
    e = ev.explained_by_family(rows)
    assert e["success"] == pytest.approx(0.8) and e["mean_gap"] == pytest.approx(1.0)


def test_pooled_keeps_the_family_order_and_skips_missing():
    by = {"star": [{"x": 1}], "netlist": [{"x": 2}, {"x": 3}]}
    assert [r["x"] for r in ev.pooled(by)] == [2, 3, 1]


def test_every_family_sweep_has_one_row_per_seed():
    rows = ev.sweep("cluster", 6, "grid", seeds=(1, 2, 3))
    assert [r["seed"] for r in rows] == [1, 2, 3] and all(r["family"] == "cluster" and r["n"] == 6 and 0 < r["success"] <= 1 for r in rows) and C.SWEEP_SIZES == (6, 8)
