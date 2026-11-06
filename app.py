"""Instanzstruktur und Schwierigkeit - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 2 der Reihe „Anordnen: relaxieren und runden“: sechs Familien der Flussmatrix an derselben Anordnungsaufgabe (Bauteile auf Plätze, Kosten = Fluss mal Abstand). Alle Anordnungen werden aufgezählt; gefragt ist, wie schwer die
Tauschsuche je nach Struktur der Instanz fällt und ob eine einfache Kennzahl der Flüsse das vorhersagt. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import izs_constants as C
from izs_evaluation import (
    Settings,
    correlations,
    de,
    explained_by_family,
    family_summary,
    fam,
    hand_view,
    instance_view,
    landscape_of,
    landscape_view,
    pct,
    pooled,
    spearman_band,
    sweep,
    verdict_core,
    verdict_instance,
    verdict_landscape,
    verdict_places,
    verdict_predict,
    verdict_spread,
)
from izs_layout import dunkles_design, kopf_css
from izs_pdf_export import build_pdf
from izs_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from izs_visualization import build_board, build_correlations, build_ends, build_flow_heatmap, build_hist, build_places, build_predict, build_spread

st.set_page_config(page_title="Instanzstruktur und Schwierigkeit – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne alle Anordnungen …")
def _landscape(family, n, seed, places):
    return landscape_of(Settings(family, n, seed, places))


@st.cache_data(show_spinner=False)
def _sweep(family, n, places):
    return sweep(family, n, places)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in izs_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧱 Instanzstruktur und Schwierigkeit")
st.markdown(
    """
