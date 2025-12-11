# bonsai_space_colonization.py
#
# Ein einfacher 2D-Bonsai-Generator auf Basis des Space-Colonization-Algorithmus.
# Inspiriert von Runions et al. (2007) und nach außen als Matplotlib-Figure nutzbar.
#
# API:
#   fig = generate_bonsai_figure(metrics_summary)
#   -> fig kann in Streamlit mit st.pyplot(fig) angezeigt werden.

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

import matplotlib.pyplot as plt


# -----------------------------
# Datenklassen
# -----------------------------

@dataclass
class Attractor:
    x: float
    y: float
    active: bool = True


@dataclass
class Branch:
    x: float
    y: float
    parent_index: Optional[int]
    direction_x: float
    direction_y: float
    depth: int


# -----------------------------
# Hilfsfunktionen
# -----------------------------

def _normalize(vx: float, vy: float) -> Tuple[float, float]:
    length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0
    return vx / length, vy / length


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


# -----------------------------
# Bonsai-Parameter
# -----------------------------

@dataclass
class BonsaiParams:
    """
    Parameter für den Space-Colonization-Baum.
    Viele davon werden später leicht an Disce-Metriken gekoppelt.
    """
    crown_radius: float = 1.0
    crown_height: float = 1.2
    trunk_height: float = 0.4
    num_attractors: int = 400

    influence_radius: float = 0.25    # Radius, in dem ein Ast von einem Blatt angezogen wird
    kill_radius: float = 0.08         # Abstand, bei dem ein Blatt als "erreicht" gilt
    branch_step: float = 0.03         # Länge eines neuen Astsegments pro Iteration
    max_iterations: int = 200

    # Form-Parameter für bonsai-typische Silhouetten
    # 0 = runde Krone; >0 = stärker zur Seite gezogen (bspw. "Kaskaden-Bonsai")
    lean_factor: float = 0.0

    # zufällige Variation
    direction_jitter: float = 0.2


def _params_from_metrics(metrics: Dict) -> BonsaiParams:
    """
    Erzeugt BonsaiParams heuristisch aus Disce-Metriken (metrics_summary oder disce_metrics).
    Alles sehr vorsichtig skaliert, damit der Baum nie 'kaputt' geht.
    """
    # Fallbacks
    dims = metrics.get("dims", {})
    text_difficulty = float(dims.get("text_difficulty", 0.5))
    synt_complexity = float(dims.get("syntactic_complexity", 0.4))
    cohesion = float(dims.get("cohesion", 0.4))
    register_informality = float(dims.get("register_informality", 0.2))

    # Krone: höher/schlanker bei höherer Komplexität
    crown_height = _lerp(1.0, 1.5, synt_complexity)
    crown_radius = _lerp(0.8, 1.2, cohesion)  # mehr Kohäsion → leicht breiter

    # Anzahl Attraktoren ~ "Komplexität" & "Schwierigkeit"
    num_attractors = int(300 + 300 * (text_difficulty))

    # Stammhöhe: etwas höher bei schwierigerem / formellerem Text
    trunk_height = _lerp(0.3, 0.5, text_difficulty)

    # lean_factor: informeller = leicht schiefer Baum
    lean_factor = _lerp(0.0, 0.5, register_informality)

    # Schrittweite: etwas größer bei höherer syntaktischer Komplexität
    branch_step = _lerp(0.025, 0.04, synt_complexity)

    # Iterationen: moderat erhöhen mit text_difficulty
    max_iterations = int(160 + 80 * text_difficulty)

    return BonsaiParams(
        crown_radius=crown_radius,
        crown_height=crown_height,
        trunk_height=trunk_height,
        num_attractors=num_attractors,
        influence_radius=0.25,
        kill_radius=0.07,
        branch_step=branch_step,
        max_iterations=max_iterations,
        lean_factor=lean_factor,
        direction_jitter=0.18,
    )


# -----------------------------
# Attractor-Generierung (Kronenvolumen)
# -----------------------------

