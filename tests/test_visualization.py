"""Abbildungen: Spuren des Netzes (Gerüst, eingesetzte Kanten, Kreuzungen, Schrittweise), Verteilung, Reihen; alle Achsen gesperrt."""

import pln_algorithm as A
import pln_constants as C
import pln_evaluation as ev
import pln_scenario as S
import pln_visualization as V


def octahedron_run():
    n = 6
    pos = ((0.0, 0.0), (6.0, 0.0), (3.0, 5.0), (3.0, 1.2), (2.0, 2.8), (4.0, 2.8))
    edges = tuple(sorted(((0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (0, 3), (1, 3), (0, 4), (2, 4), (1, 5), (2, 5), (0, 5))))
    kept = [e for e in edges if e != (0, 5)]
    p = A.planarize(n, edges, kept, [(0, 5)], A.rotation_from_positions(n, kept, pos), [(0, 5)])
    g = S.Graph(n, edges, pos, "Oktaeder")
    return g, ev.Run(tuple(kept), ((0, 5),), p, "geometry", False)


def test_net_figure_by_hand():
    g, run = octahedron_run()
    fig = V.build_net(g, run, title="x")
    gray, red, cross, nodes = fig.data
    assert gray.x.count(None) == 12                                                                         # 12 Gerüstkanten, die eingesetzte Kante nicht grau
    assert red.x.count(None) == 1 and len([x for x in red.x if x is not None]) == 3                          # ein Streckenzug mit drei Punkten (Quelle, Kreuzung, Ziel)
    assert len(cross.x) == 1 and cross.marker.symbol == "x" and len(nodes.x) == 6
    dpos = A.dummy_positions(run.planarization, g.pos)
    assert (cross.x[0], cross.y[0]) == dpos[6]
    assert red.line.color == C.COLOR_INSERTED and fig.layout.yaxis.scaleanchor == "x" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_net_figure_step_by_step_hides_later_insertions():
    pos = tuple((float(i), 0.0) for i in range(6))
    g = S.Graph(6, ((0, 1), (2, 3), (4, 5)), pos, "x")
    p = A.start_planarization(6, g.edges, [(0, 1)], {0: [1], 1: [0], 2: [], 3: [], 4: [], 5: []})
    A.insert_edge(p, (2, 3))
    A.insert_edge(p, (4, 5))
    run = ev.Run(((0, 1),), ((2, 3), (4, 5)), p, "arbitrary", False)
    zero = V.build_net(g, run, shown=0)
    one = V.build_net(g, run, shown=1)
    full = V.build_net(g, run)
    assert zero.data[0].x.count(None) == 1 and zero.data[1].x.count(None) == 0
    assert one.data[0].x.count(None) == 1 and one.data[1].x.count(None) == 1
    assert full.data[0].x.count(None) == 1 and full.data[1].x.count(None) == 2


def test_per_edge_and_series_figures_use_the_rows():
    fig = V.build_per_edge([0, 0, 1, 3, 3, 3])
    assert list(fig.data[0].x) == ["0", "1", "2", "3"] and list(fig.data[0].y) == [2, 1, 0, 3] and list(V.build_per_edge([]).data[0].x) == ["0"]
    rows = [{"name": "K5", "known": 1, "best": 1, "first": 1}, {"name": "K4,4", "known": 4, "best": 4, "first": 5}]
    cl = V.build_classic(rows)
    by = {t.name: list(t.y) for t in cl.data}
    assert by["bekannte Kreuzungszahl"] == [1, 4] and by["beste Reihenfolge"] == [1, 4] and by["erste Reihenfolge"] == [1, 5] and list(cl.data[0].x) == ["K5", "K4,4"]
    order = [{"extras": 1, "removed_random": 1, "removed_length": 1, "straight": 7, "crossings": 6}, {"extras": 5, "removed_random": 31, "removed_length": 5, "straight": 63, "crossings": 34}]
    o = V.build_order(order)
    by = {t.name: list(t.y) for t in o.data}
    assert by["zufällige Reihenfolge"] == [1, 31] and by["kürzeste zuerst"] == [1, 5] and by["Zahl der Zusatzkanten"] == [1, 5]
    c = V.build_crossings(order)
    by = {t.name: list(t.y) for t in c.data}
    assert by["gerade Strecken"] == [7, 63] and by["Planarisierung"] == [6, 34]
    emb = V.build_embedding([{"name": "A", "straight": 103, "geometry": 61, "arbitrary": 61}, {"name": "B", "straight": 125, "geometry": 35, "arbitrary": 40}])
    by = {t.name: list(t.y) for t in emb.data}
    assert by["Einbettung aus den Koordinaten"] == [61, 35] and by["beliebige Einbettung"] == [61, 40] and by["gerade Strecken"] == [103, 125]


def test_all_axes_are_locked():
    g, run = octahedron_run()
    figs = [V.build_net(g, run), V.build_per_edge([1]), V.build_classic([{"name": "K5", "known": 1, "best": 1, "first": 1}]),
            V.build_order([{"extras": 1, "removed_random": 1, "removed_length": 1, "straight": 7, "crossings": 6}]),
            V.build_crossings([{"extras": 1, "straight": 7, "crossings": 6}]), V.build_embedding([{"name": "A", "straight": 1, "geometry": 1, "arbitrary": 1}])]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
