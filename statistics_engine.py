"""
statistics_engine.py
====================
Pure Python — zero Pygame imports. All number-crunching lives here.
Visualizer calls these functions and receives plain data structures
it can render however it likes.

Implements the feature list in Statistics_Feature_List.md:
    Phase 1 — run_analytics_batch()     : runs all algorithms silently
    Phase 2 — generate_table_stats()    : derived metrics + verdict badges
    Phase 3 — calculate_scatter_data()  : Pearson r, (nodes, score) points
    Phase 4 — calculate_terrain_profile(): terrain % breakdown per path
"""

import math
import time

from config import PLAIN, MUD, WATER, WALL, BACKGROUND, START, END

# Algorithm files live flat in the project root (bfs.py, dfs.py, etc.)
# test_algorithms.py uses "from algorithms.bfs import bfs" only because
# __init__.py in root re-exports them — we import directly here.
from algorithms.bfs    import bfs
from algorithms.dfs    import dfs
from algorithms.ucs    import ucs
from algorithms.greedy import greedy
from algorithms.astar  import astar


# ------------------------------------------------------------------ #
# PHASE 1 — DATA EXTRACTION CORE
# ------------------------------------------------------------------ #

# The 7 algorithm variants that Compare All / Analytics runs.
# Each entry: (display_name, factory_fn, kwargs)
_VARIANTS = [
    ("BFS",       bfs,    {}),
    ("DFS",       dfs,    {}),
    ("UCS",       ucs,    {}),
    ("Greedy",    greedy, {}),
    ("A* (0%)",   astar,  {"greed": 0}),
    ("A* (50%)",  astar,  {"greed": 50}),
    ("A* (100%)", astar,  {"greed": 100}),
]


def run_analytics_batch(grid, start_pos, end_pos):
    """
    Runs all 7 algorithm variants silently (no animation) and returns
    a dict of raw results keyed by display name.

    Each value is a dict with:
        nodes_explored   (int)
        path             (list of (r,c), empty list if no path found)
        path_length      (int)
        path_cost        (float)
        coins_collected  (int)
        score            (int)
        execution_time_ms (float)
        path_found       (bool)

    This is the single source of truth — Phases 2-4 all read from here.
    """
    results = {}

    for name, fn, kwargs in _VARIANTS:
        t0        = time.perf_counter()
        gen       = fn(grid, start_pos, end_pos, **kwargs)
        last_state = None
        path       = []

        for state in gen:
            last_state = state
            if state["path"] is not None:
                path = state["path"]
                break   # stop as soon as path is found

        elapsed = (time.perf_counter() - t0) * 1000

        # If generator exhausted without a path, last_state still holds
        # the final visited set; path stays []
        nodes = len(last_state["visited"]) if last_state else 0

        path_cost = sum(grid.get_cost(*cell) for cell in path) if path else 0.0
        coins     = grid.get_coins_in_path(path) if path else 0
        score     = (coins * 100) - int(path_cost) if path else 0

        results[name] = {
            "nodes_explored":    nodes,
            "path":              path,
            "path_length":       len(path),
            "path_cost":         path_cost,
            "coins_collected":   coins,
            "score":             score,
            "execution_time_ms": round(elapsed, 2),
            "path_found":        bool(path),
        }

    return results


# ------------------------------------------------------------------ #
# PHASE 2 — SUMMARY STATISTICS TABLE
# ------------------------------------------------------------------ #

def generate_table_stats(raw_data, total_coins):
    """
    Takes raw_data from run_analytics_batch() and returns a list of row
    dicts ready for the UI to render as a table.

    Each row dict adds these derived fields on top of the raw data:
        terrain_penalty  (int)   — extra cost paid due to terrain
        coins_missed     (int)   — coins left uncollected
        efficiency_ratio (float) — score per node explored
        verdicts         (list)  — badge strings e.g. ["Fastest", "Best Score"]

    Also returns a 'descriptive_stats' dict with cross-algorithm
    summary statistics (mean, median, std_dev, min, max) for the
    columns that matter analytically. These map directly to the
    Math 2205 syllabus topics: central tendency + dispersion.
    """
    rows = []

    for name, data in raw_data.items():
        path_len  = data["path_length"]
        path_cost = data["path_cost"]
        nodes     = data["nodes_explored"]
        score     = data["score"]
        coins     = data["coins_collected"]

        # Terrain penalty = extra cost paid beyond a plain-cost path.
        # A plain path of the same length would cost exactly path_length
        # (1 per step). Any excess = mud/water cells walked through.
        # BFS always shows 0 here because it ignores costs — it treats
        # mud as cost-1 even though it isn't. That zero is intentional
        # and worth pointing out: BFS appears "efficient" but is wrong.
        terrain_penalty = int(path_cost - path_len) if path_len > 0 else 0

        coins_missed = total_coins - coins

        # Guard: nodes=0 only if algorithm instantly failed
        efficiency = round(score / nodes, 3) if nodes > 0 else 0.0

        rows.append({
            "name":             name,
            "nodes_explored":   nodes,
            "path_length":      path_len,
            "path_cost":        path_cost,
            "terrain_penalty":  terrain_penalty,
            "coins_collected":  coins,
            "coins_missed":     coins_missed,
            "score":            score,
            "efficiency_ratio": efficiency,
            "time_ms":          data["execution_time_ms"],
            "path_found":       data["path_found"],
            "verdicts":         [],   # filled in below
        })

    _assign_verdicts(rows)

    descriptive = _compute_descriptive_stats(rows)

    return rows, descriptive


