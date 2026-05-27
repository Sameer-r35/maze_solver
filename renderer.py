import pygame
from config import (
    COLORS, CELL_SIZE, X_OFFSET, Y_OFFSET,
    SIDEBAR_WIDTH, GRID_VIEWPORT_X, SCREEN_HEIGHT,
    BG_COLOR, SIDEBAR_BG, SIDEBAR_BORDER,
    GOLD_COLOR, GOLD_BORDER,
    START, END,
)


class Renderer:
    def __init__(self):
        pygame.font.init()

    def draw_grid(self, screen, grid):
        """Draws terrain cells and coins. 1px gap between cells for crisp borders."""
        for r in range(grid.rows):
            for c in range(grid.cols):
                terrain_type = grid.get_cell(r, c)
                color = pygame.Color(COLORS.get(terrain_type, "#000000"))
                x = X_OFFSET + c * CELL_SIZE
                y = Y_OFFSET + r * CELL_SIZE
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE - 1, CELL_SIZE - 1))

                if (r, c) in grid.coins:
                    cx = x + CELL_SIZE // 2
                    cy = y + CELL_SIZE // 2
                    r2 = CELL_SIZE // 4
                    pygame.draw.circle(screen, pygame.Color(GOLD_BORDER), (cx, cy), r2 + 1)
                    pygame.draw.circle(screen, pygame.Color(GOLD_COLOR),  (cx, cy), r2)

    def draw_sidebar_background(self, screen):
        """Draws the sidebar panel background and right border. No content."""
        pygame.draw.rect(
            screen,
            pygame.Color(SIDEBAR_BG),
            (0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        )
        pygame.draw.line(
            screen,
            pygame.Color(SIDEBAR_BORDER),
            (SIDEBAR_WIDTH, 0),
            (SIDEBAR_WIDTH, SCREEN_HEIGHT),
            2
        )

    def render(self, screen, grid):
        """Full scene draw — background, sidebar, grid. Called by visualizer."""
        screen.fill(pygame.Color(BG_COLOR))
        self.draw_sidebar_background(screen)
        self.draw_grid(screen, grid)
        pygame.display.flip()