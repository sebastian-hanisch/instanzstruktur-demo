"""Orakel (ORACLE-PLAYBOOK §5): scipy rechnet die Rangkorrelation und die Kruskal-Wallis-Statistik unabhängig nach, und `quadratic_assignment` (2opt) darf das aufgezählte Optimum nie unterschreiten.
Ohne scipy (nur requirements-dev.txt) werden die Tests übersprungen."""

import numpy as np
import pytest

import izs_constants as C
import izs_evaluation as ev
import izs_instance as I
import izs_landscape as L

stats = pytest.importorskip("scipy.stats")
scipy_opt = pytest.importorskip("scipy.optimize")


def test_spearman_equals_scipy_on_random_and_tied_data():
    rng = np.random.default_rng(0)
    for _ in range(20):
        a, b = rng.random(40), rng.random(40)
        assert ev.spearman(a, b) == pytest.approx(float(stats.spearmanr(a, b).statistic), abs=1e-12)
    a, b = rng.integers(0, 5, 60), rng.integers(0, 4, 60)                           # viele Gleichstände
    assert ev.spearman(a, b) == pytest.approx(float(stats.spearmanr(a, b).statistic), abs=1e-12)


def test_spearman_equals_scipy_on_real_comparison_data():
    rows = ev.pooled({f: ev.sweep(f, 6, "grid", range(100000, 100008)) for f in C.FAMILIES})
    for key in ("fd", "dens", "gini", "top3", "mean_gap"):
        assert ev.spearman([r[key] for r in rows], [r["success"] for r in rows]) == pytest.approx(float(stats.spearmanr([r[key] for r in rows], [r["success"] for r in rows]).statistic), abs=1e-12)


def test_eta_squared_is_the_kruskal_wallis_statistic_divided_by_n_minus_one():
    """H = (N − 1) · SS_zwischen / SS_gesamt der Ränge (mit Korrektur für Gleichstände, wie scipy sie rechnet)."""
    rows = ev.pooled({f: ev.sweep(f, 6, "grid", range(100000, 100010)) for f in C.FAMILIES})
    groups = [[r["success"] for r in rows if r["family"] == f] for f in C.FAMILIES]
    h = float(stats.kruskal(*groups).statistic)
    assert ev.eta_squared([r["family"] for r in rows], [r["success"] for r in rows]) == pytest.approx(h / (len(rows) - 1), abs=1e-12)


def _scipy_cost(F, D, seed):
    """Koopmans–Beckmann-Kosten, die scipy minimiert (Fluss A, Abstand B; ganze Summe, also das Doppelte der Paarkosten)."""
    res = scipy_opt.quadratic_assignment(F.astype(float), D.astype(float), method="2opt", options={"rng": seed, "partial_guess": None, "maximize": False})
    return res.fun / 2.0


@pytest.mark.parametrize("family", ("cluster", "skewed", "sparse"))
@pytest.mark.parametrize("places", C.PLACES)
def test_the_two_opt_solver_never_beats_the_enumeration(family, places):
    for seed in range(3):
        inst = I.make_instance(family, 6, seed, places)
        opt = L.landscape(inst).opt
        found = [_scipy_cost(inst.F, inst.D, s) for s in range(30)]
        assert min(found) >= opt - 1e-9 and min(found) == pytest.approx(opt)
