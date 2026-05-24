# Configuration constants for Maze Solver

# Terrain types
PLAIN = "PLAIN"
MUD = "MUD"
WATER = "WATER"
WALL = "WALL"
BACKGROUND = "BACKGROUND"
START = "START"
END = "END"

# Costs associated with each terrain
COSTS = {
    PLAIN: 1,
    MUD: 5,
    WATER: 10,
    WALL: float('inf'),
    BACKGROUND: float('inf'),
    START: 0,
    END: 0
}

# Hex color definitions
COLORS = {
    PLAIN: "#F5F0E8",   # Beige
    MUD: "#8B5E3C",     # Dark Brown
    WATER: "#4A90D9",   # Blue
    WALL: "#9EA2AE",    # Sleek Slate-Gray (standing out from background)
    BACKGROUND: "#181822",  # Dark background cell color
    START: "#EF4444",   # Red
    END: "#22C55E"      # Green
}

# Window and layout dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SIDEBAR_WIDTH = 200
GRID_VIEWPORT_WIDTH = 800
GRID_VIEWPORT_HEIGHT = 600

# Grid dimensions (odd numbers for symmetric recursive backtracking corridors)
GRID_ROWS = 29
GRID_COLS = 39
CELL_SIZE = 20

# Offset coordinates to center the grid inside the 800x600 viewport
X_OFFSET = (GRID_VIEWPORT_WIDTH - (GRID_COLS * CELL_SIZE)) // 2
Y_OFFSET = (GRID_VIEWPORT_HEIGHT - (GRID_ROWS * CELL_SIZE)) // 2

# Theme colors
BG_COLOR = "#181822"          # Deep obsidian black for high contrast
SIDEBAR_BG = "#212126"        # Premium slightly lighter charcoal for sidebar
SIDEBAR_BORDER = "#32323E"    # Elegant separator border color
TEXT_COLOR = "#E2E8F0"        # Crisp readable off-white
TEXT_MUTED = "#94A3B8"        # Modern cool-gray for hints/subtitles
GOLD_COLOR = "#FCD34D"        # Sparkling gold for coins
GOLD_BORDER = "#B45309"       # Deep amber border for coin highlights
