from config import PLAIN, MUD, WATER, WALL, BACKGROUND, START, END, COSTS

class Grid:
    def __init__(self, rows, cols):
        """
        Initializes a Grid of dimensions rows x cols.
        By default, the entire grid is initialized to BACKGROUND terrain.
        """
        self.rows = rows
        self.cols = cols
        self.grid = [[BACKGROUND for _ in range(cols)] for _ in range(rows)]
        self.coins = set()
        self.reset_search()

    def set_cell(self, row, col, terrain_type):
        """Sets the terrain type of the cell at (row, col)."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = terrain_type

    def get_cell(self, row, col):
        """Gets the terrain type of the cell at (row, col). Returns BACKGROUND if out of bounds."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return BACKGROUND

    def get_cost(self, row, col):
        """Returns the cost of traversing the cell at (row, col)."""
        cell_type = self.get_cell(row, col)
        return COSTS.get(cell_type, float('inf'))

    def get_neighbors(self, row, col):
        """
        Returns the 4-way neighbors (up, down, left, right) of a given cell.
        Only returns coordinate tuples (r, c) that are within the grid bounds.
        """
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def reset_search(self):
        """
        Resets any transient search state such as visited matrices, path parent pointers,
        and distance scores for pathfinding algorithms.
        """
        self.visited = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.parent = {}
        self.g_score = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
        self.f_score = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]

    def add_coin(self, row, col):
        """Adds a coin at the specified coordinate tuple (row, col)."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.coins.add((row, col))

    def remove_coin(self, row, col):
        """Removes a coin from the specified coordinate tuple (row, col) if present."""
        self.coins.discard((row, col))

    def get_coins_in_path(self, path):
        """
        Computes how many coins lie along a given traversal path.
        The path is represented as a list of (row, col) coordinate tuples.
        """
        if not path:
            return 0
        return sum(1 for cell in path if cell in self.coins)
