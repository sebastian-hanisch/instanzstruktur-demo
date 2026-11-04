"""Konstanten: Größen, Raster, Familien der Flussmatrix, feste Reihen der Experimente, Farben und Presets."""

SIZES = (6, 8, 9)                                     # Bauteile = Plätze (alle n! Anordnungen werden aufgezählt); n = 9 nur als Einzelinstanz auf Knopfdruck
DEFAULT_N = 8
SWEEP_SIZES = (6, 8)                                  # Größen der Vergleiche über viele Instanzen
GRID = {6: (2, 3), 8: (2, 4), 9: (3, 3)}              # Plätze als Raster (Zeilen, Spalten), Abstand = Manhattan
SEED_MAX, DEFAULT_SEED = 999999, 35
SWEEP_SEEDS = tuple(range(100000, 100020))            # feste Instanzen: nie ein einzelner Seed als Befund
START_MAX = 999999

FAMILIES = ("netlist", "uniform", "sparse", "cluster", "star", "skewed")
DEFAULT_FAMILY = "netlist"
FAMILY_NAMES = {"netlist": "Netzliste", "uniform": "Gleichverteilt", "sparse": "Dünn besetzt", "cluster": "Zwei Cluster", "star": "Stern", "skewed": "Wenige starke Flüsse"}
FAMILY_HELP = {
    "netlist": "Netzliste aus Dreiergruppen (IC, Kondensator, Widerstand), jedes Paar in einem Netz zählt Fluss 1: die Familie aus Stück 1.",
    "uniform": "Jedes Paar von Bauteilen hat einen zufälligen Fluss von 0 bis 9, gleichverteilt: dichte Matrix ohne Struktur.",
    "sparse": "Nur drei von zehn Paaren haben Fluss (1 bis 9), die übrigen keinen: dünn besetzt ohne weitere Struktur.",
    "cluster": "Zwei Gruppen von Bauteilen: innerhalb einer Gruppe starker Fluss (8 bis 10), zwischen den Gruppen schwacher (0 bis 2).",
    "star": "Ein Bauteil (die Nabe) hat starken Fluss (1 bis 9) zu allen anderen; zwischen den übrigen höchstens 1.",
    "skewed": "Die Flüsse sind schief verteilt: viele Paare ohne oder mit kleinem Fluss, wenige mit sehr großem (bis 60).",
}
PLACES = ("grid", "random")
PLACE_NAMES = {"grid": "Raster", "random": "zufällige Plätze"}
DEFAULT_PLACES = "grid"
RANDOM_PLACE_SPAN = 10                                # zufällige Plätze: Koordinaten 0 bis 9 in beiden Richtungen, Abstand Manhattan

# Netzliste (wie in Stück 1)
N_NETS_PER_COMPONENT = 1.5
NET_SIZES = (2, 3, 4)
NET_WEIGHTS = (5, 3, 2)
LOCAL_NET_PERCENT = 70
GROUP = 3
# Dünn besetzt, Cluster, Stern, schief
SPARSE_PERCENT = 30
UNIFORM_MAX = 9
CLUSTER_STRONG, CLUSTER_WEAK_MAX = 8, 2
SKEW_VALUES = (0, 1, 2, 4, 8, 16, 32, 60)
SKEW_WEIGHTS = (45, 22, 13, 8, 6, 3, 2, 1)           # ganzzahlige Gewichte (Summe 100), schweres Ende

HAND_FLOWS = ((0, 1, 5), (1, 2, 1))                   # Handbeispiel: drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1
HAND_GRID = (1, 3)

COLORS = {"best": "#2F6B65", "local": "#c0504d", "other": "rgba(150,150,150,0.6)", "line": "#4c78a8", "ok": "#2F6B65", "warn": "#b08a2e", "bad": "#b34a4a",
          "family": {"netlist": "#4c78a8", "uniform": "#9c755f", "sparse": "#b08a2e", "cluster": "#2F6B65", "star": "#8e6bb0", "skewed": "#c0504d"}}

_BASE = {"family": DEFAULT_FAMILY, "n": DEFAULT_N, "seed": DEFAULT_SEED, "places": DEFAULT_PLACES}
PRESETS = {
    "Standardfall: Netzliste, acht Bauteile": dict(_BASE),
    "Gleichverteilte Flüsse": dict(_BASE, family="uniform"),
    "Zwei Cluster": dict(_BASE, family="cluster"),
    "Dünn besetzt": dict(_BASE, family="sparse"),
    "Stern: eine Nabe": dict(_BASE, family="star"),
    "Wenige starke Flüsse": dict(_BASE, family="skewed"),
    "Zufällige Plätze statt Raster": dict(_BASE, family="uniform", places="random"),
    "Sechs Bauteile": dict(_BASE, n=6),
}
PRESET_HELP = {
    "Standardfall: Netzliste, acht Bauteile": "Die Familie aus Stück 1 mit acht Bauteilen auf dem 2×4-Raster: 40 320 Anordnungen, alle werden gerechnet.",
    "Gleichverteilte Flüsse": "Jedes Paar hat einen zufälligen Fluss von 0 bis 9: die dichte Matrix ohne Struktur, die man als Zufallsinstanz kennt.",
    "Zwei Cluster": "Zwei Gruppen mit starkem Fluss innerhalb und schwachem zwischen den Gruppen.",
    "Dünn besetzt": "Nur ein Teil der Paare hat überhaupt Fluss: viele Nullen in der Matrix.",
    "Stern: eine Nabe": "Ein Bauteil hängt mit allen anderen stark zusammen, die übrigen kaum untereinander.",
    "Wenige starke Flüsse": "Schiefe Flüsse: die meisten Paare klein oder null, wenige sehr groß.",
    "Zufällige Plätze statt Raster": "Gleichverteilte Flüsse, aber die Plätze liegen zufällig in einem 10×10-Feld statt auf einem Raster: ohne Spiegelsymmetrie.",
    "Sechs Bauteile": "Sechs Bauteile auf dem 2×3-Raster: 720 Anordnungen, die Rechnung dauert Sekundenbruchteile.",
}


def n_text(n: int) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 362880 → „362 880“."""
    return f"{n:,}".replace(",", " ")


assert set(PRESETS) == set(PRESET_HELP) and set(FAMILY_NAMES) == set(FAMILIES) == set(FAMILY_HELP) and set(PLACE_NAMES) == set(PLACES)
assert all(p["n"] in SIZES and p["family"] in FAMILIES and p["places"] in PLACES and 0 <= p["seed"] <= SEED_MAX for p in PRESETS.values())
assert all(r * c == n for n, (r, c) in GRID.items()) and sum(SKEW_WEIGHTS) == 100 and len(SKEW_VALUES) == len(SKEW_WEIGHTS)
