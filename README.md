# Instanzstruktur und Schwierigkeit – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-instanzstruktur-demo.streamlit.app/)** -->

Stück 2 von 15 der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). Stück 1, [QAP an einer Mini-Halle](https://github.com/sebastian-hanisch/quadratische-zuordnung-demo), zeigt die Tauschlandschaft **einer** Familie von Instanzen (Netzlisten). Dieses Stück fragt: **Wie sehr hängt die Schwierigkeit der Tauschsuche von der Struktur der Instanz ab?** Dieselbe Aufgabe (Bauteile auf Plätze, Kosten gleich Fluss mal Abstand), sechs erfundene Familien der Flussmatrix nebeneinander, alle Anordnungen aufgezählt.

## Warum dieses Problem

Man sagt, strukturierte Instanzen seien für einfache Suchverfahren leichter als Zufallsinstanzen, und man hofft, die Schwierigkeit an einer einfachen Kennzahl wie der **Flussdominanz** (wie ungleich der Fluss verteilt ist) ablesen zu können. Bei bis zu neun Bauteilen kann man das prüfen, statt es zu glauben: Man zählt alle Anordnungen auf, lässt von **jeder** den steilsten Abstieg laufen und erhält den **Erfolg eines Abstiegs** exakt. Die Kernfrage: **Sind strukturierte Instanzen für die Tauschsuche wirklich leichter, und sagt eine einfache Kennzahl der Flüsse das voraus?**

Die Antwort dieser Messung: Die Familie erklärt etwa ein Fünftel der Streuung des Erfolgs (statistisch deutlich, aber der größte Teil der Streuung steckt innerhalb der Familien), die Rangfolge der Familien ändert sich zwischen sechs und acht Bauteilen (belastbar vor allem für Cluster), und die einfachen Kennzahlen sagen den Erfolg nicht stabil voraus. Das ist ein **Befund für diese erfundenen Familien**, kein Satz über Instanzen im Allgemeinen.

## Modell

- **Aufgabe** (wie in Stück 1): `n` Bauteile auf `n` Plätze, Kosten gleich der Summe über alle Paare von Fluss mal Abstand der Plätze; der Tausch zweier Bauteile ändert die Kosten um `Δ = Σ_{k≠a,b} (F[a,k] − F[b,k]) · (D[p_b,p_k] − D[p_a,p_k])`. Die Kosten-, Tausch- und Aufzählungs-Module (`izs_cost.py`, `izs_landscape.py`, `izs_rng.py`) sind Kopien aus Stück 1, die Familie „Netzliste“ erzeugt dieselben Instanzen (ein Test vergleicht das, wenn das Schwester-Repo nebenan liegt).
- **Sechs Familien der Flussmatrix** (`izs_instance.py`, alle über SplitMix64): **Netzliste** (Stück 1: Dreiergruppen, Fluss 1 je Paar im Netz), **gleichverteilt** (jedes Paar 0 bis 9), **dünn besetzt** (30 % der Paare mit Fluss 1 bis 9), **zwei Cluster** (innerhalb einer Hälfte 8 bis 10, dazwischen 0 bis 2), **Stern** (eine Nabe mit Fluss 1 bis 9 zu allen, sonst 0 oder 1), **wenige starke Flüsse** (schiefe Verteilung aus 0, 1, 2, 4, 8, 16, 32, 60 mit Gewichten 45, 22, 13, 8, 6, 3, 2, 1). Die Familien sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen.
- **Plätze:** ein Raster (2×3, 2×4, 3×3, Manhattan-Abstand) oder zufällige Plätze in einem 10×10-Feld (Plätze dürfen zusammenfallen); sie sind die Gegenprobe zu den Spiegelungen des Rasters.
- **Kennzahlen der Flüsse** (`izs_evaluation.py`): Flussdominanz `fd = 100 · Standardabweichung / Mittel` der Paarflüsse (Grundgesamtheit), Dichte (Anteil Paare mit Fluss), Gini-Koeffizient, Anteil der drei stärksten Paare. **Ergebnisgrößen:** Erfolg eines Abstiegs (Anteil der Startanordnungen, die ein globales Optimum erreichen), **Endlücke** (mittlere relative Lücke der Endkosten zum Optimum über alle Starts), **Kostenlücke einer Zufallsanordnung** (Mittel minus Optimum, relativ zum Optimum).
- **Statistik:** Rangkorrelation nach Spearman (Pearson-Korrelation der Ränge, Gleichstände mit mittlerem Rang), grobe Unsicherheit `1,96 · 1,06 / √(N − 3)` (bei 120 Instanzen ±0,19), und `η²` der Ränge als Anteil der Streuung, den die Familie erklärt (Kruskal–Wallis-Art).
- **Experimente:** (1) die Instanz und ihre Kennzahlen; (2) die Landschaft dieser Instanz; (3) die Streuung über je 20 Instanzen; (4) sagt eine Kennzahl den Erfolg voraus; (5) Raster gegen zufällige Plätze. Formeln im 📐-Expander der App.

## Methodik

Experiment 1 und 2 rechnen **eine** Instanz (n = 6 oder 8 sofort, n = 9 auf Knopfdruck, rund eine Viertelminute). Experiment 3 bis 5 rechnen auf Knopfdruck **feste Instanzen**: je Familie die Seeds 100000 bis 100019, dazu 20 Instanzen mit gleichverteilten Flüssen auf zufälligen Plätzen; bei n = 6 dauert das Sekunden, bei n = 8 rund vier bis fünf Minuten (140 Instanzen zu je rund zwei Sekunden; Zeiten hängen vom Rechner ab und werden nicht getestet). Alle Aussagen laufen über feste Seeds, nie über einen einzelnen. Der Vergleich ist bewusst auf n = 6 und n = 8 beschränkt: neun Bauteile (rund eine Viertelminute je Instanz) wären für 140 Instanzen zu langsam.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (die Aufzählung ist deterministisch, die Zahlen sind exakt bis auf die genannte Rundung). Familien: die sechs erfundenen oben, je 20 Instanzen, Raster 2×3 (n = 6) und 2×4 (n = 8).

| Frage | Befund |
|---|---|
| Handbeispiel (drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1) | Kosten der sechs Anordnungen 6, 6, 7, 7, 11, 11; `fd = 108,0`, Dichte 2/3, Gini 5/9; beide Optima sind lokale Optima, jeder Abstieg endet im Optimum |
| Standardinstanz (Netzliste, n = 8, Seed 35: die Instanz aus Stück 1) | 40 320 Anordnungen, Optimum 31, schlechteste 69; 112 lokale Optima (roh gezählt), 108 davon kein globales; Erfolg eines Abstiegs 26,6 % |
| Erfolg eines Abstiegs, n = 6 (Median, Spanne über 20 Instanzen) | Netzliste 81,4 % (28,9 bis 100); gleichverteilt 68,9 % (31,1 bis 100); dünn besetzt 85,8 % (41,1 bis 100); Cluster 57,5 % (21,1 bis 98,3); Stern 83,1 % (59,4 bis 100); wenige starke Flüsse 67,8 % (27,8 bis 100); zufällige Plätze (gleichverteilt) 45,6 % (19,4 bis 91,1) |
| Erfolg eines Abstiegs, n = 8 | Netzliste 35,9 % (11,6 bis 81,6); gleichverteilt 32,6 % (11,7 bis 62,4); dünn besetzt 38,4 % (13,3 bis 100); Cluster 61,0 % (19,8 bis 86,2); Stern 41,9 % (16,8 bis 72,0); wenige starke Flüsse 24,9 % (11,2 bis 51,8); zufällige Plätze 24,8 % (7,8 bis 49,8) |
| Kennzahlen der Flüsse, n = 8 (Median über 20 Instanzen) | Flussdominanz `fd`: Netzliste 105,7; gleichverteilt 60,5; dünn besetzt 179,3; Cluster 93,1; Stern 149,5; wenige starke Flüsse 224,8; Dichte (Anteil Paare mit Fluss): 62,5 / 92,9 / 30,4 / 78,6 / 57,1 / 53,6 % |
| Anteil der Instanzen mit Erfolg ab 50 %, n = 8 | Netzliste 40 %, gleichverteilt 20 %, dünn 40 %, Cluster 55 %, Stern 30 %, schief 5 %; mit Erfolg bis 20 %: 15 / 20 / 25 / 5 / 20 / 30 % |
| Rangfolge der Familien nach dem Median des Erfolgs | n = 6: dünn, Stern, Netzliste, gleichverteilt, schief, **Cluster (schwerste)**; n = 8: **Cluster (leichteste)**, Stern, dünn, Netzliste, gleichverteilt, schief: die Rangfolge kehrt sich für Cluster um |
| Anteil der Streuung, den die Familie erklärt (`η²` der Ränge, 120 Instanzen) | Erfolg 0,20 (n = 6) und 0,19 (n = 8); Endlücke 0,10 und 0,27; Kostenlücke einer Zufallsanordnung 0,74 und 0,84 |
| Rangkorrelation mit dem Erfolg (120 Instanzen, Unsicherheit grob ±0,19), n = 6 / n = 8 | `fd` +0,23 / −0,10; Dichte −0,35 / +0,08; Gini +0,25 / −0,08; drei stärkste Paare +0,27 / −0,10; Kostenlücke +0,17 / −0,09 |
| Innerhalb der Familien (je 20 Instanzen), n = 8 | Rangkorrelation von `fd` mit dem Erfolg zwischen −0,59 (gleichverteilt) und +0,67 (dünn besetzt) |
| Endlücke (Median der mittleren relativen Lücke der Endkosten zum Optimum) | n = 6: 0,5 % (Stern) bis 1,5 % (schief); n = 8: 1,8 % (Stern) bis 5,4 % (dünn besetzt); mit der Kostenlücke einer Zufallsanordnung korreliert sie bei n = 8 mit +0,51 |
| Raster gegen zufällige Plätze (gleichverteilte Flüsse) | Erfolg im Median 68,9 % gegen 45,6 % (n = 6) und 32,6 % gegen 24,8 % (n = 8); zufällige Plätze senken den Erfolg im Median (bei n = 6 deutlich, bei n = 8 nicht eindeutig), und die Instanzen streuen stark |
| Orakel | Rangkorrelation gleich `scipy.stats.spearmanr`, `η²` gleich `kruskal / (N − 1)`; `scipy.optimize.quadratic_assignment` (2opt) unterschreitet das aufgezählte Optimum nie |

**Was die Zahlen nicht sagen:** Die Familien sind erfunden; eine andere Wahl der Parameter (etwa andere Flusswerte im Cluster) kann die Rangfolge ändern. Die Rangkorrelation `fd` ~ Erfolg liegt bei n = 6 knapp außerhalb der Unsicherheit (+0,23 gegen ±0,19), bei n = 8 deutlich innerhalb (−0,10); der Vorzeichenwechsel ist daher **kein** belastbarer Befund über die Richtung, nur über das Fehlen einer stabilen. Der Erfolg eines Abstiegs ist eine harte Zahl (Anteil aller Starts), die **Endlücke** ist im Median klein (0,5 bis 5,4 %), in einzelnen Instanzen aber bis über 14 % (Messung der unabhängigen Prüfung, nicht Teil der Tests).

## Ehrliche Grenzen

- **Erfundene Familien:** keine echten Platinen, keine QAPLIB-Instanzen; jede Aussage gilt für diese sechs Familien mit diesen Parametern.
- **Wenige Bauteile:** sechs bis neun; ob sich Zusammenhänge bei größeren Instanzen anders verhalten, bleibt offen (zwischen n = 6 und n = 8 ändern sich schon Rangfolge und Vorzeichen). Der Vergleich über viele Instanzen läuft nur für n = 6 und n = 8.
- **Wenige Instanzen:** 20 je Familie, 120 je Größe; Unterschiede von wenigen Prozentpunkten zwischen Familien sind nicht belastbar.
- **Eine Nachbarschaft, keine Heuristik:** gemessen wird der steilste Abstieg mit dem Paartausch; Tabu-Suche und Annealing (Fall-Demo Tor-Zuordnung) laufen weiter, wo er stehenbleibt.
- **Nur einfache Kennzahlen:** Kennzahlen, die auch die Plätze oder das Spektrum der Matrizen einbeziehen (Stück 4), fehlen.
- **Roh gezählt:** lokale Optima werden nicht je Bahn gezählt (Stück 1 tut es), weil zufällige Plätze keine Spiegelbilder haben; Vergleichsgrößen sind Erfolg und Endlücke.
- **Quellen:** die Flussdominanz (Vollmann–Buffa), Taillard-Familien, QAPLIB und Kennzahlen der Landschaft (Stützle u. a.) sind aus der Fachliteratur übernommen und **nicht nachgelesen**; die Formeln in der App sind die gängigen Definitionen, die Zahlen eigene Rechnungen.

## Verifikation

- **Tests** (`pytest tests/`): **167 Tests**, rund drei Minuten (Windows, Python 3.14). Handwerte (Handbeispiel, Kosten, Tausch-`Δ`, Flusskennzahlen, `ρ`, `η²`), Eigenschaften (Tausch-`Δ` gegen Neuberechnung für jede Familie und beide Platzarten, vektorisierte `Δ` gegen Einzelformel, jedes globale Optimum ein lokales, die Einzugsgebiete decken alle `n!` Starts, Kennzahlen unter Umnummerierung und Skalierung invariant, Merkmale jeder Familie), Orakel (Einzelrechnung ohne Vektorisierung als Referenz der Landschaft; `scipy` für Rangkorrelation, Kruskal–Wallis und `quadratic_assignment`, nur mit `requirements-dev.txt`), Randfälle (zwei Bauteile, Nullfluss, gleiche Flüsse, zusammenfallende Plätze, ungültige Eingaben), Verdikte an handgesetzten Werten, Abbildungen, PDF, Rauchtest und Pfade der App (jede Familie, beide Platzarten, Knopf `n = 9`, Vergleich), Layout, Footer und Laufzeit-Importe. `test_claims.py` rechnet jede Zahl dieser README nach (rund zwei Minuten).
- **Kopie:** ein Test vergleicht die Netzlisten mit denen von Stück 1, sofern das Schwester-Repo nebenan liegt.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: grün (166 Tests bestanden, 1 übersprungen, Python 3.12; letzter Lauf auf `main`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Experimente, Grenzen, Formulierung |
| `izs_rng.py` | SplitMix64 (Kopie aus Stück 1) |
| `izs_instance.py` | Instanzen: sechs Familien der Flussmatrix, zwei Arten von Plätzen, Handbeispiel |
| `izs_cost.py` | Kosten, Tausch-`Δ` (Kopie aus Stück 1, ohne Lawler-Form) |
| `izs_landscape.py` | Aufzählung, lokale Optima, Abstieg, Einzugsgebiete, Endlücke |
| `izs_evaluation.py` | Kennzahlen der Flüsse, Statistik, Vergleiche über Instanzen, Verdikte |
| `izs_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `izs_pdf_export.py` | PDF-Export des Ergebnisses |
| `izs_constants.py` | Größen, Familien, feste Reihen, Farben, Presets |
| `izs_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `izs_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Kosten, Instanzen, Landschaft, Statistik, Randfälle, Verdikte, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **n = 9 im Vergleich:** zu langsam für 140 Instanzen; im Repo nur als Einzelinstanz auf Knopfdruck, nicht als Vergleich und ohne Zahl in dieser README.
- **Spektral- und Landschaftskennzahlen:** Stück 4 (Spektrum); Autokorrelation der Landschaft wurde nicht gemessen.
- **Metaheuristiken:** Fall-Demo Tor-Zuordnung und Linie Trajektorien-Metaheuristiken.
- **QAPLIB- und Taillard-Instanzen:** nicht nachgebaut, nicht im Repo.
- **Symmetriezählung je Bahn:** Stück 1; hier roh.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
