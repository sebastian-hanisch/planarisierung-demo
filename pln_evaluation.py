"""Auswertung: ein Netz planarisieren (Gerüst, Einbettung, Einsetzen), Urteile (reine Funktionen) und die Messreihen der App.

Die Reihen (`classic_series`, `order_series`, `embedding_series`) laufen über feste Pläne (`C.SWEEP_SEEDS`), nie über einen einzelnen Seed. Anzahlen (Kreuzungen, entfernte Kanten) sind exakt, Zeiten hängen von Maschine
und Umsetzung ab. Alle Kreuzungszahlen sind **Obergrenzen durch ein Verfahren**, keine Optima."""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass

import pln_algorithm as A
import pln_constants as C
import pln_scenario as S


def num(x: float, digits: int = 0) -> str:
    """Zahl im deutschen Format: Tausenderpunkt, Dezimalkomma."""
    return f"{x:,.{digits}f}".translate(str.maketrans({",": ".", ".": ","}))


def plural(count: int, singular: str, plural_form: str) -> str:
    return f"{count} {singular if count == 1 else plural_form}"


def ms_text(seconds: float) -> str:
    """Zeit in Millisekunden, bei einer Sekunde und mehr in Sekunden."""
    return f"{num(seconds, 2)} s" if seconds >= 1 else f"{num(seconds * 1000, 1)} ms"


@dataclass(frozen=True)
class Settings:
    vehicle: str = C.DEFAULT_VEHICLE
    n: int = C.DEFAULT_N
    extras: int = C.DEFAULT_EXTRAS
    classic: str = C.DEFAULT_CLASSIC
    skeleton: str = C.DEFAULT_SKELETON
    embedding: str = C.DEFAULT_EMBEDDING
    tries: int = C.DEFAULT_TRIES
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Run:
    kept: tuple[tuple[int, int], ...]
    removed: tuple[tuple[int, int], ...]
    planarization: A.Planarization
    embedding_used: str              # 'geometry' oder 'arbitrary'
    fallback: bool                   # 'geometry' gewünscht, die Streckenzeichnung des Gerüsts hat aber Kreuzungen

    @property
    def crossings(self) -> int:
        return self.planarization.crossings


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    graph: S.Graph
    straight: int                    # Streckenkreuzungen der gegebenen Zeichnung
    run: Run
    tries_done: int
    seconds: float

    @property
    def inserted(self) -> list[A.Insertion]:
        return self.run.planarization.inserted

    @property
    def per_edge(self) -> list[int]:
        return [i.crossings for i in self.inserted]

    @property
    def share_at_most_one(self) -> float:
        per = self.per_edge
        return sum(1 for c in per if c <= 1) / len(per) if per else 1.0

    @property
    def known(self) -> int | None:
        return S.KNOWN_CROSSING_NUMBER.get(self.graph.name) if self.settings.vehicle == "classic" else None


def run_once(graph: S.Graph, skeleton: str, embedding: str, seed: int) -> Run:
    """Ein Lauf: Gerüst, Einbettung, entfernte Kanten einsetzen (Reihenfolge `C.INSERT_ORDER` mit dem Zufalls-Seed)."""
    kept, removed = A.skeleton(graph.n, graph.edges, graph.pos, skeleton, seed)
    used, fallback = embedding, False
    rot = None
    if embedding == "geometry":
        rot = A.rotation_from_positions(graph.n, kept, graph.pos)
        if not A.is_planar_embedding(rot):
            fallback, used, rot = True, "arbitrary", None
    if rot is None:
        rot = A.rotation_from_networkx(graph.n, kept)
    order = A.insertion_order(removed, graph.pos, C.INSERT_ORDER, seed)
    return Run(tuple(kept), tuple(removed), A.planarize(graph.n, graph.edges, kept, removed, rot, order), used, fallback)


def analyse(settings: Settings) -> Analysis:
    graph = S.make_graph(settings.vehicle, settings.n, settings.extras, settings.classic, settings.seed)
    straight = len(A.crossing_pairs(graph.edges, graph.pos))
    t0 = time.perf_counter()
    tries = settings.tries if settings.skeleton == "random" else 1
    best = None
    for t in range(tries):
        run = run_once(graph, settings.skeleton, settings.embedding, settings.seed + t)
        if best is None or run.crossings < best.crossings:
            best = run
    return Analysis(settings, graph, straight, best, tries, time.perf_counter() - t0)


# --- Messreihen --------------------------------------------------------------------------------------------------------------------------------


def _median(values):
    return statistics.median(values) if values else None


def euler_lower_bound(graph: S.Graph) -> int:
    """Untere Schranke der Schiefheit aus Euler: m − (3n − 6) für n ≥ 3 (planare Graphen haben höchstens 3n − 6 Kanten), nie unter 0."""
    return max(0, graph.m - (3 * graph.n - 6)) if graph.n >= 3 else 0


