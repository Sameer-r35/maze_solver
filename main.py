import sys
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_ROWS, GRID_COLS
from generator import generate_maze
from renderer import Renderer

def main():
    # 1. Initialize Pygame modules
    pygame.init()
    
    # 2. Set up screen viewport
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Procedural Maze & Multi-Terrain Visualizer")
    
    # 3. Create clock to control framerate
    clock = pygame.time.Clock()
    
    # 4. Initialize Renderer and generate the initial maze grid
    renderer = Renderer()
    grid = generate_maze(GRID_ROWS, GRID_COLS)
    
    # 5. Core Game Loop
    running = True
    while running:
        # Tick at a stable 30 frames per second (very low CPU usage)
        clock.tick(30)
        
        # Handle interaction and system events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Regenerate a new randomized multi-terrain maze on demand!
                    grid = generate_maze(GRID_ROWS, GRID_COLS)
                    
        # 6. Render the entire scene
        renderer.render(screen, grid)
        
    # Clean up and exit cleanly
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()