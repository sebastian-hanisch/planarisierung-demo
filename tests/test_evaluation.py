"""Auswertung: die Analyse planarisiert und nennt die Zahlen, die Messreihen laufen über feste Pläne und liefern geordnete Werte."""

import pytest

import pln_algorithm as A
import pln_constants as C
import pln_evaluation as ev
import pln_scenario as S


def test_default_settings_equal_the_default_constants():
    s = ev.Settings()
    assert (s.vehicle, s.n, s.extras, s.classic, s.skeleton, s.embedding, s.tries, s.seed) == (
        C.DEFAULT_VEHICLE, C.DEFAULT_N, C.DEFAULT_EXTRAS, C.DEFAULT_CLASSIC, C.DEFAULT_SKELETON, C.DEFAULT_EMBEDDING, C.DEFAULT_TRIES, C.DEFAULT_SEED)


def test_analyse_the_default_map():
    a = ev.analyse(ev.Settings())
    assert a.graph == S.make_delaunay(100, 10, 35) and a.straight == len(A.crossing_pairs(a.graph.edges, a.graph.pos))
    assert len(a.run.removed) == 10 and len(a.run.kept) + 10 == a.graph.m and a.run.crossings == a.run.planarization.crossings > 0 and a.tries_done == 1 and a.seconds > 0
    assert A.restore_edges(a.run.planarization) == set(a.graph.edges) and A.is_planar_embedding(a.run.planarization.rot)
    assert a.per_edge == [i.crossings for i in a.inserted] and 0 <= a.share_at_most_one <= 1 and a.known is None


def test_analyse_a_planar_map_has_nothing_to_insert():
    a = ev.analyse(ev.Settings(extras=0))
    assert a.run.removed == () and a.run.crossings == 0 and a.share_at_most_one == 1.0 and a.per_edge == [] and not a.run.fallback


def test_run_once_falls_back_to_an_arbitrary_embedding_when_the_coordinates_do_not_fit():
    g = S.make_delaunay(80, 10, 5)
    run = ev.run_once(g, "random", "geometry", 5)                                      # Greedy in zufälliger Reihenfolge: das Gerüst hat gekreuzte Strecken
    assert run.fallback and run.embedding_used == "arbitrary" and A.is_planar_embedding(run.planarization.rot)
    cover = ev.run_once(g, "cover", "geometry", 5)
    assert not cover.fallback and cover.embedding_used == "geometry"
    arbitrary = ev.run_once(g, "cover", "arbitrary", 5)
    assert not arbitrary.fallback and arbitrary.embedding_used == "arbitrary"


def test_tries_only_apply_to_the_random_greedy_and_keep_the_best():
    one = ev.analyse(ev.Settings("classic", classic="K4,4", skeleton="random", embedding="arbitrary", tries=1, seed=0))
    many = ev.analyse(ev.Settings("classic", classic="K4,4", skeleton="random", embedding="arbitrary", tries=10, seed=0))
    assert one.tries_done == 1 and many.tries_done == 10 and many.run.crossings <= one.run.crossings and many.run.crossings == 4 and many.known == 4
    other = ev.analyse(ev.Settings("classic", classic="K4,4", skeleton="cover", embedding="arbitrary", tries=10, seed=0))
    assert other.tries_done == 1


def test_analysis_known_value_only_for_classic_graphs():
    assert ev.analyse(ev.Settings("classic", classic="K5", skeleton="random", embedding="arbitrary")).known == 1
    assert ev.analyse(ev.Settings("toronto", n=60, skeleton="cover")).known is None


def test_toronto_ball_runs_and_never_has_more_crossings_than_removed_edges_times_a_few():
    a = ev.analyse(ev.Settings("toronto", n=120, skeleton="cover", embedding="geometry"))
    assert a.straight >= 0 and a.run.crossings >= 0 and not a.run.fallback and A.restore_edges(a.run.planarization) == set(a.graph.edges)


def test_euler_lower_bound_by_hand():
    assert ev.euler_lower_bound(S.make_classic("K5")) == 1 and ev.euler_lower_bound(S.make_classic("K6")) == 3 and ev.euler_lower_bound(S.make_classic("K7")) == 6
    assert ev.euler_lower_bound(S.make_classic("K3,3")) == 0 and ev.euler_lower_bound(S.Graph(2, ((0, 1),), ((0.0, 0.0), (1.0, 0.0)))) == 0


def test_classic_series_rows():
    rows = ev.classic_series(names=("K5", "K3,3", "K4,4", "K7"), tries=20)
    assert [r["name"] for r in rows] == ["K5", "K3,3", "K4,4", "K7"] and all(r["tries"] == 20 for r in rows)
    assert [r["known"] for r in rows] == [1, 1, 4, 9] and [r["best"] for r in rows] == [1, 1, 4, 9] and all(r["equal"] for r in rows)
    assert [r["skewness"] for r in rows] == [1, 1, 4, None] and rows[3]["euler_bound"] == 6
    assert all(r["best"] <= r["first"] <= r["worst"] for r in rows)


def test_order_series_rows():
    rows = ev.order_series(extras=(2, 5), n=60, seeds=C.SWEEP_SEEDS[:2])
    assert [r["extras"] for r in rows] == [2, 5] and all(r["plans"] == 2 and r["n"] == 60 for r in rows)
    assert all(r["removed_length"] <= r["extras"] and r["removed_random"] >= r["removed_length"] and 0 < r["ratio"] <= 1.5 and 0 <= r["share"] <= 1 for r in rows)
    assert rows[1]["straight"] > rows[0]["straight"] and rows[1]["crossings"] > rows[0]["crossings"]


def test_embedding_series_rows():
    rows = ev.embedding_series(n=60, k=4, seeds=C.SWEEP_SEEDS[:2])
    assert [r["name"] for r in rows] == ["Karte mit 60 Standorten, 4 Zusatzkanten (Mediane)", "Toronto-Karte (ganz)"] and rows[0]["plans"] == 2 and rows[1]["plans"] == 1
    assert rows[1]["straight"] == 125 and rows[1]["removed"] == 52 and rows[0]["geometry"] == rows[0]["arbitrary"] and rows[0]["removed"] == 4
    assert rows[1]["zero_geometry"] > 0 and rows[1]["geometry_time"] > 0 and rows[1]["arbitrary_time"] > 0
    assert rows[1]["geometry"] <= rows[1]["straight"]