**Sind Instanzen mit Struktur für die Tauschsuche wirklich leichter?** Dieselbe Aufgabe wie in Stück 1: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand** über alle Paare; eine **Tauschsuche** vertauscht zwei Bauteile, solange es besser wird.
Neu ist die **Familie der Flussmatrix**: gleichverteilt, dünn besetzt, zwei Cluster, ein Stern, wenige starke Flüsse oder die Netzliste aus Stück 1. Bei bis zu neun Bauteilen werden **alle Anordnungen aufgezählt**, der Erfolg eines Abstiegs ist **exakt** gezählt. Gemessen wird,
wie stark die Familie den Erfolg bestimmt und ob eine einfache Kennzahl wie die Flussdominanz ihn vorhersagt. Die Familien sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen. Stück 2 der Reihe „Anordnen: relaxieren und runden“;
Heuristiken wie Tabu-Suche und Annealing stehen in der Fall-Demo [Tor-Zuordnung](https://sebastianhanisch-dockdoor-demo.streamlit.app/).

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Die Familie:** wie der Fluss zwischen den Bauteilen verteilt ist (sechs Möglichkeiten, Hilfetext am Regler). Die Plätze sind ein Raster oder zufällig in einem Feld verteilt.
2. **Alle Anordnungen:** bei `n ≤ 9` werden alle `n!` Anordnungen gerechnet; das Optimum ist bewiesen, und von **jeder** Anordnung aus läuft ein steilster Abstieg (Tausch mit dem größten Gewinn, bis keiner mehr hilft).
3. **Erfolg eines Abstiegs:** der Anteil aller Startanordnungen, deren Abstieg ein globales Optimum erreicht (exakt gezählt, nicht gewürfelt). **Endlücke:** wie weit über dem Optimum die Endkosten im Mittel liegen.
4. **Flussdominanz `fd`:** 100 · Standardabweichung / Mittel der Paarflüsse. Hoch heißt: wenige Paare tragen viel. Ob `fd` den Erfolg vorhersagt, ist die Frage von Experiment 4.
5. **Feste Instanzen:** Vergleiche laufen über je 20 feste Seeds, nie über einen einzelnen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz (Experiment 1 und 2)**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Bauteile = Plätze. Bei n = 9 liegen 362 880 Anordnungen vor; die Rechnung läuft auf Knopfdruck (rund eine Viertelminute).")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    places = st.radio("Plätze", C.PLACES, key="places_radio", format_func=lambda p: C.PLACE_NAMES[p], help="Raster: feste Zeilen und Spalten, Spiegelbilder kosten dasselbe. Zufällig: die Plätze liegen zufällig in einem 10×10-Feld.")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "places_radio": places})
settings = Settings(family, int(n), int(seed), places)

gated = settings.n == 9 and not st.session_state.get("n9_ok")
if gated:
    st.info("Bei n = 9 sind es 362 880 Anordnungen; die vollständige Rechnung dauert rund eine Viertelminute (auf Streamlit Cloud eher länger). Mit dem Knopf starten:")
    if st.button("⏱️ n = 9 rechnen", key="n9_button"):
        st.session_state["n9_ok"] = True
        st.rerun()
else:
    ls = _landscape(settings.family, settings.n, settings.seed, settings.places)
    iv = instance_view(settings, ls)
    lv = landscape_view(settings, ls)
    st_ = iv["stats"]

    # --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

    st.markdown("## 🎯 Ergebnis")
    m1, m2, m3 = st.columns(3)
    m4, m5 = st.columns(2)
    m1.metric("Optimale Kosten", str(ls.opt), help="Die kleinsten Kosten aller n! Anordnungen: aufgezählt, also bewiesen.")
    m2.metric("Flussdominanz fd", de(st_["fd"], 0), help="100 · Standardabweichung / Mittel der Paarflüsse: hoch heißt, wenige Paare tragen viel.")
    m3.metric("Lokale Optima", C.n_text(ls.n_local), help="Schwache lokale Optima der Tauschnachbarschaft (Gleichstände erlaubt), roh gezählt: Spiegelbilder eines Rasters zählen mit.")
    m4.metric("Erfolg eines Abstiegs", pct(ls.success, 1), help="Anteil aller Startanordnungen, deren steilster Abstieg ein globales Optimum erreicht (exakt gezählt, nicht gewürfelt).")
    m5.metric("Endlücke", pct(ls.end_gap, 1), help="Mittlere relative Lücke der Endkosten eines Abstiegs zum Optimum, über alle Startanordnungen.")
    st.plotly_chart(build_board(iv["inst"], iv["best"], f"Eine beste Anordnung (Kosten {ls.opt})"), width="stretch", key="board_chart")
    st.caption("Grau die Plätze, grün die Bauteile auf ihrem Platz, blau die Verbindungen mit Fluss (je dicker, desto mehr Fluss). Gezeigt ist die lexikographisch erste der besten Anordnungen.")

    if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
        st.session_state["pdf_made"] = (settings, build_pdf(settings, iv, ls))
    made = st.session_state.get("pdf_made")
    if made and made[0] == settings:
        st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="instanzstruktur.pdf", mime="application/pdf", key="pdf_download")

    # --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

    st.markdown("## ❓ Kernfrage: Sind strukturierte Instanzen für die Tauschsuche leichter?")
    verdict(verdict_core(settings, iv, ls))

    st.markdown("---")

    # --- Experimente 1 und 2 -------------------------------------------------------------------------------------------------------------------

    st.subheader("🔬 Experiment 1: Die Instanz und ihre Kennzahlen")
    st.caption("Die Flussmatrix der gewählten Familie und ihre Kennzahlen. Darunter das Handbeispiel mit drei Bauteilen, in dem man alles von Hand nachrechnen kann.")
    st.plotly_chart(build_flow_heatmap(iv["inst"]), width="stretch", key="flow_chart")
    st.dataframe(pd.DataFrame([{"Kennzahl": "Flussdominanz fd", "Wert": de(st_["fd"], 1)}, {"Kennzahl": "Dichte (Anteil Paare mit Fluss)", "Wert": pct(st_["dens"])},
                               {"Kennzahl": "Gini der Paarflüsse", "Wert": de(st_["gini"], 2)}, {"Kennzahl": "Anteil der drei stärksten Paare", "Wert": pct(st_["top3"])},
                               {"Kennzahl": "Gesamtfluss / größter Fluss", "Wert": f"{st_['total']} / {st_['max']}"}]), hide_index=True, width="stretch")
    verdict(verdict_instance(settings, iv, ls))
    hv = hand_view()
    with st.expander("Das Handbeispiel: drei Bauteile auf einer Zeile"):
        st.markdown(
            f"Drei Plätze nebeneinander (Abstände 1, 1 und 2), Fluss A–B: 5, B–C: 1, A–C: 0. Die Paarflüsse 5, 1, 0 haben Mittel 2 und Standardabweichung √(14/3) ≈ 2,16, also **fd = {de(hv['stats']['fd'], 0)}**. Alle sechs Anordnungen mit ihren Kosten "
            "(Plätze von A, B, C): ")
        st.dataframe(pd.DataFrame([{"Kosten": c, "Plätze von A, B, C": ", ".join(str(x + 1) for x in p)} for c, p in hv["rows"]]), hide_index=True, width="stretch")

    st.markdown("---")

    st.subheader("🔬 Experiment 2: Die Landschaft dieser Instanz")
    st.caption("Alle Anordnungen als Histogramm (grün: das Optimum) und rechts daneben, wo die Abstiege von allen Startanordnungen enden. **Eine Instanz ist kein Befund über die Familie**: dazu Experiment 3.")
    e1, e2 = st.columns(2)
    with e1:
        st.plotly_chart(build_hist(ls), width="stretch", key="hist_chart")
    with e2:
        st.plotly_chart(build_ends(ls), width="stretch", key="ends_chart")
    verdict(verdict_landscape(settings, lv))

    st.markdown("---")

