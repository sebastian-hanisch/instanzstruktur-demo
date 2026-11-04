"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, jede Familie, die Rechenknöpfe, Eckfälle (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import izs_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "places_radio": "radio", "seed_input": "number_input"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown))


def test_default_page_shows_the_metrics_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Optimale Kosten", "Flussdominanz fd", "Lokale Optima", "Erfolg eines Abstiegs", "Endlücke"}
    assert values["Optimale Kosten"] == "31" and values["Erfolg eines Abstiegs"].endswith(" %")
    text = _texts(at)
    for part in ("Familie **Netzliste**, 8 Bauteile, Raster 2×4, Seed 35", "kein Befund über die Familie", "Die Frage lässt sich an einer Instanz nicht beantworten"):
        assert part in text, part


def test_the_five_experiments_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬")] == [f"🔬 Experiment {i}" for i in (1, 2, 3)] and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Das Handbeispiel: drei Bauteile auf einer Zeile", "📐 Mathematische Formulierung"]
    assert not at.error and len(at.get("plotly_chart")) == 4


def test_every_family_and_place_type_renders():
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=6)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 4
    at = _app(places_radio="random", n_select=6)
    assert "zufällige Plätze" in _texts(at)


def test_nine_waits_for_the_button():
    at9 = _app(n_select=9)
    assert any("362 880 Anordnungen" in str(i.value) for i in at9.info) and any(b.label == "⏱️ n = 9 rechnen" for b in at9.button)
    assert not at9.metric and "Familie **" not in _texts(at9)


def test_the_pdf_button_makes_a_download():
    at = _app(n_select=6)
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button"))


def test_the_comparison_for_six_components_fills_experiments_three_to_five():
    at = _app(n_select=6)
    assert any(b.label == "⏱️ Vergleich für n = 6 rechnen" for b in at.button)
    at.button(key="sweep_button_6").click().run()
    assert not at.exception
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬")] == [f"🔬 Experiment {i}" for i in range(1, 6)]
    text = _texts(at)
    for part in ("Erfolg eines Abstiegs bei n = 6", "Rangkorrelation (Spearman) der Flussdominanz", "Gleichverteilte Flüsse bei n = 6, je 20 Instanzen"):
        assert part in text, part
    assert len(at.get("plotly_chart")) == 4 + 4 and any("zweite Größe" in str(c.value) for c in at.caption)


def test_the_size_choice_of_the_comparison_switches_the_button():
    at = _app()
    at.radio(key="sweep_n").set_value(8).run()
    assert any(b.label == "⏱️ Vergleich für n = 8 rechnen" for b in at.button) and not at.exception
