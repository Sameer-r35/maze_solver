# Configuration constants for Maze Solver

# Terrain types
PLAIN      = "PLAIN"
MUD        = "MUD"
WATER      = "WATER"
WALL       = "WALL"
BACKGROUND = "BACKGROUND"
START      = "START"
END        = "END"

# Costs associated with each terrain
COSTS = {
    PLAIN:      1,
    MUD:        5,
    WATER:      10,
    WALL:       float('inf'),
    BACKGROUND: float('inf'),
    START:      0,
    END:        0,
}

# Hex color definitions
COLORS = {
    PLAIN:      "#F5F0E8",
    MUD:        "#8B5E3C",
    WATER:      "#4A90D9",
    WALL:       "#9EA2AE",
    BACKGROUND: "#181822",
    START:      "#EF4444",
    END:        "#22C55E",
}

# Window dimensions
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

# Sidebar on the LEFT
SIDEBAR_WIDTH        = 220
GRID_VIEWPORT_X      = SIDEBAR_WIDTH
GRID_VIEWPORT_WIDTH  = SCREEN_WIDTH - SIDEBAR_WIDTH
GRID_VIEWPORT_HEIGHT = SCREEN_HEIGHT

# Grid dimensions — odd numbers required for recursive backtracking
CELL_SIZE = 18
GRID_COLS = (GRID_VIEWPORT_WIDTH  // CELL_SIZE)
GRID_ROWS = (GRID_VIEWPORT_HEIGHT // CELL_SIZE)

# Force odd dimensions
if GRID_COLS % 2 == 0:
    GRID_COLS -= 1
if GRID_ROWS % 2 == 0:
    GRID_ROWS -= 1

# Center the grid inside the viewport
X_OFFSET = GRID_VIEWPORT_X + (GRID_VIEWPORT_WIDTH  - GRID_COLS * CELL_SIZE) // 2
Y_OFFSET =                    (GRID_VIEWPORT_HEIGHT - GRID_ROWS * CELL_SIZE) // 2

# Theme colors
BG_COLOR       = "#181822"
SIDEBAR_BG     = "#212126"
SIDEBAR_BORDER = "#32323E"
TEXT_COLOR     = "#E2E8F0"
TEXT_MUTED     = "#94A3B8"
GOLD_COLOR     = "#FCD34D"
GOLD_BORDER    = "#B45309"