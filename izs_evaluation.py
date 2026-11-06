"""Kennzahlen, Vergleiche über Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen und die sechs erfundenen Familien (siehe README), nicht für echte Platinen oder QAPLIB; Zeiten stehen nie in Verdikten."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import permutations

import numpy as np

import izs_constants as C
import izs_cost as K
import izs_landscape as L
from izs_instance import hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    places: str = C.DEFAULT_PLACES


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def sgn(x: float, digits: int = 2) -> str:
    """Mit Vorzeichen: +0,44 / −0,13."""
    return ("+" if x >= 0 else "") + de(x, digits)


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


# ----------------------------------------------------------------------------- Kennzahlen der Flussmatrix

def pair_values(F) -> np.ndarray:
    return np.asarray(F)[np.triu_indices(len(F), 1)].astype(float)


def flow_dominance(F) -> float:
    """fd = 100 · Standardabweichung / Mittel der Paarflüsse (Grundgesamtheit, alle n(n−1)/2 Paare); NaN, wenn der Mittelwert 0 ist."""
    v = pair_values(F)
    return float(100.0 * v.std() / v.mean()) if v.size and v.mean() > 0 else float("nan")


def density(F) -> float:
    """Anteil der Paare mit Fluss größer als 0."""
    v = pair_values(F)
    return float((v > 0).mean()) if v.size else float("nan")


def gini(F) -> float:
    """Gini-Koeffizient der Paarflüsse (0 = alle gleich, nahe 1 = ein Paar trägt fast alles); NaN, wenn die Summe 0 ist."""
    v = np.sort(pair_values(F))
    if not v.size or v.sum() == 0:
        return float("nan")
    k = len(v)
    return float((2 * np.arange(1, k + 1) - k - 1).dot(v) / (k * v.sum()))


def top_share(F, k: int = 3) -> float:
    """Anteil der k stärksten Paare am Gesamtfluss; NaN, wenn die Summe 0 ist."""
    v = pair_values(F)
    return float(np.sort(v)[::-1][:k].sum() / v.sum()) if v.size and v.sum() > 0 else float("nan")


def flow_stats(F) -> dict:
    return {"fd": flow_dominance(F), "dens": density(F), "gini": gini(F), "top3": top_share(F, 3), "total": int(pair_values(F).sum()), "max": int(pair_values(F).max()) if len(F) > 1 else 0}


PREDICTORS = (("fd", "Flussdominanz fd"), ("dens", "Dichte"), ("gini", "Gini der Flüsse"), ("top3", "Anteil der drei stärksten Paare"), ("mean_gap", "Kostenlücke einer Zufallsanordnung"))


# ----------------------------------------------------------------------------- Statistik (reine Ganzzahl- und Float-Rechnung, numpy)

def ranks(x) -> np.ndarray:
    """Ränge 1..N, Gleichstände erhalten den mittleren Rang."""
    x = np.asarray(x, dtype=float)
    order = x.argsort(kind="mergesort")
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    for u in np.unique(x):
        m = x == u
        r[m] = r[m].mean()
    return r


def spearman(a, b) -> float:
    """Rangkorrelation (Pearson-Korrelation der Ränge); NaN, wenn eine Seite konstant ist oder weniger als zwei Werte vorliegen."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) != len(b):
        raise ValueError("gleich lange Reihen")
    if len(a) < 2 or np.isnan(a).any() or np.isnan(b).any():
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_band(count: int) -> float:
    """Grobe 95-%-Unsicherheit einer Rangkorrelation bei `count` Instanzen: 1,96 · 1,06 / √(count − 3) (Näherung nach Fieller u. a.; nur eine Größenordnung)."""
    return 1.96 * 1.06 / math.sqrt(count - 3) if count > 3 else float("nan")


def eta_squared(groups, values) -> float:
    """Anteil der Streuung der Ränge von `values`, den die Gruppenzugehörigkeit erklärt (Quadratsumme zwischen den Gruppen / gesamte Quadratsumme der Ränge)."""
    r = ranks(values)
    g = np.asarray(list(groups))
    total = ((r - r.mean()) ** 2).sum()
    if total == 0:
        return float("nan")
    between = sum(((r[g == u]).mean() - r.mean()) ** 2 * (g == u).sum() for u in np.unique(g))
    return float(between / total)


