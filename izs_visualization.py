"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

import izs_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


# ----------------------------------------------------------------------------- Experiment 1: die Instanz

def build_flow_heatmap(inst) -> go.Figure:
    """Die Flussmatrix als Heatmap (obere Hälfte; die Matrix ist symmetrisch). Dunkel = starker Fluss."""
    n = inst.n
    z = [[(int(inst.F[a, b]) if b > a else None) for b in range(n)] for a in range(n)]
    fig = go.Figure(go.Heatmap(z=z, x=list(inst.names), y=list(inst.names), colorscale=[[0, "rgba(150,150,150,0.10)"], [1, C.COLORS["line"]]], zmin=0, zmax=max(1, int(inst.F.max())),
                               hovertemplate="%{y} – %{x}: Fluss %{z}<extra></extra>", colorbar=dict(title="Fluss", thickness=12), xgap=2, ygap=2))
    fig.update_layout(title="Fluss zwischen den Bauteilen")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=340, legend_below=False)


def build_board(inst, p, title: str) -> go.Figure:
    """Plätze als graue Quadrate, Bauteile als Punkte mit Namen auf ihrem Platz; Verbindungen mit Fluss als Linien (Dicke = Fluss, nach dem größten Fluss der Instanz skaliert)."""
    xs_, ys_ = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs_[int(p[i])], ys_[int(p[i])]) for i in range(inst.n)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs_, y=ys_, mode="markers", marker=dict(symbol="square", size=40, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    fmax = max(1, int(inst.F.max()))
    levels = sorted({min(4, 1 + int(3 * int(inst.F[a, b]) / fmax)) for a in range(inst.n) for b in range(a + 1, inst.n) if inst.F[a, b]})
    for lv in levels:
        xs, ys = [], []
        for a in range(inst.n):
            for b in range(a + 1, inst.n):
                if inst.F[a, b] and min(4, 1 + int(3 * int(inst.F[a, b]) / fmax)) == lv:
                    xs += [pos[a][0], pos[b][0], None]
                    ys += [pos[a][1], pos[b][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=0.8 + 1.4 * lv, color="rgba(76,120,168,0.45)"), name=("schwacher Fluss", "mittlerer Fluss", "starker Fluss", "stärkster Fluss")[lv - 1], hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False,
                             marker=dict(size=28, color=C.COLORS["best"]), textfont=dict(color="white", size=11), hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs_.min() - 0.7, xs_.max() + 0.7])
    fig.update_yaxes(visible=False, range=[ys_.min() - 0.7, ys_.max() + 0.7])
    return _base(fig, height=300, legend_below=True)


# ----------------------------------------------------------------------------- Experiment 2: die Landschaft dieser Instanz

def build_hist(ls) -> go.Figure:
    """Zahl der Anordnungen je Kostenwert; das Optimum ist grün, der Mittelwert eine Linie."""
    colors = [C.COLORS["best"] if v == ls.opt else C.COLORS["other"] for v in ls.cost_values]
    fig = go.Figure(go.Bar(x=ls.cost_values, y=ls.cost_counts, marker_color=colors, hovertemplate="Kosten %{x}: %{y} Anordnungen<extra></extra>", showlegend=False))
    fig.add_vline(x=ls.mean_cost, line=dict(color=C.COLORS["line"], dash="dot"), annotation_text="Mittel", annotation_position="top right")
    fig.update_layout(title=f"Kosten aller {C.n_text(ls.perms)} Anordnungen")
    fig.update_xaxes(title_text="Kosten (Summe Fluss · Abstand)")
    fig.update_yaxes(title_text="Zahl der Anordnungen")
    return _base(fig, legend_below=False)


def build_ends(ls) -> go.Figure:
    """Wo die Abstiege enden: jedes lokale Optimum, Kosten gegen den Anteil der Starts (grün = globales Optimum)."""
    is_opt = ls.local_cost == ls.opt
    fig = go.Figure()
    for flag, name, color in ((True, "globales Optimum", C.COLORS["best"]), (False, "lokales Optimum", C.COLORS["local"])):
        m = is_opt == flag
        fig.add_trace(go.Scatter(x=ls.local_cost[m], y=100.0 * ls.local_basin[m] / ls.perms, mode="markers", name=name, marker=dict(size=9, color=color, opacity=0.75),
                                 hovertemplate="Kosten %{x}: %{y:.2f} % der Starts<extra></extra>"))
    fig.update_layout(title="Wohin die Abstiege führen")
    fig.update_xaxes(title_text="Kosten des lokalen Optimums")
    fig.update_yaxes(title_text="Anteil der Starts (%)", rangemode="tozero")
    return _base(fig)