def _assign_verdicts(rows):
    """
    Scans all rows and tags winners per category.
    A row can hold multiple verdict badges.
    Only awards badges to algorithms that actually found a path.
    """
    found = [r for r in rows if r["path_found"]]
    if not found:
        return

    # Fastest — min execution time
    fastest = min(found, key=lambda r: r["time_ms"])
    fastest["verdicts"].append("Fastest")

    # Cheapest path — min path cost
    cheapest = min(found, key=lambda r: r["path_cost"])
    cheapest["verdicts"].append("Cheapest Path")

    # Most coins collected
    most_coins = max(found, key=lambda r: r["coins_collected"])
    most_coins["verdicts"].append("Most Coins")

    # Best score
    best_score = max(found, key=lambda r: r["score"])
    best_score["verdicts"].append("Best Score")

    # Best efficiency (score per node) — bonus badge
    best_eff = max(found, key=lambda r: r["efficiency_ratio"])
    best_eff["verdicts"].append("Most Efficient")


def _compute_descriptive_stats(rows):
    """
    Computes mean, median, std_dev, min, max for the four key numeric
    columns across all algorithm variants that found a path.

    These map to Math 2205 Chapter 2 (Descriptive Statistics):
        - Central tendency: mean, median
        - Dispersion: std_dev, min, max, IQR (derivable from sorted values)

    Returns a dict keyed by metric name, each value is a stats dict.
    """
    found = [r for r in rows if r["path_found"]]
    if not found:
        return {}

    metrics = {
        "Nodes Explored": [r["nodes_explored"]    for r in found],
        "Path Cost":      [r["path_cost"]         for r in found],
        "Score":          [r["score"]             for r in found],
        "Time (ms)":      [r["time_ms"]           for r in found],
    }

    stats = {}
    for metric, values in metrics.items():
        stats[metric] = _five_number_summary(values)

    return stats


def _five_number_summary(values):
    """
    Returns a dict with mean, median, std_dev, minimum, maximum, IQR,
    and skewness for a list of numeric values.

    All computed in pure Python — no numpy or scipy required.
    Uses Pearson's moment coefficient of skewness:
        skewness = 3 * (mean - median) / std_dev

    This is a simplified but valid measure — appropriate for a stats
    course project and easy to explain. Sign tells you direction:
        positive → right tail (DFS outlier drags mean up)
        negative → left tail
        near 0   → roughly symmetric
    """
    n = len(values)
    if n == 0:
        return {}

    sorted_vals = sorted(values)
    mean        = sum(values) / n
    median      = _median(sorted_vals)
    variance    = sum((x - mean) ** 2 for x in values) / n
    std_dev     = math.sqrt(variance)
    minimum     = sorted_vals[0]
    maximum     = sorted_vals[-1]
    iqr         = _iqr(sorted_vals)
    skewness    = (3 * (mean - median) / std_dev) if std_dev > 0 else 0.0

    return {
        "mean":     round(mean,    2),
        "median":   round(median,  2),
        "std_dev":  round(std_dev, 2),
        "min":      round(minimum, 2),
        "max":      round(maximum, 2),
        "iqr":      round(iqr,     2),
        "skewness": round(skewness, 3),
        "n":        n,
    }


def _median(sorted_vals):
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2


