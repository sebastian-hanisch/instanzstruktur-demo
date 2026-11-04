"""Jede Zahl aus README.md, den Hilfetexten der Presets und den App-Texten wird hier über dieselben Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4).

Die Aufzählung ist deterministisch (SplitMix64, ganzzahlige Kosten): alle Zahlen unten sind **exakt** bis auf die Rundung, die README nennt; Zeiten stehen nie in Tests.
Die Vergleiche laufen über je 20 feste Instanzen (Seeds 100000 bis 100019) für n = 6 und n = 8 (zusammen rund zwei Minuten)."""

import math

import pytest

import izs_constants as C
import izs_evaluation as ev
import izs_instance as I
import izs_landscape as L


@pytest.fixture(scope="module")
def sweep6():
    return {f: ev.sweep(f, 6) for f in C.FAMILIES}, ev.sweep("uniform", 6, "random")


@pytest.fixture(scope="module")
def sweep8():
    return {f: ev.sweep(f, 8) for f in C.FAMILIES}, ev.sweep("uniform", 8, "random")


def _p(x, d=1):
    return round(100 * x, d)


def test_the_hand_example_of_the_readme(hand):
    """README: Fluss A–B 5, B–C 1 auf drei Plätzen einer Zeile; Kosten 6, 6, 7, 7, 11, 11; fd = 108,0; Dichte 2/3; Gini 5/9; Erfolg 1,0."""
    hv = ev.hand_view()
    assert [c for c, _ in hv["rows"]] == [6, 6, 7, 7, 11, 11] and round(hv["stats"]["fd"], 1) == 108.0
    ls = L.landscape(hand)
    assert (ls.opt, ls.n_opt, ls.n_local, ls.success) == (6, 2, 2, 1.0) and ev.density(hand.F) == pytest.approx(2 / 3) and ev.gini(hand.F) == pytest.approx(5 / 9)


def test_the_default_instance_is_stueck_1_standard_case():
    """README: die Netzliste mit acht Bauteilen und Seed 35 ist die Instanz aus Stück 1: Optimum 31, 112 lokale Optima (roh), 108 davon kein globales, Erfolg 26,6 %."""
    ls = ev.landscape_of(ev.Settings())
    assert (ls.perms, ls.opt, ls.n_local, ls.n_local_nonglobal) == (40320, 31, 112, 108) and _p(ls.success) == 26.6 and int(ls.cost_values[-1]) == 69


def test_the_families_have_the_dominance_the_readme_names():
    """README: Flussdominanz fd (Median über die 20 Instanzen) n = 8: Netzliste 105,7, gleichverteilt 60,5, dünn 179,3, Cluster 93,1, Stern 149,5, schief 224,8; Dichte 62,5 / 92,9 / 30,4 / 78,6 / 57,1 / 53,6 %."""
    med = {f: ev.family_summary([_flow_row(f, 8, s) for s in C.SWEEP_SEEDS]) for f in C.FAMILIES}
    assert [med[f]["fd"] for f in C.FAMILIES] == pytest.approx([105.7, 60.5, 179.3, 93.1, 149.5, 224.8], abs=0.06)
    assert [100 * med[f]["dens"] for f in C.FAMILIES] == pytest.approx([62.5, 92.9, 30.4, 78.6, 57.1, 53.6], abs=0.06)


def _flow_row(f, n, s):
    """Nur die Kennzahlen der Flüsse (ohne Landschaft), im Format von family_summary."""
    st = ev.flow_stats(I.make_instance(f, n, s).F)
    return {"success": 0.5, "end_gap": 0.0, "mean_gap": 0.0, "fd": st["fd"], "dens": st["dens"], "n_local": 0}


