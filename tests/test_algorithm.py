"""Einheiten des Kerns an handgerechneten Mini-Graphen (eine Regel = eine Funktion)."""

import itertools

import pytest

import pln_algorithm as A
from conftest import random_graph


# --- Geometrie ---------------------------------------------------------------------------------------------------------------------------------


def test_segments_cross_by_hand():
    assert A.segments_cross((0, 0), (2, 2), (0, 2), (2, 0))
    assert not A.segments_cross((0, 0), (1, 0), (2, 0), (3, 0))              # kollinear, getrennt
    assert not A.segments_cross((0, 0), (2, 0), (1, 0), (1, 1))              # T-Stück: Berührung, keine Kreuzung
    assert not A.segments_cross((1, 0), (1, 1), (0, 0), (2, 0))              # dasselbe, anders herum
    assert not A.segments_cross((0, 0), (1, 1), (1, 1), (2, 0))              # gemeinsamer Endpunkt
    assert not A.segments_cross((0, 0), (1, 0), (0, 1), (1, 1))              # parallel


def test_crossing_pairs_by_hand(k4_square):
    n, edges, pos = k4_square
    assert A.crossing_pairs(edges, pos) == [(1, 4)]                           # (0,2) und (1,3)
    assert A.crossing_pairs(edges[:3] + edges[3:4], pos) == []


def test_crossing_pairs_agrees_with_the_double_loop_on_random_drawings():
    for seed in range(60):
        n, edges, pos = random_graph(9, 14, seed)
        brute = [(i, j) for i, j in itertools.combinations(range(len(edges)), 2)
                 if len(set(edges[i]) | set(edges[j])) == 4 and A.segments_cross(pos[edges[i][0]], pos[edges[i][1]], pos[edges[j][0]], pos[edges[j][1]])]
        assert A.crossing_pairs(edges, pos) == brute


# --- Planarität, Reihenfolgen, Gerüst ---------------------------------------------------------------------------------------------------------------


def complete(n):
    return tuple((i, j) for i in range(n) for j in range(i + 1, n))


def test_is_planar_by_hand(k4_square, octahedron):
    assert A.is_planar(4, k4_square[1]) and A.is_planar(6, octahedron[1]) and A.is_planar(0, ()) and A.is_planar(3, ())
    assert not A.is_planar(5, complete(5)) and not A.is_planar(6, tuple((i, 3 + j) for i in range(3) for j in range(3)))
    petersen = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    assert not A.is_planar(10, tuple((min(u, v), max(u, v)) for u, v in petersen))
    assert A.is_planar(5, tuple((u, v) for u, v in complete(5) if (u, v) != (0, 1)))                      # K5 ohne eine Kante ist planar


def test_edge_order_by_hand(octahedron):
    pos = ((0.0, 0.0), (3.0, 0.0), (1.0, 0.0), (10.0, 0.0))
    edges = [(0, 1), (0, 2), (0, 3), (2, 3)]
    assert A.edge_order(edges, pos, "length") == [(0, 2), (0, 1), (2, 3), (0, 3)]                          # Längen 1, 3, 7, 10
    r = A.edge_order(edges, pos, "random", 5)
    assert sorted(r) == sorted(edges) and r == A.edge_order(edges, pos, "random", 5) and r != A.edge_order(edges, pos, "random", 6)
    with pytest.raises(ValueError):
        A.edge_order(edges, pos, "alphabetisch")
    tie = A.edge_order([(1, 2), (0, 1)], ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)), "length")
    assert tie == [(0, 1), (1, 2)]                                                                           # gleiche Länge: die kleinere Kante zuerst


def test_greedy_planar_subgraph_on_k5_and_k33():
    kept, rejected = A.greedy_planar_subgraph(5, complete(5))
    assert len(kept) == 9 and rejected == [(3, 4)]                                                           # die letzte Kante macht K5 nichtplanar
    k33 = tuple((i, 3 + j) for i in range(3) for j in range(3))
    kept, rejected = A.greedy_planar_subgraph(6, k33)
    assert len(kept) == 8 and rejected == [(2, 5)]
    kept, rejected = A.greedy_planar_subgraph(4, complete(4))
    assert len(kept) == 6 and rejected == []


def test_greedy_planar_subgraph_depends_on_the_order():
    order = [(3, 4)] + [e for e in complete(5) if e != (3, 4)]
    kept, rejected = A.greedy_planar_subgraph(5, order)
    assert rejected == [(2, 4)] and (3, 4) in kept                                                           # eine andere Kante wird abgelehnt


def test_cover_skeleton_by_hand(k4_square):
    n, edges, pos = k4_square
    kept, removed = A.cover_skeleton(edges, pos)
    assert removed == [(0, 2)] and kept == [(0, 1), (0, 3), (1, 2), (1, 3), (2, 3)]                           # beide Diagonalen haben eine Kreuzung: Gleichstand, der kleinere Index (0,2) fällt
    assert A.crossing_pairs(kept, pos) == []
    assert A.cover_skeleton(edges[:1], pos) == ([(0, 1)], [])


