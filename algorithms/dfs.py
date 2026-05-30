from config import WALL, BACKGROUND


def dfs(grid, start, end):
    """
    Depth-First Search — explores as deep as possible before backtracking.
    Unweighted; ignores terrain costs like BFS.
    Typically explores far more cells than BFS and rarely finds the optimal path.

    Yields a state dict each step:
        visited   : set of (r, c) cells already expanded
        frontier  : set of (r, c) cells currently on the stack
        current   : (r, c) cell being processed this step
        path      : list of (r, c) from start → end, or None if not yet found
    """
    stack = [start]
    came_from = {start: None}
    visited = set()

    while stack:
        current = stack.pop()

        if current in visited:
            continue
        visited.add(current)

        yield {
            "visited": set(visited),
            "frontier": set(stack),
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
                stack.append(neighbor)

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