def _generate_bonsai_attractors(params: BonsaiParams) -> List[Attractor]:
    """
    Erzeugt zufällige Attraktoren im Kronenvolumen eines Bonsai.
    Wir nehmen eine kappenförmige / leicht asymmetrische Kontur.
    """
    attractors: List[Attractor] = []

    for _ in range(params.num_attractors):
        # y im Kronenbereich (0 = Wurzel, nach oben positiv)
        y = random.uniform(params.trunk_height, params.trunk_height + params.crown_height)

        # normierte Höhe in der Krone (0..1)
        t = (y - params.trunk_height) / params.crown_height

        # horizontaler Radius: oben enger, unten breiter (Bonsai-Schirm)
        # Form: leicht nach außen gewölbt
        base_radius = params.crown_radius * (0.5 + 0.7 * (1 - abs(2 * t - 1)))
        # lean_factor: Kippung nach rechts/links
        x_center = params.lean_factor * (t - 0.3)

        # zufälliger Punkt im Querschnitt (x in [-base_radius, base_radius])
        x = random.uniform(-base_radius, base_radius)
        x += x_center

        attractors.append(Attractor(x=x, y=y))

    return attractors


def _initialize_trunk(attractors: List[Attractor], params: BonsaiParams) -> List[Branch]:
    """
    Lässt den Stamm von (0,0) nach oben wachsen, bis er in den Einflussbereich
    der Krone kommt (oder die Kronenhöhe überschritten ist).
    Dadurch haben die ersten Attraktoren überhaupt eine Chance, Äste anzuziehen.
    """
    branches: List[Branch] = [
        Branch(x=0.0, y=0.0, parent_index=None, direction_x=0.0, direction_y=1.0, depth=0)
    ]

    # Solange der letzte Stamm-Branch noch "weit weg" von allen Attraktoren ist,
    # wächst er Schritt für Schritt nach oben.
    max_trunk_iterations = 200  # Sicherheitsgrenze
    for _ in range(max_trunk_iterations):
        last = branches[-1]

        # Abstand zur nächstgelegenen Attraktor
        if attractors:
            min_dist = min(math.hypot(a.x - last.x, a.y - last.y) for a in attractors)
        else:
            min_dist = float("inf")

        # Wenn wir nah genug an der Krone sind, brechen wir ab
        if min_dist < params.influence_radius * 1.2:
            break

        # Oder wenn wir die geplante Kronenhöhe überschreiten, auch abbrechen
        if last.y > params.trunk_height + params.crown_height:
            break

        # Sonst Stamm weiter nach oben wachsen lassen
        new_y = last.y + params.branch_step
        new_branch = Branch(
            x=last.x,
            y=new_y,
            parent_index=len(branches) - 1,
            direction_x=0.0,
            direction_y=1.0,
            depth=last.depth + 1,
        )
        branches.append(new_branch)

    return branches



# -----------------------------
# Space-Colonization-Hauptschleife (2D)
# -----------------------------

