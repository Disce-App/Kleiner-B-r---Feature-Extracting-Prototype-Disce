# bonsai_disce_tree.py
#
# Port eines vereinfachten Disce-Tree-L-Systems von JS nach Python.
# - Axiom: "X"
# - Regel: X -> F[@[-X]+X]
# - Befehle: F, X, +, -, [, ], @
#
# Zeichnet mit matplotlib eine 2D-Baumfigur.
# Mapping: 6 Disce-Dimensionen -> TreeOptions (Iterations, Länge, Winkel, Farbe, usw.)

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Tuple

import math
import random
import matplotlib.pyplot as plt


# ---------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _safe_dim(dims: Dict, key: str, default: float) -> float:
    v = dims.get(key, default)
    try:
        return float(v)
    except Exception:
        return default


# ---------------------------------------------------
# Optionen analog zu treeLSystemData.options
# ---------------------------------------------------

@dataclass
class TreeOptions:
    iterations: int = 10
    length: float = 80.0
    length_decrease_ratio: float = 0.8
    width: float = 6.0
    width_decrease_ratio: float = 0.85
    color_r: float = 40.0
    color_g: float = 100.0
    color_b: float = 30.0
    color_decrease_ratio: float = 1.10
    angle_min: float = 10.0   # Grad
    angle_max: float = 35.0   # Grad
    length_randomness: float = 0.15
    angle_asymmetry: float = 0.25
    depth: int = 0


# ---------------------------------------------------
# Mapping: 6 Text-Dimensionen -> TreeOptions
# (vereinfachte Übertragung von DisceTreeMapper.metricsToOptions)
# ---------------------------------------------------

def options_from_dims(dims: Dict) -> TreeOptions:
    """
    dims: result["dims"] aus analyze_text_for_ui.
    Verwendete Keys:
      grammar_accuracy, syntactic_complexity,
      lexical_diversity, cohesion,
      text_difficulty, register_informality
    """

    grammar = _clamp(_safe_dim(dims, "grammar_accuracy", 0.7))
    synt = _clamp(_safe_dim(dims, "syntactic_complexity", 0.5))
    lex = _clamp(_safe_dim(dims, "lexical_diversity", 0.7))
    coh = _clamp(_safe_dim(dims, "cohesion", 0.5))
    diff = _clamp(_safe_dim(dims, "text_difficulty", 0.5))
    reg_inf = _clamp(_safe_dim(dims, "register_informality", 0.2))

    # Iterationen: 6–11, mehr bei höherer Schwierigkeit & Komplexität
    base_iterations = 6 + int(diff * 3) + int(synt * 2)
    iterations = max(6, min(11, base_iterations))

    # Länge: 60–140 (stärker bei Schwierigkeit + syntaktischer Komplexität)
    base_len = 60.0 + diff * 60.0 + synt * 20.0
    length = min(base_len, 140.0)

    # Dicke: 4–12, abhängig von Grammatik & Schwierigkeit
    base_width = 4.0 + grammar * 4.0 + diff * 4.0
    width = min(base_width, 12.0)

    # Winkelbereich: ähnlich wie dein JS-Mapping
    # Kohäsion hoch -> enger Winkel
    min_angle = 10.0 + (1.0 - coh) * 5.0      # 10–15
    max_angle = 20.0 + (1.0 - coh) * 10.0     # 20–30
    # + etwas Stretch über Schwierigkeit
    max_angle += diff * 5.0                   # +0–5
    min_angle = min(min_angle, 18.0)
    max_angle = min(max_angle, 35.0)

    # Längenverkürzung: 0.68–0.82, wie bei dir
    length_dec = 0.68 + synt * 0.14

    # Breitenverkürzung: 0.82–0.93, je nach Kohäsion
    width_dec = 0.82 + coh * 0.11

    # Zufall / Asymmetrie: mehr bei geringer Kohäsion & hoher Informalität
    length_rand = 0.05 + (1.0 - coh) * 0.15
    angle_asym = 0.05 + reg_inf * 0.20

    # Farbe grob an Schwierigkeitsgrad koppeln (dunkler/grüner)
    # hier stark vereinfacht
    color_r = 40.0
    color_g = 90.0 + diff * 50.0
    color_b = 30.0 + diff * 20.0
    color_dec = 1.10

    return TreeOptions(
        iterations=iterations,
        length=length,
        length_decrease_ratio=length_dec,
        width=width,
        width_decrease_ratio=width_dec,
        color_r=color_r,
        color_g=color_g,
        color_b=color_b,
        color_decrease_ratio=color_dec,
        angle_min=min_angle,
        angle_max=max_angle,
        length_randomness=length_rand,
        angle_asymmetry=angle_asym,
        depth=0,
    )


# ---------------------------------------------------
# L-System: X -> F[@[-X]+X]
# ---------------------------------------------------

