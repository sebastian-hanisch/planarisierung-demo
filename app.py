"""Fast planare Netze – Planarisieren - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import math

import streamlit as st

import pln_constants as C
import pln_evaluation as ev
from pln_layout import dunkles_design, kopf_css
from pln_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from pln_visualization import build_classic, build_crossings, build_embedding, build_net, build_order, build_per_edge

st.set_page_config(page_title="Fast planare Netze – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _classic():
    return ev.classic_series()


@st.cache_data(show_spinner=False)
def _order():
    return ev.order_series()


@st.cache_data(show_spinner=False)
def _embedding():
    return ev.embedding_series()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in pln_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("✂️ Fast planare Netze – Planarisieren")
st.markdown(
    """
Ein Straßennetz, ein Leitungsplan, eine Landkarte mit ein paar Fernverbindungen: **fast** planar, aber nicht ganz. Wie viele Kanten muss man entfernen, damit das Netz planar wird (**Schiefheit**), und wie viele **Kreuzungen** bleiben, wenn man sie wieder einsetzt?
Das Verfahren der **Planarisierung** bildet erst ein **planares Gerüst** (Greedy: Kanten der Reihe nach einfügen, solange der Graph planar bleibt), setzt dann jede übrige Kante über den **kürzesten Weg im Dualgraphen** ein
und schreibt jede Kreuzung als Hilfsknoten fest. Die Zahl der Kreuzungen ist eine **Obergrenze der Kreuzungszahl** (sie selbst ist NP-schwer), kein Optimum.
Die Demo misst, was die Reihenfolge des Greedy und die Wahl des Gerüsts ausmachen, wie viel weniger Kreuzungen das gegenüber **geraden Strecken** gibt, und wie viel vom Befund der **Straßenkarte von Toronto** ein Artefakt der Zeichnung ist.
Neuntes (optionales) Stück der Linie *Planarität und Zeichnen*; Voraussetzungen: `planaritaet-demo` (Planarität, Einbettung), `planar-dual-demo` (Dualgraph, kürzester Weg), `graph-zeichnen-demo` (Toronto-Karte, Kreuzungen).

