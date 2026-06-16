"""
test_statistics_engine.py
=========================
Verifies statistics_engine.py without launching Pygame.
Run from the project root: python test_statistics_engine.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator import generate_maze
from config import GRID_ROWS, GRID_COLS
from statistics_engine import (
    run_analytics_batch,
    generate_table_stats,
    calculate_scatter_data,
    calculate_all_terrain_profiles,
)

# ------------------------------------------------------------------ #
# Setup
# ------------------------------------------------------------------ #
print("Generating maze...")
grid      = generate_maze(GRID_ROWS, GRID_COLS)
start_pos = (1, 1)
end_pos   = (GRID_ROWS - 2, GRID_COLS - 2)
total_coins = len(grid.coins)
print(f"Grid: {GRID_ROWS}×{GRID_COLS}  |  Total coins: {total_coins}\n")

# ------------------------------------------------------------------ #
# Phase 1 — Raw batch
# ------------------------------------------------------------------ #
print("=" * 60)
print("PHASE 1 — Running all algorithms silently...")
print("=" * 60)
raw = run_analytics_batch(grid, start_pos, end_pos)

for name, data in raw.items():
    status = "✓" if data["path_found"] else "✗ NO PATH"
    print(
        f"  {name:<12} {status}  "
        f"nodes={data['nodes_explored']:<5}  "
        f"cost={data['path_cost']:<7.1f}  "
        f"coins={data['coins_collected']:<3}  "
        f"score={data['score']:<6}  "
        f"time={data['execution_time_ms']:.2f}ms"
    )

# ------------------------------------------------------------------ #
# Phase 2 — Summary table stats
# ------------------------------------------------------------------ #
print("\n" + "=" * 60)
print("PHASE 2 — Summary Table + Derived Metrics")
print("=" * 60)
rows, descriptive = generate_table_stats(raw, total_coins)

print(f"\n{'Algorithm':<14} {'Nodes':>6} {'Cost':>7} {'Terrain+':>9} {'Coins':>6} {'Missed':>7} {'Score':>7} {'Effic.':>7} {'Time':>8}  Verdicts")
print("-" * 100)
for r in rows:
    badges = ", ".join(r["verdicts"]) if r["verdicts"] else ""
    found  = "" if r["path_found"] else " [NO PATH]"
    print(
        f"  {r['name']:<12} "
        f"{r['nodes_explored']:>6}  "
        f"{r['path_cost']:>7.1f}  "
        f"{r['terrain_penalty']:>8}  "
        f"{r['coins_collected']:>5}  "
        f"{r['coins_missed']:>6}  "
        f"{r['score']:>6}  "
        f"{r['efficiency_ratio']:>7.3f}  "
        f"{r['time_ms']:>6.2f}ms  "
        f"{badges}{found}"
    )

print("\n--- Descriptive Statistics ---")
for metric, stats in descriptive.items():
    print(f"\n  {metric}:")
    print(f"    Mean={stats['mean']}  Median={stats['median']}  "
          f"StdDev={stats['std_dev']}  IQR={stats['iqr']}")
    print(f"    Min={stats['min']}  Max={stats['max']}  "
          f"Skewness={stats['skewness']}  (n={stats['n']})")

# ------------------------------------------------------------------ #
# Phase 3 — Scatter + Correlation
# ------------------------------------------------------------------ #
print("\n" + "=" * 60)
print("PHASE 3 — Scatter Data + Pearson Correlation")
print("=" * 60)
points, r_val, r_label = calculate_scatter_data(raw)

print(f"\n  Pearson r = {r_val}  →  {r_label}")
print(f"\n  {'Algorithm':<14} {'Nodes (X)':>10} {'Score (Y)':>10}")
print("  " + "-" * 38)
for p in points:
    print(f"  {p['name']:<14} {p['x']:>10}  {p['y']:>10}")

# ------------------------------------------------------------------ #
# Phase 4 — Terrain Profiles
# ------------------------------------------------------------------ #
print("\n" + "=" * 60)
print("PHASE 4 — Terrain Profiles (Algorithm Personality)")
print("=" * 60)
profiles = calculate_all_terrain_profiles(raw, grid)

print(f"\n  {'Algorithm':<14} {'PLAIN':>8} {'MUD':>8} {'WATER':>8}")
print("  " + "-" * 42)
for name, profile in profiles.items():
    print(f"  {name:<14} {profile['PLAIN']:>7.1f}%  {profile['MUD']:>7.1f}%  {profile['WATER']:>7.1f}%")

print("\n✓ All phases complete.\n")