def test_the_comparison_for_six_components(sweep6):
    """README n = 6, je 20 Instanzen (Erfolg Median, Spanne): Netzliste 81,4 % (28,9 bis 100), gleichverteilt 68,9 % (31,1 bis 100), dünn 85,8 % (41,1 bis 100), Cluster 57,5 % (21,1 bis 98,3), Stern 83,1 % (59,4 bis 100), schief 67,8 % (27,8 bis 100); zufällige Plätze 45,6 % (19,4 bis 91,1)."""
    by, rnd = sweep6
    got = {f: ev.family_summary(by[f]) for f in C.FAMILIES}
    assert [_p(got[f]["success"]) for f in C.FAMILIES] == [81.4, 68.9, 85.8, 57.5, 83.1, 67.8]
    assert [(_p(got[f]["success_min"]), _p(got[f]["success_max"])) for f in C.FAMILIES] == [(28.9, 100.0), (31.1, 100.0), (41.1, 100.0), (21.1, 98.3), (59.4, 100.0), (27.8, 100.0)]
    assert [_p(got[f]["end_gap"], 2) for f in C.FAMILIES] == [1.07, 1.47, 0.75, 0.72, 0.53, 1.50]
    assert [_p(got[f]["share_half"], 0) for f in C.FAMILIES] == [90, 70, 95, 65, 100, 70] and all(got[f]["share_low"] == 0 for f in C.FAMILIES)
    r = ev.family_summary(rnd)
    assert (_p(r["success"]), _p(r["success_min"]), _p(r["success_max"]), _p(r["end_gap"], 2)) == (45.6, 19.4, 91.1, 1.44)


def test_the_comparison_for_eight_components(sweep8):
    """README n = 8, je 20 Instanzen: Netzliste 35,9 % (11,6 bis 81,6), gleichverteilt 32,6 % (11,7 bis 62,4), dünn 38,4 % (13,3 bis 100), Cluster 61,0 % (19,8 bis 86,2), Stern 41,9 % (16,8 bis 72,0), schief 24,9 % (11,2 bis 51,8); zufällige Plätze 24,8 % (7,8 bis 49,8)."""
    by, rnd = sweep8
    got = {f: ev.family_summary(by[f]) for f in C.FAMILIES}
    assert [_p(got[f]["success"]) for f in C.FAMILIES] == [35.9, 32.6, 38.4, 61.0, 41.9, 24.9]
    assert [(_p(got[f]["success_min"]), _p(got[f]["success_max"])) for f in C.FAMILIES] == [(11.6, 81.6), (11.7, 62.4), (13.3, 100.0), (19.8, 86.2), (16.8, 72.0), (11.2, 51.8)]
    assert [(_p(got[f]["success_q1"]), _p(got[f]["success_q3"])) for f in C.FAMILIES] == [(28.3, 59.7), (21.0, 47.2), (21.4, 56.6), (42.5, 79.2), (31.2, 52.6), (16.3, 34.9)]
    assert [_p(got[f]["end_gap"], 2) for f in C.FAMILIES] == [2.84, 1.85, 5.41, 2.89, 1.83, 2.87]
    assert [_p(got[f]["share_half"], 0) for f in C.FAMILIES] == [40, 20, 40, 55, 30, 5] and [_p(got[f]["share_low"], 0) for f in C.FAMILIES] == [15, 20, 25, 5, 20, 30]
    assert [_p(got[f]["mean_gap"]) for f in C.FAMILIES] == [41.1, 21.8, 82.7, 41.6, 36.6, 76.5]
    r = ev.family_summary(rnd)
    assert (_p(r["success"]), _p(r["success_min"]), _p(r["success_max"]), _p(r["end_gap"], 2)) == (24.8, 7.8, 49.8, 1.66)


def test_the_family_ranking_changes_with_the_size(sweep6, sweep8):
    """README: Cluster ist bei n = 6 die schwerste Familie (57,5 %), bei n = 8 die leichteste (61,0 %); dünn besetzt umgekehrt von der leichtesten zur drittleichtesten."""
    o6 = sorted(C.FAMILIES, key=lambda f: ev.family_summary(sweep6[0][f])["success"], reverse=True)
    o8 = sorted(C.FAMILIES, key=lambda f: ev.family_summary(sweep8[0][f])["success"], reverse=True)
    assert o6 == ["sparse", "star", "netlist", "uniform", "skewed", "cluster"] and o8 == ["cluster", "star", "sparse", "netlist", "uniform", "skewed"]


