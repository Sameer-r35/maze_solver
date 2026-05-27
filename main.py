import sys
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_ROWS, GRID_COLS
from generator import generate_maze
from renderer import Renderer
from visualizer import Visualizer


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Maze Solver")
    clock = pygame.time.Clock()

    renderer   = Renderer()
    grid       = generate_maze(GRID_ROWS, GRID_COLS)
    visualizer = Visualizer(screen, renderer, grid)

    def on_generate():
        new_grid = generate_maze(GRID_ROWS, GRID_COLS)
        visualizer.set_grid(new_grid)

    visualizer.on_generate = on_generate

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                visualizer.handle_event(event)
        visualizer.update()
        visualizer.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()