"""Urteile sind reine Funktionen: jede Zahl im Text wird an handgesetzten Werten geprüft; Art (success/info/warning) und Schwellen ebenfalls."""

import pln_algorithm as A
import pln_evaluation as ev
import pln_scenario as S


def fake(straight, kept, removed, per_edge, *, vehicle="delaunay", name="Karte", tries=1, fallback=False, extras=()):
    """Eine Analyse mit handgesetzten Zahlen: Streckenkreuzungen, Zahl der Gerüstkanten und entfernten Kanten, Kreuzungen je eingesetzter Kante (ihre Summe sind die Kreuzungen der Planarisierung)."""
    n = 40
    rot = {v: [] for v in range(n)}
    for i in range(sum(per_edge)):
        rot[n + i] = []
    edges = tuple((i, i + 1) for i in range(kept + removed))
    kept_edges = edges[:kept]
    removed_edges = edges[kept:]
    ins = [A.Insertion(e, i, [e[0], e[1]], [(0, 1)] * c) for i, (e, c) in enumerate(zip(removed_edges, per_edge))]
    p = A.Planarization(n, edges, rot, {}, ins, {})
    run = ev.Run(kept_edges, removed_edges, p, "arbitrary" if fallback else "geometry", fallback)
    graph = S.Graph(n, edges, tuple((0.0, 0.0) for _ in range(n)), name)
    return ev.Analysis(ev.Settings(vehicle, skeleton="random", tries=tries), graph, straight, run, tries, 0.5)


def test_num_plural_and_ms_text_use_german_format():
    assert ev.num(1234567) == "1.234.567" and ev.num(3.14159, 2) == "3,14" and ev.num(0) == "0"
    assert ev.ms_text(0.0115) == "11,5 ms" and ev.ms_text(1.5) == "1,50 s"
    assert ev.plural(1, "Kante", "Kanten") == "1 Kante" and ev.plural(0, "Kante", "Kanten") == "0 Kanten"


def test_planarization_verdict_success_with_fewer_crossings_than_straight_lines():
    kind, text = ev.verdict_planarization(fake(145, 286, 10, [6, 5, 6, 5, 6, 5, 6, 5, 5, 4]))
    assert kind == "success"
    for part in ("Das planare Gerüst hat 286 Kanten", "**10 Kanten wurden entfernt**", "**53 Kreuzungen**", "gegen 145 Streckenkreuzungen", "Das sind **0,37-mal so viele** wie bei geraden Strecken.",
                 "0 % der eingesetzten Kanten kreuzen höchstens eine Kante."):
        assert part in text, part
    assert "Beste von" not in text and "Die Streckenzeichnung des Gerüsts" not in text


def test_planarization_verdict_shares_and_singulars():
    kind, text = ev.verdict_planarization(fake(5, 20, 1, [1]))
    assert "**1 Kante wurde entfernt**" in text and "**1 Kreuzung**" in text and "gegen 5 Streckenkreuzungen" in text and "100 % der eingesetzten" in text
    kind, text = ev.verdict_planarization(fake(9, 20, 4, [0, 0, 1, 3]))
    assert "75 % der eingesetzten Kanten" in text and "**4 Kreuzungen**" in text and "**4 Kanten wurden entfernt**" in text


def test_planarization_verdict_info_when_equal_and_warning_when_worse():
    assert ev.verdict_planarization(fake(5, 20, 2, [2, 3]))[0] == "info"
    kind, text = ev.verdict_planarization(fake(5, 20, 2, [3, 4]))
    assert kind == "warning" and "mal so viele" not in text
    kind, text = ev.verdict_planarization(fake(0, 20, 2, [1, 0]))
    assert kind == "warning" and "mal so viele" not in text


def test_planarization_verdict_for_a_planar_net():
    kind, text = ev.verdict_planarization(fake(7, 30, 0, []))
    assert kind == "success" and text == "Das Netz ist planar: 7 Streckenkreuzungen der gegebenen Zeichnung, aber keine Kante muss entfernt werden und es bleibt keine Kreuzung."