# --- Experimente 3 bis 5: Vergleiche über feste Instanzen ---------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Streuung über je 20 Instanzen")
st.caption("Je Familie 20 feste Instanzen (Seeds 100000 bis 100019), alle Anordnungen aufgezählt: der Erfolg eines Abstiegs je Instanz. Die Größe wählen und die Rechnung starten (n = 6: Sekunden, n = 8: einige Minuten).")
sweep_n = st.radio("Größe des Vergleichs", C.SWEEP_SIZES, key="sweep_n", horizontal=True, format_func=lambda x: f"n = {x}")
done = st.session_state.setdefault("sweeps_done", {})
if not done.get(sweep_n):
    wait = "wenige Sekunden" if sweep_n == 6 else "rund vier bis fünf Minuten (auf Streamlit Cloud eher länger)"
    st.info(f"Der Vergleich für n = {sweep_n} rechnet 7 Reihen zu je 20 Instanzen und dauert {wait}. Mit dem Knopf starten:")
    if st.button(f"⏱️ Vergleich für n = {sweep_n} rechnen", key=f"sweep_button_{sweep_n}"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        todo = [(f, "grid") for f in C.FAMILIES] + [("uniform", "random")]
        for i, (f, p) in enumerate(todo):
            _sweep(f, sweep_n, p)
            bar.progress((i + 1) / len(todo), text=f"{C.FAMILY_NAMES[f]} ({C.PLACE_NAMES[p]}) fertig")
        done[sweep_n] = True
        st.rerun()
else:
    by = {f: _sweep(f, sweep_n, "grid") for f in C.FAMILIES}
    rnd = _sweep("uniform", sweep_n, "random")
    allrows = pooled(by)
    eta = explained_by_family(allrows)
    st.plotly_chart(build_spread(sweep_n, by), width="stretch", key="spread_chart")
    table = []
    for f in C.FAMILIES:
        s = family_summary(by[f])
        table.append({"Familie": fam(f), "fd (Median)": de(s["fd"], 0), "Dichte (Median)": pct(s["dens"]), "Erfolg (Median)": pct(s["success"], 1), "Quartile": f"{pct(s['success_q1'])} bis {pct(s['success_q3'])}",
                      "Spanne": f"{pct(s['success_min'])} bis {pct(s['success_max'])}", "Anteil mit Erfolg ≥ 50 %": pct(s["share_half"]), "Endlücke (Median)": pct(s["end_gap"], 1)})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_spread(sweep_n, by, eta))

    st.markdown("---")

    st.subheader("🔬 Experiment 4: Sagt eine Kennzahl den Erfolg voraus?")
    st.caption("Ein Punkt je Instanz (120 Instanzen je Größe): die Kennzahl der Flüsse gegen den Erfolg eines Abstiegs, und die Rangkorrelation (Spearman) für alle gerechneten Größen. Der Balken zeigt nur die Größenordnung, nicht die Unsicherheit; sie steht im Text.")
    labels = {"fd": "Flussdominanz fd", "dens": "Dichte", "gini": "Gini der Flüsse", "top3": "Anteil der drei stärksten Paare"}
    pick = st.selectbox("Kennzahl im Streudiagramm", list(labels), key="predictor_select", format_func=lambda k: labels[k])
    p1, p2 = st.columns(2)
    with p1:
        st.plotly_chart(build_predict(sweep_n, by, pick, labels[pick]), width="stretch", key="predict_chart")
    corr_by_n, counts = {}, {}
    for m in C.SWEEP_SIZES:
        if done.get(m):
            rows_m = pooled({f: _sweep(f, m, "grid") for f in C.FAMILIES})
            corr_by_n[m] = correlations(rows_m)
            counts[m] = len(rows_m)
    with p2:
        st.plotly_chart(build_correlations(corr_by_n), width="stretch", key="corr_chart")
    st.dataframe(pd.DataFrame([{"Größe": f"n = {m}", "Instanzen": counts[m], "Unsicherheit grob ±": de(spearman_band(counts[m]), 2), **{name: f"{de(r, 2)}" for _, name, r, _ in corr_by_n[m]}} for m in corr_by_n]), hide_index=True, width="stretch")
    verdict(verdict_predict(corr_by_n, counts))
    if len(corr_by_n) < len(C.SWEEP_SIZES):
        st.caption("Ob das Vorzeichen mit n wechselt, zeigt erst der Vergleich für die zweite Größe: oben die andere Größe wählen und rechnen.")

    st.markdown("---")

    st.subheader("🔬 Experiment 5: Raster gegen zufällige Plätze")
    st.caption("Dieselben gleichverteilten Flüsse, aber die Plätze liegen zufällig in einem 10×10-Feld statt auf einem Raster (ohne Spiegelsymmetrie): 20 Instanzen je Seite.")
    st.plotly_chart(build_places(sweep_n, by["uniform"], rnd), width="stretch", key="places_chart")
    verdict(verdict_places(sweep_n, by["uniform"], rnd))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die sechs Familien sind erfunden** | Echte Platinen oder QAPLIB-Instanzen haben andere Strukturen. Jede Aussage gilt nur für diese Familien mit diesen Parametern, nicht für „strukturierte Instanzen“ im Allgemeinen. | – |
