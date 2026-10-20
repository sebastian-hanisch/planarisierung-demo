"""Kern: fast planare Graphen planarisieren – ein planares Gerüst bilden, die übrigen Kanten über den kürzesten Weg im Dualgraphen einsetzen, Kreuzungen als Hilfsknoten.

Ein Graph hat Knoten 0 bis n − 1 und Kanten als Paare (u, v) mit u < v. Eine **Einbettung** ist ein **Rotationssystem**: je Knoten die Nachbarn in der Reihenfolge gegen den Uhrzeigersinn. Die Flächen entstehen,
indem man von der Halbkante (a, b) zu (b, c) geht, c = der Nachbar von b, der in der Liste vor a steht. **Einsetzen** einer Kante (s, t): kürzester Weg von einer Fläche an s zu einer Fläche an t im Dualgraphen,
jede gekreuzte Kante bekommt einen Hilfsknoten, das Rotationssystem wird dabei fortgeschrieben (nicht neu berechnet). Der Planaritätstest kommt aus `networkx` (Laufzeit-Abhängigkeit). Gleichstand entscheidet die kleinere Nummer;
Zufall nur aus `random.Random(seed)`."""

from __future__ import annotations

import itertools
import math
import random
from collections import deque
from dataclasses import dataclass, field

import networkx as nx

Edge = tuple[int, int]
Rotation = dict[int, list[int]]

# --- Geometrie: Streckenkreuzungen -----------------------------------------------------------------------------------------------------------------


def _orient(a, b, c) -> int:
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return int(v > 1e-12) - int(v < -1e-12)


def segments_cross(p1, p2, q1, q2) -> bool:
    """Schneiden sich die Strecken p1–p2 und q1–q2 echt (nicht nur in einem Endpunkt oder auf einer Geraden)?"""
    return _orient(p1, p2, q1) * _orient(p1, p2, q2) < 0 and _orient(q1, q2, p1) * _orient(q1, q2, p2) < 0


def crossing_pairs(edges, pos) -> list[tuple[int, int]]:
    """Indexpaare (i < j) der Kanten, die sich als Strecken kreuzen und keinen Endpunkt teilen; mit Filter über die Umrandungen der Strecken (Sortierung nach kleinstem x)."""
    boxes = [(min(pos[u][0], pos[v][0]), max(pos[u][0], pos[v][0]), min(pos[u][1], pos[v][1]), max(pos[u][1], pos[v][1])) for u, v in edges]
    order = sorted(range(len(edges)), key=lambda i: (boxes[i][0], i))
    found = []
    for ii, i in enumerate(order):
        for j in order[ii + 1:]:
            if boxes[j][0] > boxes[i][1]:
                break
            if boxes[j][2] > boxes[i][3] or boxes[j][3] < boxes[i][2]:
                continue
            a, b = edges[i]
            c, d = edges[j]
            if len({a, b, c, d}) == 4 and segments_cross(pos[a], pos[b], pos[c], pos[d]):
                found.append((min(i, j), max(i, j)))
    return sorted(found)


# --- Planarität, Gerüst ----------------------------------------------------------------------------------------------------------------------------


def is_planar(n: int, edges) -> bool:
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    return nx.check_planarity(g)[0]


def edge_order(edges, pos, kind: str, seed: int = 0) -> list[Edge]:
    """Reihenfolge der Kanten für den Greedy: 'random' (gemischt mit `random.Random(seed)`) oder 'length' (kürzeste Strecke zuerst, Gleichstand: kleinere Kante)."""
    es = list(edges)
    if kind == "random":
        random.Random(seed).shuffle(es)
        return es
    if kind == "length":
        return sorted(es, key=lambda e: (math.dist(pos[e[0]], pos[e[1]]), e))
    raise ValueError(kind)


def greedy_planar_subgraph(n: int, order) -> tuple[list[Edge], list[Edge]]:
    """Kanten der Reihe nach einfügen, solange der Graph planar bleibt. Rückgabe: (eingefügte Kanten in Einfügereihenfolge, abgelehnte Kanten in Ablehnungsreihenfolge). Der Teilgraph ist **maximal planar im Sinne des Einfügens**:
    jede abgelehnte Kante macht ihn (und jeden späteren Zustand) nichtplanar."""
    g = nx.Graph()
    g.add_nodes_from(range(n))
    kept, rejected = [], []
    for u, v in order:
        g.add_edge(u, v)
        if nx.check_planarity(g)[0]:
            kept.append((u, v))
        else:
            g.remove_edge(u, v)
            rejected.append((u, v))
    return kept, rejected


