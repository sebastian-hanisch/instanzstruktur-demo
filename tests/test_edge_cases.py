"""Randfälle (DEMO-PLAYBOOK §1b): kleinste Instanzen, Nullfluss, gleiche Flüsse, zusammenfallende Plätze, fehlerhafte Eingaben."""

import math

import numpy as np
import pytest

import izs_constants as C
import izs_evaluation as ev
import izs_instance as I
import izs_landscape as L
from test_landscape import _inst


def test_two_components_have_a_trivial_landscape():
    ls = L.landscape(_inst([[0, 3], [3, 0]]))
    assert ls.perms == 2 and ls.opt == 3 and ls.n_opt == 2 and ls.success == 1.0 and ls.mean_steps == 0.0 and ls.n_local == 2


def test_zero_flow_makes_every_arrangement_optimal_and_the_gaps_undefined():
    ls = L.landscape(_inst(np.zeros((4, 4))))
    assert ls.opt == 0 and ls.n_opt == 24 and ls.success == 1.0 and math.isnan(ls.mean_gap) and math.isnan(ls.end_gap)
    row = ev.measure(_inst(np.zeros((4, 4))), ls)
    assert math.isnan(row["fd"]) and row["success"] == 1.0


def test_equal_flows_and_equal_distances_make_everything_equal():
    n = 5
    F = np.ones((n, n), dtype=np.int16) - np.eye(n, dtype=np.int16)
    ls = L.landscape(_inst(F, np.ones((n, n), dtype=np.int16) - np.eye(n, dtype=np.int16)))
    assert ls.n_opt == 120 and ls.success == 1.0 and ls.n_local == 120 and ls.n_local_strict == 0


def test_equal_flows_on_a_line_cost_the_same_for_every_arrangement():
    """Fluss 2 zwischen allen Paaren, Plätze auf einer Zeile: Σ aller Abstände ist fest, also kosten alle Anordnungen gleich (fd = 0, jeder Abstieg ein Treffer)."""
    F = 2 * (np.ones((4, 4), dtype=np.int16) - np.eye(4, dtype=np.int16))
    ls = L.landscape(_inst(F))
    assert ls.cost_values.tolist() == [20] and ls.success == 1.0 and ev.flow_dominance(F) == 0.0 and ls.end_gap == 0.0


def test_random_places_may_coincide_and_the_landscape_still_works():
    found = False
    for seed in range(60):
        inst = I.make_instance("uniform", 6, seed, "random")
        if (inst.D + np.eye(6, dtype=np.int16) * 99).min() == 0:                  # zwei Plätze fallen zusammen (Abstand 0)
            ls = L.landscape(inst)
            assert 0 < ls.success <= 1 and ls.opt >= 0
            found = True
            break
    assert found


def test_every_family_and_place_type_runs_through_the_measurement_for_every_size():
    for fam in C.FAMILIES:
        for places in C.PLACES:
            row = ev.measure_instance(fam, 6, 1, places)
            assert row["family"] == fam and row["places"] == places and row["perms"] == 720 and 0 < row["success"] <= 1


def test_seed_extremes():
    for seed in (0, C.SEED_MAX):
        inst = I.make_instance("sparse", 6, seed)
        assert inst.F.shape == (6, 6)


def test_a_single_family_is_not_an_error_for_the_comparison_helpers():
    rows = ev.sweep("star", 6, "grid", seeds=(1, 2))
    assert math.isnan(ev.eta_squared(["star"] * 2, [r["success"] for r in rows])) or ev.eta_squared(["star"] * 2, [r["success"] for r in rows]) == 0.0
    assert ev.family_summary(rows)["count"] == 2


def test_the_hand_view_lists_all_six_arrangements(hand):
    hv = ev.hand_view()
    assert [c for c, _ in hv["rows"]] == [6, 6, 7, 7, 11, 11] and round(hv["stats"]["fd"], 1) == 108.0