def quartiles(x) -> tuple:
    x = np.asarray(x, dtype=float)
    return float(np.percentile(x, 25)), float(np.median(x)), float(np.percentile(x, 75))


# ----------------------------------------------------------------------------- Messung einer Instanz und Vergleiche

def landscape_of(s: Settings) -> L.Landscape:
    return L.landscape(make_instance(s.family, s.n, s.seed, s.places))


def measure(inst, ls: L.Landscape) -> dict:
    """Eine Zeile für den Vergleich: Kennzahlen der Flüsse und Ergebnis der Landschaft."""
    row = flow_stats(inst.F)
    row.update(family=inst.family, places=inst.places, n=inst.n, seed=inst.seed, opt=ls.opt, success=ls.success, end_gap=ls.end_gap, mean_gap=ls.mean_gap, n_local=ls.n_local,
               n_nonglobal=ls.n_local_nonglobal, steps=ls.mean_steps, perms=ls.perms)
    return row


def measure_instance(family: str, n: int, seed: int, places: str = "grid") -> dict:
    inst = make_instance(family, n, seed, places)
    return measure(inst, L.landscape(inst))


def sweep(family: str, n: int, places: str = "grid", seeds=C.SWEEP_SEEDS) -> list:
    """Die festen Instanzen einer Familie: je Seed eine Zeile."""
    return [measure_instance(family, n, x, places) for x in seeds]


def family_summary(rows: list) -> dict:
    """Zusammenfassung der Zeilen einer Familie: Quartile und Spanne des Erfolgs, Median der Endlücke und der Dichte, Anteil der Instanzen mit Erfolg ab 50 % und bis 20 %."""
    succ = np.array([r["success"] for r in rows])
    q1, med, q3 = quartiles(succ)
    return {"count": len(rows), "success_q1": q1, "success": med, "success_q3": q3, "success_min": float(succ.min()), "success_max": float(succ.max()),
            "end_gap": float(np.median([r["end_gap"] for r in rows])), "mean_gap": float(np.median([r["mean_gap"] for r in rows])), "fd": float(np.median([r["fd"] for r in rows])),
            "dens": float(np.median([r["dens"] for r in rows])), "n_local": float(np.median([r["n_local"] for r in rows])),
            "share_half": float((succ >= 0.5).mean()), "share_low": float((succ <= 0.2).mean())}


def pooled(rows_by_family: dict) -> list:
    return [r for f in C.FAMILIES for r in rows_by_family.get(f, [])]


def correlations(rows: list) -> list:
    """Rangkorrelation jeder Kennzahl mit dem Erfolg und der Endlücke über alle Zeilen: [(Schlüssel, Name, mit Erfolg, mit Endlücke)]."""
    succ = [r["success"] for r in rows]
    gap = [r["end_gap"] for r in rows]
    return [(k, name, spearman([r[k] for r in rows], succ), spearman([r[k] for r in rows], gap)) for k, name in PREDICTORS]


def explained_by_family(rows: list) -> dict:
    """η² der Ränge: wie viel der Streuung von Erfolg, Endlücke und Kostenlücke die Familie erklärt."""
    g = [r["family"] for r in rows]
    return {k: eta_squared(g, [r[k] for r in rows]) for k in ("success", "end_gap", "mean_gap")}


# ----------------------------------------------------------------------------- Experiment 1: die Instanz

def instance_view(s: Settings, ls: L.Landscape) -> dict:
    inst = make_instance(s.family, s.n, s.seed, s.places)
    best = [int(x) for x in ls.optima[0]]
    return {"inst": inst, "best": best, "stats": flow_stats(inst.F), "cost": ls.opt, "worst": int(ls.cost_values[-1]), "mean": ls.mean_cost, "n_opt": ls.n_opt}