def _iqr(sorted_vals):
    """Inter-quartile range: Q3 - Q1 using the exclusive quartile method."""
    n = len(sorted_vals)
    if n < 4:
        return sorted_vals[-1] - sorted_vals[0]
    q1 = _median(sorted_vals[:n // 2])
    q3 = _median(sorted_vals[(n + 1) // 2:])
    return q3 - q1


# ------------------------------------------------------------------ #
# PHASE 3 — SCATTER PLOT + PEARSON CORRELATION
# ------------------------------------------------------------------ #

def calculate_scatter_data(raw_data):
    """
    Extracts (nodes_explored, score) coordinates for the scatter plot
    and calculates Pearson r to answer:

        "Does exploring more nodes actually lead to a better score?"

    Expected finding: r is weak or negative — A*(50%) explores ~150
    nodes and scores very high. DFS explores 500+ and scores worse.
    This is your strongest counterintuitive result.

    Returns:
        points  — list of {"name": str, "x": int, "y": int}
        r       — Pearson correlation coefficient (float, -1 to 1)
        label   — human-readable interpretation string
    """
    found = {k: v for k, v in raw_data.items() if v["path_found"]}
    if len(found) < 2:
        return [], 0.0, "Not enough data"

    points = [
        {"name": name, "x": data["nodes_explored"], "y": data["score"]}
        for name, data in found.items()
    ]

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    r  = _pearson_r(xs, ys)

    label = _interpret_r(r)

    return points, round(r, 3), label


def _pearson_r(xs, ys):
    """
    Manual Pearson r — no scipy needed.

    Formula:
        r = Σ((xi - x̄)(yi - ȳ)) / sqrt(Σ(xi-x̄)² · Σ(yi-ȳ)²)

    This is exactly what Math 2205 Chapter 3 covers.
    """
    n    = len(xs)
    xbar = sum(xs) / n
    ybar = sum(ys) / n

    num   = sum((xs[i] - xbar) * (ys[i] - ybar) for i in range(n))
    denom = math.sqrt(
        sum((xs[i] - xbar) ** 2 for i in range(n)) *
        sum((ys[i] - ybar) ** 2 for i in range(n))
    )

    return num / denom if denom != 0 else 0.0


def _interpret_r(r):
    """Returns a plain-English interpretation of Pearson r."""
    abs_r = abs(r)
    direction = "Positive" if r >= 0 else "Negative"

    if abs_r >= 0.9:
        strength = "Very Strong"
    elif abs_r >= 0.7:
        strength = "Strong"
    elif abs_r >= 0.5:
        strength = "Moderate"
    elif abs_r >= 0.3:
        strength = "Weak"
    else:
        strength = "Very Weak / None"

    return f"{strength} {direction}"


# ------------------------------------------------------------------ #
# PHASE 4 — ALGORITHM PERSONALITY (Radar Graph)
# ------------------------------------------------------------------ #

def calculate_algo_personality(name, data, grid, total_coins):
    """
    Computes 3 radar axes that meaningfully differentiate algorithms:

        1. Avg Step Cost  — inverted avg cost per step, normalized 0–100
                           100% = all plain (cheapest), 0% = all water (costliest)
                           BFS/DFS: medium. UCS/A*0%: high. A*100%: low.

        2. Coin Ratio     — coins_collected / total_coins * 100
                           0–100%. Directly shows coin aggressiveness.
                           BFS/UCS: low. A*100%: high.

        3. Path Efficiency — min_possible_cost / actual_cost * 100
                            100% = perfectly optimal plain path.
                            BFS: low (ignores terrain). UCS/A*0%: high.
                            A*100%: low (takes costly detours for coins).
    """
    if not data["path_found"] or not data["path"]:
        return {"avg_step_cost": 0.0, "coin_ratio": 0.0, "path_efficiency": 0.0}

    path_len  = data["path_length"]
    path_cost = data["path_cost"]
    coins     = data["coins_collected"]

    # Axis 1: avg step cost inverted — higher % means cheaper terrain
    avg_cost     = path_cost / path_len if path_len > 0 else 1.0
    avg_cost_pct = max(0.0, min(100.0, (1.0 - (avg_cost - 1.0) / 9.0) * 100))

    # Axis 2: coin collection ratio
    coin_ratio = (coins / total_coins * 100) if total_coins > 0 else 0.0
    coin_ratio = max(0.0, min(100.0, coin_ratio))

    # Axis 3: path efficiency vs plain-cost baseline
    min_cost   = path_len * 1
    efficiency = (min_cost / path_cost * 100) if path_cost > 0 else 100.0
    efficiency = max(0.0, min(100.0, efficiency))

    return {
        "avg_step_cost":   round(avg_cost_pct, 1),
        "coin_ratio":      round(coin_ratio,   1),
        "path_efficiency": round(efficiency,   1),
    }


def calculate_all_terrain_profiles(raw_data, grid):
    """
    Computes algorithm personality profiles for all variants.
    Returns dict keyed by algorithm name.
    Each value has: avg_step_cost, coin_ratio, path_efficiency (all 0–100).
    """
    total_coins = len(grid.coins)
    return {
        name: calculate_algo_personality(name, data, grid, total_coins)
        for name, data in raw_data.items()
        if data["path_found"]
    }