| **Wenige Bauteile (6 bis 9)** | Die Aufzählung wächst mit `n!`. Dass sich ein Zusammenhang bei größeren Instanzen anders verhält (zwischen n = 6 und n = 8 kann sich das Vorzeichen einer Rangkorrelation ändern), ist hier nicht auszuschließen. | spätere Stücke (Schranken statt Aufzählung) |
| **Eine Nachbarschaft** | Alles gilt für den Paartausch; andere Nachbarschaften haben andere lokale Optima. | Trajektorien-Metaheuristiken |
| **Keine Heuristik gemessen** | Tabu-Suche und Annealing laufen weiter, wenn die Tauschsuche stehenbleibt: wie schwer eine Instanz für sie ist, zeigt diese Demo nicht. | Fall-Demo Tor-Zuordnung |
| **Nur einfache Kennzahlen** | Gemessen werden Flussdominanz, Dichte, Gini und der Anteil der stärksten Paare. Kennzahlen, die auch die Plätze oder das Spektrum der Matrizen einbeziehen, fehlen. | Stück 4 (Spektrum) |
| **Wenige Instanzen je Familie** | 20 Instanzen je Familie und 120 je Größe: die Rangkorrelationen schwanken um grob ±0,2. Kleine Unterschiede zwischen Familien sind nicht belastbar. | – |
| **Roh gezählt** | Anders als in Stück 1 werden lokale Optima nicht je Bahn gezählt; auf zufälligen Plätzen gibt es keine Spiegelbilder. Verglichen wird nur Erfolg und Endlücke, nicht die rohe Zahl lokaler Optima zwischen Raster und Zufall. | Stück 1 (Bahnen) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe (wie in Stück 1).** Symmetrischer Fluss $F \in \mathbb{N}^{n \times n}$, symmetrischer Abstand $D$ der Plätze, beide mit Diagonale 0; gesucht ist die Permutation $p$ mit kleinsten Kosten $\mathrm{cost}(p) = \sum_{i<k} F_{ik}\, D_{p_i p_k}$.
Der Tausch zweier Bauteile $a, b$ ändert die Kosten um $\Delta(p; a, b) = \sum_{k \ne a, b} (F_{ak} - F_{bk})(D_{p_b p_k} - D_{p_a p_k})$. Ein schwaches lokales Optimum hat $\Delta \ge 0$ für alle Paare.