def hand_view() -> dict:
    """Das Handbeispiel: drei Bauteile auf einer Zeile, alle sechs Anordnungen mit Kosten."""
    inst = hand_instance()
    rows = sorted((K.cost(p, inst.F, inst.D), p) for p in permutations(range(3)))
    return {"inst": inst, "rows": rows, "stats": flow_stats(inst.F)}


# ----------------------------------------------------------------------------- Experiment 2: die Landschaft dieser Instanz

def landscape_view(s: Settings, ls: L.Landscape) -> dict:
    return {"ls": ls, "n_local": ls.n_local, "strict": ls.n_local_strict, "nonglobal": ls.n_local_nonglobal, "success": ls.success, "end_gap": ls.end_gap, "mean_gap": ls.mean_gap,
            "share_local": ls.n_local / ls.perms, "restarts": ls.restarts}


# ----------------------------------------------------------------------------- Verdikte

def verdict_instance(s: Settings, v: dict, ls: L.Landscape):
    st = v["stats"]
    where = f"{C.PLACE_NAMES[s.places]}" if s.places == "random" else f"Raster {C.GRID[s.n][0]}×{C.GRID[s.n][1]}"
    return "info", (f"Familie **{fam(s.family)}**, {s.n} Bauteile, {where}, Seed {s.seed}: Flussdominanz **fd = {de(st['fd'], 0)}**, Dichte {pct(st['dens'])}, Gini {de(st['gini'], 2)}, die drei stärksten Paare tragen {pct(st['top3'])} des Flusses. "
                    f"Die beste von {C.n_text(ls.perms)} Anordnungen kostet **{ls.opt}**, die schlechteste {v['worst']}, im Mittel kosten sie {de(v['mean'], 1)} ({pct(ls.mean_gap)} über dem Optimum). Alles ist aufgezählt: das Optimum ist bewiesen.")


def verdict_landscape(s: Settings, v: dict):
    ls = v["ls"]
    kind = "success" if ls.success >= 0.5 else "warning"
    return kind, (f"Von den {C.n_text(ls.perms)} Anordnungen sind **{C.n_text(ls.n_local)}** lokale Optima der Tauschnachbarschaft (roh gezählt, Spiegelbilder zählen mit), davon {ls.n_local_strict} streng; {v['nonglobal']} sind kein globales Optimum. "
                  f"Ein steilster Abstieg von einer Zufallsanordnung erreicht in **{pct(ls.success, 1)}** der Starts ein globales Optimum (exakt über alle Starts gezählt), im Mittel brauchte man {de(ls.restarts, 1)} Zufallsstarts. "
                  f"Die Endkosten liegen im Mittel {pct(ls.end_gap, 1)} über dem Optimum, eine Zufallsanordnung {pct(ls.mean_gap)}. Das ist eine Instanz, kein Befund über die Familie: dazu Experiment 3.")


def verdict_spread(n: int, by_family: dict, eta: dict):
    summ = {f: family_summary(r) for f, r in by_family.items() if r}
    easy = max(summ, key=lambda f: summ[f]["success"])
    hard = min(summ, key=lambda f: summ[f]["success"])
    widest = max(summ, key=lambda f: summ[f]["success_max"] - summ[f]["success_min"])
    total = sum(x["count"] for x in summ.values())
    e = eta["success"]
    weak = e < 0.5
    parts = "; ".join(f"{fam(f)} {pct(x['success'])} ({pct(x['success_min'])} bis {pct(x['success_max'])})" for f, x in summ.items())
    claim = (f"Die Familie erklärt nur **{pct(e)}** der Streuung des Erfolgs (η² der Ränge) und damit weniger als die Hälfte: der größere Teil der Streuung liegt innerhalb der Familien" if weak else
             f"Die Familie erklärt **{pct(e)}** der Streuung des Erfolgs (η² der Ränge): der Unterschied zwischen den Familien ist größer als die Streuung innerhalb")
    return ("warning" if weak else "success"), (f"Erfolg eines Abstiegs bei n = {n}, Median und Spanne über {total} Instanzen ({summ[easy]['count']} je Familie): {parts}. Am leichtesten ist im Median **{fam(easy)}**, am schwersten **{fam(hard)}**; "
                                               f"die größte Spanne hat {fam(widest)}. {claim}. Die mittlere Kostenlücke einer Zufallsanordnung erklärt die Familie zu {pct(eta['mean_gap'])}, die Endlücke eines Abstiegs zu {pct(eta['end_gap'])}.")


