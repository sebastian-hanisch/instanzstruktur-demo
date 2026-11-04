"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Beschriftungen und Daten stimmen mit den Werten überein; PDF-Export."""

import izs_constants as C
import izs_evaluation as ev
import izs_instance as I
import izs_visualization as V
from izs_pdf_export import build_pdf


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_heatmap_shows_the_upper_half_of_the_flow_matrix(land6):
    inst, _ = land6
    fig = V.build_flow_heatmap(inst)
    z = fig.data[0].z
    assert len(z) == 6 and z[0][0] is None and z[0][1] == inst.F[0, 1] and z[5][5] is None and z[3][1] is None and list(fig.data[0].x) == list(inst.names) and _locked(fig)


def test_board_chart_has_a_marker_and_a_label_for_every_component(land6):
    inst, ls = land6
    fig = V.build_board(inst, [int(x) for x in ls.optima[0]], "Titel")
    comp = fig.data[-1]
    assert list(comp.text) == list(inst.names) and len(comp.x) == 6 and len(fig.data[0].x) == 6 and fig.layout.title.text == "Titel" and _locked(fig)
    assert tuple(fig.layout.xaxis.range) == (-0.7, inst.xy[:, 0].max() + 0.7)                    # feste Bereiche (ein Anker an die andere Achse hatte in Stück 1 die Fläche zerstört)


def test_board_chart_for_every_family_place_type_and_the_hand_example(hand):
    for fam in C.FAMILIES:
        for places in C.PLACES:
            inst = I.make_instance(fam, 8, 3, places)
            fig = V.build_board(inst, list(range(8)), f"{fam}")
            assert len(fig.data[-1].x) == 8
    assert len(V.build_board(hand, [0, 1, 2], "Hand").data[-1].x) == 3


def test_histogram_marks_the_optimum_and_counts_all_arrangements(land6):
    _, ls = land6
    fig = V.build_hist(ls)
    bar = fig.data[0]
    assert int(sum(bar.y)) == 720 and bar.marker.color[0] == C.COLORS["best"] and all(c == C.COLORS["other"] for c in bar.marker.color[1:]) and _locked(fig)


def test_end_chart_shares_sum_to_one_hundred_percent(land6):
    _, ls = land6
    fig = V.build_ends(ls)
    assert abs(sum(sum(t.y) for t in fig.data) - 100.0) < 1e-9 and sum(len(t.x) for t in fig.data) == ls.n_local and _locked(fig)


def _rows(n=6, seeds=(1, 2, 3)):
    return {f: ev.sweep(f, n, "grid", seeds) for f in C.FAMILIES}


def test_spread_and_predict_charts_have_one_point_per_instance():
    by = _rows()
    sp = V.build_spread(6, by)
    assert len(sp.data) == 6 and all(len(t.y) == 3 for t in sp.data) and _locked(sp)
    for key in ("fd", "dens", "gini", "top3"):
        pr = V.build_predict(6, by, key, key)
        assert len(pr.data) == 6 and sum(len(t.x) for t in pr.data) == 18 and _locked(pr)


def test_charts_skip_families_without_rows():
    by = _rows()
    by["star"] = []
    assert len(V.build_spread(6, by).data) == 5 and len(V.build_predict(6, by, "fd", "fd").data) == 5


def test_correlation_chart_has_one_bar_group_per_size():
    by = _rows()
    corr = {6: ev.correlations(ev.pooled(by)), 8: ev.correlations(ev.pooled(by))}
    fig = V.build_correlations(corr)
    assert [t.name for t in fig.data] == ["n = 6", "n = 8"] and len(fig.data[0].x) == len(ev.PREDICTORS) and _locked(fig)


def test_places_chart_has_two_boxes():
    by = _rows()
    fig = V.build_places(6, by["uniform"], ev.sweep("uniform", 6, "random", (1, 2, 3)))
    assert [t.name for t in fig.data] == ["Raster", "zufällige Plätze"] and _locked(fig)


def test_the_pdf_export_returns_a_pdf_for_two_settings(land6, land8):
    for (inst, ls), s in ((land6, ev.Settings("netlist", 6, 35)), (land8, ev.Settings("uniform", 8, 35, "random"))):
        data = build_pdf(s, ev.instance_view(s, ls), ls)
        assert data[:5] == b"%PDF-" and len(data) > 1500
