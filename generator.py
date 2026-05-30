import random
from collections import deque
from config import PLAIN, MUD, WATER, WALL, BACKGROUND, START, END
from grid import Grid


def generate_maze(rows, cols):
    grid = Grid(rows, cols)

    start_pos = (1, 1)
    end_pos = (rows - 2, cols - 2)

    # STEP 1: Carve perfect maze via recursive backtracking
    stack = [start_pos]
    grid.set_cell(*start_pos, PLAIN)
    visited = {start_pos}

    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < rows - 1 and 0 < nc < cols - 1:
                if (nr, nc) not in visited:
                    neighbors.append((nr, nc))
        if neighbors:
            nr, nc = random.choice(neighbors)
            wall_r = r + (nr - r) // 2
            wall_c = c + (nc - c) // 2
            grid.set_cell(wall_r, wall_c, PLAIN)
            grid.set_cell(nr, nc, PLAIN)
            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    # STEP 2: Add loops — remove ~18% of internal walls for alternate routes
    internal_walls = []
    for r in range(2, rows - 2):
        for c in range(2, cols - 2):
            if grid.get_cell(r, c) == BACKGROUND:
                horiz = (grid.get_cell(r, c - 1) == PLAIN and grid.get_cell(r, c + 1) == PLAIN)
                vert  = (grid.get_cell(r - 1, c) == PLAIN and grid.get_cell(r + 1, c) == PLAIN)
                if horiz or vert:
                    internal_walls.append((r, c))

    loop_count = int(len(internal_walls) * 0.18)
    for r, c in random.sample(internal_walls, min(loop_count, len(internal_walls))):
        grid.set_cell(r, c, PLAIN)

    # STEP 3: Random internal walls — adds dead ends and detours
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) == PLAIN and (r, c) not in (start_pos, end_pos):
                if random.random() < 0.06:
                    grid.set_cell(r, c, WALL)

    # STEP 4: Guarantee connectivity
    if not _is_connected(grid, start_pos, end_pos):
        _fix_connectivity(grid, start_pos, end_pos)

    # STEP 5: Distribute MUD and WATER
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) == PLAIN and (r, c) not in (start_pos, end_pos):
                rand = random.random()
                if rand < 0.12:
                    grid.set_cell(r, c, MUD)
                elif rand < 0.20:
                    grid.set_cell(r, c, WATER)

    # STEP 6: Spawn coin clusters — more clusters, more coins per cluster
    # 5 clusters of 8 coins = ~40 coins total, spread across MUD/WATER terrain.
    # This makes the greed slider's effect clearly visible on the path.
    spawn_coin_clusters(grid, start_pos, end_pos, clusters=5, coins_per_cluster=8)

    # STEP 7: Place START and END
    grid.set_cell(*start_pos, START)
    grid.set_cell(*end_pos, END)

    return grid


def spawn_coin_clusters(grid, start_pos, end_pos, clusters=5, coins_per_cluster=8):
    """
    Places coins in tight clusters on MUD and WATER cells only.
    More clusters and coins per cluster than before to make greed
    slider effect clearly visible — A* at high greed will visibly
    detour through costly terrain to collect them.
    """
    eligible = [
        (r, c)
        for r in range(1, grid.rows - 1)
        for c in range(1, grid.cols - 1)
        if grid.get_cell(r, c) in (MUD, WATER)
        and (r, c) not in (start_pos, end_pos)
    ]

    if not eligible:
        return

    random.shuffle(eligible)
    eligible_set = set(eligible)
    anchors_placed = 0
    used = set()

    for anchor in eligible:
        if anchors_placed >= clusters:
            break
        if anchor in used:
            continue

        cluster_cells = []
        queue = deque([anchor])
        seen = {anchor}

        while queue and len(cluster_cells) < coins_per_cluster:
            r, c = queue.popleft()
            if (r, c) in eligible_set and (r, c) not in used:
                cluster_cells.append((r, c))
            for nr, nc in grid.get_neighbors(r, c):
                if (nr, nc) not in seen:
                    seen.add((nr, nc))
                    queue.append((nr, nc))

        for r, c in cluster_cells:
            grid.add_coin(r, c)
            used.add((r, c))

        anchors_placed += 1


def _is_connected(grid, start, end):
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        if (r, c) == end:
            return True
        for nr, nc in grid.get_neighbors(r, c):
            if (nr, nc) not in seen and grid.get_cell(nr, nc) not in (WALL, BACKGROUND):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return False


def _fix_connectivity(grid, start, end):
    random_walls = [
        (r, c)
        for r in range(1, grid.rows - 1)
        for c in range(1, grid.cols - 1)
        if grid.get_cell(r, c) == WALL
    ]
    random.shuffle(random_walls)
    for r, c in random_walls:
        grid.set_cell(r, c, PLAIN)
        if _is_connected(grid, start, end):
            return