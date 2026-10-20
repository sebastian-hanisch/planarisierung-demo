"""Szenario: Delaunay-Karten mit Zusatzkanten, die Toronto-Karte (OpenStreetMap, ODbL, Auszug aus `graph-zeichnen-demo`) und klassische Graphen mit bekannter Kreuzungszahl.

Ein Graph hat Knoten 0 bis n − 1, Kanten (u, v) mit u < v und eine Lage in der Ebene. Zufall nur aus `numpy.random.default_rng(seed)` und `random.Random(seed)`."""

from __future__ import annotations

import json
import math
import random
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class Graph:
    n: int
    edges: tuple[tuple[int, int], ...]
    pos: tuple[tuple[float, float], ...]
    name: str = ""
    extras: tuple[tuple[int, int], ...] = ()          # bei Karten mit Zusatzkanten: die zusätzlich eingefügten Kanten

    @property
    def m(self) -> int:
        return len(self.edges)


def normalize(edges) -> tuple[tuple[int, int], ...]:
    return tuple(sorted({(min(u, v), max(u, v)) for u, v in edges if u != v}))


def delaunay_edges(points: np.ndarray) -> list[tuple[int, int]]:
    """Kanten der Delaunay-Triangulierung (scipy/Qhull)."""
    from scipy.spatial import Delaunay

    found = set()
    for simplex in Delaunay(points).simplices:
        a, b, c = (int(x) for x in simplex)
        found.update({(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))})
    return sorted(found)


def make_delaunay(n: int, extras: int, seed: int) -> Graph:
    """Zufällige Standorte im Einheitsquadrat, alle Delaunay-Kanten (planar) und `extras` zufällige Zusatzkanten zwischen Standorten ohne Kante (Zufallspaare mit `random.Random(seed)`)."""
    points = np.random.default_rng(seed).random((n, 2))
    base = delaunay_edges(points)
    have = set(base)
    rng = random.Random(seed)
    added: set[tuple[int, int]] = set()
    while len(added) < extras:
        u, v = rng.sample(range(n), 2)
        e = (min(u, v), max(u, v))
        if e not in have and e not in added:
            added.add(e)
    pos = tuple((round(float(x), 6), round(float(y), 6)) for x, y in points)
    return Graph(n, normalize(have | added), pos, f"Karte mit {n} Standorten und {extras} Zusatzkanten", tuple(sorted(added)))


CLASSICS = {
    "K5": ("vollständig", 5, 1),
    "K6": ("vollständig", 6, 3),
    "K7": ("vollständig", 7, 9),
    "K3,3": ("bipartit", (3, 3), 1),
    "K3,4": ("bipartit", (3, 4), 2),
    "K3,5": ("bipartit", (3, 5), 4),
    "K4,4": ("bipartit", (4, 4), 4),
    "Petersen": ("petersen", 10, 2),
}
KNOWN_CROSSING_NUMBER = {name: spec[2] for name, spec in CLASSICS.items()}      # Kreuzungszahlen aus dem Gedächtnis (Guy, Zarankiewicz): vor dem Zitieren zu prüfen


def make_classic(name: str) -> Graph:
    """K5, K6, K7, K3,3, K3,4, K3,5, K4,4, Petersen; Lage auf einem Kreis (die Streckenzeichnung ist nur eine Ausgangslage)."""
    kind, size, _ = CLASSICS[name]
    if kind == "vollständig":
        n = size
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    elif kind == "bipartit":
        a, b = size
        n = a + b
        edges = [(i, a + j) for i in range(a) for j in range(b)]
    else:
        n = 10
        edges = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    pos = tuple((round(math.cos(2 * math.pi * i / n), 6), round(math.sin(2 * math.pi * i / n), 6)) for i in range(n))
    return Graph(n, normalize(edges), pos, name)


@lru_cache(maxsize=1)
def _toronto_raw() -> tuple[tuple[tuple[float, float], ...], tuple[tuple[int, int], ...]]:
    payload = json.loads((DATA / "toronto_campus.json").read_text(encoding="utf-8"))
    pos = tuple((float(x), float(y)) for x, y in payload["nodes_xy_m"])
    return pos, normalize((u, v) for u, v, _ in payload["arcs"])


def _relabel(keep: list[int], pos, edges) -> tuple[tuple[tuple[float, float], ...], tuple[tuple[int, int], ...]]:
    index = {v: i for i, v in enumerate(keep)}
    return tuple(pos[v] for v in keep), normalize((index[u], index[v]) for u, v in edges if u in index and v in index)


def make_toronto(n: int | None = None) -> Graph:
    """Straßenkarte (Meter): ohne Angabe die größte Komponente um Knoten 0 (5 072 Knoten), sonst die n Knoten um die Mitte der Karte (Breitensuche ab dem Knoten nächst dem Median der Lage, Nachbarn aufsteigend)."""
    pos, edges = _toronto_raw()
    adj: dict[int, list[int]] = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    if n is None:
        seen = {0}
        stack = [0]
        while stack:
            x = stack.pop()
            for y in adj.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        keep = sorted(seen)
        p, e = _relabel(keep, pos, edges)
        return Graph(len(keep), e, p, "Toronto-Karte")
    arr = np.array(pos)
    centre = np.median(arr, axis=0)
    start = int(np.argmin(np.linalg.norm(arr - centre, axis=1)))
    order = [start]
    seen = {start}
    queue = deque([start])
    while queue and len(order) < n:
        x = queue.popleft()
        for y in sorted(adj.get(x, ())):
            if y not in seen and len(order) < n:
                seen.add(y)
                order.append(y)
                queue.append(y)
    keep = sorted(order)
    p, e = _relabel(keep, pos, edges)
    return Graph(len(keep), e, p, f"Straßenausschnitt mit {len(keep)} Knoten")


def make_graph(vehicle: str, n: int, extras: int, classic: str, seed: int) -> Graph:
    """Deterministisch aus den Argumenten: gleiche Eingabe, gleicher Graph."""
    if vehicle == "delaunay":
        return make_delaunay(n, extras, seed)
    if vehicle == "toronto":
        return make_toronto(n)
    if vehicle == "classic":
        return make_classic(classic)
    raise ValueError(vehicle)
