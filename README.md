# Fast planare Netze – Planarisieren – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-planarisierung-demo.streamlit.app/)** -->

Neuntes und optionales Stück der **Planarität-und-Zeichnen-Linie** (Graphentheorie) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Es setzt die ersten Stücke voraus: Planarität und Einbettung ([planaritaet-demo](https://github.com/sebastian-hanisch/planaritaet-demo)), den Dualgraphen mit kürzestem Weg ([planar-dual-demo](https://github.com/sebastian-hanisch/planar-dual-demo)) und die Toronto-Karte mit ihren Kreuzungen ([graph-zeichnen-demo](https://github.com/sebastian-hanisch/graph-zeichnen-demo)).

Ein Straßennetz, ein Leitungsplan, eine Landkarte mit ein paar Fernverbindungen: **fast** planar, aber nicht ganz. Wie viele Kanten muss man entfernen, damit das Netz planar wird (**Schiefheit**), und wie viele **Kreuzungen** bleiben, wenn man sie wieder einsetzt? Die **Planarisierung** bildet ein planares Gerüst (Greedy: Kanten der Reihe nach einfügen, solange der Graph planar bleibt, oder Überdeckung der Streckenkreuzungen), setzt jede übrige Kante über den **kürzesten Weg im Dualgraphen** ein und schreibt jede Kreuzung als Hilfsknoten fest. Die Zahl der Kreuzungen ist eine **Obergrenze der Kreuzungszahl** (sie selbst ist NP-schwer), kein Optimum.

## Warum dieses Problem

In der Praxis sind Netze selten ganz planar und selten ganz wirr: eine planare Karte plus wenige Fernverbindungen, ein Straßennetz mit ein paar Brücken. Kernfrage: **Wie viele Kreuzungen bleiben, was kostet das Planarisieren, und wie viel vom Befund der Straßenkarte ist ein Artefakt der geraden Strecken?** Der Befund ist mehrseitig: die Kantenreihenfolge des Greedy entscheidet (zufällig entfernt er bis zum Sechsfachen der nötigen Kanten), die Planarisierung braucht etwa die Hälfte der Kreuzungen gerader Strecken, auf klassischen Graphen findet sie die bekannten Kreuzungszahlen, und auf der Toronto-Karte kreuzen 36 der 52 störenden Kanten in der richtigen Einbettung nichts.

## Modell

Graphen: **Delaunay-Karten mit Zusatzkanten** (zufällige Standorte, alle Delaunay-Kanten, dazu zufällige „Fernverbindungen“), die **Toronto-Karte** (OpenStreetMap, ODbL, Auszug aus `graph-zeichnen-demo`; Ausschnitte um die Mitte oder ganz), **klassische Graphen** (K5, K6, K7, K3,3, K3,4, K3,5, K4,4, Petersen). **Gerüst:** Greedy in zufälliger Reihenfolge oder „kürzeste Kante zuerst“ (Planaritätsprobe je Kante mit `networkx`), oder die **Überdeckung** der Streckenkreuzungen (wiederholt die Kante mit den meisten Kreuzungen entfernen; die Streckenzeichnung des Gerüsts ist kreuzungsfrei). **Einbettung** des Gerüsts als Rotationssystem: aus den Koordinaten (Kanten um jeden Knoten nach dem Winkel, gültig nur bei kreuzungsfreier Streckenzeichnung, sonst Rückfall auf die beliebige) oder beliebig (`networkx`). **Einsetzen:** kürzester Weg im Dualgraphen von einer Fläche am einen Ende der Kante zu einer Fläche am anderen, jede gekreuzte Kante erhält einen Hilfsknoten, das Rotationssystem wird fortgeschrieben (nicht neu berechnet); Kanten zwischen verschiedenen Komponenten brauchen keine Kreuzung. Formeln im 📐-Expander der App.

## Methodik

- **Ein Netz:** Netz, Größe, Zusatzkanten, Gerüst, Einbettung, Versuche (zufälliger Greedy: beste von bis zu 20 Reihenfolgen), Zufalls-Seed; Streckenkreuzungen, entfernte Kanten, Kreuzungen der Planarisierung, Anteil der Kanten mit höchstens einer Kreuzung, Urteil, Zeichnung mit Gerüst, eingesetzten Kanten (rot) und Kreuzungen.
- **Kante für Kante einsetzen:** die ersten j eingesetzten Kanten, Tabelle mit Länge und Kreuzungen.
- **Messreihen auf Klick** (feste Pläne 100000 bis 100004, Mediane): klassische Graphen gegen die bekannten Kreuzungszahlen, Reihenfolge und Strecken (Karten mit 100 Standorten, 1 bis 40 Zusatzkanten), Einbettung und die ganze Toronto-Karte.
- **Aufwandsmaß:** Kreuzungen und entfernte Kanten exakt; Zeiten gelten für diese Python-Umsetzung.

## Befunde (gemessen, keine Behauptungen)

Zeiten sind auf dem Entwicklungsrechner (Windows, reines Python) gemessen. Klassische Graphen und Toronto (Überdeckung, Einbettung aus den Koordinaten) sind exakt; bei Delaunay-Karten gilt im Test ein Band; Zahlen, die von der beliebigen Einbettung von `networkx` abhängen, gelten nur als Band.

| Frage | Befund | Test |
|---|---|---|
| Findet die Planarisierung die bekannten Kreuzungszahlen? (Werte aus dem Gedächtnis: K5 1, K6 3, K7 9, K3,3 1, K3,4 2, K3,5 4, K4,4 4, Petersen 2) | Die beste von 100 zufälligen Reihenfolgen findet sie bei **8 von 8** Graphen. Mit nur der ersten Reihenfolge reicht es bei 7 von 8 (K4,4: 5 statt 4; die Zahl hängt von der Einbettung ab). **Bewiesen** ist die Zahl, wo die exakte Schiefheit (Aufzählen aller Kantenmengen) gleich ihr ist: K5 1, K6 3, K3,3 1, K3,4 2, K4,4 4, Petersen 2; bei K3,5 ist die Schiefheit 3 gegen gefundene 4, bei K7 gilt nur die Euler-Schranke 6 gegen 9. | `test_classic_crossing_numbers_are_found_with_100_orders`, `test_one_order_is_enough_for_all_but_k44`, `test_skewness_is_a_lower_bound_and_proves_most_crossing_numbers` |
| Entscheidet die Reihenfolge des Greedy? (Karten mit 100 Standorten, 5 Pläne, Mediane; 1 / 2 / 5 / 10 / 20 / 40 Zusatzkanten) | Zufällig eingefügt, **entfernt der Greedy 1 / 25 / 31 / 35 / 78 / 112 Kanten**, „kürzeste zuerst“ nur **1 / 2 / 5 / 10 / 22 / 41**: bei 5 Zusatzkanten das Sechsfache, bei 2 das Zwölffache. | `test_the_order_of_the_greedy_decides` |
| Wie viel sparen die Kreuzungen der Planarisierung gegenüber geraden Strecken? (dieselben Karten, Gerüst: Überdeckung, Einbettung aus den Koordinaten) | Streckenkreuzungen **7 / 20 / 48 / 103 / 219 / 575**, Planarisierung **6 / 12 / 33 / 61 / 120 / 304**: das 0,86- / 0,60- / 0,56- / 0,58- / 0,56- / 0,54-Fache, ab 5 Zusatzkanten etwa die **Hälfte**. | `test_planarization_needs_about_half_the_straight_line_crossings` |
| Sind zufällige Fernkanten 1-planar? | **Nein.** Im Median kreuzt jede eingesetzte Fernkante 6 bis 8 andere Kanten, höchstens eine Kreuzung haben im Median 0 bis 5 % der eingesetzten Kanten. | `test_random_far_edges_are_far_from_one_planar` |
| Spielt die Einbettung eine Rolle? | Bei der **Triangulierung** (Karte mit 100 Standorten, 10 Zusatzkanten) nicht: 61 Kreuzungen in der Einbettung aus den Koordinaten und 61 in einer beliebigen (eine Triangulierung hat bis auf die Spiegelung genau eine Einbettung). **Toronto** (5 072 Knoten, 7 621 Kanten): 125 Streckenkreuzungen, die Überdeckung entfernt **52 Kanten**, das Gerüst (7 569 Kanten, 15 Komponenten) ist kreuzungsfrei gezeichnet und planar; Planarisierung **35 Kreuzungen** in der Einbettung aus den Koordinaten gegen etwa 40 in einer beliebigen (Test: 35 bis 60, hängt von `networkx` ab), 1,0 s gegen 1,2 s. | `test_embedding_does_not_matter_for_a_triangulation`, `test_toronto_in_the_coordinate_embedding`, `test_toronto_is_combinatorially_nonplanar_but_the_skeleton_is_planar` |
| Wie viel vom Befund der Toronto-Karte ist Artefakt? | Das Netz bleibt **kombinatorisch nicht planar**, aber von den 52 störenden Kanten lassen sich **36 ohne Kreuzung** einsetzen (beide Enden an einer Fläche oder in verschiedenen Komponenten): die 125 Streckenkreuzungen sind zu einem großen Teil ein Artefakt der geraden Strecken, die Planarisierung braucht 35. Ob Brücken, Tunnel oder nicht verschmolzene Knoten dahinterstecken, ist mit diesen Daten nicht entscheidbar. | `test_toronto_in_the_coordinate_embedding` |
| Was zeigen die Presets? | Voreinstellung (Karte, 10 Zusatzkanten, Seed 35): etwa 145 Streckenkreuzungen, 10 entfernte Kanten, etwa **53 Kreuzungen**; zufällige Reihenfolge: **67 entfernte Kanten** und 361 Kreuzungen; 30 Zusatzkanten: 57 entfernte Kanten, 348 Kreuzungen gegen 463 Streckenkreuzungen; Toronto-Ausschnitt mit 250 Knoten: 13 Streckenkreuzungen, 5 entfernte Kanten, **4 Kreuzungen**; K4,4 mit 10 Reihenfolgen: **4**. | `test_presets_hold_what_their_help_texts_say` |

## Ehrliche Grenzen

- **Obergrenzen, keine Optima.** Die Kreuzungszahl ist NP-schwer; die Demo liefert die Kreuzungen eines Verfahrens (Gerüst, Einbettung, Reihenfolge des Einsetzens). Eine andere Reihenfolge kann weniger haben. Bewiesen sind nur die Werte, bei denen die exakte Schiefheit gleich ist.
- **Die Reihenfolge des Greedy entscheidet,** und „kürzeste zuerst“ braucht Koordinaten; bei Graphen ohne Längen gibt es diese Ordnung nicht. Bei vielen Zusatzkanten entfernt auch sie etwas mehr als die Zusatzkanten (22 bei 20, 41 bei 40).
- **Die Einbettung ist nicht frei.** Eine Triangulierung hat genau eine; nur dünne Netze mit vielen Gelenken und Komponenten haben Spielraum. Die Einbettung aus den Koordinaten gilt nur bei kreuzungsfreier Streckenzeichnung des Gerüsts; sonst rechnet die App mit einer beliebigen und sagt es.
- **Kürzester Weg je Kante, nicht im Ganzen.** Jede Kante wird in die aktuelle Planarisierung eingesetzt; Reihenfolge und frühere Einsetzungen bestimmen, was später kreuzt.
- **Anzeige.** Kreuzungen werden in der Mitte der gekreuzten Kante gezeichnet; die Strecken zwischen diesen Punkten können sich schneiden, ohne dass das eine Kreuzung der Planarisierung ist.
- **Kreuzungszahlen klassischer Graphen aus dem Gedächtnis** (Guy, Zarankiewicz); die Literaturangaben (Planarisierung nach Tamassia u. a. und Gutwenger, Mutzel, Weiskircher; Garey und Johnson 1983) sind nicht im Original geprüft.
- **Die Zahl 35 für Toronto ist eine Obergrenze,** mit den Kreuzungen der eingesetzten Kanten untereinander gezählt; eine bessere Reihenfolge kann weniger ergeben.
- **Rechenzeit.** Der Planaritätstest läuft für jede Kante des Greedy; ein Lauf mit 300 Knoten dauert einige Sekunden, die ganze Toronto-Karte mit Greedy ist in der App nicht vorgesehen (die Vormessung brauchte dafür 275 s).

## Befunde und Korrekturen gegenüber dem Plan

- **Einbettung:** die Vormessung meldete für Toronto 993 Kreuzungen bei beliebiger Einbettung gegen etwa 30 bei der aus den Koordinaten und folgerte „die Einbettung entscheidet noch mehr“. Das war ein Gerüst-Effekt: das damalige Greedy-Gerüst („kürzeste zuerst“, 83 entfernte Kanten, 275 s) in einer beliebigen Einbettung. Mit demselben Gerüst, der Überdeckung (52 entfernte Kanten), kommt die beliebige Einbettung auf etwa 40 gegen 35; bei Triangulierungen ist die Einbettung eindeutig. **Das Gerüst entscheidet mehr als die Einbettung.** Der Greedy-Lauf auf der ganzen Toronto-Karte steht nur in der Vormessung, nicht in den Tests.
- **Kreuzungen der eingesetzten Kanten untereinander:** die Vormessung zählte für Toronto 30 Kreuzungen mit dem Gerüst und nicht die der eingesetzten Kanten untereinander; mit ihnen sind es 35. 36 von 52 Kanten (Vormessung: 25 plus 14 zwischen Komponenten, also 39) werden ohne Kreuzung eingesetzt.
- **„Kürzeste zuerst“ entfernt genau k Kanten:** gilt in der Vormessung (Median bei n = 150, k bis 40), nicht in der Reihe mit n = 100 bei großem k (22 bei 20, 41 bei 40).
- **Planaritätstest:** der Plan sah eine Kopie des Fragmentverfahrens vor; die App nutzt `networkx.check_planarity` als Laufzeit-Abhängigkeit (schneller, exakt). Das Fragmentverfahren bleibt Gegenstand von `planaritaet-demo`.
- **Preset „Überdeckung, beliebige Einbettung“** entfiel: auf Karten ist das Ergebnis dasselbe wie in der Einbettung aus den Koordinaten (eindeutige Einbettung), das Preset hätte das Gegenteil behauptet.
- **Port:** 9138 wie im Einzelplan vorgesehen.

## Verifikation

- **Kern gegen Handrechnung** (`tests/test_algorithm.py`): Streckenkreuzungen (Berührung ist keine Kreuzung), Planarität, Reihenfolgen, Greedy an K5 und K3,3, Überdeckung an K4 im Quadrat, exakte Schiefheit, Rotationssystem, Flächen, Euler, Einsetzen ohne Kreuzung (K4 im Quadrat), mit genau einer Kreuzung (Oktaeder mit Achse), über Komponenten hinweg, K5 und K3,3 mit je 1, K6 mit 3.
- **Orakel:** `tests/test_oracle_planarisierung.py`: Gerüst planar und maximal und Planarisierung planar nach `networkx`, Kreuzungen nie unter der exakten Schiefheit, Hilfsknoten ergeben den Ausgangsgraphen zurück, Euler für die Planarisierung, Kreuzungszahlen klassischer Graphen (K5, K3,3 durch Nichtplanarität, K6, K3,4, K4,4, Petersen durch Schiefheit), ein planarer Graph ist seine eigene Planarisierung.
- **Szenario, Randfälle, Auswertung, Darstellung:** Karten, Zusatzkanten, klassische Graphen, Toronto (`tests/test_scenario.py`); jedes Netz und jedes Gerüst an den Reglergrenzen, isolierte Knoten, Komponenten (`tests/test_edge_cases.py`); Messreihen (`tests/test_evaluation.py`); Spuren der Zeichnung (`tests/test_visualization.py`).
- **Verdikte** als reine Funktionen, jede Zahl im Text (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 104 Stellen im Kern `pln_algorithm.py`, 94 Mutanten gefangen (ganze Suite 100 %, nur die Orakel-Tests 65 %), 10 Stellen als äquivalent festgehalten (Sortierungen, deren Reihenfolge nichts ändert, und Zählschleifen über Knoten ohne Kanten); der Stand steht in `tests/mutation_state.json`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an beiden Enden), Layout, Footer, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `pln_algorithm.py` | Kern: Streckenkreuzungen, Greedy- und Überdeckungsgerüst, Rotationssystem und Flächen, Einsetzen über den Dualgraphen, Rückbau, Schiefheit |
| `pln_constants.py` | Regler-Grenzen, Rechengrenzen, feste Pläne, Farben, Presets |
| `pln_evaluation.py` | Analyse, Urteile (reine Funktionen), Messreihen |
| `pln_scenario.py` | Karten mit Zusatzkanten, klassische Graphen, Toronto |
| `pln_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `pln_layout.py` | Fester Kopf (Stylesheet) |
| `pln_presets.py` | Permalink (Begrenzen), Presets (Schnellstart oben, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `data/toronto_campus.json`, `data/LICENSE-ODbL.md` | Straßenkarte (OpenStreetMap, ODbL; Kopie aus `graph-zeichnen-demo`) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt, mit `networkx`) |
| `tests/` | Handrechnung, Orakel, Szenario, Randfälle, Verdikte, Claims, Darstellung, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Optimale Kreuzungszahl** (NP-schwer): nur Obergrenzen durch ein Verfahren.
- **Verbessern der Einfügereihenfolge** und **Einfügen mehrerer Kanten zugleich:** eigene Aufgaben.
- **Greedy auf der ganzen Toronto-Karte** in der App (275 s): nur in der Vormessung.
- **Brücken und Tunnel aus den Kartendaten:** die Daten enthalten keine Marken.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy und NetworkX.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