def test_the_family_explains_a_fifth_of_the_success(sweep6, sweep8):
    """README: η² der Ränge: Erfolg 0,20 (n = 6) und 0,19 (n = 8); Endlücke 0,10 / 0,27; Kostenlücke einer Zufallsanordnung 0,74 / 0,84."""
    e6, e8 = ev.explained_by_family(ev.pooled(sweep6[0])), ev.explained_by_family(ev.pooled(sweep8[0]))
    assert (round(e6["success"], 2), round(e8["success"], 2)) == (0.20, 0.19) and (round(e6["end_gap"], 2), round(e8["end_gap"], 2)) == (0.10, 0.27) and (round(e6["mean_gap"], 2), round(e8["mean_gap"], 2)) == (0.74, 0.84)


def test_the_rank_correlations_of_the_readme(sweep6, sweep8):
    """README: Rangkorrelation (Spearman) mit dem Erfolg, 120 Instanzen je Größe (Unsicherheit grob ±0,19), n = 6 / n = 8: fd +0,23 / −0,10; Dichte −0,35 / +0,08; Gini +0,25 / −0,08; drei stärkste Paare +0,27 / −0,10; Kostenlücke +0,17 / −0,09. Mit der Endlücke (n = 8): fd +0,22, Dichte −0,35, Kostenlücke +0,51."""
    c6, c8 = ev.correlations(ev.pooled(sweep6[0])), ev.correlations(ev.pooled(sweep8[0]))
    assert [round(r, 2) for _, _, r, _ in c6] == [0.23, -0.35, 0.25, 0.27, 0.17] and [round(r, 2) for _, _, r, _ in c8] == [-0.10, 0.08, -0.08, -0.10, -0.09]
    assert [round(g, 2) for _, _, _, g in c8] == [0.22, -0.35, 0.24, 0.19, 0.51]
    assert round(ev.spearman_band(120), 2) == 0.19 and len(ev.pooled(sweep6[0])) == len(ev.pooled(sweep8[0])) == 120


def test_the_correlations_inside_the_families_vary_in_sign(sweep6, sweep8):
    """README: innerhalb der Familien liegt die Rangkorrelation von fd mit dem Erfolg (je 20 Instanzen) bei n = 8 zwischen −0,59 (gleichverteilt) und +0,67 (dünn besetzt)."""
    w8 = {f: ev.spearman([r["fd"] for r in sweep8[0][f]], [r["success"] for r in sweep8[0][f]]) for f in C.FAMILIES}
    assert round(min(w8.values()), 2) == -0.59 and min(w8, key=w8.get) == "uniform" and round(max(w8.values()), 2) == 0.67 and max(w8, key=w8.get) == "sparse"


def test_the_verdicts_of_the_readme_hold(sweep6, sweep8):
    kind, text = ev.verdict_spread(8, sweep8[0], ev.explained_by_family(ev.pooled(sweep8[0])))
    assert kind == "warning" and "erklärt nur **19 %**" in text and "Am leichtesten ist im Median **Zwei Cluster**, am schwersten **Wenige starke Flüsse**" in text and "über 120 Instanzen (20 je Familie)" in text
    corr = {6: ev.correlations(ev.pooled(sweep6[0])), 8: ev.correlations(ev.pooled(sweep8[0]))}
    kind, text = ev.verdict_predict(corr, {6: 120, 8: 120})
    assert kind == "info" and "n = 6: fd +0,23" in text and "n = 8: fd −0,10" in text and "nur bei n = 6" in text
    kind, text = ev.verdict_places(8, sweep8[0]["uniform"], sweep8[1])
    assert kind == "warning" and "32,6 % auf dem Raster gegen 24,8 % auf zufälligen Plätzen" in text
    kind, text = ev.verdict_places(6, sweep6[0]["uniform"], sweep6[1])
    assert kind == "warning" and "68,9 % auf dem Raster gegen 45,6 % auf zufälligen Plätzen" in text


def test_the_counts_in_the_texts():
    """Texte: n! für n = 6, 8, 9 (720, 40 320, 362 880); 120 Instanzen = 6 Familien · 20 Seeds; 7 Reihen je Vergleich (sechs Familien und zufällige Plätze)."""
    assert [math.factorial(n) for n in C.SIZES] == [720, 40320, 362880] and C.n_text(math.factorial(9)) == "362 880"
    assert len(C.FAMILIES) * len(C.SWEEP_SEEDS) == 120 and len(C.FAMILIES) + 1 == 7 and C.SWEEP_SEEDS[0] == 100000 and C.SWEEP_SEEDS[-1] == 100019