def cover_skeleton(edges, pos) -> tuple[list[Edge], list[Edge]]:
    """Gerüst durch Überdeckung der Streckenkreuzungen: wiederholt die Kante mit den meisten verbleibenden Kreuzungen entfernen (Gleichstand: der kleinere Index), bis keine Kreuzung mehr bleibt. Das Gerüst hat eine kreuzungsfreie
    Streckenzeichnung, ist also planar, ohne dass ein Planaritätstest läuft. Rückgabe: (Gerüstkanten in Ausgangsreihenfolge, entfernte Kanten in Entfernungsreihenfolge)."""
    pairs = crossing_pairs(edges, pos)
    partners: dict[int, set[int]] = {}
    for i, j in pairs:
        partners.setdefault(i, set()).add(j)
        partners.setdefault(j, set()).add(i)
    removed_idx = []
    while True:
        live = {e: len(p) for e, p in partners.items() if p}
        if not live:
            break
        e = max(live, key=lambda k: (live[k], -k))
        removed_idx.append(e)
        for o in partners[e]:
            partners[o].discard(e)
        partners[e] = set()
    gone = set(removed_idx)
    return [e for k, e in enumerate(edges) if k not in gone], [edges[k] for k in removed_idx]


def skeleton(n: int, edges, pos, kind: str, seed: int = 0) -> tuple[list[Edge], list[Edge]]:
    """Planares Gerüst und entfernte Kanten: 'random' / 'length' (Greedy in der Reihenfolge, `edge_order`) oder 'cover' (Überdeckung der Streckenkreuzungen)."""
    if kind == "cover":
        return cover_skeleton(edges, pos)
    return greedy_planar_subgraph(n, edge_order(edges, pos, kind, seed))


def skewness_exact(n: int, edges, limit: int = 8) -> int | None:
    """Kleinste Zahl von Kanten, nach deren Entfernen der Graph planar ist (Schiefheit), durch Aufzählen aller Teilmengen bis `limit` Kanten; None, wenn mehr als `limit` nötig sind. Nur für kleine Graphen."""
    es = list(edges)
    for k in range(limit + 1):
        for gone in itertools.combinations(range(len(es)), k):
            drop = set(gone)
            if is_planar(n, [e for i, e in enumerate(es) if i not in drop]):
                return k
    return None


# --- Einbettung: Rotationssystem und Flächen --------------------------------------------------------------------------------------------------------


def rotation_from_positions(n: int, edges, pos) -> Rotation:
    """Nachbarn jedes Knotens nach dem Winkel der Kante (gegen den Uhrzeigersinn). Die Einbettung ist planar genau dann, wenn die Streckenzeichnung kreuzungsfrei ist."""
    rot: Rotation = {v: [] for v in range(n)}
    for u, v in edges:
        rot[u].append(v)
        rot[v].append(u)
    for v in range(n):
        rot[v].sort(key=lambda w: (math.atan2(pos[w][1] - pos[v][1], pos[w][0] - pos[v][0]), w))
    return rot


def rotation_from_networkx(n: int, edges) -> Rotation:
    """Eine beliebige planare Einbettung (die `networkx` findet), als Rotationssystem gegen den Uhrzeigersinn. ValueError, wenn der Graph nicht planar ist."""
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    ok, emb = nx.check_planarity(g)
    if not ok:
        raise ValueError("Der Graph ist nicht planar.")
    return {v: list(reversed(list(emb.neighbors_cw_order(v)))) if g.degree(v) else [] for v in range(n)}


def faces_from_rotation(rot: Rotation) -> tuple[list[list[int]], dict[tuple[int, int], int]]:
    """Flächen als Knotenfolgen und die Fläche je Halbkante (Fläche links der Halbkante). Von (a, b) geht es zu (b, c), c = der Nachbar von b, der in der Liste von b vor a steht."""
    index = {v: {w: i for i, w in enumerate(nb)} for v, nb in rot.items()}
    face_of: dict[tuple[int, int], int] = {}
    faces: list[list[int]] = []
    for u in sorted(rot):
        for v in rot[u]:
            if (u, v) in face_of:
                continue
            face = []
            a, b = u, v
            while (a, b) not in face_of:
                face_of[(a, b)] = len(faces)
                face.append(a)
                c = rot[b][(index[b][a] - 1) % len(rot[b])]
                a, b = b, c
            faces.append(face)
    return faces, face_of


def component_count(rot: Rotation) -> int:
    seen: set[int] = set()
    count = 0
    for s in rot:
        if s in seen:
            continue
        count += 1
        seen.add(s)
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in rot[x]:
                if y not in seen:
                    seen.add(y)
                    queue.append(y)
    return count


