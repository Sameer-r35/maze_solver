import heapq
from config import WALL, BACKGROUND


def ucs(grid, start, end):
    """
    Uniform Cost Search (Dijkstra's algorithm) — expands by cumulative path cost.
    Unlike BFS, it respects terrain costs: mud (5) and water (10) are expensive.
    Always finds the optimal (lowest-cost) path.

    This is the first algorithm in the lineup that will visibly detour around
    mud/water when walking around costs less than walking through.

    Yields a state dict each step:
        visited   : set of (r, c) cells already expanded
        frontier  : set of (r, c) cells currently in the priority queue
        current   : (r, c) cell being processed this step
        path      : list of (r, c) from start → end, or None if not yet found
    """
    # heap entries: (cumulative_cost, (row, col))
    heap = [(0, start)]
    came_from = {start: None}
    g_cost = {start: 0}
    visited = set()

    while heap:
        cost, current = heapq.heappop(heap)

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
            new_cost = cost + step_cost

            if new_cost < g_cost.get(neighbor, float('inf')):
                g_cost[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(heap, (new_cost, neighbor))

    # No path found
    yield {
        "visited": set(visited),
        "frontier": set(),
        "current": None,
        "path": [],
    }


def _reconstruct_path(came_from, start, end):
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = came_from.get(node)
    path.reverse()
    return path if path[0] == start else []
