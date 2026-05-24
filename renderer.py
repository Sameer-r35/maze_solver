import pygame
from config import (
    COLORS, CELL_SIZE, X_OFFSET, Y_OFFSET, GRID_ROWS, GRID_COLS,
    SIDEBAR_WIDTH, GRID_VIEWPORT_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BG, SIDEBAR_BORDER, TEXT_COLOR, TEXT_MUTED,
    GOLD_COLOR, GOLD_BORDER,
    PLAIN, MUD, WATER, WALL, BACKGROUND, START, END
)

class Renderer:
    def __init__(self):
        """Initializes the renderer and pre-caches the system fonts for high performance."""
        pygame.font.init()
        # Choose Segoe UI, Arial, or default system font for premium sans-serif typography
        self.title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.section_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.label_font = pygame.font.SysFont("Segoe UI", 12, bold=False)
        self.bold_label_font = pygame.font.SysFont("Segoe UI", 12, bold=True)

    def draw_grid(self, screen, grid):
        """
        Draws the grid terrain cells and coins.
        Renders with a 1px gap to reveal the background, creating crisp borders.
        """
        # Render each cell in the grid
        for r in range(grid.rows):
            for c in range(grid.cols):
                terrain_type = grid.get_cell(r, c)
                hex_color = COLORS.get(terrain_type, "#000000")
                color = pygame.Color(hex_color)

                x = X_OFFSET + c * CELL_SIZE
                y = Y_OFFSET + r * CELL_SIZE

                # Cell rectangle leaving a 1px gap for high-quality grid aesthetics
                rect = pygame.Rect(x, y, CELL_SIZE - 1, CELL_SIZE - 1)
                pygame.draw.rect(screen, color, rect)

                # Render coin if present in cell (placed inside path-type cells)
                if (r, c) in grid.coins:
                    center_x = x + CELL_SIZE // 2
                    center_y = y + CELL_SIZE // 2
                    radius = CELL_SIZE // 4
                    
                    # Double-layered circle for the gold coin (inner gold, outer deep amber)
                    pygame.draw.circle(screen, pygame.Color(GOLD_BORDER), (center_x, center_y), radius + 1)
                    pygame.draw.circle(screen, pygame.Color(GOLD_COLOR), (center_x, center_y), radius)

    def draw_sidebar(self, screen):
        """
        Draws the sidebar layout containing titles, terrain swatches, travel costs,
        and keyboard control legends in a sleek, dark aesthetic.
        """
        # 1. Sidebar Background Panel
        sidebar_rect = pygame.Rect(GRID_VIEWPORT_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, pygame.Color(SIDEBAR_BG), sidebar_rect)

        # 2. Left vertical border to separate viewport and sidebar
        pygame.draw.line(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (GRID_VIEWPORT_WIDTH, 0),
            (GRID_VIEWPORT_WIDTH, SCREEN_HEIGHT),
            2
        )

        # Draw sidebar padding coordinates
        start_x = GRID_VIEWPORT_WIDTH + 20

        # 3. Main Header
        title_surf = self.title_font.render("MAZE SOLVER", True, pygame.Color(TEXT_COLOR))
        screen.blit(title_surf, (start_x, 25))

        # Thin accent line under title
        pygame.draw.line(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (start_x, 62),
            (GRID_VIEWPORT_WIDTH + SIDEBAR_WIDTH - 20, 62),
            1
        )

        # 4. Section: Terrain Costs Legend
        section_y = 78
        terrain_title = self.section_font.render("TERRAIN COSTS", True, pygame.Color(TEXT_MUTED))
        screen.blit(terrain_title, (start_x, section_y))

        # List of terrains to display
        terrains = [
            (PLAIN, "Plain", "1"),
            (MUD, "Mud", "5"),
            (WATER, "Water", "10"),
            (WALL, "Wall", "inf"),
            (START, "Start", "0"),
            (END, "End", "0")
        ]

        swatch_start_y = 105
        swatch_height = 18
        swatch_width = 18
        spacing_y = 28

        for idx, (terrain_type, name, cost) in enumerate(terrains):
            current_y = swatch_start_y + idx * spacing_y
            
            # Swatch rectangle with neat border
            swatch_rect = pygame.Rect(start_x, current_y, swatch_width, swatch_height)
            pygame.draw.rect(screen, pygame.Color(COLORS[terrain_type]), swatch_rect)
            pygame.draw.rect(screen, pygame.Color(SIDEBAR_BORDER), swatch_rect, 1)

            # Label name
            name_surf = self.label_font.render(name, True, pygame.Color(TEXT_COLOR))
            screen.blit(name_surf, (start_x + 28, current_y + 1))

            # Cost value highlighted in bold
            cost_text = f"Cost: {cost}"
            cost_surf = self.bold_label_font.render(cost_text, True, pygame.Color(TEXT_MUTED))
            screen.blit(cost_surf, (start_x + 105, current_y + 1))

        # 5. Collectibles Legend
        collect_y = swatch_start_y + len(terrains) * spacing_y + 8
        
        # Draw Gold Coin icon in the sidebar
        coin_center_x = start_x + 9
        coin_center_y = collect_y + 9
        coin_radius = 5
        pygame.draw.circle(screen, pygame.Color(GOLD_BORDER), (coin_center_x, coin_center_y), coin_radius + 1)
        pygame.draw.circle(screen, pygame.Color(GOLD_COLOR), (coin_center_x, coin_center_y), coin_radius)

        coin_label = self.label_font.render("Coin (Bonus)", True, pygame.Color(TEXT_COLOR))
        screen.blit(coin_label, (start_x + 28, collect_y + 2))

        # 6. Controls Section
        controls_y = 395
        pygame.draw.line(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (start_x, controls_y - 12),
            (GRID_VIEWPORT_WIDTH + SIDEBAR_WIDTH - 20, controls_y - 12),
            1
        )

        controls_title = self.section_font.render("KEYBOARD ACTION", True, pygame.Color(TEXT_MUTED))
        screen.blit(controls_title, (start_x, controls_y))

        # R: Regenerate
        r_key_surf = self.bold_label_font.render("[R]", True, pygame.Color(COLORS[START]))
        r_desc_surf = self.label_font.render("Generate New Maze", True, pygame.Color(TEXT_COLOR))
        screen.blit(r_key_surf, (start_x, controls_y + 26))
        screen.blit(r_desc_surf, (start_x + 30, controls_y + 26))

        # ESC: Exit
        esc_key_surf = self.bold_label_font.render("[ESC]", True, pygame.Color(TEXT_MUTED))
        esc_desc_surf = self.label_font.render("Exit Program", True, pygame.Color(TEXT_COLOR))
        screen.blit(esc_key_surf, (start_x, controls_y + 52))
        screen.blit(esc_desc_surf, (start_x + 40, controls_y + 52))

    def render(self, screen, grid):
        """Draws the entire scene (grid + sidebar)."""
        screen.fill(pygame.Color(BG_COLOR))
        self.draw_grid(screen, grid)
        self.draw_sidebar(screen)
        pygame.display.flip()
