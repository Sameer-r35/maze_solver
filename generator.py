import random
from collections import deque
from config import PLAIN, MUD, WATER, WALL, BACKGROUND, START, END
from grid import Grid


def generate_maze(rows, cols):
    """
    Generates a maze using randomized recursive backtracking, then adds loops
    to create alternate routes so algorithms have meaningful choices to make.

    Steps:
        1. Fill grid with BACKGROUND
        2. Carve a perfect maze (one path between any two points)
        3. Add loops by removing extra walls — creates alternate routes
        4. Add random internal walls (obstacles, not full blockers)
        5. Guarantee connectivity between START and END
        6. Distribute MUD and WATER terrain
        7. Scatter coins
        8. Place START and END
    """
    grid = Grid(rows, cols)

    start_pos = (1, 1)
    end_pos = (rows - 2, cols - 2)

    # ------------------------------------------------------------------ #
    # STEP 1: Carve perfect maze via recursive backtracking
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # STEP 2: Add loops — remove ~18% of internal walls to create
    # alternate routes. This is what makes algorithm comparison meaningful.
    # Without loops, all algorithms follow the same single corridor.
    # ------------------------------------------------------------------ #
    internal_walls = []
    for r in range(2, rows - 2):
        for c in range(2, cols - 2):
            if grid.get_cell(r, c) == BACKGROUND:
                # Only remove walls that connect two carved cells
                # (i.e., walls between passages, not boundary walls)
                horiz = (grid.get_cell(r, c - 1) == PLAIN and grid.get_cell(r, c + 1) == PLAIN)
                vert = (grid.get_cell(r - 1, c) == PLAIN and grid.get_cell(r + 1, c) == PLAIN)
                if horiz or vert:
                    internal_walls.append((r, c))

    loop_count = int(len(internal_walls) * 0.18)
    for r, c in random.sample(internal_walls, min(loop_count, len(internal_walls))):
        grid.set_cell(r, c, PLAIN)

    # ------------------------------------------------------------------ #
    # STEP 3: Random internal obstacle walls — adds dead ends and detours.
    # 6% of carved PLAIN cells become walls. Connectivity is checked after.
    # ------------------------------------------------------------------ #
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) == PLAIN and (r, c) not in (start_pos, end_pos):
                if random.random() < 0.06:
                    grid.set_cell(r, c, WALL)

    # ------------------------------------------------------------------ #
    # STEP 4: Guarantee connectivity — if random walls disconnected
    # start from end, remove walls along the broken path until connected.
    # ------------------------------------------------------------------ #
    if not _is_connected(grid, start_pos, end_pos):
        _fix_connectivity(grid, start_pos, end_pos)

    # ------------------------------------------------------------------ #
    # STEP 5: Distribute MUD and WATER on remaining PLAIN cells
    # ------------------------------------------------------------------ #
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) == PLAIN and (r, c) not in (start_pos, end_pos):
                rand = random.random()
                if rand < 0.12:
                    grid.set_cell(r, c, MUD)
                elif rand < 0.20:
                    grid.set_cell(r, c, WATER)

    # ------------------------------------------------------------------ #
    # STEP 6: Spawn coin clusters on MUD and WATER cells only.
    # Coins are placed exclusively on costly terrain to create genuine
    # risk/reward tension — collecting them means paying terrain costs.
    # ------------------------------------------------------------------ #
    spawn_coin_clusters(grid, start_pos, end_pos)

    # ------------------------------------------------------------------ #
    # STEP 7: Place START and END markers
    # ------------------------------------------------------------------ #
    grid.set_cell(*start_pos, START)
    grid.set_cell(*end_pos, END)

    return grid


# ------------------------------------------------------------------ #
# Coin placement — clusters on MUD and WATER only
# ------------------------------------------------------------------ #
def spawn_coin_clusters(grid, start_pos, end_pos, clusters=3, coins_per_cluster=6):
    """
    Places coins in small clusters, exclusively on MUD (cost 5) and WATER (cost 10)
    cells. This creates genuine risk/reward zones — an algorithm must pay terrain
    costs to collect them, so only high-greed A* finds it worthwhile to detour.

    Strategy:
        1. Collect all eligible MUD/WATER cells (excludes start and end).
        2. Pick `clusters` random anchor cells from that pool.
        3. Around each anchor, place up to `coins_per_cluster` coins on the
           nearest eligible neighbours (BFS-order so the cluster is tight).
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


# ------------------------------------------------------------------ #
# Helper: flood fill connectivity check
# ------------------------------------------------------------------ #
def _is_connected(grid, start, end):
    """Returns True if end is reachable from start."""
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


# ------------------------------------------------------------------ #
# Helper: remove walls until start and end are connected
# ------------------------------------------------------------------ #
def _fix_connectivity(grid, start, end):
    """
    Removes randomly placed WALL cells one by one until start and end
    are connected. Only touches cells that were randomly added in Step 3
    — never removes the maze's structural BACKGROUND boundary walls.
    """
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