def test_planarization_verdict_mentions_fallback_tries_and_known_values():
    kind, text = ev.verdict_planarization(fake(145, 286, 3, [2, 2, 2], fallback=True, tries=7))
    assert "gerechnet wurde mit einer beliebigen Einbettung" in text and "Beste von 7 zufälligen Reihenfolgen." in text
    kind, text = ev.verdict_planarization(fake(5, 16, 1, [4], vehicle="classic", name="K4,4"))
    assert "Für K4,4 ist die Kreuzungszahl 4 (aus dem Gedächtnis); das Ergebnis ist gleich der bekannten Kreuzungszahl." in text
    kind, text = ev.verdict_planarization(fake(5, 16, 1, [5], vehicle="classic", name="K4,4"))
    assert "das Ergebnis ist über der bekannten Kreuzungszahl 4." in text
    assert "Kreuzungszahl" in ev.verdict_planarization(fake(5, 16, 1, [4], vehicle="delaunay", name="K4,4"))[1] and "Für K4,4" not in ev.verdict_planarization(fake(5, 16, 1, [4], vehicle="delaunay", name="K4,4"))[1]


def classic_row(name, known, best, first, worst=None, tries=100):
    return {"name": name, "known": known, "best": best, "first": first, "worst": worst if worst is not None else first, "tries": tries, "equal": best == known}


def test_classic_verdict_by_hand():
    rows = [classic_row("K5", 1, 1, 1), classic_row("K6", 3, 3, 3), classic_row("K4,4", 4, 4, 5)]
    kind, text = ev.verdict_classic(rows)
    assert kind == "success"
    assert "Die beste von 100 zufälligen Reihenfolgen findet die bekannte Kreuzungszahl bei **3 von 3** Graphen. Mit nur einer Reihenfolge reicht es bei 2 von 3 (zum Beispiel K4,4: 5 statt 4)." in text
    rows = [classic_row("K5", 1, 1, 1), classic_row("K7", 9, 10, 10)]
    kind, text = ev.verdict_classic(rows)
    assert kind == "info" and "bei **1 von 2** Graphen, nicht bei K7 (10 statt 9)" in text and "reicht es bei 1 von 2" in text
    assert ev.verdict_classic([classic_row("K5", 1, 1, 1)])[1].endswith("reicht es bei 1 von 1.")


def order_row(k, rr, rl, straight, crossings, share=0.05, plans=5, n=100):
    return {"extras": k, "n": n, "plans": plans, "straight": straight, "removed_random": rr, "removed_length": rl, "crossings": crossings, "ratio": crossings / straight, "share": share, "per_edge": 5}


def test_order_verdict_by_hand():
    rows = [order_row(1, 1, 1, 7, 6), order_row(5, 31, 5, 63, 34), order_row(40, 145, 40, 600, 300)]
    kind, text = ev.verdict_order(rows)
    assert kind == "info"
    for part in ("Karten mit 100 Standorten, 5 Pläne (Mediane)", "bei 5 Zusatzkanten entfernt der Greedy in zufälliger Reihenfolge **31** Kanten, „kürzeste zuerst“ **5**", "**0,50- bis 0,86-mal so viele Kreuzungen**",
                 "bei 40 Zusatzkanten 300 gegen 600", "5 % der eingesetzten Kanten"):
        assert part in text, part
    two = [order_row(2, 6, 2, 26, 12), order_row(10, 56, 10, 132, 74)]
    assert "bei 10 Zusatzkanten entfernt der Greedy in zufälliger Reihenfolge **56**" in ev.verdict_order(two)[1]                 # kein Eintrag mit 5: die mittlere Zeile


def test_embedding_verdict_by_hand():
    rows = [{"name": "Karte (Mediane)", "straight": 103, "removed": 10, "geometry": 61, "arbitrary": 61, "zero_geometry": 0},
            {"name": "Toronto-Karte (ganz)", "straight": 125, "removed": 52, "geometry": 35, "arbitrary": 40, "zero_geometry": 36}]
    kind, text = ev.verdict_embedding(rows)
    assert kind == "info"
    for part in ("Karte (Mediane): 103 Streckenkreuzungen, 10 entfernte Kanten, Planarisierung 61 Kreuzungen in der Einbettung aus den Koordinaten gegen 61 in einer beliebigen (0 der eingesetzten Kanten ohne Kreuzung)",
                 "Toronto-Karte (ganz): 125 Streckenkreuzungen, 52 entfernte Kanten, Planarisierung 35 Kreuzungen in der Einbettung aus den Koordinaten gegen 40 in einer beliebigen (36 der eingesetzten Kanten ohne Kreuzung)",
                 "Bei einer Triangulierung ist die Einbettung bis auf die Spiegelung eindeutig"):
        assert part in text, part
