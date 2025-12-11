# bonsai_lsystem.py
#
# Ein 2D-Bonsai-Renderer auf Basis eines einfachen L-Systems + Turtle-Grafik.
# Ziel: Die 6 Disce-Dimensionen (grammar_accuracy, syntactic_complexity,
# lexical_diversity, cohesion, text_difficulty, register_informality/written_formality)
# werden deterministisch auf Baumparameter gemappt.
#
# API:
#   fig = generate_bonsai_figure(metrics_or_dims)
#   -> fig kann in Streamlit mit st.pyplot(fig) angezeigt werden.
#
#   metrics_or_dims kann entweder:
#     - ein dict mit "dims": {...} sein (z.B. metrics_summary)
#     - oder direkt das dims-Dict aus analyze_text_for_ui (result["dims"])

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import math
import matplotlib.pyplot as plt


# -----------------------------
# Hilfsfunktionen
# -----------------------------


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _safe_dim(dims: Dict, key: str, default: float) -> float:
    val = dims.get(key, default)
    try:
        return float(val)
    except Exception:
        return default


# -----------------------------
# Parameter-Datenklasse
# -----------------------------


@dataclass
class LSystemBonsaiParams:
    iterations: int
    angle_min_deg: float
    angle_max_deg: float
    segment_length: float
    length_decay: float
    thickness_start: float
    thickness_decay: float
    lean_angle_deg: float
    leaf_probability: float
    leaf_size: float


# -----------------------------
# Mapping: 6 Dimensionen → Baum-Parameter
# -----------------------------


def params_from_dims(dims: Dict) -> LSystemBonsaiParams:
    """
    Nimmt das dims-Dict aus compute_dimension_scores(...) und
    baut klar interpretierbare Baum-Parameter.

    Erwartete Keys in dims:
      - "grammar_accuracy"
      - "syntactic_complexity"
      - "lexical_diversity"
      - "cohesion"
      - "text_difficulty"
      - "register_informality"
      - "written_formality" (üblicherweise 1 - register_informality)
    """

    grammar_accuracy = _clamp(_safe_dim(dims, "grammar_accuracy", 0.7))
    synt_complexity = _clamp(_safe_dim(dims, "syntactic_complexity", 0.4))
    lexical_div = _clamp(_safe_dim(dims, "lexical_diversity", 0.7))
    cohesion = _clamp(_safe_dim(dims, "cohesion", 0.4))
    text_difficulty = _clamp(_safe_dim(dims, "text_difficulty", 0.5))
    register_informality = _clamp(_safe_dim(dims, "register_informality", 0.2))
    # written_formality = 1 - register_informality — wird unten indirekt genutzt

    # 1) Iterationstiefe – Syntaktische Komplexität & Schwierigkeit
    #    3..7 Iterationen: mehr Tiefe = komplexerer Baum
    iterations_float = 3 + synt_complexity * 3 + text_difficulty * 1
    iterations = int(round(iterations_float))
    iterations = max(3, min(7, iterations))

    # 2) Segmentlänge – Textschwierigkeit (höhere Schwierigkeit = größerer Baum)
    #    Normale Segmentlänge: 0.12..0.25 im "Baumraum"
    segment_length = _lerp(0.12, 0.25, text_difficulty)

    # 3) Längenabnahme pro Tiefe – syntaktische Komplexität
    #    0.65..0.85 – hohe Komplexität => Äste bleiben länger, Krone fülliger
    length_decay = _lerp(0.65, 0.85, synt_complexity)

    # 4) Dicke (Stamm) + Abnahme – Grammatikgenauigkeit + Schwierigkeit
    #    Startdicke 4..9; hoher text_difficulty => kräftiger Stamm
    thickness_start = _lerp(4.0, 9.0, text_difficulty)

    #    Dicke-Abnahme: 0.5..0.8 – hohe grammar_accuracy => stabiler, weniger "brüchig"
    thickness_decay = _lerp(0.5, 0.8, grammar_accuracy)

    # 5) Winkelbereich – Kohäsion: niedrige Kohäsion => "zerfaserte" Krone, größere Winkelstreuung
    #    Basismittelwinkel 25°; Range 8°..25°
    base_angle = 25.0
    angle_range = _lerp(25.0, 8.0, cohesion)  # viel Kohäsion -> enger, "geordneter"
    angle_min_deg = base_angle - angle_range / 2.0
    angle_max_deg = base_angle + angle_range / 2.0

    # 6) Lean – Register: informeller => Baum neigt sich
    #    -18°..+18°
    lean_angle_deg = (register_informality - 0.5) * 36.0

    # 7) Blattdichte & -größe – Lexikalische Diversität
    #    Mehr Diversität => mehr & größere Blätter
    leaf_probability = _lerp(0.35, 0.85, lexical_div)
    leaf_size = _lerp(0.01, 0.03, lexical_div)  # relativ zur Figurgröße

    return LSystemBonsaiParams(
        iterations=iterations,
        angle_min_deg=angle_min_deg,
        angle_max_deg=angle_max_deg,
        segment_length=segment_length,
        length_decay=length_decay,
        thickness_start=thickness_start,
        thickness_decay=thickness_decay,
        lean_angle_deg=lean_angle_deg,
        leaf_probability=leaf_probability,
        leaf_size=leaf_size,
    )


# -----------------------------
# L-System-Generierung
# -----------------------------


def build_lsystem_string(axiom: str, rules: Dict[str, str], iterations: int) -> str:
    """
    Einfache L-System-Expansion:
      - axiom: Startstring (z.B. "F")
      - rules: Dict wie {"F": "F[+F]F[-F]F"}
      - iterations: Anzahl der Anwendungen
    """
    current = axiom
    for _ in range(iterations):
        next_s = []
        for ch in current:
            if ch in rules:
                next_s.append(rules[ch])
            else:
                next_s.append(ch)
        current = "".join(next_s)
    return current


