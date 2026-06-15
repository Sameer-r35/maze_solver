"""
main.py
=======
Application entry point. Manages the top-level state machine that
routes between screens.

States:
    STATE_MENU      — landing page (MenuScreen)
    STATE_PLAY      — maze solver (Visualizer)
    STATE_ANALYTICS — analytics dashboard (AnalyticsScreen)
    STATE_TUTORIAL  — how to play (TutorialScreen)

The Visualizer and grid are created lazily on first entry to STATE_PLAY
so the menu loads instantly without waiting for maze generation.
"""

import sys
import pygame

from config     import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_ROWS, GRID_COLS
from generator  import generate_maze
from renderer   import Renderer
from visualizer import Visualizer
from menu       import MenuScreen
from analytics  import AnalyticsScreen
from tutorial   import TutorialScreen

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
    menu_screen     = MenuScreen()
    tutorial_screen = TutorialScreen()

    # Visualizer is created lazily — only when Play is first clicked.
    # This keeps the menu instant on startup.
    renderer         = None
    visualizer       = None
    analytics_screen = None

    # Tracks the grid currently loaded in the solver.
    # Analytics uses this so it analyses the same maze the user just solved.
    # None means the user has not played yet — analytics will generate a fresh maze.
    current_grid = [None]   # list so nested functions can rebind it

    def _init_play():
        """Create (or re-enter) the solver screen with a fresh maze."""
        nonlocal renderer, visualizer
        if visualizer is None:
            renderer            = Renderer()
            current_grid[0]     = generate_maze(GRID_ROWS, GRID_COLS)
            visualizer          = Visualizer(screen, renderer, current_grid[0])

            def on_generate():
                current_grid[0] = generate_maze(GRID_ROWS, GRID_COLS)
                visualizer.set_grid(current_grid[0])

            visualizer.on_generate = on_generate

    def _init_analytics():
        """Create a fresh AnalyticsScreen using the solver grid if available."""
        nonlocal analytics_screen
        fresh = False
        if current_grid[0] is None:
            # User skipped Play — generate a maze silently and flag it
            current_grid[0] = generate_maze(GRID_ROWS, GRID_COLS)
            fresh = True
        analytics_screen = AnalyticsScreen(screen, current_grid[0], fresh_maze=fresh)

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
                if current_state in (STATE_PLAY, STATE_ANALYTICS, STATE_TUTORIAL):
                    if current_state == STATE_TUTORIAL:
                        tutorial_screen.current_step = 0  # Reset progress on sudden exit
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
                _init_analytics()
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
            nav = analytics_screen.handle_events(events)
            analytics_screen.draw()
            if nav == "MENU":
                current_state = STATE_MENU

        elif current_state == STATE_TUTORIAL:
            nav = tutorial_screen.handle_events(events)
            tutorial_screen.draw(screen)
            pygame.display.flip()
            
            if nav == "MENU":
                tutorial_screen.current_step = 0  # Reset tutorial index back to slide 1
                current_state = STATE_MENU

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()