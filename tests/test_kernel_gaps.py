"""Zusatztests aus der Mutationsprüfung: Fälle, die die ersten Tests nicht berührten (Grenze des Aufzählens der Schiefheit, Reihenfolge der Hilfsknoten)."""

import pln_algorithm as A


def complete(n):
    return tuple((i, j) for i in range(n) for j in range(i + 1, n))


def test_skewness_exact_at_the_limit():
    assert A.skewness_exact(5, complete(5), limit=1) == 1                                       # genau an der Grenze
    assert A.skewness_exact(5, complete(5), limit=0) is None                                    # eine Kante wäre nötig, null erlaubt
    assert A.skewness_exact(5, complete(5), limit=2) == 1
    assert A.skewness_exact(6, complete(6), limit=3) == 3 and A.skewness_exact(6, complete(6), limit=2) is None


def test_dummies_are_listed_in_ascending_order():
    n = 6
    edges = complete(6)
    kept, removed = A.greedy_planar_subgraph(n, edges)
    p = A.planarize(n, edges, kept, removed, A.rotation_from_networkx(n, kept), removed)
    assert p.crossings >= 3
    assert p.dummies == sorted(p.dummies) and p.dummies == list(range(6, 6 + p.crossings))


def test_skewness_exact_considers_the_last_edge():
    import networkx as nx
    edges = sorted(nx.icosahedral_graph().edges()) + [(0, 3)]                                   # maximal planar plus eine Kante: nur diese eine Kante (die letzte) macht den Graphen planar
    assert [i for i in range(len(edges)) if A.is_planar(12, edges[:i] + edges[i + 1:])] == [len(edges) - 1]
    assert A.skewness_exact(12, edges, limit=1) == 1
