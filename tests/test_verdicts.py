"""Verdikte (reine Funktionen in izs_evaluation.py) an handgesetzten Werten: Art, Schwellen und jede Zahl im Text (DEMO-PLAYBOOK §1b)."""

import izs_evaluation as ev


def _row(family, success, end_gap=0.02, mean_gap=0.3, fd=100.0, dens=0.5):
    return {"family": family, "success": success, "end_gap": end_gap, "mean_gap": mean_gap, "fd": fd, "dens": dens, "gini": 0.3, "top3": 0.2, "n_local": 10}


def _by(**successes):
    return {f: [_row(f, s) for s in vals] for f, vals in successes.items()}


def test_spread_verdict_names_easiest_hardest_widest_and_the_explained_share():
    by = _by(netlist=[0.4, 0.5, 0.6], cluster=[0.7, 0.8, 0.9], skewed=[0.1, 0.2, 0.5])
    kind, text = ev.verdict_spread(8, by, {"success": 0.2, "end_gap": 0.5, "mean_gap": 0.8})
    assert kind == "warning"
    for part in ("bei n = 8", "über 9 Instanzen (3 je Familie)", "Netzliste 50 % (40 % bis 60 %)", "Zwei Cluster 80 % (70 % bis 90 %)", "Wenige starke Flüsse 20 % (10 % bis 50 %)",
                 "Am leichtesten ist im Median **Zwei Cluster**, am schwersten **Wenige starke Flüsse**", "die größte Spanne hat Wenige starke Flüsse", "erklärt nur **20 %**", "zu 80 %", "zu 50 %"):
        assert part in text, part


def test_spread_verdict_says_so_when_the_family_explains_most():
    kind, text = ev.verdict_spread(6, _by(netlist=[0.1, 0.2], cluster=[0.8, 0.9]), {"success": 0.75, "end_gap": 0.1, "mean_gap": 0.9})
    assert kind == "success" and "erklärt **75 %**" in text and "erklärt nur" not in text


def test_predict_verdict_when_no_correlation_is_outside_the_uncertainty():
    corr = {6: [("fd", "Flussdominanz fd", 0.15, 0.0)], 8: [("fd", "Flussdominanz fd", -0.10, 0.0)]}
    kind, text = ev.verdict_predict(corr, {6: 120, 8: 120})
    assert kind == "warning" and "n = 6: fd +0,15 (120 Instanzen, Unsicherheit grob ±0,19)" in text and "n = 8: fd −0,10" in text
    assert "nicht nachweisbar" in text and "das Vorzeichen wechselt von n = 6 nach n = 8" in text


def test_predict_verdict_when_the_sign_flips_outside_the_uncertainty():
    corr = {6: [("fd", "fd", 0.5, 0.0)], 8: [("fd", "fd", -0.4, 0.0)]}
    kind, text = ev.verdict_predict(corr, {6: 120, 8: 120})
    assert kind == "warning" and "beide Werte liegen außerhalb der Unsicherheit" in text and "taugt nicht als Vorhersage" in text


def test_predict_verdict_with_one_clear_size_and_with_one_size_only():
    corr = {6: [("fd", "fd", 0.5, 0.0)], 8: [("fd", "fd", 0.05, 0.0)]}
    kind, text = ev.verdict_predict(corr, {6: 120, 8: 120})
    assert kind == "info" and "nur bei n = 6" in text and "nicht nachweisbar" not in text
    kind1, text1 = ev.verdict_predict({6: [("fd", "fd", 0.1, 0.0)]}, {6: 120})
    assert kind1 == "warning" and "nicht nachweisbar" in text1 and "wechselt" not in text1


def test_predict_verdict_uses_the_instance_count_for_the_band():
    _, text = ev.verdict_predict({9: [("fd", "fd", -0.35, 0.0)]}, {9: 30})
    assert "Unsicherheit grob ±0,40" in text and "nicht nachweisbar" in text            # 0,35 liegt innerhalb von 0,40


def test_places_verdict_lower_and_not_lower():
    grid = [_row("uniform", s) for s in (0.2, 0.4, 0.6)]
    low = [_row("uniform", s, end_gap=0.04) for s in (0.1, 0.2, 0.3)]
    kind, text = ev.verdict_places(8, grid, low)
    assert kind == "warning" and "Gleichverteilte Flüsse bei n = 8, je 3 Instanzen" in text and "40,0 % auf dem Raster gegen 20,0 % auf zufälligen Plätzen" in text
    assert "schwerer" in text and "nicht schwerer" not in text and "mittlere Endlücke 2,0 % gegen 4,0 %" in text and "Die Instanzen streuen auf dem Raster von 20 % bis 60 %" in text
    kind2, text2 = ev.verdict_places(6, low, grid)
    assert kind2 == "info" and "nicht schwerer" in text2


def test_instance_and_landscape_verdicts_quote_the_computed_values(land6):
    inst, ls = land6
    s = ev.Settings("netlist", 6, 35, "grid")
    v = ev.instance_view(s, ls)
    kind, text = ev.verdict_instance(s, v, ls)
    assert kind == "info" and "Familie **Netzliste**, 6 Bauteile, Raster 2×3, Seed 35" in text and f"kostet **{ls.opt}**" in text and "720 Anordnungen" in text
    assert f"fd = {ev.de(v['stats']['fd'], 0)}" in text
    kind2, text2 = ev.verdict_landscape(s, ev.landscape_view(s, ls))
    assert kind2 == ("success" if ls.success >= 0.5 else "warning") and f"**{ev.pct(ls.success, 1)}**" in text2 and f"**{ls.n_local}**" in text2 and "kein Befund über die Familie" in text2
    kind3, text3 = ev.verdict_instance(ev.Settings("uniform", 6, 1, "random"), v, ls)
    assert "zufällige Plätze" in text3 and "Raster" not in text3


def test_core_verdict_asks_for_the_comparison(land6):
    _, ls = land6
    s = ev.Settings("netlist", 6, 35, "grid")
    kind, text = ev.verdict_core(s, ev.instance_view(s, ls), ls)
    assert kind == "info" and f"{ev.pct(ls.success)} der Starts" in text and "Experiment 3" in text and "Experiment 4" in text


def test_formatting_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.pct(0.266, 1) == "26,6 %" and ev.sgn(0.44) == "+0,44" and ev.sgn(-0.13) == "−0,13" and ev.sgn(0.0) == "+0,00" and ev.fam("star") == "Stern"