def classic_series(names=C.CLASSIC_NAMES, tries: int = C.CLASSIC_TRIES) -> list[dict]:
    """Klassische Graphen: bekannte Kreuzungszahl (aus dem Gedächtnis), die beste Planarisierung aus `tries` zufälligen Reihenfolgen und mit nur einer, die Schiefheit (exakt bis `C.EXACT_SKEWNESS_MAX_M` Kanten, sonst Euler-Schranke)."""
    rows = []
    for name in names:
        g = S.make_classic(name)
        crossings = []
        for t in range(tries):
            run = run_once(g, "random", "arbitrary", t)
            crossings.append(run.crossings)
        exact = A.skewness_exact(g.n, g.edges, limit=10) if g.m <= C.EXACT_SKEWNESS_MAX_M else None
        rows.append({"name": name, "n": g.n, "m": g.m, "known": S.KNOWN_CROSSING_NUMBER[name], "best": min(crossings), "first": crossings[0], "worst": max(crossings), "tries": tries,
                     "skewness": exact, "euler_bound": euler_lower_bound(g), "equal": min(crossings) == S.KNOWN_CROSSING_NUMBER[name]})
    return rows


def order_series(extras=C.ORDER_EXTRAS, n: int = C.ORDER_N, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Karten mit Zusatzkanten: Streckenkreuzungen, vom Greedy entfernte Kanten bei zufälliger und bei „kürzeste zuerst“-Reihenfolge, Kreuzungen der Planarisierung (Gerüst: Überdeckung der Streckenkreuzungen,
    Einbettung aus den Koordinaten) und Anteil der eingesetzten Kanten mit höchstens einer Kreuzung; Mediane über die Pläne."""
    rows = []
    for k in extras:
        straight, removed_random, removed_length, crossings, share, per_edge = [], [], [], [], [], []
        for seed in seeds:
            g = S.make_delaunay(n, k, seed)
            straight.append(len(A.crossing_pairs(g.edges, g.pos)))
            removed_random.append(len(A.skeleton(g.n, g.edges, g.pos, "random", seed)[1]))
            removed_length.append(len(A.skeleton(g.n, g.edges, g.pos, "length", seed)[1]))
            a = Analysis(Settings("delaunay", n, k, skeleton="cover", seed=seed), g, straight[-1], run_once(g, "cover", "geometry", seed), 1, 0.0)
            crossings.append(a.run.crossings)
            share.append(a.share_at_most_one)
            per_edge.append(statistics.median(a.per_edge) if a.per_edge else 0)
        rows.append({"extras": k, "n": n, "plans": len(seeds), "straight": _median(straight), "removed_random": _median(removed_random), "removed_length": _median(removed_length),
                     "crossings": _median(crossings), "ratio": _median([c / s for c, s in zip(crossings, straight)]), "share": _median(share), "per_edge": _median(per_edge)})
    return rows


def embedding_series(n: int = C.EMBEDDING_N, k: int = C.EMBEDDING_EXTRAS, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Gerüst (Überdeckung der Streckenkreuzungen) in zwei Einbettungen, aus den Koordinaten und beliebig: Delaunay-Karten (Mediane) und die ganze Toronto-Karte."""
    rows = []
    maps = [S.make_delaunay(n, k, seed) for seed in seeds]
    for name, graphs in ((f"Karte mit {n} Standorten, {k} Zusatzkanten (Mediane)", maps), ("Toronto-Karte (ganz)", [S.make_toronto()])):
        geo, arb, removed, straight, zero_geo = [], [], [], [], []
        t_geo = t_arb = 0.0
        for g in graphs:
            straight.append(len(A.crossing_pairs(g.edges, g.pos)))
            t0 = time.perf_counter()
            run_geo = run_once(g, "cover", "geometry", 0)
            t_geo += time.perf_counter() - t0
            t0 = time.perf_counter()
            run_arb = run_once(g, "cover", "arbitrary", 0)
            t_arb += time.perf_counter() - t0
            geo.append(run_geo.crossings)
            arb.append(run_arb.crossings)
            removed.append(len(run_geo.removed))
            zero_geo.append(sum(1 for i in run_geo.planarization.inserted if i.crossings == 0))
        rows.append({"name": name, "plans": len(graphs), "straight": _median(straight), "removed": _median(removed), "geometry": _median(geo), "arbitrary": _median(arb),
                     "zero_geometry": _median(zero_geo), "geometry_time": t_geo / len(graphs), "arbitrary_time": t_arb / len(graphs)})
    return rows


# --- Urteile (rein) ----------------------------------------------------------------------------------------------------------------------------


def verdict_planarization(a: Analysis) -> tuple[str, str]:
    """Urteil über ein Netz als (Art, Text): Streckenkreuzungen, entfernte Kanten, Kreuzungen der Planarisierung (Obergrenze), Anteil der Kanten mit höchstens einer Kreuzung; die App ruft st.<Art>(Text),
    der Test prüft jede Zahl an handgesetzten Werten."""
    run = a.run
    removed = len(run.removed)
    c = run.crossings
    if removed == 0:
        return "success", f"Das Netz ist planar: {a.straight} Streckenkreuzungen der gegebenen Zeichnung, aber keine Kante muss entfernt werden und es bleibt keine Kreuzung."
    head = (f"Das planare Gerüst hat {plural(len(run.kept), 'Kante', 'Kanten')}, **{plural(removed, 'Kante', 'Kanten')} {'wurde' if removed == 1 else 'wurden'} entfernt** und über den kürzesten Dualweg wieder eingesetzt: "
            f"**{plural(c, 'Kreuzung', 'Kreuzungen')}** (eine Obergrenze der Kreuzungszahl, kein Optimum) gegen {plural(a.straight, 'Streckenkreuzung', 'Streckenkreuzungen')} der gegebenen Zeichnung.")
    parts = [head]
    if a.straight > 0 and c < a.straight:
        parts.append(f"Das sind **{num(c / a.straight, 2)}-mal so viele** wie bei geraden Strecken.")
    share = a.share_at_most_one
    parts.append(f"{num(100 * share, 0)} % der eingesetzten Kanten kreuzen höchstens eine Kante.")
    if run.fallback:
        parts.append("Die Streckenzeichnung des Gerüsts hat Kreuzungen, die Einbettung aus den Koordinaten gilt deshalb nicht: gerechnet wurde mit einer beliebigen Einbettung.")
    if a.tries_done > 1:
        parts.append(f"Beste von {a.tries_done} zufälligen Reihenfolgen.")
    if a.known is not None:
        verdict = "gleich der bekannten Kreuzungszahl" if c == a.known else f"über der bekannten Kreuzungszahl {a.known}"
        parts.append(f"Für {a.graph.name} ist die Kreuzungszahl {a.known} (aus dem Gedächtnis); das Ergebnis ist {verdict}.")
    kind = "success" if a.straight > c else ("info" if a.straight == c else "warning")
    return kind, " ".join(parts)


def verdict_classic(rows: list[dict]) -> tuple[str, str]:
    equal = [r for r in rows if r["equal"]]
    above = [r for r in rows if not r["equal"]]
    text = f"Die beste von {rows[0]['tries']} zufälligen Reihenfolgen findet die bekannte Kreuzungszahl bei **{len(equal)} von {len(rows)}** Graphen"
    if above:
        text += ", nicht bei " + ", ".join(f"{r['name']} ({r['best']} statt {r['known']})" for r in above)
    first = [r for r in rows if r["first"] > r["known"]]
    text += f". Mit nur einer Reihenfolge reicht es bei {len(rows) - len(first)} von {len(rows)}"
    text += f" (zum Beispiel {first[0]['name']}: {first[0]['first']} statt {first[0]['known']})." if first else "."
    return ("success" if not above else "info"), text


def verdict_order(rows: list[dict]) -> tuple[str, str]:
    mid = next((r for r in rows if r["extras"] == 5), rows[len(rows) // 2])
    last = rows[-1]
    ratios = [r["ratio"] for r in rows]
    text = (f"Karten mit {rows[0]['n']} Standorten, {rows[0]['plans']} Pläne (Mediane): bei {mid['extras']} Zusatzkanten entfernt der Greedy in zufälliger Reihenfolge **{num(mid['removed_random'])}** Kanten, "
            f"„kürzeste zuerst“ **{num(mid['removed_length'])}**. Die Planarisierung (Gerüst: Überdeckung, Einbettung aus den Koordinaten) braucht **{num(min(ratios), 2)}- bis {num(max(ratios), 2)}-mal so viele Kreuzungen** wie die geraden Strecken "
            f"(bei {last['extras']} Zusatzkanten {num(last['crossings'])} gegen {num(last['straight'])}); höchstens eine Kreuzung haben im Median {num(100 * last['share'], 0)} % der eingesetzten Kanten.")
    return "info", text


def verdict_embedding(rows: list[dict]) -> tuple[str, str]:
    parts = []
    for r in rows:
        parts.append(f"{r['name']}: {num(r['straight'])} Streckenkreuzungen, {num(r['removed'])} entfernte Kanten, Planarisierung {num(r['geometry'])} Kreuzungen in der Einbettung aus den Koordinaten gegen {num(r['arbitrary'])} in einer beliebigen"
                     f" ({num(r['zero_geometry'])} der eingesetzten Kanten ohne Kreuzung)")
    text = "; ".join(parts) + ". Bei einer Triangulierung ist die Einbettung bis auf die Spiegelung eindeutig, die Wahl ändert dort nichts; bei dünnen Straßennetzen mit vielen Komponenten bleibt sie klein."
    return "info", text