def is_planar_embedding(rot: Rotation) -> bool:
    """Ist das Rotationssystem eine Einbettung in die Ebene? Euler für die Knoten mit Kanten: Knoten − Kanten + Flächen = 2 · Komponenten (jede Komponente zählt ihre Flächen für sich, auch ihre Außenfläche);
    isolierte Knoten haben keine Halbkanten und zählen nicht mit."""
    faces, _ = faces_from_rotation(rot)
    active = {v: nb for v, nb in rot.items() if nb}
    edges = sum(len(nb) for nb in active.values()) // 2
    return len(active) - edges + len(faces) == 2 * component_count(active)


# --- Einsetzen -------------------------------------------------------------------------------------------------------------------------------------


@dataclass
class Insertion:
    edge: Edge                  # die eingesetzte Kante (u, v)
    index: int                  # Index in der Kantenliste des ursprünglichen Graphen
    path: list[int]             # Knotenfolge u, Hilfsknoten …, v
    crossed: list[Edge]         # die gekreuzten Kanten (als Stücke zum Zeitpunkt des Einsetzens, Paare (a, b) in der Richtung mit der Quellfläche links)

    @property
    def crossings(self) -> int:
        return len(self.crossed)


@dataclass
class Planarization:
    n: int
    edges: tuple[Edge, ...]
    rot: Rotation
    piece_of: dict[frozenset, int]
    inserted: list[Insertion] = field(default_factory=list)
    midpoints: dict[int, tuple[int, int]] = field(default_factory=dict)       # Hilfsknoten → die zwei Endpunkte der gekreuzten Kante zum Zeitpunkt der Kreuzung

    @property
    def dummies(self) -> list[int]:
        return sorted(v for v in self.rot if v >= self.n)

    @property
    def crossings(self) -> int:
        return len(self.dummies)


def start_planarization(n: int, edges, kept, rot: Rotation) -> Planarization:
    """Planarisierung mit dem Gerüst `kept` (Kanten aus `edges`) und seiner Einbettung `rot`; weitere Kanten werden mit `insert_edge` eingesetzt."""
    index = {e: i for i, e in enumerate(edges)}
    return Planarization(n, tuple(edges), {v: list(nb) for v, nb in rot.items()}, {frozenset(e): index[e] for e in kept})


def _insert_after(lst: list[int], anchor: int, value: int) -> None:
    lst.insert(lst.index(anchor) + 1, value)


def insert_edge(p: Planarization, edge: Edge) -> Insertion:
    """Setzt `edge` = (s, t) mit möglichst wenigen Kreuzungen ein (kürzester Weg im Dualgraphen der aktuellen Einbettung), unterteilt die gekreuzten Kanten durch Hilfsknoten und schreibt das Rotationssystem fort.
    Liegen s und t in verschiedenen Komponenten, ist keine Kreuzung nötig."""
    s, t = edge
    rot = p.rot
    index = p.edges.index(edge)
    if s == t or t in rot[s] or index in p.piece_of.values():
        raise ValueError("Die Kante ist eine Schleife oder schon vorhanden.")
    if not rot[s] or not rot[t] or _component(rot, s) != _component(rot, t):
        _link(rot, s, t)
        p.piece_of[frozenset(edge)] = index
        ins = Insertion(edge, index, [s, t], [])
        p.inserted.append(ins)
        return ins
    faces, face_of = faces_from_rotation(rot)
    sources: dict[int, int] = {}
    for x in rot[s]:
        sources.setdefault(face_of[(s, x)], x)
    targets: dict[int, int] = {}
    for y in rot[t]:
        targets.setdefault(face_of[(t, y)], y)
    dual: dict[int, list[tuple[int, tuple[int, int]]]] = {}
    for (a, b), f in face_of.items():
        dual.setdefault(f, []).append((face_of[(b, a)], (a, b)))
    shared = sorted(set(sources) & set(targets))
    if shared:
        f = shared[0]
        _insert_after(rot[s], sources[f], t)
        _insert_after(rot[t], targets[f], s)
        p.piece_of[frozenset(edge)] = index
        ins = Insertion(edge, index, [s, t], [])
        p.inserted.append(ins)
        return ins
    parent: dict[int, tuple[int, tuple[int, int]] | None] = {f: None for f in sorted(sources)}
    queue = deque(sorted(sources))
    end = None
    while queue:
        f = queue.popleft()
        if f in targets:
            end = f
            break
        for g, he in sorted(dual.get(f, ())):
            if g not in parent:
                parent[g] = (f, he)
                queue.append(g)
    assert end is not None
    chain: list[tuple[int, int]] = []
    f = end
    while parent[f] is not None:
        f, he = parent[f]
        chain.append(he)
    chain.reverse()
    first_face = f
    next_id = max(max(rot) + 1, p.n)
    dummies = []
    for a, b in chain:
        d = next_id
        next_id += 1
        dummies.append(d)
        label = p.piece_of.pop(frozenset((a, b)))
        p.piece_of[frozenset((a, d))] = label
        p.piece_of[frozenset((d, b))] = label
        p.midpoints[d] = (a, b)
    nodes = [s] + dummies + [t]
    for i, (a, b) in enumerate(chain):
        d = dummies[i]
        prev, nxt = nodes[i], nodes[i + 2]
        rot[a][rot[a].index(b)] = d
        rot[b][rot[b].index(a)] = d
        rot[d] = [b, prev, a, nxt]
    for i in range(len(nodes) - 1):
        p.piece_of[frozenset((nodes[i], nodes[i + 1]))] = index
    _insert_after(rot[s], sources[first_face], nodes[1])
    _insert_after(rot[t], targets[end], nodes[-2])
    ins = Insertion(edge, index, nodes, chain)
    p.inserted.append(ins)
    return ins