def expand_lsystem(axiom: str, iterations: int) -> str:
    """
    Repliziert grob treeLSystemData:
      Regel: X -> F[@[-X]+X]
    """
    current = axiom
    rule_X = "F[@[-X]+X]"

    for _ in range(iterations):
        next_s: List[str] = []
        for ch in current:
            if ch == "X":
                next_s.append(rule_X)
            else:
                next_s.append(ch)
        current = "".join(next_s)

    return current


# ---------------------------------------------------
# Turtle-Renderer für X/F/+/−/[/]/@
# ---------------------------------------------------

def _draw_tree(lsys: str, opts: TreeOptions) -> plt.Figure:
    # Turtle-State
    @dataclass
    class State:
        x: float
        y: float
        angle_deg: float
        opts: TreeOptions

    # Start unten Mitte, nach oben
    x, y = 0.0, 0.0
    angle_deg = 90.0  # nach oben
    state_stack: List[State] = []

    # Für Scaling
    min_x = max_x = x
    min_y = max_y = y

    fig, ax = plt.subplots(figsize=(4, 5), dpi=150)

    rng = random.Random(0)  # deterministisch

    for ch in lsys:
        if ch in ("F", "X"):
            # effektive Länge
            jitter = 1.0 + (rng.random() - 0.5) * opts.length_randomness
            seg_len = opts.length * jitter
            rad = math.radians(angle_deg)

            dx = math.cos(rad) * seg_len
            dy = math.sin(rad) * seg_len

            new_x = x + dx
            new_y = y + dy

            # Linienbreite abhängig von Tiefe
            line_width = max(0.7, opts.width)

            # Farbe: Stamm unten brauner, oben grüner
            t = _clamp(opts.depth / 12.0)
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

            # einfache Blätter an X-Segmenten, wenn Baum tiefer
            if ch == "X" and opts.depth >= 3:
                leaf_size = 5.0 * (1.0 + diff_factor_from_opts(opts))
                ax.scatter(
                    [new_x],
                    [new_y],
                    s=leaf_size,
                    c=[[0.2, 0.6, 0.2, 0.8]],
                    marker="o",
                    linewidths=0,
                )

            x, y = new_x, new_y
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)

        elif ch == "+":
            base_angle = rng.uniform(opts.angle_min, opts.angle_max)
            asym = base_angle * opts.angle_asymmetry * (rng.random() - 0.5)
            angle_deg += base_angle + asym

        elif ch == "-":
            base_angle = rng.uniform(opts.angle_min, opts.angle_max)
            asym = base_angle * opts.angle_asymmetry * (rng.random() - 0.5)
            angle_deg -= base_angle + asym

        elif ch == "[":
            # State pushen
            state_stack.append(State(x, y, angle_deg, replace(opts)))
            # Tiefe +1
            opts.depth += 1

        elif ch == "]":
            # State poppen
            if state_stack:
                s = state_stack.pop()
                x, y, angle_deg, opts = s.x, s.y, s.angle_deg, s.opts

        elif ch == "@":
            # entspricht JS: Länge, Breite, Farbe reduzieren, Tiefe erhöhen
            opts.length *= opts.length_decrease_ratio
            opts.width = max(1.0, opts.width * opts.width_decrease_ratio)
            opts.color_r *= opts.color_decrease_ratio
            opts.color_g *= opts.color_decrease_ratio
            opts.color_b *= opts.color_decrease_ratio
            opts.depth += 1

        else:
            # andere Zeichen ignorieren
            continue

    # Bodenlinie
    ax.plot([min_x - 0.3, max_x + 0.3], [0.0, 0.0], color="#444444", linewidth=1.0)

    ax.set_aspect("equal", "box")
    x_margin = 0.4
    y_margin = 0.3
    ax.set_xlim(min_x - x_margin, max_x + x_margin)
    ax.set_ylim(-0.2, max_y + y_margin)
    ax.axis("off")
    fig.tight_layout(pad=0.1)
    return fig


def diff_factor_from_opts(opts: TreeOptions) -> float:
    # kleine Heuristik: etwas mehr Blätter bei „schwierigerem“ Text (aus Länge ableiten)
    return _clamp((opts.length / 100.0) - 0.5, -0.2, 0.5)


# ---------------------------------------------------
# Öffentliche API
# ---------------------------------------------------

def generate_disce_bonsai_figure(result: Dict) -> plt.Figure:
    """
    Nimmt das full result aus analyze_text_for_ui und erzeugt
    einen Disce-Baum, der grob dem JS-Tree entspricht.
    """
    dims = result.get("dims", {}) or {}
    opts = options_from_dims(dims)
    lsys = expand_lsystem("X", opts.iterations)
    fig = _draw_tree(lsys, opts)
    return fig