Weiter unten: **🔬 Kante für Kante einsetzen**, **🔬 Messreihen** (klassische Graphen, Reihenfolge, Einbettung und Toronto), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So planarisiert man", expanded=True):
    st.markdown(
        """
1. **Planares Gerüst:** Der Greedy fügt die Kanten in einer Reihenfolge ein (kürzeste zuerst oder zufällig) und lehnt jede Kante ab, die den Graphen nichtplanar machen würde. Alternativ wird das Gerüst durch **Überdeckung der Streckenkreuzungen** gebildet (wiederholt die Kante mit den meisten Kreuzungen entfernen); dessen Streckenzeichnung ist kreuzungsfrei.
2. **Einbettung und Flächen:** Das Gerüst hat eine Einbettung (die Reihenfolge der Kanten um jeden Knoten); sie zerlegt die Ebene in Flächen. Man nimmt sie aus den **Koordinaten** (Winkel) oder beliebig von `networkx`.
3. **Einsetzen:** Für jede entfernte Kante wird im **Dualgraphen** der kürzeste Weg von einer Fläche an ihrem einen Ende zu einer Fläche an ihrem anderen Ende gesucht; jede gekreuzte Kante bekommt einen **Hilfsknoten** (rotes Kreuz), und die Einbettung wird fortgeschrieben. Danach ist das Netz wieder planar.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    vehicle = st.selectbox("Netz", list(C.VEHICLES), key="vehicle_select", format_func=C.VEHICLES.get, help=C.VEHICLE_HELP)
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", help="Bei der Karte die Zahl der Standorte, bei Toronto die Zahl der Knoten um die Mitte; wirkt bei klassischen Graphen nicht.")
    extras = st.slider("Zusatzkanten", *bounds("extras_slider"), key="extras_slider", help="Zufällige Fernverbindungen zusätzlich zur planaren Karte; wirkt nur bei der Karte.")
    classic = st.selectbox("Klassischer Graph", list(C.CLASSIC_NAMES), key="classic_select", help="Wirkt nur beim klassischen Graphen; die Kreuzungszahlen stammen aus dem Gedächtnis.")
    skeleton = st.selectbox("Planares Gerüst", list(C.SKELETONS), key="skeleton_select", format_func=C.SKELETONS.get, help=C.SKELETON_HELP)
    embedding = st.selectbox("Einbettung", list(C.EMBEDDINGS), key="embedding_select", format_func=C.EMBEDDINGS.get, help=C.EMBEDDING_HELP)
    tries = st.slider("Versuche (zufälliger Greedy)", *bounds("tries_slider"), key="tries_slider", help="Beste Planarisierung aus so vielen zufälligen Reihenfolgen; wirkt nur beim Gerüst „Greedy, zufällige Reihenfolge“.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({
    "vehicle_select": vehicle, "n_slider": int(n), "extras_slider": int(extras), "classic_select": classic, "skeleton_select": skeleton, "embedding_select": embedding,
    "tries_slider": int(tries), "seed_input": int(seed),
})

settings = ev.Settings(vehicle, int(n), int(extras), classic, skeleton, embedding, int(tries), int(seed))
with st.spinner("Planarisiere..."):
    a = _analysis(settings)
g = a.graph
run = a.run

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Netz", f"{g.n} Knoten", delta=f"{ev.num(g.m)} Kanten", delta_color="off", help="Knoten und Kanten des Netzes.")
m2.metric("Streckenkreuzungen", ev.num(a.straight), delta="gerade Strecken", delta_color="off", help="Kantenpaare ohne gemeinsamen Endpunkt, die sich als Strecken zwischen den gegebenen Lagen kreuzen.")
m3.metric("Entfernte Kanten", ev.num(len(run.removed)), delta=f"Gerüst: {ev.num(len(run.kept))} Kanten", delta_color="off", help="Kanten, die nicht im planaren Gerüst liegen und eingesetzt werden müssen.")
m4.metric("Kreuzungen (Planarisierung)", ev.num(run.crossings), delta=f"{ev.num(100 * a.share_at_most_one, 0)} % der Kanten mit höchstens 1" if run.removed else "planar", delta_color="off",
          help="Hilfsknoten der Planarisierung: eine Obergrenze der Kreuzungszahl, kein Optimum.")
kind, text = ev.verdict_planarization(a)
getattr(st, kind)(text)
st.plotly_chart(build_net(g, run, title=f"{g.name}: {ev.num(run.crossings)} Kreuzungen"), width="stretch", key="main_chart")
st.caption(
    "Graue Linien: Kanten des Gerüsts (als Strecken), rot: eingesetzte Kanten als Streckenzug durch ihre Kreuzungspunkte, schwarze Kreuze: Kreuzungen (Hilfsknoten, in der Mitte der gekreuzten Kante dargestellt; "
    f"die Darstellung kann Kreuzungen der Strecken vortäuschen). Einbettung: {C.EMBEDDINGS[run.embedding_used][0].lower() + C.EMBEDDINGS[run.embedding_used][1:]}; Rechenzeit {ev.ms_text(a.seconds)}."
)
if run.removed:
    st.plotly_chart(build_per_edge(a.per_edge), width="stretch", key="chart_per_edge")

st.markdown("---")

# --- Kante für Kante einsetzen ---------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Kante für Kante einsetzen")
if not run.removed:
    st.info("Das Netz ist planar: es gibt keine Kante einzusetzen. Mit Zusatzkanten oder einem anderen Netz erscheint hier der Ablauf.")
else:
    total = len(a.inserted)
    st.session_state["step"] = min(st.session_state.get("step", total), total)
    step = st.slider("Eingesetzte Kanten", 1, total, key="step", help="Die entfernten Kanten werden in dieser Reihenfolge eingesetzt (zufällig mit festem Seed); das Bild zeigt die ersten so vielen.") if total > 1 else 1
    ins = a.inserted[step - 1]
    st.plotly_chart(build_net(g, run, shown=step, title=f"Nach {step} von {total} eingesetzten Kanten"), width="stretch", key="step_chart")
    length = math.dist(g.pos[ins.edge[0]], g.pos[ins.edge[1]])
    st.caption(f"Zuletzt eingesetzt: Kante {ins.edge[0]} – {ins.edge[1]} (Länge {ev.num(length, 3)}) mit {ev.plural(ins.crossings, 'Kreuzung', 'Kreuzungen')}.")
    st.dataframe(
        [{"Kante": f"{i.edge[0]} – {i.edge[1]}", "Länge": ev.num(math.dist(g.pos[i.edge[0]], g.pos[i.edge[1]]), 3), "Kreuzungen": i.crossings} for i in a.inserted[:step]],
        hide_index=True, width="stretch",
    )

st.markdown("---")

# --- Messreihen ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Messreihen")
st.markdown(
    f"Feste Pläne ({len(C.SWEEP_SEEDS)} je Zeile, Mediane), Karten mit {C.ORDER_N} Standorten. Kreuzungen und entfernte Kanten sind exakt, Zeiten gelten für diese Umsetzung; alle Kreuzungszahlen sind Obergrenzen durch ein Verfahren."
)
tab_classic, tab_order, tab_embed = st.tabs(["Klassische Graphen", "Reihenfolge und Strecken", "Einbettung und Toronto"])

with tab_classic:
    st.caption(f"K5, K6, K7, K3,3, K3,4, K3,5, K4,4 und der Petersen-Graph: die beste Planarisierung aus {C.CLASSIC_TRIES} zufälligen Reihenfolgen gegen die bekannte Kreuzungszahl (aus dem Gedächtnis).")
    if st.button("Klassische Graphen prüfen (wenige Sekunden)", key="classic_start"):
        st.session_state["classic_done"] = True
    if st.session_state.get("classic_done"):
        with st.spinner("Planarisiere die klassischen Graphen..."):
            rows = _classic()
        getattr(st, ev.verdict_classic(rows)[0])(ev.verdict_classic(rows)[1])
        st.dataframe(
            [{"Graph": r["name"], "Knoten": r["n"], "Kanten": r["m"], "Bekannte Kreuzungszahl": r["known"], "Beste Planarisierung": r["best"], "Erste Reihenfolge": r["first"], "Schlechteste": r["worst"],
              "Schiefheit": r["skewness"] if r["skewness"] is not None else f"≥ {r['euler_bound']} (Euler)", "Gleich": "ja" if r["equal"] else "nein"} for r in rows],
            hide_index=True, width="stretch",
        )
        st.plotly_chart(build_classic(rows), width="stretch", key="chart_classic")
with tab_order:
    st.caption(f"Karten mit {C.ORDER_N} Standorten und {', '.join(str(k) for k in C.ORDER_EXTRAS)} Zusatzkanten: vom Greedy entfernte Kanten (zufällig gegen kürzeste zuerst) und die Kreuzungen der Planarisierung gegen die geraden Strecken.")
    if st.button("Reihenfolge und Strecken messen (etwa 30 Sekunden)", key="order_start"):
        st.session_state["order_done"] = True
    if st.session_state.get("order_done"):
        with st.spinner("Rechne die Greedy-Gerüste und die Planarisierungen..."):
            rows = _order()
        getattr(st, ev.verdict_order(rows)[0])(ev.verdict_order(rows)[1])
        st.dataframe(
            [{"Zusatzkanten": r["extras"], "Streckenkreuzungen": ev.num(r["straight"]), "Entfernt (zufällig)": ev.num(r["removed_random"]), "Entfernt (kürzeste zuerst)": ev.num(r["removed_length"]),
              "Kreuzungen der Planarisierung": ev.num(r["crossings"]), "Verhältnis": ev.num(r["ratio"], 2), "Anteil mit höchstens 1 Kreuzung": f"{ev.num(100 * r['share'], 0)} %",
              "Kreuzungen je eingesetzter Kante (Median)": ev.num(r["per_edge"], 1)} for r in rows],
            hide_index=True, width="stretch",
        )
        left, right = st.columns(2)
        left.plotly_chart(build_order(rows), width="stretch", key="chart_order")
        right.plotly_chart(build_crossings(rows), width="stretch", key="chart_crossings")
with tab_embed:
    st.caption(f"Das Gerüst aus der Überdeckung der Streckenkreuzungen in zwei Einbettungen: Karten mit {C.EMBEDDING_N} Standorten und {C.EMBEDDING_EXTRAS} Zusatzkanten, und die ganze Toronto-Karte (5 072 Knoten, 7 621 Kanten).")
    if st.button("Einbettung und Toronto messen (einige Sekunden)", key="embed_start"):
        st.session_state["embed_done"] = True
    if st.session_state.get("embed_done"):
        with st.spinner("Planarisiere die Karten und Toronto..."):
            rows = _embedding()
        getattr(st, ev.verdict_embedding(rows)[0])(ev.verdict_embedding(rows)[1])
        st.dataframe(
            [{"Netz": r["name"], "Streckenkreuzungen": ev.num(r["straight"]), "Entfernte Kanten": ev.num(r["removed"]), "Kreuzungen (Koordinaten)": ev.num(r["geometry"]), "Kreuzungen (beliebig)": ev.num(r["arbitrary"]),
              "Kanten ohne Kreuzung (Koordinaten)": ev.num(r["zero_geometry"]), "Zeit (Koordinaten)": ev.ms_text(r["geometry_time"]), "Zeit (beliebig)": ev.ms_text(r["arbitrary_time"])} for r in rows],
            hide_index=True, width="stretch",
        )
        st.plotly_chart(build_embedding(rows), width="stretch", key="chart_embedding")

st.markdown("---")

# --- Wo die Annahmen enden -------------------------------------------------------------------------------------------------------------------

st.markdown("## 🚧 Wo die Annahmen enden")
st.markdown(
    f"""
- **Obergrenzen, keine Optima.** Die Kreuzungszahl eines Graphen ist NP-schwer; die Demo liefert die Kreuzungen eines Verfahrens (Gerüst, Einbettung, Einfügen Kante für Kante). Eine andere Reihenfolge kann weniger haben.
- **Die Reihenfolge des Greedy entscheidet.** In zufälliger Reihenfolge entfernt er oft ein Mehrfaches der nötigen Kanten; mit „kürzeste zuerst“ entfernt er auf Karten genau die Zusatzkanten. Das gilt für Karten mit Koordinaten, bei Graphen ohne Längen gibt es diese Ordnung nicht.
- **Die Einbettung ist nicht frei.** Eine Triangulierung hat bis auf die Spiegelung genau eine Einbettung; nur dünne Netze mit vielen Gelenken haben Spielraum. Die Einbettung aus den Koordinaten gilt nur, wenn die Streckenzeichnung des Gerüsts kreuzungsfrei ist; sonst rechnet die App mit einer beliebigen und sagt es.
- **Der Kürzeste Weg ist pro Kante optimal, nicht im Ganzen.** Jede Kante wird in die aktuelle Einbettung eingesetzt, die Reihenfolge und frühere Einsetzungen bestimmen, was später kreuzt.
- **Kreuzungen sind Hilfsknoten.** Die Zeichnung setzt sie in die Mitte der gekreuzten Kante; die Strecken zwischen diesen Punkten können sich in der Anzeige schneiden, ohne dass das eine Kreuzung der Planarisierung ist.
- **Toronto: Artefakt oder echt?** Das Netz ist kombinatorisch nicht planar (ein lokales K3,3), aber ein großer Teil der Streckenkreuzungen verschwindet in der richtigen Einbettung; ob Brücken, Tunnel oder nicht verschmolzene Knoten dahinterstecken, ist mit diesen Daten nicht entscheidbar.
- **Kreuzungszahlen klassischer Graphen aus dem Gedächtnis** (K5: 1, K6: 3, K7: 9, K3,3: 1, K3,4: 2, K3,5: 4, K4,4: 4, Petersen: 2); die Literaturangaben sind nicht im Original geprüft.
- **Die Ausschnittgröße begrenzt die Rechenzeit.** Der Planaritätstest läuft für jede Kante des Greedy; bei {C.N_MAX} Knoten dauert ein Lauf einige Sekunden.
    """
)

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        """
| Symbol | Bedeutung |
|---|---|
| $G=(V,E)$ | Graph mit $n$ Knoten und $m$ Kanten |
| $\\operatorname{sk}(G)$ | Schiefheit: kleinste Zahl von Kanten, nach deren Entfernen $G$ planar ist |
| $\\operatorname{cr}(G)$ | Kreuzungszahl: kleinste Zahl von Kreuzungen in einer Zeichnung von $G$ |
| $G'=(V,E')$ | planares Gerüst, $R=E\\setminus E'$ die entfernten Kanten |
| $F$ | Flächen der Einbettung von $G'$, $G'^{*}$ sein Dualgraph |