# -----------------------------
# Turtle-Interpreter & Zeichnen
# -----------------------------


def _draw_bonsai_from_string(s: str, params: LSystemBonsaiParams):
    """
    Interpretiert das L-System-String als Turtle-Kommandos und
    liefert eine Matplotlib-Figure zurück.

    Alphabet:
      F  : vorwärts zeichnen
      +  : drehen (rechts)
      -  : drehen (links)
      [  : Zustand pushen
      ]  : Zustand poppen
    """
    fig, ax = plt.subplots(figsize=(4, 5), dpi=150)

    # Initialzustand: Stammfuß bei (0, 0), Blick nach oben (90°),
    # Lean-Winkel als Anfangs-Tilt
    angle_deg = 90.0 + params.lean_angle_deg
    x, y = 0.0, 0.0
    thickness = params.thickness_start
    depth = 0

    state_stack = []

    # Für Skalierung: wir merken uns min/max-Koordinaten beim Zeichnen
    min_x = max_x = x
    min_y = max_y = y

    # Linien und Blätter gleich zeichnen
    for ch in s:
        if ch == "F":
            # Strich zeichnen
            rad = math.radians(angle_deg)
            dx = math.cos(rad) * params.segment_length * (params.length_decay ** depth)
            dy = math.sin(rad) * params.segment_length * (params.length_decay ** depth)

            new_x = x + dx
            new_y = y + dy

            # Liniendicke abhängig von Tiefe
            line_width = max(0.5, thickness * (params.thickness_decay ** depth))

            # Farbe: Stamm unten braun, oben grünlicher – via Tiefe
            t = _clamp(depth / 12.0)  # grobe Tiefennormierung
            r = _lerp(90, 40, t) / 255.0
            g = _lerp(60, 140, t) / 255.0
            b = _lerp(40, 60, t) / 255.0

            ax.plot(
                [x, new_x],
                [y, new_y],
                color=(r, g, b),
                linewidth=line_width,
                solid_capstyle="round",
            )

            # Blätter: an tiefen Ästen mit gewisser Wahrscheinlichkeit
            if depth >= 3 and params.leaf_probability > 0:
                # einfache Heuristik: immer Blätter an Enden, leichte Überzeichnung
                # (kein Zufall, damit deterministisch)
                # Größe abhängig von leaf_size
                leaf_r = params.leaf_size
                ax.scatter(
                    [new_x],
                    [new_y],
                    s=(leaf_r * 1000),
                    c=[(0.2, 0.6, 0.2, 0.8)],
                    marker="o",
                    linewidths=0,
                )

            # Position updaten
            x, y = new_x, new_y
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)

        elif ch == "+":
            # Drehung nach rechts (positive Richtung)
            angle = _lerp(params.angle_min_deg, params.angle_max_deg, 0.75)
            angle_deg -= angle
        elif ch == "-":
            # Drehung nach links
            angle = _lerp(params.angle_min_deg, params.angle_max_deg, 0.25)
            angle_deg += angle
        elif ch == "[":
            # Zustand pushen
            state_stack.append((x, y, angle_deg, depth))
            depth += 1
        elif ch == "]":
            # Zustand poppen
            if state_stack:
                x, y, angle_deg, saved_depth = state_stack.pop()
                depth = saved_depth

    # Bodenlinie
    ax.plot([min_x - 0.2, max_x + 0.2], [0, 0], color="#444444", linewidth=1.0)

    # Achsen / Ansicht
    ax.set_aspect("equal", "box")
    # Leicht erweitern, damit Krone nicht angeschnitten wird
    x_margin = 0.3
    y_margin = 0.3
    ax.set_xlim(min_x - x_margin, max_x + x_margin)
    ax.set_ylim(-0.2, max_y + y_margin)
    ax.axis("off")

    fig.tight_layout(pad=0.1)
    return fig


# -----------------------------
# Haupt-API
# -----------------------------


def generate_bonsai_figure(metrics_or_dims: Dict | None = None):
    """
    Erzeugt eine Matplotlib-Figure mit einem 2D-LSystem-Bonsai.

    metrics_or_dims:
      - entweder ein Dict mit "dims": {...}
      - oder direkt das dims-Dict (wie result["dims"] aus analyze_text_for_ui)
    """
    if metrics_or_dims is None:
        dims = {}
    elif "dims" in metrics_or_dims:
        dims = metrics_or_dims["dims"] or {}
    else:
        dims = metrics_or_dims or {}

    params = params_from_dims(dims)

    # Einfaches Baum-L-System:
    #   F  -> F[+F]F[-F]F
    #   axiom: F
    # Mit 3–7 Iterationen erzeugt das hübsch verzweigte Bäume.
    axiom = "F"
    rules = {
        "F": "F[+F]F[-F]F"
    }

    s = build_lsystem_string(axiom, rules, params.iterations)
    
    # Debug-Ausgabe in die Konsole
    print("Bonsai debug:",
          "iterations=", params.iterations,
          "len_string=", len(s))
    
    fig = _draw_bonsai_from_string(s, params)
    return fig


# Optionaler Testlauf
if __name__ == "__main__":
    # grobe Testdims
    test_dims = {
        "grammar_accuracy": 0.8,
        "syntactic_complexity": 0.6,
        "lexical_diversity": 0.7,
        "cohesion": 0.5,
        "text_difficulty": 0.65,
        "register_informality": 0.2,
    }
    fig = generate_bonsai_figure({"dims": test_dims})
    fig.savefig("bonsai_lsystem_test.png")