def _component(rot: Rotation, s: int) -> frozenset[int]:
    seen = {s}
    queue = deque([s])
    while queue:
        x = queue.popleft()
        for y in rot[x]:
            if y not in seen:
                seen.add(y)
                queue.append(y)
    return frozenset(seen)


def _link(rot: Rotation, s: int, t: int) -> None:
    """Verbindet zwei Komponenten (oder isolierte Knoten) durch die Kante (s, t) in je einer beliebigen Ecke."""
    if rot[s]:
        _insert_after(rot[s], rot[s][0], t)
    else:
        rot[s] = [t]
    if rot[t]:
        _insert_after(rot[t], rot[t][0], s)
    else:
        rot[t] = [s]


def insertion_order(removed, pos, kind: str, seed: int = 0) -> list[Edge]:
    """Reihenfolge, in der die entfernten Kanten eingesetzt werden: 'given' (wie entfernt), 'random' oder 'short' (kürzeste Strecke zuerst)."""
    es = list(removed)
    if kind == "given":
        return es
    if kind == "random":
        random.Random(seed).shuffle(es)
        return es
    if kind == "short":
        return sorted(es, key=lambda e: (math.dist(pos[e[0]], pos[e[1]]), e))
    raise ValueError(kind)


def planarize(n: int, edges, kept, removed, rot: Rotation, order) -> Planarization:
    """Gerüst `kept` mit Einbettung `rot` plus Einsetzen der Kanten `removed` in der Reihenfolge `order` (eine Umordnung von `removed`)."""
    assert sorted(order) == sorted(removed)
    p = start_planarization(n, edges, kept, rot)
    for e in order:
        insert_edge(p, e)
    return p


def restore_edges(p: Planarization) -> set[Edge]:
    """Hilfsknoten wieder entfernen: je ursprünglicher Kante die zwei Endpunkte der Kette ihrer Stücke. Ergibt die Kantenmenge des Ausgangsgraphen, wenn die Planarisierung stimmt."""
    chains: dict[int, dict[int, list[int]]] = {}
    for piece, label in p.piece_of.items():
        a, b = sorted(piece)
        chains.setdefault(label, {}).setdefault(a, []).append(b)
        chains[label].setdefault(b, []).append(a)
    out = set()
    for label, adj in chains.items():
        ends = sorted(v for v, nb in adj.items() if len(nb) == 1)
        out.add((ends[0], ends[1]))
    return out


def planarization_edges(p: Planarization) -> set[frozenset]:
    """Alle Kanten der Planarisierung (einschließlich der Stücke gekreuzter Kanten) aus dem Rotationssystem."""
    return {frozenset((u, v)) for u, nb in p.rot.items() for v in nb}


def crossings_per_edge(p: Planarization) -> list[int]:
    """Zahl der Kreuzungen jeder ursprünglichen Kante (Index wie in `edges`): eine Kreuzung gehört zu beiden beteiligten Ketten."""
    counts = [0] * len(p.edges)
    labels: dict[int, set[int]] = {}
    for piece, label in p.piece_of.items():
        for v in piece:
            if v >= p.n:
                labels.setdefault(v, set()).add(label)
    for d, ls in labels.items():
        for label in ls:
            counts[label] += 1
    return counts


def dummy_positions(p: Planarization, pos) -> dict[int, tuple[float, float]]:
    """Lage der Hilfsknoten für die Anzeige: Mitte der gekreuzten Kante zum Zeitpunkt der Kreuzung (die Endpunkte können selbst Hilfsknoten sein; sie werden nach ihrer Entstehung aufgelöst)."""
    out: dict[int, tuple[float, float]] = {v: tuple(pos[v]) for v in range(p.n)}
    for d in sorted(p.midpoints):
        a, b = p.midpoints[d]
        out[d] = ((out[a][0] + out[b][0]) / 2, (out[a][1] + out[b][1]) / 2)
    return out
