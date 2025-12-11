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
from typing import Dict, List, Optional

import math
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


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

    # Winkelbereich
    # Kohäsion hoch -> enger Winkel
    min_angle = 10.0 + (1.0 - coh) * 5.0      # 10–15
    max_angle = 20.0 + (1.0 - coh) * 10.0     # 20–30
    # + etwas Stretch über Schwierigkeit
    max_angle += diff * 5.0                   # +0–5
    min_angle = min(min_angle, 18.0)
    max_angle = min(max_angle, 35.0)

    # Längenverkürzung: 0.68–0.82
    length_dec = 0.68 + synt * 0.14

    # Breitenverkürzung: 0.82–0.93, je nach Kohäsion
    width_dec = 0.82 + coh * 0.11

    # Zufall / Asymmetrie: mehr bei geringer Kohäsion & hoher Informalität
    length_rand = 0.05 + (1.0 - coh) * 0.15
    angle_asym = 0.05 + reg_inf * 0.20

    # Farbe grob an Schwierigkeitsgrad koppeln (dunkler/grüner)
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

def _draw_tree(lsys: str, opts: TreeOptions, dims: Dict) -> plt.Figure:
    # Turtle-State
    @dataclass
    class State:
        x: float
        y: float
        angle_deg: float
        opts: TreeOptions
        last_seg_idx: Optional[int]

    @dataclass
    class Segment:
        start_x: float
        start_y: float
        end_x: float
        end_y: float
        depth: int
        is_x: bool
        has_child: bool = False

    # Start unten Mitte, nach oben
    x, y = 0.0, 0.0
    angle_deg = 90.0  # nach oben
    state_stack: List[State] = []

    # Für Scaling
    min_x = max_x = x
    min_y = max_y = y

    # Alle Segmente sammeln, um hinterher Endäste zu kennen
    segments: List[Segment] = []
    last_seg_idx: Optional[int] = None

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

            # Segment speichern
            seg = Segment(
                start_x=x,
                start_y=y,
                end_x=new_x,
                end_y=new_y,
                depth=opts.depth,
                is_x=(ch == "X"),
            )
            # Elternsegment als "hat Kind" markieren
            if last_seg_idx is not None:
                segments[last_seg_idx].has_child = True
            segments.append(seg)
            last_seg_idx = len(segments) - 1

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
            state_stack.append(State(x, y, angle_deg, replace(opts), last_seg_idx))
            # Tiefe +1
            opts.depth += 1

        elif ch == "]":
            # State poppen
            if state_stack:
                s = state_stack.pop()
                x, y, angle_deg, opts, last_seg_idx = (
                    s.x,
                    s.y,
                    s.angle_deg,
                    s.opts,
                    s.last_seg_idx,
                )

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

    # Blätter basierend auf Endästen zeichnen
    _draw_leaves(ax, segments, dims, rng)

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


def _draw_leaves(ax, segments, dims: Dict, rng: random.Random) -> None:
    """
    Zeichnet organische Blatt-Cluster (Ellipsen-Büschel) an Endästen.

    Heuristik:
      - Blätter nur an Segmenten ohne Kinder (has_child == False)
      - Mindesttiefe, damit nicht am Stammende schon Laub hängt
      - Blattdichte ~ lexical_diversity
      - Ordnung/Cluster-Spread ~ cohesion
      - Blattgröße/Farbnuance ~ text_difficulty
    """
    if not segments:
        return

    lex = _clamp(_safe_dim(dims, "lexical_diversity", 0.7))
    coh = _clamp(_safe_dim(dims, "cohesion", 0.5))
    diff = _clamp(_safe_dim(dims, "text_difficulty", 0.5))

    # Nur "hohe" Äste: ab Tiefe 3
    min_leaf_depth = 3

    leaf_segments = [
        s for s in segments
        if not s.has_child and s.depth >= min_leaf_depth
    ]

    if not leaf_segments:
        return

    # Basis-Anzahl von Clustern pro Endast, skaliert mit lexical_diversity
    base_clusters_per_segment = 1 + int(lex * 3)   # 1–4 Cluster pro Endast

    # Begrenze Gesamtanzahl Cluster, damit das Bild nicht überladen wird
    max_total_clusters = 160
    est_total_clusters = len(leaf_segments) * base_clusters_per_segment
    if est_total_clusters <= 0:
        return
    density_scale = min(1.0, max_total_clusters / est_total_clusters)

    # Kohäsion: hoher Wert -> engerer Spread um die Ast-Richtung (20–45°)
    spread_deg = 20.0 + (1.0 - coh) * 25.0
    spread = math.radians(spread_deg)

    # Blattgröße: schwierigere Texte -> etwas kleinere Blätter
    size_scale = 0.7 + (1.0 - diff) * 0.6  # 0.7–1.3

    for seg in leaf_segments:
        dx = seg.end_x - seg.start_x
        dy = seg.end_y - seg.start_y
        base_theta = math.atan2(dy, dx)
        seg_len = max(1e-3, math.hypot(dx, dy))

        # Cluster-Zentrum: etwas vom Astende weg
        r_min = 0.3 * seg_len
        r_max = 0.9 * seg_len

        n_clusters = max(1, int(round(base_clusters_per_segment * density_scale)))

        for _ in range(n_clusters):
            theta_center = base_theta + rng.uniform(-spread, spread)
            r = rng.uniform(r_min, r_max)
            cx = seg.end_x + math.cos(theta_center) * r
            cy = seg.end_y + math.sin(theta_center) * r

            # Pro Cluster 2–4 überlappende Ellipsen als "Blattbüschel"
            n_ellipses = rng.randint(2, 4)
            for _ in range(n_ellipses):
                # Leichter Versatz um das Clusterzentrum
                off_r = rng.uniform(0.0, 0.3 * seg_len)
                off_theta = theta_center + rng.uniform(-0.8, 0.8)
                ex = cx + math.cos(off_theta) * off_r
                ey = cy + math.sin(off_theta) * off_r

                # Ellipsen-Geometrie: Breite ~ Astlänge, Höhe etwas kleiner
                base_width = max(0.25 * seg_len, 0.15)
                base_height = base_width * 0.6

                width = base_width * (0.8 + rng.random() * 0.6) * size_scale
                height = base_height * (0.8 + rng.random() * 0.6) * size_scale

                # Orientierung leicht um die Ast-Richtung herum variieren
                angle_deg = math.degrees(base_theta) + rng.uniform(-25.0, 25.0)

                # Grünnuance: lexical_diversity und difficulty leicht einfließen lassen
                g_base = 0.55 + 0.3 * lex       # 0.55–0.85
                g = max(0.45, min(0.9, g_base))
                darken = 0.15 * diff
                r_col = 0.16 - darken * 0.3
                b_col = 0.20 - darken * 0.2

                color = (max(0.0, r_col), g, max(0.0, b_col), 0.85)

                leaf = Ellipse(
                    (ex, ey),
                    width=width,
                    height=height,
                    angle=angle_deg,
                    facecolor=color,
                    edgecolor="none",
                )
                ax.add_patch(leaf)


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
    fig = _draw_tree(lsys, opts, dims)
    return fig
