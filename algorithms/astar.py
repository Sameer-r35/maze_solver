import heapq
from config import WALL, BACKGROUND


def astar(grid, start, end, greed=0):
    """
    A* Search — combines actual path cost (g) with a heuristic estimate (h).
    f = g + h, where h is Manhattan distance to end (admissible: min cost is 1).

    The `greed` parameter (0–100) blends the heuristic between:
        greed=0   → pure A* (goal-directed, optimal)
        greed=100 → coin-chasing (heuristic points toward nearest coin)
        greed=50  → blend: 50% coin attraction + 50% goal direction

    When greed > 0 and coins exist, the heuristic shifts toward the nearest coin.
    This can make A* take costlier paths to collect more coins, raising the score:
        Score = (coins × 100) - path_cost

    Admissibility note: Manhattan distance never overestimates because the minimum
    terrain cost is 1 (plain). Booster pads (cost < 1) are excluded for this reason.

    Yields a state dict each step:
        visited   : set of (r, c) cells already expanded
        frontier  : set of (r, c) cells currently in the priority queue
        current   : (r, c) cell being processed this step
        path      : list of (r, c) from start → end, or None if not yet found
    """
    heap = [(0, start)]
    came_from = {start: None}
    g_cost = {start: 0}
    visited = set()

    while heap:
        _, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        frontier_set = {cell for _, cell in heap}

        yield {
            "visited": set(visited),
            "frontier": frontier_set,
            "current": current,
            "path": None,
        }

        if current == end:
            path = _reconstruct_path(came_from, start, end)
            yield {
                "visited": set(visited),
                "frontier": set(),
                "current": current,
                "path": path,
            }
            return

        for neighbor in grid.get_neighbors(*current):
            terrain = grid.get_cell(*neighbor)
            if terrain in (WALL, BACKGROUND):
                continue

            step_cost = grid.get_cost(*neighbor)
            new_g = g_cost[current] + step_cost

            if new_g < g_cost.get(neighbor, float('inf')):
                g_cost[neighbor] = new_g
                came_from[neighbor] = current
                h = _heuristic(neighbor, end, grid, greed)
                f = new_g + h
                heapq.heappush(heap, (f, neighbor))

    # No path found
    yield {
        "visited": set(visited),
        "frontier": set(),
        "current": None,
        "path": [],
    }


def _heuristic(cell, end, grid, greed):
    """
    Adaptive heuristic based on greed level.
    - greed=0  : pure Manhattan distance to goal
    - greed=100: Manhattan distance to nearest coin (if any coins exist)
    - in between: weighted blend of both
    """
    goal_h = _manhattan(cell, end)

    if greed == 0 or not grid.coins:
        return goal_h

    nearest_coin = min(grid.coins, key=lambda c: _manhattan(cell, c))
    coin_h = _manhattan(cell, nearest_coin)

    blend = greed / 100
    return blend * coin_h + (1 - blend) * goal_h


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_path(came_from, start, end):
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = came_from.get(node)
    path.reverse()
    return path if path[0] == start else []
