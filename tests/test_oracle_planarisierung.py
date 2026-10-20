"""Orakel-Test planarisierung-demo / planarisierung: das Planarisieren gegen andere Rechenwege.

Orakel (ORACLE-PLAYBOOK, Verfahrenstyp „Heuristik mit prüfbarem Ergebnis“):
1. **`networkx.check_planarity`** (Bibliothek, anderer Algorithmus als die Flächenzählung des Kerns): der Greedy-Teilgraph ist planar und **maximal**, die Planarisierung ist planar (Knoten: n + Kreuzungen);
2. **Aufzählen** aller Kantenteilmengen für die **exakte Schiefheit** kleiner Graphen: die Planarisierung braucht nie weniger Kreuzungen als die Schiefheit, der Greedy entfernt nie weniger Kanten; wo beides gleich ist, ist die Kreuzungszahl **bewiesen**;
3. **Doppelschleife über alle Kantenpaare** für die Streckenkreuzungen (siehe `tests/test_algorithm.py`);
dazu: Euler für die Einbettungen (Flächenzahl), `restore_edges` ergibt den Ausgangsgraphen, die Kreuzungen sind die Summe der Kreuzungen je eingesetzter Kante, jede Kreuzung gehört zu zwei Ketten,
und die Kreuzungszahlen klassischer Graphen (K5, K3,3 = 1 bewiesen durch Nichtplanarität; K6, K3,4, K4,4, Petersen bewiesen durch Schiefheit = gefundene Kreuzungen)."""

import networkx as nx
import pytest

import pln_algorithm as A
import pln_scenario as S
from conftest import random_graph


def nx_graph(n, edges):
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    return g


def rotation_graph(p):
    g = nx.Graph()
    g.add_nodes_from(p.rot)
    g.add_edges_from((u, v) for u, nb in p.rot.items() for v in nb)
    return g


def small_cases():
    for seed in range(40):
        n = (6, 7, 8, 9)[seed % 4]
        m = min(n * (n - 1) // 2, 3 * n - 6 + 1 + seed % 3)
        yield pytest.param(n, m, seed, id=f"n{n}-m{m}-s{seed}")


@pytest.mark.parametrize("n,m,seed", list(small_cases()))
def test_planarization_is_planar_restores_the_graph_and_respects_the_skewness(n, m, seed):
    n, edges, pos = random_graph(n, m, seed)
    skew = A.skewness_exact(n, edges, limit=8)
    assert skew is not None
    for kind in ("random", "length"):
        kept, removed = A.skeleton(n, edges, pos, kind, seed)
        g = nx_graph(n, kept)
        assert nx.check_planarity(g)[0]
        assert all(not nx.check_planarity(nx_graph(n, kept + [e]))[0] for e in removed)          # maximal im Sinne des Einfügens
        assert len(removed) >= skew
        p = A.planarize(n, edges, kept, removed, A.rotation_from_networkx(n, kept), removed)
        assert nx.check_planarity(rotation_graph(p))[0] and A.is_planar_embedding(p.rot)
        assert rotation_graph(p).number_of_nodes() == n + p.crossings
        assert A.restore_edges(p) == set(edges)
        assert p.crossings >= skew                                                                # jede Kreuzung braucht mindestens eine entfernte Kante
        assert p.crossings == sum(i.crossings for i in p.inserted) and sum(A.crossings_per_edge(p)) == 2 * p.crossings


@pytest.mark.parametrize("seed", range(20))
def test_cover_skeleton_with_the_coordinate_embedding_on_random_drawings(seed):
    n, edges, pos = random_graph(14, 34, seed)
    kept, removed = A.cover_skeleton(edges, pos)
    rot = A.rotation_from_positions(n, kept, pos)
    assert A.is_planar_embedding(rot) and nx.check_planarity(nx_graph(n, kept))[0]
    p = A.planarize(n, edges, kept, removed, rot, A.insertion_order(removed, pos, "random", seed))
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(edges) and nx.check_planarity(rotation_graph(p))[0]


@pytest.mark.parametrize("seed", range(10))
def test_delaunay_plus_extras_planarization_is_planar_and_not_far_above_the_straight_line_crossings(seed):
    g = S.make_delaunay(60, 4, seed)
    kept, removed = A.cover_skeleton(g.edges, g.pos)
    p = A.planarize(g.n, g.edges, kept, removed, A.rotation_from_positions(g.n, kept, g.pos), removed)
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(g.edges)
    straight = {tuple(e): 0 for e in removed}
    for i, j in A.crossing_pairs(g.edges, g.pos):
        for e in (g.edges[i], g.edges[j]):
            if e in straight:
                straight[e] += 1
    assert p.crossings <= sum(straight.values()) + len(removed)                                    # grobe Schranke: nie mehr als die Streckenkreuzungen der entfernten Kanten plus eine je Kante


def test_classic_crossing_numbers_are_found_and_proven_where_the_skewness_matches():
    for name, proven in (("K5", True), ("K3,3", True), ("K6", True), ("K3,4", True), ("K4,4", True), ("Petersen", True), ("K3,5", False), ("K7", False)):
        g = S.make_classic(name)
        best = min(A.planarize(g.n, g.edges, *k, A.rotation_from_networkx(g.n, k[0]), k[1]).crossings
                   for k in (A.greedy_planar_subgraph(g.n, A.edge_order(g.edges, g.pos, "random", s)) for s in range(40)))
        assert best == S.KNOWN_CROSSING_NUMBER[name], name
        if proven and g.m <= 16:
            skew = A.skewness_exact(g.n, g.edges, limit=6)
            assert skew <= best                                                                    # untere Schranke: Schiefheit
            if name != "K3,5":
                assert skew == best                                                                # gleich: die Kreuzungszahl ist bewiesen


def test_k5_and_k33_need_at_least_one_crossing_because_they_are_not_planar():
    for name in ("K5", "K3,3"):
        g = S.make_classic(name)
        assert not nx.check_planarity(nx_graph(g.n, g.edges))[0]
        kept, removed = A.greedy_planar_subgraph(g.n, g.edges)
        assert A.planarize(g.n, g.edges, kept, removed, A.rotation_from_networkx(g.n, kept), removed).crossings == 1


@pytest.mark.parametrize("seed", range(12))
def test_a_planar_graph_is_its_own_planarization(seed):
    g = S.make_delaunay(40, 0, seed)
    kept, removed = A.skeleton(g.n, g.edges, g.pos, "length", seed)
    assert removed == [] and set(kept) == set(g.edges)
    p = A.planarize(g.n, g.edges, kept, removed, A.rotation_from_networkx(g.n, kept), removed)
    assert p.crossings == 0 and A.restore_edges(p) == set(g.edges)


def test_euler_face_count_of_the_planarization():
    g = S.make_delaunay(50, 5, 2)
    kept, removed = A.cover_skeleton(g.edges, g.pos)
    p = A.planarize(g.n, g.edges, kept, removed, A.rotation_from_positions(g.n, kept, g.pos), removed)
    faces, _ = A.faces_from_rotation(p.rot)
    nodes = g.n + p.crossings
    edges = sum(len(nb) for nb in p.rot.values()) // 2
    assert len(faces) == edges - nodes + 2 and edges == g.m + 2 * p.crossings                       # jede Kreuzung unterteilt zwei Kanten: aus 2 werden 4
