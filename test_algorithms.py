from generator import generate_maze
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.ucs import ucs
from algorithms.greedy import greedy
from algorithms.astar import astar
from config import GRID_ROWS, GRID_COLS
import time

grid = generate_maze(GRID_ROWS, GRID_COLS)
start = (1, 1)
end = (GRID_ROWS - 2, GRID_COLS - 2)

algorithms = [
    ("BFS",    bfs(grid, start, end)),
    ("DFS",    dfs(grid, start, end)),
    ("UCS",    ucs(grid, start, end)),
    ("Greedy", greedy(grid, start, end)),
    ("A*",     astar(grid, start, end, greed=0)),
]

for name, gen in algorithms:
    t0 = time.time()
    steps = 0
    result = None
    for state in gen:
        steps += 1
        if state["path"] is not None:
            result = state
            break
    ms = round((time.time() - t0) * 1000, 2)

    path = result["path"] if result and result["path"] else []
    path_len = len(path) if path else "No path"
    path_cost = sum(grid.get_cost(*cell) for cell in path) if path else "N/A"

    print(f"{name:<8} Steps: {steps:<6} Path length: {path_len:<6} Path cost: {path_cost:<8} Time: {ms}ms")