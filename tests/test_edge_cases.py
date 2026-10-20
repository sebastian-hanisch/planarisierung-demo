"""Randfälle: planare Netze, kleinste Netze, jedes Netz und jedes Gerüst an den Reglergrenzen, Toronto-Ausschnitt, klassische Graphen."""

import pytest

import pln_algorithm as A
import pln_constants as C
import pln_evaluation as ev
import pln_scenario as S


def test_empty_edge_set_and_single_edge():
    assert A.crossing_pairs((), ()) == [] and A.greedy_planar_subgraph(3, []) == ([], []) and A.cover_skeleton([], ()) == ([], [])
    p = A.start_planarization(2, ((0, 1),), [], {0: [], 1: []})
    ins = A.insert_edge(p, (0, 1))
    assert ins.crossings == 0 and p.rot == {0: [1], 1: [0]} and A.restore_edges(p) == {(0, 1)}


@pytest.mark.parametrize("vehicle", list(C.VEHICLES))
@pytest.mark.parametrize("skeleton", list(C.SKELETONS))
@pytest.mark.parametrize("embedding", list(C.EMBEDDINGS))
def test_every_combination_planarizes_the_smallest_net(vehicle, skeleton, embedding):
    a = ev.analyse(ev.Settings(vehicle, C.N_MIN, C.EXTRAS_MAX, "K5", skeleton, embedding, C.TRIES_MIN, 0))
    p = a.run.planarization
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(a.graph.edges)
    assert p.crossings == sum(a.per_edge) and a.run.embedding_used in C.EMBEDDINGS


@pytest.mark.parametrize("seed", [0, C.SEED_MAX])
@pytest.mark.parametrize("extras", [C.EXTRAS_MIN, C.EXTRAS_MAX])
@pytest.mark.parametrize("skeleton", list(C.SKELETONS))
def test_largest_map_at_the_regler_bounds(seed, extras, skeleton):
    a = ev.analyse(ev.Settings("delaunay", C.N_MAX if skeleton != "random" else 120, extras, skeleton=skeleton, embedding="arbitrary", seed=seed))
    p = a.run.planarization
    assert A.is_planar_embedding(p.rot) and A.restore_edges(p) == set(a.graph.edges)
    if extras == 0:
        assert a.run.crossings == 0 and a.run.removed == ()


@pytest.mark.parametrize("name", C.CLASSIC_NAMES)
def test_every_classic_graph_with_all_tries_at_the_limit(name):
    a = ev.analyse(ev.Settings("classic", classic=name, skeleton="random", embedding="arbitrary", tries=C.TRIES_MAX, seed=0))
    assert a.tries_done == C.TRIES_MAX and a.run.crossings >= S.KNOWN_CROSSING_NUMBER[name]                    # eine Planarisierung ist eine Zeichnung: nie weniger als die Kreuzungszahl
    assert a.run.crossings >= ev.euler_lower_bound(a.graph)


def test_toronto_ball_at_the_node_bounds():
    for n in (C.N_MIN, C.N_MAX):
        a = ev.analyse(ev.Settings("toronto", n=n, skeleton="cover", embedding="geometry"))
        assert a.graph.n == n and not a.run.fallback and A.restore_edges(a.run.planarization) == set(a.graph.edges)


def test_a_graph_with_isolated_nodes_and_two_components_is_planarized():
    pos = ((0.0, 0.0), (1.0, 0.0), (0.5, 1.0), (5.0, 0.0), (6.0, 0.0), (5.5, 1.0), (9.0, 9.0))
    edges = ((0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 5))
    kept, removed = A.cover_skeleton(edges, pos)
    assert removed == []
    p = A.planarize(7, edges, kept, removed, A.rotation_from_positions(7, kept, pos), removed)
    assert p.crossings == 0 and A.is_planar_embedding(p.rot) and p.rot[6] == []
    p2 = A.start_planarization(7, edges, edges[:3] + edges[3:6], A.rotation_from_positions(7, edges[:6], pos))
    assert A.insert_edge(p2, (2, 5)).crossings == 0                                                         # zwei Komponenten: keine Kreuzung nötig
    assert A.is_planar_embedding(p2.rot)


def test_a_bridge_edge_is_never_crossed_to_reach_the_other_side_of_itself():
    # Baum 0 – 1 – 2 – 3: eine einzige Fläche; die Kante (0,3) kann in dieser Fläche ohne Kreuzung eingesetzt werden
    pos = ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0))
    edges = ((0, 1), (0, 3), (1, 2), (2, 3))
    p = A.start_planarization(4, edges, [(0, 1), (1, 2), (2, 3)], A.rotation_from_positions(4, [(0, 1), (1, 2), (2, 3)], pos))
    assert A.insert_edge(p, (0, 3)).crossings == 0 and A.is_planar_embedding(p.rot)