def verdict_predict(corr_by_n: dict, counts: dict):
    """corr_by_n: {n: correlations(rows)}; counts: {n: Zahl der Instanzen}."""
    sizes = sorted(corr_by_n)
    fd = {n: next(c for c in corr_by_n[n] if c[0] == "fd")[2] for n in sizes}
    band = {n: spearman_band(counts[n]) for n in sizes}
    parts = "; ".join(f"n = {n}: fd {sgn(fd[n])} ({counts[n]} Instanzen, Unsicherheit grob ±{de(band[n], 2)})" for n in sizes)
    clear = [n for n in sizes if abs(fd[n]) > band[n]]
    flip = len(sizes) >= 2 and fd[sizes[0]] * fd[sizes[-1]] < 0
    if not clear:
        tail = ("In keiner gerechneten Größe liegt die Rangkorrelation der Flussdominanz außerhalb der Unsicherheit: ein Zusammenhang mit dem Erfolg eines Abstiegs ist in dieser Messung nicht nachweisbar"
                + (f"; das Vorzeichen wechselt von n = {sizes[0]} nach n = {sizes[-1]}." if flip else "."))
        return "warning", f"Rangkorrelation (Spearman) der Flussdominanz mit dem Erfolg eines Abstiegs: {parts}. {tail}"
    if flip and len(clear) == len(sizes):
        tail = f"Das Vorzeichen wechselt von n = {sizes[0]} nach n = {sizes[-1]}, beide Werte liegen außerhalb der Unsicherheit: der Zusammenhang hängt von der Größe ab und taugt nicht als Vorhersage."
        return "warning", f"Rangkorrelation (Spearman) der Flussdominanz mit dem Erfolg eines Abstiegs: {parts}. {tail}"
    where = ", ".join(f"n = {n}" for n in clear)
    return "info", (f"Rangkorrelation (Spearman) der Flussdominanz mit dem Erfolg eines Abstiegs: {parts}. Außerhalb der Unsicherheit liegt sie nur bei {where}; "
                    f"das gilt für diese Familien und Größen und sagt nichts über andere Instanzen.")


def verdict_places(n: int, grid_rows: list, random_rows: list):
    g, r = family_summary(grid_rows), family_summary(random_rows)
    lower = r["success"] < g["success"]
    claim = "Zufällige Plätze machen den Abstieg in dieser Messung im Median schwerer" if lower else "Zufällige Plätze machen den Abstieg in dieser Messung im Median nicht schwerer"
    return ("warning" if lower else "info"), (f"Gleichverteilte Flüsse bei n = {n}, je {g['count']} Instanzen: Erfolg eines Abstiegs im Median {pct(g['success'], 1)} auf dem Raster gegen {pct(r['success'], 1)} auf zufälligen Plätzen "
                                              f"(Spanne {pct(r['success_min'])} bis {pct(r['success_max'])}); mittlere Endlücke {pct(g['end_gap'], 1)} gegen {pct(r['end_gap'], 1)}. {claim}. "
                                              f"Die Instanzen streuen auf dem Raster von {pct(g['success_min'])} bis {pct(g['success_max'])}: der Unterschied der Mediane ist im Verhältnis zu dieser Streuung zu lesen; ob er über die Instanzen trägt, zeigt erst ein gepaarter Vergleich.")


def verdict_core(s: Settings, v: dict, ls: L.Landscape):
    return "info", (f"Die Frage lässt sich an einer Instanz nicht beantworten: hier erreicht ein Abstieg {pct(ls.success)} der Starts, bei anderem Seed oder anderer Familie sieht es anders aus. Erst über viele feste Instanzen je Familie "
                    f"(Experiment 3) und die Frage, ob eine Kennzahl der Flüsse den Erfolg vorhersagt (Experiment 4), wird daraus ein Befund.")