**Zusammenhang.** Jede Kreuzung lässt sich durch Entfernen einer ihrer zwei Kanten beseitigen, also

$$\\operatorname{sk}(G)\\;\\le\\;\\operatorname{cr}(G).$$

**Einsetzen einer Kante.** Für $e=(s,t)\\in R$ und eine feste Einbettung von $G'$ ist die kleinste Zahl von Kreuzungen, die $e$ mit Kanten von $G'$ hat, die Länge eines kürzesten Weges (jede Dualkante hat Länge 1) von einer Fläche an $s$ zu einer Fläche an $t$ in $G'^{*}$:

$$\\operatorname{cr}_{G'}(e)=\\min_{f\\ni s,\\;f'\\ni t}\\;\\operatorname{dist}_{G'^{*}}(f,f').$$

Die Summe über die nacheinander eingesetzten Kanten (jeweils in der aktuellen Planarisierung) ist eine Obergrenze von $\\operatorname{cr}(G)$.

**Euler.** Ein planarer Graph mit $n\\ge 3$ Knoten hat höchstens $3n-6$ Kanten (bipartit: $2n-4$), also $\\operatorname{sk}(G)\\ge m-(3n-6)$.

**1-planar.** Ein Graph heißt 1-planar, wenn er so gezeichnet werden kann, dass jede Kante höchstens einmal gekreuzt wird; die Demo zählt den Anteil der eingesetzten Kanten mit höchstens einer Kreuzung.

**Literatur** (nicht im Original gelesen; Angaben vor einer Zitation zu prüfen): Planarisierung durch kürzeste Dualwege nach Tamassia u. a. und Gutwenger, Mutzel und Weiskircher; Garey und Johnson, *Crossing number is NP-complete* (1983); Zarankiewicz und Guy zu den Kreuzungszahlen vollständiger (bipartiter) Graphen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
