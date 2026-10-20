"""Plotly-Abbildungen: das Netz mit Gerüst, eingesetzten Kanten und Kreuzungen; Verteilung der Kreuzungen je Kante; Messreihen (klassische Graphen, Reihenfolge, Einbettung). Alle Achsen gesperrt (fixedrange)."""

from __future__ import annotations

import plotly.graph_objects as go

import pln_algorithm as A
import pln_constants as C


def _frame(fig, title=None, height=540):
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)) if title else None, height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    fig.update_xaxes(visible=False, fixedrange=True, constrain="domain")
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1, constrain="domain")
    return fig


def build_net(graph, run, shown: int | None = None, title=None, height=540):
    """Das Netz: Gerüstkanten grau (als Strecken), eingesetzte Kanten rot (Streckenzug durch die Kreuzungspunkte), Kreuzungen als schwarze Punkte. `shown`: nur die ersten so vielen eingesetzten Kanten (Schritt für Schritt)."""
    p = run.planarization
    dpos = A.dummy_positions(p, graph.pos)
    inserted = p.inserted if shown is None else p.inserted[:shown]
    hidden = {i.edge for i in p.inserted[len(inserted):]}
    xs, ys = [], []
    for u, v in graph.edges:
        if (u, v) in hidden:
            continue
        if any(i.edge == (u, v) for i in inserted):
            continue
        xs += [graph.pos[u][0], graph.pos[v][0], None]
        ys += [graph.pos[u][1], graph.pos[v][1], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_EDGE, width=1), hoverinfo="skip"))
    rx, ry, cx, cy = [], [], [], []
    for ins in inserted:
        for node in ins.path:
            rx.append(dpos[node][0])
            ry.append(dpos[node][1])
        rx.append(None)
        ry.append(None)
        for node in ins.path[1:-1]:
            cx.append(dpos[node][0])
            cy.append(dpos[node][1])
    fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color=C.COLOR_INSERTED, width=2.5), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=cx, y=cy, mode="markers", marker=dict(size=7, color=C.COLOR_CROSSING, symbol="x"), hovertext=["Kreuzung"] * len(cx), hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[q[0] for q in graph.pos], y=[q[1] for q in graph.pos], mode="markers", marker=dict(size=5 if graph.n <= 150 else 3, color="#4c78a8"), hoverinfo="skip"))
    return _frame(fig, title, height)


def _layout(fig, title, height=340, y_title=None, x_title=None):
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)) if title else None, height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
                      legend=dict(orientation="h", y=-0.25, x=0), plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(fixedrange=True, title=x_title)
    fig.update_yaxes(fixedrange=True, title=y_title)
    return fig


def build_per_edge(per_edge):
    """Wie viele der eingesetzten Kanten kreuzen 0, 1, 2, … andere Kanten."""
    top = max(per_edge, default=0)
    counts = [sum(1 for c in per_edge if c == k) for k in range(top + 1)]
    fig = go.Figure(go.Bar(x=[str(k) for k in range(top + 1)], y=counts, marker_color=C.COLOR_INSERTED, hovertemplate="%{y} Kanten mit %{x} Kreuzungen<extra></extra>"))
    fig.update_xaxes(type="category")
    return _layout(fig, "Kreuzungen je eingesetzter Kante", height=280, x_title="Kreuzungen", y_title="Kanten")


def build_classic(rows):
    """Bekannte Kreuzungszahl, beste Planarisierung und die der ersten Reihenfolge je klassischem Graphen."""
    names = [r["name"] for r in rows]
    fig = go.Figure()
    for key, label, color in (("known", "bekannte Kreuzungszahl", C.COLOR_CROSSING), ("best", "beste Reihenfolge", C.COLOR_FIRST), ("first", "erste Reihenfolge", C.COLOR_THIRD)):
        fig.add_trace(go.Bar(x=names, y=[r[key] for r in rows], name=label, marker_color=color, hovertemplate="%{y}<extra>" + label + "</extra>"))
    fig.update_layout(barmode="group")
    return _layout(fig, "Kreuzungen der Planarisierung", y_title="Kreuzungen")


def build_order(rows):
    """Vom Greedy entfernte Kanten je Zahl der Zusatzkanten: zufällige Reihenfolge, kürzeste zuerst, und die Zusatzkanten selbst."""
    ks = [str(r["extras"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[r["removed_random"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_INSERTED, width=3), name="zufällige Reihenfolge", hovertemplate="%{y}<extra>zufällig</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["removed_length"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_FIRST, width=3), name="kürzeste zuerst", hovertemplate="%{y}<extra>kürzeste zuerst</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r["extras"] for r in rows], mode="lines", line=dict(color=C.COLOR_CROSSING, dash="dot"), name="Zahl der Zusatzkanten", hovertemplate="%{y}<extra>Zusatzkanten</extra>"))
    fig.update_xaxes(type="category")
    return _layout(fig, "Entfernte Kanten (Mediane)", x_title="Zusatzkanten", y_title="Kanten")


def build_crossings(rows):
    """Streckenkreuzungen und Kreuzungen der Planarisierung je Zahl der Zusatzkanten."""
    ks = [str(r["extras"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ks, y=[r["straight"] for r in rows], name="gerade Strecken", marker_color=C.COLOR_THIRD, hovertemplate="%{y}<extra>Strecken</extra>"))
    fig.add_trace(go.Bar(x=ks, y=[r["crossings"] for r in rows], name="Planarisierung", marker_color=C.COLOR_FIRST, hovertemplate="%{y}<extra>Planarisierung</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    return _layout(fig, "Kreuzungen (Mediane)", x_title="Zusatzkanten", y_title="Kreuzungen")


def build_embedding(rows):
    """Streckenkreuzungen und Kreuzungen der Planarisierung in zwei Einbettungen, je Netz."""
    names = [r["name"] for r in rows]
    fig = go.Figure()
    for key, label, color in (("straight", "gerade Strecken", C.COLOR_THIRD), ("geometry", "Einbettung aus den Koordinaten", C.COLOR_FIRST), ("arbitrary", "beliebige Einbettung", C.COLOR_SECOND)):
        fig.add_trace(go.Bar(x=names, y=[r[key] for r in rows], name=label, marker_color=color, hovertemplate="%{y}<extra>" + label + "</extra>"))
    fig.update_layout(barmode="group")
    return _layout(fig, "Kreuzungen nach Einbettung", y_title="Kreuzungen")