def test_cover_skeleton_removes_the_edge_with_most_crossings_first():
    # eine lange waagerechte Kante (0,1) wird von drei senkrechten Kanten gekreuzt: sie fällt als einzige
    pos = ((0.0, 0.0), (10.0, 0.0), (2.0, -1.0), (2.0, 1.0), (5.0, -1.0), (5.0, 1.0), (8.0, -1.0), (8.0, 1.0))
    edges = [(0, 1), (2, 3), (4, 5), (6, 7)]
    kept, removed = A.cover_skeleton(edges, pos)
    assert removed == [(0, 1)] and kept == [(2, 3), (4, 5), (6, 7)]


def test_skeleton_dispatch_and_cover_has_a_crossing_free_drawing():
    n, edges, pos = random_graph(12, 30, 4)
    kept, removed = A.skeleton(n, edges, pos, "cover")
    assert A.crossing_pairs(kept, pos) == [] and A.is_planar(n, kept) and sorted(kept + removed) == sorted(edges)
    kept2, removed2 = A.skeleton(n, edges, pos, "length")
    assert A.is_planar(n, kept2) and sorted(kept2 + removed2) == sorted(edges)
    with pytest.raises(ValueError):
        A.skeleton(n, edges, pos, "mitte")


def test_skewness_exact_by_hand():
    k33 = tuple((i, 3 + j) for i in range(3) for j in range(3))
    assert A.skewness_exact(5, complete(5)) == 1 and A.skewness_exact(6, k33) == 1 and A.skewness_exact(6, complete(6)) == 3
    assert A.skewness_exact(4, complete(4)) == 0 and A.skewness_exact(3, ()) == 0
    assert A.skewness_exact(7, complete(7), limit=3) is None


# --- Einbettung --------------------------------------------------------------------------------------------------------------------------------


def test_rotation_from_positions_by_hand():
    pos = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))
    rot = A.rotation_from_positions(5, ((0, 1), (0, 2), (0, 3), (0, 4)), pos)
    assert rot[0] == [4, 1, 2, 3]                                                                            # Winkel −90°, 0°, 90°, 180°
    assert rot[1] == [0] and rot[2] == [0]


def test_faces_from_rotation_by_hand():
    tri = {0: [1, 2], 1: [2, 0], 2: [0, 1]}
    faces, face_of = A.faces_from_rotation(tri)
    assert len(faces) == 2 and all(len(f) == 3 for f in faces) and len(face_of) == 6
    assert A.faces_from_rotation({0: [1], 1: [0], 2: []})[0] == [[0, 1]] and A.faces_from_rotation({0: [], 1: []}) == ([], {})
    path = {0: [1], 1: [0, 2], 2: [1]}
    assert len(A.faces_from_rotation(path)[0]) == 1


def test_is_planar_embedding_by_hand(k4_square):
    n, edges, pos = k4_square
    five = [e for e in edges if e != (0, 2)]
    assert A.is_planar_embedding(A.rotation_from_positions(n, five, pos))
    assert not A.is_planar_embedding(A.rotation_from_positions(n, edges, pos))                                # die Diagonalen kreuzen: keine Einbettung
    two_triangles = {0: [1, 2], 1: [2, 0], 2: [0, 1], 3: [4, 5], 4: [5, 3], 5: [3, 4]}
    assert A.is_planar_embedding(two_triangles) and A.is_planar_embedding({0: [], 1: []}) and A.is_planar_embedding({})
    assert A.is_planar_embedding({**two_triangles, 6: []})                                                    # isolierter Knoten zählt nicht


def test_rotation_from_networkx_is_a_planar_embedding_and_rejects_nonplanar(octahedron):
    n, edges, _ = octahedron
    rot = A.rotation_from_networkx(n, edges)
    assert A.is_planar_embedding(rot) and sorted(sum(rot.values(), [])) == sorted(v for e in edges for v in e)
    assert A.rotation_from_networkx(3, ()) == {0: [], 1: [], 2: []}
    with pytest.raises(ValueError):
        A.rotation_from_networkx(5, complete(5))


def test_component_count_by_hand():
    assert A.component_count({0: [1], 1: [0], 2: [], 3: [4], 4: [3]}) == 3 and A.component_count({}) == 0


# --- Einsetzen -----------------------------------------------------------------------------------------------------------------------------------


def test_insert_into_a_shared_face_needs_no_crossing(k4_square):
    n, edges, pos = k4_square
    kept, removed = A.cover_skeleton(edges, pos)
    p = A.planarize(n, edges, kept, removed, A.rotation_from_positions(n, kept, pos), removed)
    assert p.crossings == 0 and p.inserted[0].path == [0, 2] and p.inserted[0].crossed == [] and A.is_planar_embedding(p.rot)
    assert A.restore_edges(p) == set(edges)


