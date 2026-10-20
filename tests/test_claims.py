"""Jede Zahl der README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie in der App.

Klassische Graphen (die beste von 100 Reihenfolgen) und die Toronto-Karte mit Gerüst aus der Überdeckung und Einbettung aus den Koordinaten sind exakt; bei den Delaunay-Karten (scipy/Qhull) gelten Bänder,
weil eine andere Qhull-Fassung bei fast entarteten Punkten eine andere Triangulierung wählen könnte, und Zahlen, die von der beliebigen Einbettung von `networkx` abhängen, gelten nur als Bänder.
Zeiten nur als weite Obergrenzen."""

import networkx as nx
import pytest

import pln_algorithm as A
import pln_constants as C
import pln_evaluation as ev
import pln_scenario as S


@pytest.fixture(scope="module")
def classic():
    return ev.classic_series()


@pytest.fixture(scope="module")
def order():
    return ev.order_series()


@pytest.fixture(scope="module")
def embedding():
    return ev.embedding_series()


def test_the_series_use_the_documented_fixed_plans_and_limits():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100005)) and C.CLASSIC_TRIES == 100 and C.ORDER_N == 100 and C.ORDER_EXTRAS == (1, 2, 5, 10, 20, 40)
    assert C.EMBEDDING_N == 100 and C.EMBEDDING_EXTRAS == 10 and C.EXACT_SKEWNESS_MAX_M == 16 and C.INSERT_ORDER == "random"
    assert (C.N_MIN, C.N_MAX, C.EXTRAS_MAX, C.TRIES_MAX) == (20, 300, 40, 20) and C.CLASSIC_NAMES == ("K5", "K6", "K7", "K3,3", "K3,4", "K3,5", "K4,4", "Petersen")


# --- Klassische Graphen --------------------------------------------------------------------------------------------------------------------------


def test_classic_crossing_numbers_are_found_with_100_orders(classic):
    assert [r["name"] for r in classic] == list(C.CLASSIC_NAMES) and all(r["tries"] == 100 for r in classic)
    assert [r["known"] for r in classic] == [1, 3, 9, 1, 2, 4, 4, 2] and [r["best"] for r in classic] == [1, 3, 9, 1, 2, 4, 4, 2] and all(r["equal"] for r in classic)


def test_one_order_is_enough_for_all_but_k44(classic):
    by = {r["name"]: r for r in classic}
    assert all(by[name]["first"] == by[name]["known"] for name in by if name != "K4,4")
    assert 4 <= by["K4,4"]["first"] <= 6 and by["K4,4"]["first"] > 4                          # gemessen 5 statt 4 (hängt von der Einbettung ab)
    assert all(r["best"] <= r["first"] <= r["worst"] for r in classic)


def test_skewness_is_a_lower_bound_and_proves_most_crossing_numbers(classic):
    by = {r["name"]: r for r in classic}
    assert [by[n]["skewness"] for n in C.CLASSIC_NAMES] == [1, 3, None, 1, 2, 3, 4, 2] and by["K7"]["euler_bound"] == 6
    assert all(r["skewness"] <= r["best"] for r in classic if r["skewness"] is not None)
    assert [n for n in by if by[n]["skewness"] == by[n]["best"]] == ["K5", "K6", "K3,3", "K3,4", "K4,4", "Petersen"]       # dort ist die Kreuzungszahl bewiesen
    assert by["K3,5"]["skewness"] == 3 and by["K3,5"]["best"] == 4


# --- Reihenfolge und Strecken (Karten mit 100 Standorten) ------------------------------------------------------------------------------------


def test_the_order_of_the_greedy_decides(order):
    assert [r["extras"] for r in order] == [1, 2, 5, 10, 20, 40] and all(r["plans"] == 5 and r["n"] == 100 for r in order)
    assert [r["removed_random"] for r in order] == pytest.approx([1, 25, 31, 35, 78, 112], abs=6)
    assert [r["removed_length"] for r in order] == pytest.approx([1, 2, 5, 10, 22, 41], abs=2)
    assert all(r["removed_length"] <= r["extras"] + 2 for r in order) and all(r["removed_random"] >= 2 * r["removed_length"] for r in order[1:])
    assert order[2]["removed_random"] >= 4 * order[2]["extras"]                               # 5 Zusatzkanten: zufällig etwa das Sechsfache


def test_planarization_needs_about_half_the_straight_line_crossings(order):
    assert [r["straight"] for r in order] == pytest.approx([7, 20, 48, 103, 219, 575], rel=0.12)
    assert [r["crossings"] for r in order] == pytest.approx([6, 12, 33, 61, 120, 304], rel=0.12)
    assert all(r["crossings"] < r["straight"] for r in order) and all(0.45 <= r["ratio"] <= 0.9 for r in order) and all(0.45 <= r["ratio"] <= 0.7 for r in order[2:])


def test_random_far_edges_are_far_from_one_planar(order):
    assert all(r["share"] <= 0.2 for r in order) and all(r["per_edge"] >= 5 for r in order) and order[-1]["per_edge"] >= 7


# --- Einbettung und Toronto -----------------------------------------------------------------------------------------------------------------


def test_embedding_does_not_matter_for_a_triangulation(embedding):
    karte = embedding[0]
    assert karte["plans"] == 5 and karte["removed"] == 10 and karte["geometry"] == karte["arbitrary"] and 50 <= karte["geometry"] <= 75 and 90 <= karte["straight"] <= 120
    assert karte["zero_geometry"] == 0


def test_toronto_in_the_coordinate_embedding(embedding):
    toronto = embedding[1]
    assert (toronto["plans"], toronto["straight"], toronto["removed"]) == (1, 125, 52) and toronto["geometry"] == 35 and toronto["zero_geometry"] == 36
    assert 35 <= toronto["arbitrary"] <= 60 and toronto["geometry"] <= toronto["arbitrary"] and toronto["geometry"] * 3 < toronto["straight"]
    assert toronto["geometry_time"] < 30 and toronto["arbitrary_time"] < 30


def test_toronto_is_combinatorially_nonplanar_but_the_skeleton_is_planar():
    g = S.make_toronto()
    assert not nx.check_planarity(nx.Graph(list(g.edges)))[0]
    kept, removed = A.cover_skeleton(g.edges, g.pos)
    assert len(kept) == 7569 and len(removed) == 52 and A.crossing_pairs(kept, g.pos) == [] and nx.check_planarity(nx.Graph(kept))[0]
    skeleton_graph = nx.Graph()
    skeleton_graph.add_nodes_from(range(g.n))
    skeleton_graph.add_edges_from(kept)
    assert nx.number_connected_components(skeleton_graph) == 15


# --- Presets -------------------------------------------------------------------------------------------------------------------------------------


def test_presets_hold_what_their_help_texts_say():
    by = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    default, rnd, many, toronto, k44 = (by[name] for name in C.PRESETS)
    assert 125 <= default.straight <= 165 and len(default.run.removed) == 10 and 45 <= default.run.crossings <= 62 and default.run.crossings < default.straight / 2
    assert len(rnd.run.removed) >= 4 * 10 and rnd.run.crossings > 4 * default.run.crossings
    assert many.run.crossings > default.run.crossings and many.run.crossings < many.straight and len(many.run.removed) >= 30
    assert (toronto.straight, len(toronto.run.removed), toronto.run.crossings, toronto.graph.n) == (13, 5, 4, 250) and toronto.run.crossings < toronto.straight
    assert k44.run.crossings == 4 and k44.known == 4 and k44.tries_done == 10 and k44.straight == 36
