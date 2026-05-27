from collections import deque
from config import WALL, BACKGROUND


def bfs(grid, start, end):
    """
    Breadth-First Search — unweighted, explores by number of steps.
    Ignores terrain costs entirely: mud and water are treated the same as plain.
    This is intentional — the visual contrast vs UCS/A* is the demo's strongest moment.

    Yields a state dict each step:
        visited   : set of (r, c) cells already expanded
        frontier  : set of (r, c) cells currently in the queue
        current   : (r, c) cell being processed this step
        path      : list of (r, c) from start → end, or None if not yet found
    """
    queue = deque([start])
    came_from = {start: None}
    visited = set()

    while queue:
        current = queue.popleft()

        if current in visited:
            continue
        visited.add(current)

        # Yield state before checking goal so the final cell is animated
        yield {
            "visited": set(visited),
            "frontier": set(queue),
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
                queue.append(neighbor)

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