def _grow_tree(params: BonsaiParams) -> Tuple[List[Branch], List[Attractor]]:
    """
    Führt den Space-Colonization-Algorithmus in 2D aus und liefert:
    - Liste von Branch-Segmenten
    - (verbleibende) Attractors
    """
    attractors = _generate_bonsai_attractors(params)

    # Stamm initialisieren und bis in den Einflussbereich der Krone ziehen
    branches: List[Branch] = _initialize_trunk(attractors, params)



    iteration = 0
    while iteration < params.max_iterations and any(a.active for a in attractors):
        iteration += 1

        # 1. Für jeden Attractor: nächstgelegenen Branch innerhalb influence_radius finden
        attraction_map: Dict[int, Tuple[float, float, int]] = {}
        # dict: branch_index -> (sum_dx, sum_dy, count)

        for attractor in attractors:
            if not attractor.active:
                continue

            closest_idx = None
            closest_dist = float("inf")

            for i, br in enumerate(branches):
                dx = attractor.x - br.x
                dy = attractor.y - br.y
                dist = math.hypot(dx, dy)

                if dist < params.kill_radius:
                    # Blatt ist erreicht -> wird deaktiviert
                    attractor.active = False
                    closest_idx = None
                    break

                if dist < params.influence_radius and dist < closest_dist:
                    closest_dist = dist
                    closest_idx = i

            if closest_idx is not None:
                dx = attractor.x - branches[closest_idx].x
                dy = attractor.y - branches[closest_idx].y
                dir_x, dir_y = _normalize(dx, dy)

                if closest_idx not in attraction_map:
                    attraction_map[closest_idx] = (dir_x, dir_y, 1)
                else:
                    sx, sy, c = attraction_map[closest_idx]
                    attraction_map[closest_idx] = (sx + dir_x, sy + dir_y, c + 1)

        if not attraction_map:
            # Keine aktiven Attractors mehr in Reichweite -> Ende
            break

        # 2. Für jeden Branch mit Attractors: neuen Branch entlang der gemittelten Richtung erzeugen
        new_branches: List[Branch] = []
        for idx, (sx, sy, count) in attraction_map.items():
            br = branches[idx]
            avg_dx = sx / count
            avg_dy = sy / count
            ndx, ndy = _normalize(avg_dx, avg_dy)

            # kleine zufällige Variation hinzufügen
            jitter_angle = (random.random() - 0.5) * params.direction_jitter * math.pi
            cos_a = math.cos(jitter_angle)
            sin_a = math.sin(jitter_angle)
            jdx = ndx * cos_a - ndy * sin_a
            jdy = ndx * sin_a + ndy * cos_a
            jdx, jdy = _normalize(jdx, jdy)

            new_x = br.x + jdx * params.branch_step
            new_y = br.y + jdy * params.branch_step

            new_branches.append(
                Branch(
                    x=new_x,
                    y=new_y,
                    parent_index=idx,
                    direction_x=jdx,
                    direction_y=jdy,
                    depth=br.depth + 1,
                )
            )

        branches.extend(new_branches)

    return branches, attractors


# -----------------------------
# Visualisierung mit Matplotlib
# -----------------------------

def _draw_bonsai(branches: List[Branch], params: BonsaiParams) -> plt.Figure:
    """
    Zeichnet die Branch-Segmente als Linien mit dickerem Stamm und dünnen Ästen.
    """
    fig, ax = plt.subplots(figsize=(4, 5), dpi=150)

    # Basis-Strichstärke nach Tiefe: Stamm dicker, oben dünner
    max_depth = max((b.depth for b in branches), default=1)

    for i, br in enumerate(branches):
        if br.parent_index is None:
            continue
        parent = branches[br.parent_index]

        # Dicke: linear von 4px (Stamm) zu 0.5px (feine Äste)
        t = br.depth / max_depth if max_depth > 0 else 0.0
        width = _lerp(4.0, 0.5, t)

        # Farbe: braun unten, grünlich oben
        r = _lerp(90, 40, t) / 255.0
        g = _lerp(60, 120, t) / 255.0
        b = _lerp(40, 50, t) / 255.0

        ax.plot(
            [parent.x, br.x],
            [parent.y, br.y],
            color=(r, g, b),
            linewidth=width,
            solid_capstyle="round",
        )

    # Bodenlinie
    ax.plot([-1.2, 1.2], [0, 0], color="#444444", linewidth=1.0)

    # Achsen-Einstellungen: Bonsai im Fokus
    ax.set_aspect("equal", "box")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.2, params.trunk_height + params.crown_height + 0.2)
    ax.axis("off")

    fig.tight_layout(pad=0.1)
    return fig


# -----------------------------
# Haupt-API
# -----------------------------

def generate_bonsai_figure(metrics: Dict | None = None) -> plt.Figure:
    """
    Erzeugt eine Matplotlib-Figure mit einem 2D-Bonsai, der leicht
    an Disce-Metriken angepasst wird.

    metrics kann entweder ein 'metrics_summary' aus disce_core.analyze_text_for_ui
    oder ein darauf basierendes Objekt sein.
    """
    if metrics is None:
        metrics = {}

    params = _params_from_metrics(metrics)
    branches, _ = _grow_tree(params)
    fig = _draw_bonsai(branches, params)
    return fig


# Optional: Testlauf, wenn Datei direkt ausgeführt wird
if __name__ == "__main__":
    # Dummy-Metriken für schnellen Test
    dummy_dims = {
        "dims": {
            "text_difficulty": 0.7,
            "syntactic_complexity": 0.5,
            "cohesion": 0.4,
            "register_informality": 0.2,
        }
    }
    fig = generate_bonsai_figure(dummy_dims)
    plt.show()
