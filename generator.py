import random
from config import PLAIN, MUD, WATER, WALL, BACKGROUND, START, END
from grid import Grid

def generate_maze(rows, cols):
    """
    Generates a maze using the randomized recursive backtracking algorithm.
    Automatically places START at (1, 1) and END at (rows - 2, cols - 2).
    Distributes MUD and WATER terrain randomly, and scatters coins.
    """
    # 1. Initialize a grid of walls
    grid = Grid(rows, cols)

    # 2. Carve pathways starting from (1, 1)
    stack = [(1, 1)]
    grid.set_cell(1, 1, PLAIN)
    visited = {(1, 1)}

    while stack:
        r, c = stack[-1]
        
        # Look for unvisited neighbors 2 steps away
        neighbors = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            # Must remain within grid boundaries, leaving a outer wall boundary
            if 0 < nr < rows - 1 and 0 < nc < cols - 1:
                if (nr, nc) not in visited:
                    neighbors.append((nr, nc))
        
        if neighbors:
            # Choose a random unvisited neighbor
            nr, nc = random.choice(neighbors)
            
            # Carve through the wall cell between current and neighbor
            wall_r = r + (nr - r) // 2
            wall_c = c + (nc - c) // 2
            
            grid.set_cell(wall_r, wall_c, PLAIN)
            grid.set_cell(nr, nc, PLAIN)
            
            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            # Backtrack
            stack.pop()

    # 3. Randomly distribute MUD and WATER to the carved pathways
    # We skip (1, 1) and (rows - 2, cols - 2) so they don't get overwritten yet
    start_pos = (1, 1)
    end_pos = (rows - 2, cols - 2)
    
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) == PLAIN and (r, c) != start_pos and (r, c) != end_pos:
                rand = random.random()
                if rand < 0.06:  # 6% chance of placing an internal blocker Wall
                    grid.set_cell(r, c, WALL)
                elif rand < 0.18:  # 12% chance of Mud (0.06 to 0.18)
                    grid.set_cell(r, c, MUD)
                elif rand < 0.26:  # 8% chance of Water (0.18 to 0.26)
                    grid.set_cell(r, c, WATER)

    # 4. Scatter coins on a small percentage of path cells
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid.get_cell(r, c) in [PLAIN, MUD, WATER] and (r, c) != start_pos and (r, c) != end_pos:
                if random.random() < 0.08:  # 8% chance of coin placement
                    grid.add_coin(r, c)

    # 5. Place START and END
    grid.set_cell(start_pos[0], start_pos[1], START)
    grid.set_cell(end_pos[0], end_pos[1], END)

    return grid