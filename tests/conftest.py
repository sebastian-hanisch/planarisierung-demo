"""Gemeinsame Fixtures: die Mini-Graphen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def k4_square():
    """K4 mit den Ecken des Einheitsquadrats gezeichnet: Knoten 0 (0,0), 1 (1,0), 2 (1,1), 3 (0,1); die zwei Diagonalen (0,2) und (1,3) kreuzen sich als Strecken (1 Streckenkreuzung),
    K4 ist aber planar (die Diagonale (0,2) lässt sich außen herumführen)."""
    edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    pos = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    return 4, edges, pos


@pytest.fixture
def octahedron():
    """Oktaeder ohne die drei Achsen: Knoten 0 bis 5, nicht benachbart sind die Paare (0,5), (1,4), (2,3); planare Zeichnung: äußeres Dreieck 0, 1, 2, inneres Dreieck 3, 4, 5 (3 nahe der Seite 0–1,
    4 nahe 0–2, 5 nahe 1–2). Die Kante (0,5) wird nicht mitgezeichnet; sie braucht mindestens eine Kreuzung."""
    pos = ((0.0, 0.0), (6.0, 0.0), (3.0, 5.0), (3.0, 1.2), (2.0, 2.8), (4.0, 2.8))
    edges = ((0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (0, 3), (1, 3), (0, 4), (2, 4), (1, 5), (2, 5))
    return 6, tuple(sorted(edges)), pos


def random_graph(n: int, m: int, seed: int):
    rng = random.Random(seed)
    edges = set()
    while len(edges) < m:
        u, v = rng.sample(range(n), 2)
        edges.add((min(u, v), max(u, v)))
    pos = tuple((rng.random(), rng.random()) for _ in range(n))
    return n, tuple(sorted(edges)), pos