# ----------------------------------------------------------------------------- Experiment 3: Streuung über Instanzen

def build_spread(n: int, by_family: dict) -> go.Figure:
    """Erfolg eines Abstiegs je Instanz (Punkte, seitlich versetzt) mit Median je Familie."""
    fig = go.Figure()
    names = [C.FAMILY_NAMES[f] for f in C.FAMILIES if by_family.get(f)]
    for f in C.FAMILIES:
        rows = by_family.get(f)
        if not rows:
            continue
        y = [100.0 * r["success"] for r in rows]
        fig.add_trace(go.Box(y=y, x=[C.FAMILY_NAMES[f]] * len(y), name=C.FAMILY_NAMES[f], boxpoints="all", jitter=0.5, pointpos=0, marker=dict(color=C.COLORS["family"][f], size=6, opacity=0.7),
                             line=dict(color=C.COLORS["family"][f]), fillcolor="rgba(0,0,0,0)", hovertemplate="Erfolg %{y:.1f} %<extra></extra>", showlegend=False))
    fig.update_layout(title=f"Erfolg eines Abstiegs je Instanz (n = {n})")
    fig.update_xaxes(categoryorder="array", categoryarray=names)
    fig.update_yaxes(title_text="Erfolg eines Abstiegs (%)", range=[0, 100])
    return _base(fig, legend_below=False)


# ----------------------------------------------------------------------------- Experiment 4: Kennzahl gegen Erfolg

def build_predict(n: int, by_family: dict, key: str, label: str) -> go.Figure:
    """Streudiagramm: Kennzahl der Flüsse (x) gegen Erfolg eines Abstiegs (y), ein Punkt je Instanz, nach Familie gefärbt."""
    fig = go.Figure()
    for f in C.FAMILIES:
        rows = by_family.get(f)
        if not rows:
            continue
        fig.add_trace(go.Scatter(x=[r[key] for r in rows], y=[100.0 * r["success"] for r in rows], mode="markers", name=C.FAMILY_NAMES[f], marker=dict(size=8, color=C.COLORS["family"][f], opacity=0.75),
                                 hovertemplate=f"{label} %{{x:.2f}}: Erfolg %{{y:.1f}} %<extra>{C.FAMILY_NAMES[f]}</extra>"))
    fig.update_layout(title=f"{label} gegen Erfolg (n = {n})")
    fig.update_xaxes(title_text=label)
    fig.update_yaxes(title_text="Erfolg eines Abstiegs (%)", range=[0, 100])
    return _base(fig)


def build_correlations(corr_by_n: dict) -> go.Figure:
    """Rangkorrelation jeder Kennzahl mit dem Erfolg, je Größe n ein Balken."""
    fig = go.Figure()
    palette = {6: "#4c78a8", 8: "#c0504d", 9: "#2F6B65"}
    for n in sorted(corr_by_n):
        c = corr_by_n[n]
        fig.add_trace(go.Bar(x=[name for _, name, _, _ in c], y=[r for _, _, r, _ in c], name=f"n = {n}", marker_color=palette.get(n, "#888"), hovertemplate="%{x}: %{y:+.2f}<extra>n = " + str(n) + "</extra>"))
    fig.update_layout(title="Rangkorrelation mit dem Erfolg eines Abstiegs", barmode="group")
    fig.update_yaxes(title_text="Spearman", range=[-1, 1], zeroline=True)
    fig.update_xaxes(tickangle=-20)
    return _base(fig)


# ----------------------------------------------------------------------------- Experiment 5: Plätze

def build_places(n: int, grid_rows: list, random_rows: list) -> go.Figure:
    fig = go.Figure()
    for name, rows, color in (("Raster", grid_rows, C.COLORS["best"]), ("zufällige Plätze", random_rows, C.COLORS["local"])):
        y = [100.0 * r["success"] for r in rows]
        fig.add_trace(go.Box(y=y, x=[name] * len(y), name=name, boxpoints="all", jitter=0.5, pointpos=0, marker=dict(color=color, size=6, opacity=0.7), line=dict(color=color), fillcolor="rgba(0,0,0,0)",
                             hovertemplate="Erfolg %{y:.1f} %<extra></extra>", showlegend=False))
    fig.update_layout(title=f"Gleichverteilte Flüsse: Raster gegen zufällige Plätze (n = {n})")
    fig.update_yaxes(title_text="Erfolg eines Abstiegs (%)", range=[0, 100])
    return _base(fig, legend_below=False)
