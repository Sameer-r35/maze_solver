"""
main.py
=======
Application entry point. Manages the top-level state machine that
routes between screens.

States:
    STATE_MENU      — landing page (MenuScreen)
    STATE_PLAY      — maze solver (Visualizer)
    STATE_ANALYTICS — analytics dashboard (placeholder for now)
    STATE_TUTORIAL  — how to play (placeholder for now)

The Visualizer and grid are created lazily on first entry to STATE_PLAY
so the menu loads instantly without waiting for maze generation.
"""

import sys
import pygame

from config    import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_ROWS, GRID_COLS
from generator import generate_maze
from renderer  import Renderer
from visualizer import Visualizer
from menu      import MenuScreen

# ------------------------------------------------------------------ #
# Application states
# ------------------------------------------------------------------ #
STATE_MENU      = "MENU"
STATE_PLAY      = "PLAY"
STATE_ANALYTICS = "ANALYTICS"
STATE_TUTORIAL  = "TUTORIAL"


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Maze Solver")
    clock = pygame.time.Clock()

    # ---- Screen objects -------------------------------------------- #
    menu_screen = MenuScreen()

    # Visualizer is created lazily — only when Play is first clicked.
    # This keeps the menu instant on startup.
    renderer   = None
    visualizer = None

    def _init_play():
        """Create (or re-enter) the solver screen with a fresh maze."""
        nonlocal renderer, visualizer
        if visualizer is None:
            renderer   = Renderer()
            grid       = generate_maze(GRID_ROWS, GRID_COLS)
            visualizer = Visualizer(screen, renderer, grid)

            def on_generate():
                new_grid = generate_maze(GRID_ROWS, GRID_COLS)
                visualizer.set_grid(new_grid)

            visualizer.on_generate = on_generate

    # ---- State ----------------------------------------------------- #
    current_state = STATE_MENU

    # ================================================================ #
    # MAIN LOOP
    # ================================================================ #
    running = True
    while running:
        clock.tick(60)

        # Collect all events once per frame
        events = pygame.event.get()

        # Global quit — works from any screen
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if current_state == STATE_PLAY:
                    # ESC from solver → back to menu (not quit)
                    current_state = STATE_MENU
                else:
                    running = False

        if not running:
            break

        # ---- TRAFFIC DIRECTOR -------------------------------------- #

        if current_state == STATE_MENU:
            menu_screen.update()
            nav = menu_screen.handle_events(events)
            menu_screen.draw(screen)

            if nav == "PLAY":
                _init_play()
                current_state = STATE_PLAY

            elif nav == "ANALYTICS":
                current_state = STATE_ANALYTICS

            elif nav == "TUTORIAL":
                current_state = STATE_TUTORIAL

        elif current_state == STATE_PLAY:
            for event in events:
                visualizer.handle_event(event)

            # Visualizer sets this flag when "Main Menu" is clicked
            if getattr(visualizer, "wants_main_menu", False):
                visualizer.wants_main_menu = False
                current_state = STATE_MENU
            else:
                visualizer.update()
                visualizer.draw()

        elif current_state == STATE_ANALYTICS:
            # Placeholder — analytics screen will be built next
            screen.fill(pygame.Color("#181822"))
            font = pygame.font.SysFont("Segoe UI", 28)
            msg  = font.render("Analytics — coming soon.  Press ESC to go back.", True, pygame.Color("#94A3B8"))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                               SCREEN_HEIGHT // 2 - msg.get_height() // 2))
            pygame.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU

        elif current_state == STATE_TUTORIAL:
            # Placeholder — tutorial screen will be built next
            screen.fill(pygame.Color("#181822"))
            font = pygame.font.SysFont("Segoe UI", 28)
            msg  = font.render("How to Play — coming soon.  Press ESC to go back.", True, pygame.Color("#94A3B8"))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                               SCREEN_HEIGHT // 2 - msg.get_height() // 2))
            pygame.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()