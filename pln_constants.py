"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Pläne, Farben und Presets."""

VEHICLES = {"delaunay": "Karte mit Zusatzkanten", "toronto": "Straßenkarte Toronto (Ausschnitt)", "classic": "Klassischer Graph"}
VEHICLE_HELP = (
    "Karte: zufällige Standorte mit allen Delaunay-Kanten (planar) und zufälligen Zusatzkanten, den „Fernverbindungen“. Toronto: die n Knoten um die Mitte der OpenStreetMap-Karte (Meter). "
    "Klassischer Graph: K5, K6, K7, K3,3, K3,4, K3,5, K4,4 oder Petersen, mit bekannter Kreuzungszahl (aus dem Gedächtnis)."
)
DEFAULT_VEHICLE = "delaunay"

CLASSIC_NAMES = ("K5", "K6", "K7", "K3,3", "K3,4", "K3,5", "K4,4", "Petersen")
DEFAULT_CLASSIC = "K4,4"

SKELETONS = {
    "length": "Greedy, kürzeste Kante zuerst",
    "random": "Greedy, zufällige Reihenfolge",
    "cover": "Überdeckung der Streckenkreuzungen",
}
SKELETON_HELP = (
    "Das planare Gerüst, in das die übrigen Kanten eingesetzt werden. Greedy: Kanten der Reihe nach einfügen, solange der Graph planar bleibt (kürzeste zuerst oder zufällig). "
    "Überdeckung: wiederholt die Kante mit den meisten Streckenkreuzungen entfernen; das Gerüst hat dann eine kreuzungsfreie Zeichnung."
)
DEFAULT_SKELETON = "length"

EMBEDDINGS = {"geometry": "Aus den Koordinaten", "arbitrary": "Beliebig (networkx)"}
EMBEDDING_HELP = (
    "Die Einbettung des Gerüsts, in der der kürzeste Weg im Dualgraphen gesucht wird. Aus den Koordinaten: die Reihenfolge der Kanten um jeden Knoten nach dem Winkel (nur gültig, wenn die Streckenzeichnung des Gerüsts kreuzungsfrei ist; "
    "sonst fällt die App auf die beliebige Einbettung zurück und sagt es). Beliebig: irgendeine planare Einbettung, die `networkx` findet."
)
DEFAULT_EMBEDDING = "geometry"

N_MIN, N_MAX, DEFAULT_N = 20, 300, 100
EXTRAS_MIN, EXTRAS_MAX, DEFAULT_EXTRAS = 0, 40, 10
TRIES_MIN, TRIES_MAX, DEFAULT_TRIES = 1, 20, 1
SEED_MAX, DEFAULT_SEED = 999999, 35

INSERT_ORDER = "random"                           # Reihenfolge, in der die entfernten Kanten eingesetzt werden (mit festem Zufalls-Seed)
SWEEP_SEEDS = tuple(range(100000, 100005))        # feste Pläne für alle Messreihen: nie ein einzelner Seed als Befund
CLASSIC_TRIES = 100                               # Reihenfolgen je klassischem Graphen in der Reihe
EXACT_SKEWNESS_MAX_M = 16                         # exakte Schiefheit (Aufzählen) nur bis zu dieser Kantenzahl
ORDER_N = 100
ORDER_EXTRAS = (1, 2, 5, 10, 20, 40)
EMBEDDING_N = 100
EMBEDDING_EXTRAS = 10

COLOR_EDGE = "rgba(150,150,150,0.6)"
COLOR_INSERTED = "#d62728"
COLOR_CROSSING = "#222222"
COLOR_FIRST = "#2F6B65"
COLOR_SECOND = "#4c78a8"
COLOR_THIRD = "#e8a33d"

PRESETS = {
    "Karte mit 10 Zusatzkanten (Voreinstellung)": {"vehicle": DEFAULT_VEHICLE, "n": DEFAULT_N, "extras": DEFAULT_EXTRAS, "classic": DEFAULT_CLASSIC, "skeleton": DEFAULT_SKELETON, "embedding": DEFAULT_EMBEDDING, "tries": DEFAULT_TRIES, "seed": DEFAULT_SEED},
    "Zufällige Reihenfolge im Greedy": {"vehicle": DEFAULT_VEHICLE, "n": DEFAULT_N, "extras": DEFAULT_EXTRAS, "classic": DEFAULT_CLASSIC, "skeleton": "random", "embedding": "arbitrary", "tries": DEFAULT_TRIES, "seed": DEFAULT_SEED},
    "Viele Fernverbindungen (30 Zusatzkanten)": {"vehicle": DEFAULT_VEHICLE, "n": DEFAULT_N, "extras": 30, "classic": DEFAULT_CLASSIC, "skeleton": DEFAULT_SKELETON, "embedding": DEFAULT_EMBEDDING, "tries": DEFAULT_TRIES, "seed": DEFAULT_SEED},
    "Straßenausschnitt Toronto": {"vehicle": "toronto", "n": 250, "extras": DEFAULT_EXTRAS, "classic": DEFAULT_CLASSIC, "skeleton": "cover", "embedding": "geometry", "tries": DEFAULT_TRIES, "seed": DEFAULT_SEED},
    "Klassisch: K4,4 (Kreuzungszahl 4)": {"vehicle": "classic", "n": DEFAULT_N, "extras": DEFAULT_EXTRAS, "classic": DEFAULT_CLASSIC, "skeleton": "random", "embedding": "arbitrary", "tries": 10, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Karte mit 10 Zusatzkanten (Voreinstellung)": "100 Standorte mit 10 Fernverbindungen: das Gerüst ist die planare Karte, die Zusatzkanten werden über den kürzesten Dualweg eingesetzt; das gibt deutlich weniger Kreuzungen als gerade Strecken.",
    "Zufällige Reihenfolge im Greedy": "Dieselbe Karte, der Greedy fügt die Kanten in zufälliger Reihenfolge ein: er lehnt ein Mehrfaches der 10 Zusatzkanten ab und die Planarisierung braucht entsprechend mehr Kreuzungen.",
    "Viele Fernverbindungen (30 Zusatzkanten)": "Dieselbe Karte mit 30 Fernverbindungen: die Kreuzungen wachsen mit der Zahl der Zusatzkanten, die Fernkanten kreuzen sich auch untereinander.",
    "Straßenausschnitt Toronto": "250 Knoten um die Mitte der Karte: wenige Straßen kreuzen sich als gerade Strecken, die Planarisierung braucht noch weniger Kreuzungen.",
    "Klassisch: K4,4 (Kreuzungszahl 4)": "Der vollständige bipartite Graph K4,4: zehn zufällige Reihenfolgen, die beste liefert die bekannte Kreuzungszahl 4.",
}