def test_insert_with_one_crossing_in_the_octahedron(octahedron):
    n, edges, pos = octahedron
    assert A.crossing_pairs(edges, pos) == [] and A.is_planar_embedding(A.rotation_from_positions(n, edges, pos))
    full = tuple(sorted(edges + ((0, 5),)))
    p = A.start_planarization(n, full, edges, A.rotation_from_positions(n, edges, pos))
    ins = A.insert_edge(p, (0, 5))
    assert ins.crossings == 1 and p.crossings == 1 and p.dummies == [6] and ins.path[0] == 0 and ins.path[-1] == 5 and len(ins.path) == 3
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(full) and sorted(A.crossings_per_edge(p)).count(1) == 2
    assert sum(A.crossings_per_edge(p)) == 2 * p.crossings                                                    # jede Kreuzung gehört zu zwei Kanten
    a, b = p.midpoints[6]
    assert {a, b} <= set(range(6)) and (min(a, b), max(a, b)) in set(edges) and p.rot[6] != []


def test_insertion_connects_components_without_crossing():
    rot = {0: [1], 1: [0], 2: [3], 3: [2], 4: []}
    edges = ((0, 1), (0, 2), (0, 4), (2, 3))
    p = A.start_planarization(5, edges, [(0, 1), (2, 3)], rot)
    assert A.insert_edge(p, (0, 2)).crossings == 0 and A.insert_edge(p, (0, 4)).crossings == 0
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(edges) and p.rot[4] == [0]


def test_insert_rejects_loops_and_existing_edges(octahedron):
    n, edges, pos = octahedron
    p = A.start_planarization(n, tuple(sorted(edges + ((0, 5),))), edges, A.rotation_from_positions(n, edges, pos))
    with pytest.raises(ValueError):
        A.insert_edge(p, (0, 1))
    A.insert_edge(p, (0, 5))
    with pytest.raises(ValueError):
        A.insert_edge(p, (0, 5))


def test_planarize_k5_k33_k6_by_hand():
    k33 = tuple((i, 3 + j) for i in range(3) for j in range(3))
    for n, edges, expected in ((5, complete(5), 1), (6, k33, 1)):
        kept, removed = A.greedy_planar_subgraph(n, edges)
        p = A.planarize(n, edges, kept, removed, A.rotation_from_networkx(n, kept), removed)
        assert p.crossings == expected and A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(edges)
    best = min(A.planarize(6, complete(6), *k, A.rotation_from_networkx(6, k[0]), k[1]).crossings for k in (A.greedy_planar_subgraph(6, A.edge_order(complete(6), None, "random", s)) for s in range(10)))
    assert best == 3


def test_planarize_requires_the_order_to_be_a_permutation_of_the_removed_edges(k4_square):
    n, edges, pos = k4_square
    kept, removed = A.cover_skeleton(edges, pos)
    with pytest.raises(AssertionError):
        A.planarize(n, edges, kept, removed, A.rotation_from_positions(n, kept, pos), [])


def test_insertion_order_by_hand():
    pos = ((0.0, 0.0), (4.0, 0.0), (1.0, 0.0), (9.0, 0.0))
    removed = [(0, 3), (0, 1), (0, 2)]
    assert A.insertion_order(removed, pos, "given") == removed and A.insertion_order(removed, pos, "short") == [(0, 2), (0, 1), (0, 3)]
    r = A.insertion_order(removed, pos, "random", 3)
    assert sorted(r) == sorted(removed) and r == A.insertion_order(removed, pos, "random", 3)
    with pytest.raises(ValueError):
        A.insertion_order(removed, pos, "lang")


def test_dummy_positions_are_midpoints_of_the_crossed_edges(octahedron):
    n, edges, pos = octahedron
    p = A.start_planarization(n, tuple(sorted(edges + ((0, 5),))), edges, A.rotation_from_positions(n, edges, pos))
    A.insert_edge(p, (0, 5))
    dpos = A.dummy_positions(p, pos)
    a, b = p.midpoints[6]
    assert dpos[6] == ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2) and dpos[0] == pos[0] and len(dpos) == 7


def test_planarization_edges_after_a_crossing(octahedron):
    n, edges, pos = octahedron
    p = A.start_planarization(n, tuple(sorted(edges + ((0, 5),))), edges, A.rotation_from_positions(n, edges, pos))
    A.insert_edge(p, (0, 5))
    assert len(A.planarization_edges(p)) == len(edges) + 1 + 2                                                  # 12 Kanten, eine wird unterteilt (+1), die neue Kante hat zwei Stücke (+2): 15
