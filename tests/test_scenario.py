"""Szenario: Delaunay-Karten mit Zusatzkanten, klassische Graphen, Toronto; deterministisch, die Basis ist planar."""

import math

import pytest

import pln_algorithm as A
import pln_scenario as S


def test_normalize_sorts_dedups_and_drops_loops():
    assert S.normalize([(2, 1), (1, 2), (3, 3), (0, 4)]) == ((0, 4), (1, 2))


def test_delaunay_is_deterministic_planar_and_triangulated():
    g = S.make_delaunay(60, 0, 3)
    assert g == S.make_delaunay(60, 0, 3) and g != S.make_delaunay(60, 0, 4) and g.n == 60 and g.extras == ()
    assert g.m <= 3 * 60 - 6 and A.crossing_pairs(g.edges, g.pos) == [] and A.is_planar(g.n, g.edges)
    assert all(len(g.pos[v]) == 2 for v in range(g.n)) and g.name == "Karte mit 60 Standorten und 0 Zusatzkanten"


def test_extras_are_new_edges_between_distinct_sites_and_deterministic():
    base, g = S.make_delaunay(60, 0, 3), S.make_delaunay(60, 7, 3)
    assert len(g.extras) == 7 and set(g.extras) == set(g.edges) - set(base.edges) and g.m == base.m + 7
    assert all(u < v for u, v in g.extras) and g == S.make_delaunay(60, 7, 3) and g.pos == base.pos
    assert g.name == "Karte mit 60 Standorten und 7 Zusatzkanten"


def test_extras_make_the_graph_nonplanar_in_most_cases():
    assert not A.is_planar(80, S.make_delaunay(80, 10, 5).edges)


def test_classic_graphs_by_hand():
    expected = {"K5": (5, 10), "K6": (6, 15), "K7": (7, 21), "K3,3": (6, 9), "K3,4": (7, 12), "K3,5": (8, 15), "K4,4": (8, 16), "Petersen": (10, 15)}
    for name, (n, m) in expected.items():
        g = S.make_classic(name)
        assert (g.n, g.m, g.name) == (n, m, name) and len(g.pos) == n and all(abs(math.hypot(*p) - 1.0) < 1e-5 for p in g.pos)
    petersen = S.make_classic("Petersen")
    degrees = [sum(1 for e in petersen.edges if v in e) for v in range(10)]
    assert degrees == [3] * 10 and not A.is_planar(10, petersen.edges)
    k33 = S.make_classic("K3,3")
    assert k33.edges == tuple((i, 3 + j) for i in range(3) for j in range(3))


def test_known_crossing_numbers_are_the_documented_values():
    assert S.KNOWN_CROSSING_NUMBER == {"K5": 1, "K6": 3, "K7": 9, "K3,3": 1, "K3,4": 2, "K3,5": 4, "K4,4": 4, "Petersen": 2}


def test_toronto_full_map_and_ball():
    full = S.make_toronto()
    assert (full.n, full.m, full.name) == (5072, 7621, "Toronto-Karte") and len(A.crossing_pairs(full.edges, full.pos)) == 125
    ball = S.make_toronto(250)
    assert ball.n == 250 and ball == S.make_toronto(250) and ball.name == "Straßenausschnitt mit 250 Knoten" and ball.m > 250
    assert all(0 <= u < v < 250 for u, v in ball.edges) and S.make_toronto(20).n == 20


def test_make_graph_dispatches_and_rejects_unknown():
    assert S.make_graph("delaunay", 30, 2, "K5", 1) == S.make_delaunay(30, 2, 1)
    assert S.make_graph("classic", 30, 2, "K5", 1) == S.make_classic("K5")
    assert S.make_graph("toronto", 40, 2, "K5", 1) == S.make_toronto(40)
    with pytest.raises(ValueError):
        S.make_graph("ring", 30, 2, "K5", 1)