**Erfolg eines Abstiegs.** Sei $\Pi$ die Menge aller $n!$ Anordnungen und $\mathrm{desc}(p)$ das Ende des steilsten Abstiegs von $p$ (der Tausch mit dem kleinsten $\Delta$, bei Gleichstand der erste in der Reihenfolge der Paare, solange $\Delta < 0$). Der Erfolg ist
$$\mathrm{succ} = \frac{|\{p \in \Pi : \mathrm{cost}(\mathrm{desc}(p)) = \mathrm{opt}\}|}{n!}.$$
Die **Endlücke** ist $\frac{1}{n!\,\mathrm{opt}} \sum_{p} \big(\mathrm{cost}(\mathrm{desc}(p)) - \mathrm{opt}\big)$, die **Kostenlücke einer Zufallsanordnung** $(\bar c - \mathrm{opt})/\mathrm{opt}$ mit dem Mittel $\bar c$ aller Kosten.

**Kennzahlen der Flüsse** (über alle $m = n(n-1)/2$ Paarflüsse $f_1, \dots, f_m$): die Flussdominanz $\mathrm{fd} = 100 \cdot \sigma(f)/\bar f$ mit der Standardabweichung der Grundgesamtheit, die Dichte $|\{f_j > 0\}|/m$, der Gini-Koeffizient
$G = \sum_j (2j - m - 1) f_{(j)} / (m \sum_j f_j)$ der aufsteigend sortierten Flüsse und der Anteil der drei größten Flüsse am Gesamtfluss.

**Rangkorrelation und Familie.** Die Rangkorrelation nach Spearman ist die Pearson-Korrelation der Ränge (Gleichstände erhalten den mittleren Rang). Für $N$ Instanzen ist ihre Unsicherheit grob $1{,}96 \cdot 1{,}06/\sqrt{N-3}$ (Näherung, nur eine Größenordnung).
Der Anteil der Streuung, den die Familie erklärt, ist $\eta^2 = \sum_g N_g(\bar r_g - \bar r)^2 / \sum_i (r_i - \bar r)^2$ für die Ränge $r_i$ (Kruskal–Wallis-Art).

**Literatur.** Die Flussdominanz als Kennzahl, die Taillard- und QAPLIB-Familien und Kennzahlen der Landschaft stammen aus der QAP-Literatur (Vollmann–Buffa, Taillard, Stützle u. a.; Angaben aus der Fachliteratur übernommen, hier nicht nachgelesen).
Die Formel der Flussdominanz ist die gängige Definition; die Zahlen dieser Demo sind eigene Rechnungen an eigenen, erfundenen Familien.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
