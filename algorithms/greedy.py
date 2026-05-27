import heapq
from config import WALL, BACKGROUND


def greedy(grid, start, end):
    """
    Greedy Best-First Search — always expands the cell that looks closest to the goal.
    Uses Manhattan distance as heuristic; ignores actual terrain costs entirely.
    Fast but not optimal — it can be fooled by dead ends and costly terrain.

    Yields a state dict each step:
        visited   : set of (r, c) cells already expanded
        frontier  : set of (r, c) cells currently in the priority queue
        current   : (r, c) cell being processed this step
        path      : list of (r, c) from start → end, or None if not yet found
    """
    heap = [(_manhattan(start, end), start)]
    came_from = {start: None}
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
            if neighbor not in came_from:
                came_from[neighbor] = current
                h = _manhattan(neighbor, end)
                heapq.heappush(heap, (h, neighbor))

    # No path found
    yield {
        "visited": set(visited),
        "frontier": set(),
        "current": None,
        "path": [],
    }


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
