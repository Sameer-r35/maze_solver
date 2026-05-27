import heapq
from config import WALL, BACKGROUND


def astar(grid, start, end, greed=0):
    """
    A* Search with greed parameter (0-100).

    greed=0   → pure A*: minimizes actual path cost. Ignores coins entirely.
    greed=100 → coin hunter: cells with coins are treated as nearly free to
                enter, so A* aggressively detours to collect them.
    greed=N   → blend: coin cells get a cost discount proportional to greed.

    The key insight: changing only the heuristic direction doesn't change
    the final path because A* still minimizes g+h. To actually change which
    path is chosen, we must change the effective cost of entering coin cells.

    At greed=G, entering a coin cell costs:
        effective_cost = terrain_cost * (1 - 0.95 * G/100)

    At greed=100: coin cells cost ~5% of their terrain cost → A* eagerly
    detours through mud/water coins that it would otherwise avoid.
    At greed=0:   no discount → pure optimal path.

    Yields state dict each step:
        visited   : set of (r, c)
        frontier  : set of (r, c)
        current   : (r, c)
        path      : list of (r, c) or None
    """
    heap = [(0, start)]
    came_from = {start: None}
    g_cost = {start: 0}
    visited = set()

    # Precompute coin set for O(1) lookup
    coin_set = set(grid.coins)
    blend = greed / 100.0

    while heap:
        _, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        frontier_set = {cell for _, cell in heap}

        yield {
            "visited":  set(visited),
            "frontier": frontier_set,
            "current":  current,
            "path":     None,
        }

        if current == end:
            path = _reconstruct_path(came_from, start, end)
            yield {
                "visited":  set(visited),
                "frontier": set(),
                "current":  current,
                "path":     path,
            }
            return

        for neighbor in grid.get_neighbors(*current):
            terrain = grid.get_cell(*neighbor)
            if terrain in (WALL, BACKGROUND):
                continue

            terrain_cost = grid.get_cost(*neighbor)

            # At high greed, coin cells get a steep cost discount —
            # this is what makes A* actually choose different paths,
            # not just explore in a different order.
            if neighbor in coin_set and greed > 0:
                effective_cost = terrain_cost * (1.0 - 0.95 * blend)
            else:
                effective_cost = terrain_cost

            new_g = g_cost[current] + effective_cost

            if new_g < g_cost.get(neighbor, float('inf')):
                g_cost[neighbor] = new_g
                came_from[neighbor] = current
                h = _heuristic(neighbor, end, coin_set, blend)
                heapq.heappush(heap, (new_g + h, neighbor))

    # No path found
    yield {
        "visited":  set(visited),
        "frontier": set(),
        "current":  None,
        "path":     [],
    }


def _heuristic(cell, end, coins, blend):
    """
    Blend of goal heuristic and coin waypoint heuristic.
    blend=0:   pure manhattan to goal
    blend=1:   route through nearest coin as waypoint, then to goal
    """
    goal_h = _manhattan(cell, end)

    if blend == 0 or not coins:
        return goal_h

    nearest_coin = min(coins, key=lambda c: _manhattan(cell, c))
    coin_h = _manhattan(cell, nearest_coin) + _manhattan(nearest_coin, end)

    return (1 - blend) * goal_h + blend * coin_h


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_path(came_from, start, end):
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = came_from.get(node)
    path.reverse()
    return path if path and path[0] == start else []